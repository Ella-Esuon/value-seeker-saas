from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .. import models
from ..auth import hash_password, verify_password, create_access_token, get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

SUPERADMIN_GROUP_CODE = "system"


class LoginRequest(BaseModel):
    username: str
    password: str
    group_code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    is_admin: bool
    is_superadmin: bool
    tenant_id: int | None
    tenant_name: str | None


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # ── superadmin path ──────────────────────────────────────────────────────
    if req.group_code == SUPERADMIN_GROUP_CODE:
        user = db.query(models.User).filter(
            models.User.username == req.username,
            models.User.is_superadmin == True,
        ).first()
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token({"sub": user.username, "tid": None})
        return TokenResponse(
            access_token=token, token_type="bearer",
            username=user.username, is_admin=False, is_superadmin=True,
            tenant_id=None, tenant_name=None,
        )

    # ── tenant user path ─────────────────────────────────────────────────────
    tenant = db.query(models.Tenant).filter(
        models.Tenant.slug == req.group_code,
        models.Tenant.is_active == True,
    ).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown or inactive group code")

    user = db.query(models.User).filter(
        models.User.username == req.username,
        models.User.tenant_id == tenant.id,
        models.User.is_active == True,
    ).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.username, "tid": tenant.id})
    return TokenResponse(
        access_token=token, token_type="bearer",
        username=user.username, is_admin=user.is_admin, is_superadmin=False,
        tenant_id=tenant.id, tenant_name=tenant.name,
    )


@router.get("/me")
def me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "is_superadmin": current_user.is_superadmin,
        "tenant_id": current_user.tenant_id,
    }
