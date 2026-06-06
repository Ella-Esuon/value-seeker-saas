from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from ..database import get_db
from .. import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if not username:
            raise exc
    except JWTError:
        raise exc

    tenant_id = payload.get("tid")

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

    if not user or not user.is_active:
        raise exc
    return user


def get_tenant_id(current_user: models.User = Depends(get_current_user)) -> int:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=403, detail="Superadmin has no tenant context")
    return current_user.tenant_id


def get_current_tenant(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.Tenant:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=403, detail="Superadmin has no tenant context")
    tenant = db.query(models.Tenant).filter_by(id=current_user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant not found or inactive")
    return tenant


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_admin and not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_superadmin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user


def require_role(*roles: str):
    def _check(current_user: models.User = Depends(get_current_user)) -> models.User:
        user_roles = {"user"}
        if current_user.is_admin:
            user_roles.add("admin")
        if current_user.is_superadmin:
            user_roles.add("superadmin")
        if not user_roles.intersection(roles):
            raise HTTPException(
                status_code=403,
                detail=f"One of these roles required: {', '.join(roles)}",
            )
        return current_user
    return _check
