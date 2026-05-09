"""JWT-based operator authentication.

Provides:
- hash_password / verify_password: bcrypt wrappers
- create_access_token: create a signed JWT
- get_current_operator: FastAPI dependency to verify token and return operator info
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from sequor.config import settings

logger = structlog.get_logger()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_access_token(
    operator_data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT token for the operator.

    Args:
        operator_data: dict with keys: operator_id, tenant_id, account_id,
                       name, email, role
    """
    to_encode = dict(operator_data)
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=TOKEN_EXPIRE_HOURS)
    )
    to_encode["exp"] = expire.isoformat()
    to_encode["iat"] = datetime.now(timezone.utc).isoformat()
    to_encode["jti"] = secrets.token_hex(16)

    secret = settings.jwt_secret
    if not secret:
        secret = "dev-secret-change-in-production"
        logger.warning("auth.using_dev_secret")

    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT. Returns the payload or None if invalid."""
    secret = settings.jwt_secret or "dev-secret-change-in-production"
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except JWTError:
        return None


def create_access_token_for_operator(
    operator_id: str,
    tenant_id: str,
    account_id: str,
    name: str,
    email: str,
    role: str = "operator",
) -> str:
    """Convenience: build token data and sign it."""
    return create_access_token({
        "operator_id": operator_id,
        "tenant_id": tenant_id,
        "account_id": account_id,
        "name": name,
        "email": email,
        "role": role,
    })
