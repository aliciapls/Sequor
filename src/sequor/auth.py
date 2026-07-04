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

from sequor.config import settings

logger = structlog.get_logger()

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# Minimum acceptable HMAC secret length (bytes). RFC 7518 §3.2 requires the key
# to be at least as long as the HMAC output (HS256 → 32 bytes).
MIN_JWT_SECRET_BYTES = 32

# Dev-only signing secret. NEVER used outside app_env == "development" — the
# fail-closed guard in _signing_secret() raises before this is reached elsewhere.
_DEV_ONLY_SECRET = "sequor-development-only-signing-secret-do-not-use-in-production"


def _signing_secret() -> str:
    """Resolve the JWT signing/verification secret, fail-closed outside dev.

    A world-known constant fallback is an auth-bypass: anyone can forge tokens.
    So outside ``app_env == "development"`` we REFUSE to operate without a real
    ``JWT_SECRET`` rather than silently signing with a predictable key.
    """
    secret = settings.jwt_secret
    if secret:
        if len(secret.encode()) < MIN_JWT_SECRET_BYTES:
            # Set-but-weak: surface loudly, but do not hard-break a running
            # deployment that already has a (short) real secret configured.
            logger.warning(
                "auth.jwt_secret_too_short",
                have_bytes=len(secret.encode()),
                need_bytes=MIN_JWT_SECRET_BYTES,
            )
        return secret
    if settings.app_env == "development":
        logger.warning("auth.using_dev_secret", app_env=settings.app_env)
        return _DEV_ONLY_SECRET
    raise RuntimeError(
        "JWT_SECRET is unset. Refusing to sign or verify tokens with a "
        "predictable fallback outside development (app_env="
        f"{settings.app_env!r}). Set JWT_SECRET to a >=32-byte random secret."
    )


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
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=TOKEN_EXPIRE_HOURS))
    to_encode["exp"] = int(expire.timestamp())
    to_encode["iat"] = int(datetime.now(timezone.utc).timestamp())
    to_encode["jti"] = secrets.token_hex(16)

    return jwt.encode(to_encode, _signing_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT. Returns the payload or None if invalid."""
    try:
        return jwt.decode(token, _signing_secret(), algorithms=[ALGORITHM])
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
    return create_access_token(
        {
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "account_id": account_id,
            "name": name,
            "email": email,
            "role": role,
        }
    )
