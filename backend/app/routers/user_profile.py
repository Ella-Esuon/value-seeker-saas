from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..core.security import get_current_user
from ..core.logging import log_admin_action
from ..database import get_db

router = APIRouter(prefix="/api/me", tags=["profile"])


class ProfileResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_admin: bool
    is_superadmin: bool
    tenant_id: Optional[int]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


def _profile_dict(user: models.User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": user.is_admin,
        "is_superadmin": user.is_superadmin,
        "tenant_id": user.tenant_id,
        "created_at": str(user.created_at) if user.created_at else None,
    }


@router.get("", summary="Get your profile")
def get_profile(current_user: models.User = Depends(get_current_user)):
    return _profile_dict(current_user)


@router.put("", summary="Update your profile (name and email only)")
def update_profile(
    req: ProfileUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.email is not None:
        dup_q = db.query(models.User).filter(
            models.User.email == req.email,
            models.User.id != current_user.id,
        )
        # Scope uniqueness check to the same tenant (or globally for superadmin)
        if current_user.tenant_id is not None:
            dup_q = dup_q.filter(models.User.tenant_id == current_user.tenant_id)
        if dup_q.first():
            raise HTTPException(status_code=400, detail="Email already in use within this group")
        current_user.email = req.email

    if req.full_name is not None:
        current_user.full_name = req.full_name.strip() or None

    db.commit()
    db.refresh(current_user)

    log_admin_action(
        admin_username=current_user.username,
        action="update_profile",
        target=f"user:{current_user.id}",
        tenant_id=current_user.tenant_id,
    )
    return _profile_dict(current_user)
