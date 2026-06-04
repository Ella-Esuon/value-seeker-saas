from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from .. import models
from ..auth import hash_password, require_superadmin
from ..database import get_db

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class TenantUserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    is_admin: bool = False


def tenant_dict(t: models.Tenant) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "slug": t.slug,
        "is_active": t.is_active,
        "user_count": len(t.users),
        "member_count": len(t.members),
        "created_at": str(t.created_at),
    }


@router.get("/")
def list_tenants(db: Session = Depends(get_db), _=Depends(require_superadmin)):
    tenants = db.query(models.Tenant).order_by(models.Tenant.name).all()
    return [tenant_dict(t) for t in tenants]


@router.post("/", status_code=201)
def create_tenant(data: TenantCreate, db: Session = Depends(get_db), _=Depends(require_superadmin)):
    if db.query(models.Tenant).filter_by(slug=data.slug).first():
        raise HTTPException(400, f"Slug '{data.slug}' is already taken")
    tenant = models.Tenant(name=data.name, slug=data.slug)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return {"id": tenant.id, "name": tenant.name, "slug": tenant.slug, "is_active": tenant.is_active}


@router.put("/{tenant_id}")
def update_tenant(tenant_id: int, data: TenantUpdate, db: Session = Depends(get_db), _=Depends(require_superadmin)):
    tenant = db.query(models.Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    if data.name is not None:
        tenant.name = data.name
    if data.is_active is not None:
        tenant.is_active = data.is_active
    db.commit()
    return {"id": tenant.id, "name": tenant.name, "slug": tenant.slug, "is_active": tenant.is_active}


@router.get("/{tenant_id}/users")
def list_tenant_users(tenant_id: int, db: Session = Depends(get_db), _=Depends(require_superadmin)):
    if not db.query(models.Tenant).filter_by(id=tenant_id).first():
        raise HTTPException(404, "Tenant not found")
    users = db.query(models.User).filter_by(tenant_id=tenant_id).all()
    return [
        {"id": u.id, "username": u.username, "email": u.email,
         "is_admin": u.is_admin, "is_active": u.is_active}
        for u in users
    ]


@router.post("/{tenant_id}/users", status_code=201)
def create_tenant_user(
    tenant_id: int, data: TenantUserCreate,
    db: Session = Depends(get_db), _=Depends(require_superadmin),
):
    if not db.query(models.Tenant).filter_by(id=tenant_id).first():
        raise HTTPException(404, "Tenant not found")
    if db.query(models.User).filter_by(username=data.username, tenant_id=tenant_id).first():
        raise HTTPException(400, "Username already exists in this tenant")
    user = models.User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        is_admin=data.is_admin,
        is_active=True,
        tenant_id=tenant_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "is_admin": user.is_admin}


@router.delete("/{tenant_id}/users/{user_id}")
def delete_tenant_user(
    tenant_id: int, user_id: int,
    db: Session = Depends(get_db), _=Depends(require_superadmin),
):
    user = db.query(models.User).filter_by(id=user_id, tenant_id=tenant_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    db.delete(user)
    db.commit()
    return {"detail": "Deleted"}
