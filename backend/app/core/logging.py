import json
import logging
from datetime import datetime

_logger = logging.getLogger("value_seeker")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _logger.addHandler(_handler)
_logger.setLevel(logging.INFO)


def log_login_attempt(username: str, group_code: str, success: bool, reason: str = "") -> None:
    _logger.info(json.dumps({
        "event": "login_attempt",
        "username": username,
        "group_code": group_code,
        "success": success,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    }))


def log_admin_action(admin_username: str, action: str, target: str, tenant_id: int | None = None) -> None:
    _logger.info(json.dumps({
        "event": "admin_action",
        "admin": admin_username,
        "action": action,
        "target": target,
        "tenant_id": tenant_id,
        "timestamp": datetime.utcnow().isoformat(),
    }))
