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

import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = structlog.get_logger()

from sequor.config import settings
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


def set_tenant_key(key: Optional[bytes]) -> None:
    """Set the tenant encryption key for the current async/task context.

    Pass ``None`` to clear the key (e.g. between tests); ``EncryptedString``
    then fail-closes outside development rather than reading/writing plaintext.
    """
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


def compute_email_blind_index(email: str) -> str:
    """Compute a global blind index for email lookups.

    Uses a key derived from the encryption master key so that login
    can compute the blind index without knowing the tenant key.
    """
    from sequor.config import settings

    if not settings.encryption_master_key:
        raise RuntimeError("ENCRYPTION_MASTER_KEY is not configured")
    import hashlib
    import hmac
    from base64 import b64decode

    master_key = b64decode(settings.encryption_master_key)
    # Derive a fixed global lookup key from the master key
    info = b"sequor-global-email-lookup"
    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=None,
        info=info,
    )
    lookup_key = hkdf.derive(master_key)
    mac = hmac.new(lookup_key, email.lower().strip().encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


# ---------------------------------------------------------------------------
# SQLAlchemy TypeDecorator
# ---------------------------------------------------------------------------

_NONCE_LENGTH = 12  # AES-GCM recommended nonce size


def encrypt_field(tenant_key: bytes, field_name: Optional[str], value: str) -> str:
    """Encrypt *value* to base64(``nonce || ciphertext``) under a per-field key.

    This is the single crypto implementation shared by the ``EncryptedString``
    TypeDecorator (ORM path) AND raw-SQL call sites (e.g. the pgvector learned-
    answer store) so both surfaces produce byte-compatible ciphertext. The
    ``field_name`` MUST match the value the ORM column declares, otherwise the
    HKDF-derived per-field key differs and decryption fails.
    """
    field_key = derive_field_key(tenant_key, field_name or "default")
    nonce = os.urandom(_NONCE_LENGTH)
    aesgcm = AESGCM(field_key)
    ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
    return b64encode(nonce + ciphertext).decode("ascii")


def decrypt_field(tenant_key: bytes, field_name: Optional[str], value: str) -> str:
    """Inverse of :func:`encrypt_field`. Raises on tag mismatch / bad base64."""
    field_key = derive_field_key(tenant_key, field_name or "default")
    raw = b64decode(value)
    nonce = raw[:_NONCE_LENGTH]
    ciphertext = raw[_NONCE_LENGTH:]
    aesgcm = AESGCM(field_key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


class EncryptedString(TypeDecorator):
    """SQLAlchemy type that transparently encrypts/decrypts string values.

    Storage layer sees base64-encoded ``nonce || ciphertext``.
    Requires a tenant key to be set via ``set_tenant_key()`` before any
    bind or result processing involving this column.
    """

    impl = Text
    # cache_ok=True: the type's SQL shape (TEXT impl) is constant, so SQLAlchemy
    # may cache the compiled type expression. Value-level caching is not involved
    # (AES-GCM uses a random nonce, so ciphertext is non-deterministic per write).
    cache_ok = True

    def __init__(self, field_name: Optional[str] = None, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._field_name = field_name

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        """Encrypt *value* before it is sent to the database."""
        if value is None:
            return None

        tenant_key = _current_tenant_key.get()
        if tenant_key is None:
            # Fail-CLOSED outside development: a missing tenant key must NEVER
            # silently write plaintext PII in production. Source from
            # settings.app_env (single config source, .env/env with proper
            # precedence) — NOT a second raw os.environ read that can diverge
            # and default to "development" on a misconfigured deploy.
            if settings.app_env != "development":
                # Per observability Rule 8, schema-revealing field names MUST
                # NOT appear at WARN (log aggregators have broader access than
                # the DB). Emit a hash so operators can grep without leaking the
                # column name.
                field_hash = hashlib.sha256((self._field_name or "default").encode()).hexdigest()[
                    :8
                ]
                logger.warning(
                    "encrypted.fail_closed",
                    op="bind",
                    field_hash=field_hash,
                    app_env=settings.app_env,
                )
                raise RuntimeError(
                    "EncryptedString requires a tenant key. "
                    "Call set_tenant_key() before writing encrypted columns."
                )
            return value  # store plaintext ONLY in development

        return encrypt_field(tenant_key, self._field_name, value)

    def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:
        """Decrypt *value* after it is read from the database."""
        if value is None:
            return None

        tenant_key = _current_tenant_key.get()
        if tenant_key is None:
            # Fail-CLOSED outside development (see process_bind_param). Source
            # from settings.app_env, not a raw os.environ read.
            if settings.app_env != "development":
                field_hash = hashlib.sha256((self._field_name or "default").encode()).hexdigest()[
                    :8
                ]
                logger.warning(
                    "encrypted.fail_closed",
                    op="result",
                    field_hash=field_hash,
                    app_env=settings.app_env,
                )
                raise RuntimeError(
                    "EncryptedString requires a tenant key. "
                    "Call set_tenant_key() before reading encrypted columns."
                )
            return value  # return plaintext as-is ONLY in development

        return decrypt_field(tenant_key, self._field_name, value)
