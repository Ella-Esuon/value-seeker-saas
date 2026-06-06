# Backward-compatibility shim — all auth logic lives in backend/app/core/security.py
from .core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    get_current_user,
    get_tenant_id,
    get_current_tenant,
    require_admin,
    require_superadmin,
    require_role,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "get_tenant_id",
    "get_current_tenant",
    "require_admin",
    "require_superadmin",
    "require_role",
]
