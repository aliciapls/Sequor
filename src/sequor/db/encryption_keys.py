"""Tenant encryption key management.

Each tenant gets a random 32-byte key stored encrypted under the master key
from .env.  The KeyManager caches decrypted tenant keys in-process for fast
access.
"""

import os
from base64 import b64decode, b64encode
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from sequor.db.base import Base

logger = structlog.get_logger()

_MAX_CACHE_SIZE = 1000


class TenantEncryptionKey(Base):
    __tablename__ = "tenant_encryption_keys"

    tenant_id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class KeyManager:
    """Manages per-tenant encryption keys.

    Tenant keys are 32 random bytes, encrypted with the master key from .env
    and stored in the tenant_encryption_keys table. Decrypted keys are cached
    in an LRU cache bounded to _MAX_CACHE_SIZE entries.
    """

    def __init__(self, master_key_b64: str) -> None:
        if not master_key_b64:
            raise ValueError("ENCRYPTION_MASTER_KEY is not set")
        self._master_key: bytes = b64decode(master_key_b64)
        if len(self._master_key) != 32:
            raise ValueError("ENCRYPTION_MASTER_KEY must be 32 bytes (base64-encoded)")
        self._cache: OrderedDict[UUID, bytes] = OrderedDict()

    def generate_tenant_key(self) -> bytes:
        """Generate a new random 32-byte tenant key."""
        return os.urandom(32)

    def encrypt_tenant_key(self, tenant_key: bytes) -> str:
        """Encrypt a tenant key with the master key. Returns base64 string."""
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._master_key)
        ciphertext = aesgcm.encrypt(nonce, tenant_key, None)
        return b64encode(nonce + ciphertext).decode("ascii")

    def decrypt_tenant_key(self, encrypted: str) -> bytes:
        """Decrypt a tenant key from the database. Returns 32 bytes."""
        raw = b64decode(encrypted)
        nonce, ciphertext = raw[:12], raw[12:]
        aesgcm = AESGCM(self._master_key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def _cache_get(self, tenant_id: UUID) -> Optional[bytes]:
        if tenant_id in self._cache:
            self._cache.move_to_end(tenant_id)
            return self._cache[tenant_id]
        return None

    def _cache_put(self, tenant_id: UUID, key: bytes) -> None:
        self._cache[tenant_id] = key
        self._cache.move_to_end(tenant_id)
        while len(self._cache) > _MAX_CACHE_SIZE:
            self._cache.popitem(last=False)

    async def get_tenant_key(self, session: AsyncSession, tenant_id: UUID) -> bytes:
        """Get the decrypted tenant key, using cache when available."""
        cached = self._cache_get(tenant_id)
        if cached is not None:
            return cached

        from sqlalchemy import select

        stmt = select(TenantEncryptionKey).where(
            TenantEncryptionKey.tenant_id == tenant_id
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"No encryption key found for tenant {tenant_id}")

        key = self.decrypt_tenant_key(row.encrypted_key)
        self._cache_put(tenant_id, key)
        return key

    async def provision_tenant_key(self, session: AsyncSession, tenant_id: UUID) -> bytes:
        """Generate and store a new encryption key for a tenant."""
        raw_key = self.generate_tenant_key()
        encrypted = self.encrypt_tenant_key(raw_key)
        record = TenantEncryptionKey(
            tenant_id=tenant_id,
            encrypted_key=encrypted,
            key_version=1,
        )
        session.add(record)
        await session.flush()
        self._cache_put(tenant_id, raw_key)
        logger.info("encryption.key_provisioned", tenant_id=str(tenant_id))
        return raw_key
