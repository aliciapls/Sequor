"""
Transparent AES-256-GCM column encryption for PII fields.

Uses a per-tenant key passed via a context variable.  The SQLAlchemy
TypeDecorator encrypts on write (process_bind_param) and decrypts on
read (process_result_value).  Random 12-byte nonce is prepended to
ciphertext and the whole blob is base64-encoded into a TEXT column.

Blind indexes (HMAC-SHA256) let callers do equality lookups on
encrypted data without decrypting.
"""

import contextvars
import hashlib
import hmac
import os
from base64 import b64decode, b64encode
from typing import Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from sqlalchemy import String, Text, TypeDecorator

# ---------------------------------------------------------------------------
# Context variable that holds the current tenant's 32-byte key.
# Set this before any DB write/read on encrypted columns.
# ---------------------------------------------------------------------------
_current_tenant_key: contextvars.ContextVar[Optional[bytes]] = contextvars.ContextVar(
    "tenant_key", default=None
)


def set_tenant_key(key: bytes) -> None:
    """Set the tenant encryption key for the current async/task context."""
    _current_tenant_key.set(key)


def get_tenant_key() -> Optional[bytes]:
    """Return the tenant encryption key for the current context, or None."""
    return _current_tenant_key.get()


# ---------------------------------------------------------------------------
# Key derivation & blind indexing
# ---------------------------------------------------------------------------

_INFO_PREFIX = b"sequor-field-key"


def derive_field_key(tenant_key: bytes, field_name: str) -> bytes:
    """Derive a per-field encryption key from the tenant key using HKDF-SHA256.

    Each field gets its own key so that compromising one field's ciphertext
    does not weaken the encryption of other fields encrypted under the same
    tenant key.
    """
    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=None,
        info=_INFO_PREFIX + field_name.encode("utf-8"),
    )
    return hkdf.derive(tenant_key)


def compute_blind_index(tenant_key: bytes, plaintext: str) -> str:
    """Return a hex-encoded HMAC-SHA256 of *plaintext* for equality lookups.

    The HMAC key is derived from the tenant key so that two tenants with
    the same plaintext produce different hashes.
    """
    mac = hmac.new(tenant_key, plaintext.encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


# ---------------------------------------------------------------------------
# SQLAlchemy TypeDecorator
# ---------------------------------------------------------------------------

_NONCE_LENGTH = 12  # AES-GCM recommended nonce size


class EncryptedString(TypeDecorator):
    """SQLAlchemy type that transparently encrypts/decrypts string values.

    Storage layer sees base64-encoded ``nonce || ciphertext``.
    Requires a tenant key to be set via ``set_tenant_key()`` before any
    bind or result processing involving this column.
    """

    impl = Text
    cache_ok = True  # safe to cache because encryption is deterministic per key

    def __init__(self, field_name: Optional[str] = None, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._field_name = field_name

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        """Encrypt *value* before it is sent to the database."""
        if value is None:
            return None

        tenant_key = _current_tenant_key.get()
        if tenant_key is None:
            # Development mode: store plaintext (seed data, no encryption setup)
            # Production: require tenant key for encryption
            import os as _os
            if _os.environ.get("APP_ENV", "development") != "development":
                raise RuntimeError(
                    "EncryptedString requires a tenant key. "
                    "Call set_tenant_key() before writing encrypted columns."
                )
            return value  # store plaintext in development

        field_name = self._field_name or "default"
        field_key = derive_field_key(tenant_key, field_name)

        nonce = os.urandom(_NONCE_LENGTH)
        aesgcm = AESGCM(field_key)
        ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
        return b64encode(nonce + ciphertext).decode("ascii")

    def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:
        """Decrypt *value* after it is read from the database."""
        if value is None:
            return None

        tenant_key = _current_tenant_key.get()
        if tenant_key is None:
            # Development mode: allow plaintext columns (seed data not yet encrypted)
            # Production: require tenant key to decrypt
            import os as _os
            if _os.environ.get("APP_ENV", "development") != "development":
                raise RuntimeError(
                    "EncryptedString requires a tenant key. "
                    "Call set_tenant_key() before reading encrypted columns."
                )
            return value  # return plaintext as-is in development

        field_name = self._field_name or "default"
        field_key = derive_field_key(tenant_key, field_name)

        raw = b64decode(value)
        nonce = raw[:_NONCE_LENGTH]
        ciphertext = raw[_NONCE_LENGTH:]
        aesgcm = AESGCM(field_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
