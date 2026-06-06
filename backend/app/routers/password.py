import re
import time
from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from .. import models
from ..auth import get_current_user, require_admin
from ..core.config import settings
from ..core.logging import log_admin_action
from ..core.security import create_access_token, decode_token, hash_password, verify_password
from ..database import get_db
from ..services.email_service import email_service

router = APIRouter(prefix="/api/password", tags=["password"])

# In-memory rate limit store: identifier -> list of request timestamps
_reset_attempts: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW_SECS = 3600  # 1 hour
_RATE_MAX_REQUESTS = 3


def _check_rate_limit(identifier: str) -> None:
    now = time.time()
    window = _reset_attempts[identifier]
    window[:] = [t for t in window if now - t < _RATE_WINDOW_SECS]
    if len(window) >= _RATE_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Try again in an hour.",
        )
    window.append(now)


def _validate_password(password: str) -> None:
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("at least one digit")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Password must contain: {', '.join(errors)}",
        )


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class AdminResetRequest(BaseModel):
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str
    group_code: str  # tenant slug or "system" for superadmin


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/change", summary="Change your own password")
def change_password(
    req: ChangePasswordRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_password(req.new_password)

    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if verify_password(req.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="New password must differ from current password")

    current_user.hashed_password = hash_password(req.new_password)
    db.commit()

    log_admin_action(
        admin_username=current_user.username,
        action="change_password",
        target=f"user:{current_user.id}",
        tenant_id=current_user.tenant_id,
    )
    return {"detail": "Password changed successfully"}


@router.post("/admin-reset/{user_id}", summary="Admin resets a user password")
def admin_reset_password(
    user_id: int,
    req: AdminResetRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """
    Admins can only reset passwords for users within their own tenant.
    Superadmins can reset any non-superadmin user.
    """
    _validate_password(req.new_password)

    target = db.query(models.User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_superadmin:
        if target.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Cannot reset password for users outside your tenant")
        if target.is_superadmin:
            raise HTTPException(status_code=403, detail="Cannot reset superadmin password")

    target.hashed_password = hash_password(req.new_password)
    db.commit()

    log_admin_action(
        admin_username=current_user.username,
        action="admin_reset_password",
        target=f"user:{user_id}",
        tenant_id=current_user.tenant_id,
    )
    return {"detail": f"Password for user '{target.username}' has been reset"}


@router.post("/forgot", summary="Request a password reset email")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Sends a time-limited reset link to the user's email.
    Always returns success to prevent user enumeration.
    Rate-limited to 3 requests per hour per email address.
    """
    _check_rate_limit(req.email.lower())

    user: Optional[models.User] = None

    if req.group_code == "system":
        user = db.query(models.User).filter(
            models.User.email == req.email,
            models.User.is_superadmin == True,
            models.User.is_active == True,
        ).first()
    else:
        tenant = db.query(models.Tenant).filter(
            models.Tenant.slug == req.group_code,
            models.Tenant.is_active == True,
        ).first()
        if tenant:
            user = db.query(models.User).filter(
                models.User.email == req.email,
                models.User.tenant_id == tenant.id,
                models.User.is_active == True,
            ).first()

    if user and user.email:
        # Embed last-8-chars of current hash as reuse fingerprint
        token = create_access_token(
            data={
                "sub": user.username,
                "tid": user.tenant_id,
                "purpose": "password_reset",
                "phash": user.hashed_password[-8:],
            },
            expires_delta=timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
        )
        email_service.send_password_reset(user.email, token, user.username)

    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/reset", summary="Reset password using a reset token")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Validates the reset token and sets the new password.
    Token is invalidated after use via password-hash fingerprint.
    """
    try:
        payload = decode_token(req.token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid token")

    username = payload.get("sub")
    tenant_id = payload.get("tid")
    phash_fp = payload.get("phash")

    if not username or not phash_fp:
        raise HTTPException(status_code=400, detail="Invalid token")

    if tenant_id is not None:
        user = db.query(models.User).filter(
            models.User.username == username,
            models.User.tenant_id == tenant_id,
        ).first()
    else:
        user = db.query(models.User).filter(
            models.User.username == username,
            models.User.is_superadmin == True,
        ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if user.hashed_password[-8:] != phash_fp:
        raise HTTPException(status_code=400, detail="Reset token has already been used")

    _validate_password(req.new_password)
    user.hashed_password = hash_password(req.new_password)
    db.commit()

    log_admin_action(
        admin_username=user.username,
        action="reset_password_via_token",
        target=f"user:{user.id}",
        tenant_id=user.tenant_id,
    )
    return {"detail": "Password has been reset successfully. Please log in with your new password."}
