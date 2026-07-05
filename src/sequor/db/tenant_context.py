"""Central tenant-context boundary.

A single place that binds a database session to an authenticated tenant by
setting BOTH halves of the multi-tenant security model from the same tenant id:

1. **Encryption (A1):** loads (or provisions) the tenant's AES key and installs
   it in the context var `set_tenant_key()` reads, so `EncryptedString` columns
   encrypt/decrypt under the right per-tenant key.
2. **Row-Level Security (A2):** sets the PostgreSQL GUC `app.current_tenant` on
   the current transaction so a `tenant_isolation` RLS policy can filter rows in
   the database itself (defense-in-depth against a forgotten `WHERE tenant_id`).

Before this helper the key-load was duplicated inline at ~5 call sites, each
constructing its own `KeyManager` (defeating the LRU key cache). The RLS GUC was
set nowhere. Both derive from the authenticated tenant, so one boundary call
sets both.

Transaction scoping: the GUC is set with `is_local = true` (SET LOCAL
semantics) so it is scoped to the CURRENT transaction and cleared on
commit/rollback. This is the pool-safe form — a session-level GUC would leak to
the next checkout of the same pooled connection and let a later request read a
prior tenant's rows. Callers that span multiple transactions on one session MUST
re-establish the context per transaction (RLS-critical paths do so in shard 1c).
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.config import settings

# Imported as modules (not names) so KeyManager / set_tenant_key are resolved via
# attribute lookup at call time — this keeps `@patch("sequor.db.encryption_keys
# .KeyManager")` / `@patch("sequor.db.encrypted_column.set_tenant_key")` effective
# for Tier-1 callers that mock the boundary.
from sequor.db import encrypted_column as _encrypted_column
from sequor.db import encryption_keys as _encryption_keys

logger = structlog.get_logger()

_key_manager: Optional["_encryption_keys.KeyManager"] = None


def get_key_manager() -> "_encryption_keys.KeyManager":
    """Return the process-wide KeyManager singleton (shared LRU key cache).

    Raises ValueError (from KeyManager.__init__) when ENCRYPTION_MASTER_KEY is
    unset or not 32 bytes — callers that must tolerate a missing master key
    (e.g. dev-only paths) MUST guard on `settings.encryption_master_key` before
    calling.
    """
    global _key_manager
    if _key_manager is None:
        _key_manager = _encryption_keys.KeyManager(settings.encryption_master_key)
    return _key_manager


def reset_key_manager() -> None:
    """Drop the cached singleton (tests that swap the master key)."""
    global _key_manager
    _key_manager = None


async def _set_rls_guc(session: AsyncSession, tenant_id: UUID | str) -> None:
    """Set the transaction-local ``app.current_tenant`` GUC (the RLS policy input).

    ``is_local=true`` (SET LOCAL) scopes the GUC to the current transaction so it
    clears on commit/rollback and can never leak to the next checkout of a pooled
    connection — the pool-safety invariant the ``tenant_isolation`` RLS policy
    relies on. Parameterized so the uuid text can't inject.

    Split out of ``set_tenant_context`` so the GUC can be set on its own when the
    per-tenant encryption key is unavailable (dev without a master key): RLS
    enforcement is independent of encryption, so the GUC must be set in BOTH the
    production (key + GUC) and dev (GUC only) branches — otherwise the RLS
    policy hides every tenant-scoped row in dev.
    """
    if isinstance(tenant_id, str):
        tenant_id = UUID(tenant_id)
    await session.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": str(tenant_id)},
    )


async def set_tenant_context(
    session: AsyncSession,
    tenant_id: UUID | str,
    *,
    provision: bool = False,
) -> bytes:
    """Bind *session* to *tenant_id*: install the tenant key AND set the RLS GUC.

    Returns the 32-byte tenant key. With ``provision=True`` a new key is
    generated and stored (signup); otherwise the existing key is loaded (raising
    if the tenant has none). Requires ENCRYPTION_MASTER_KEY to be set.

    ``tenant_id`` may be a ``UUID`` or a string; a string is coerced so callers
    that read the id from an ORM dict (where it round-trips as ``str``) do not
    have to convert at every site. ``None`` and non-string values pass through
    unchanged (the provisioning path tolerates a not-yet-flushed id under mocked
    sessions; production always supplies a real UUID).
    """
    if isinstance(tenant_id, str):
        tenant_id = UUID(tenant_id)
    km = get_key_manager()
    if provision:
        key = await km.provision_tenant_key(session, tenant_id)
    else:
        key = await km.get_tenant_key(session, tenant_id)
    _encrypted_column.set_tenant_key(key)
    # RLS GUC (transaction-local so it never leaks across pooled connections).
    await _set_rls_guc(session, tenant_id)
    return key


async def bind_tenant(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    provision: bool = False,
) -> None:
    """Bind *session* to *tenant_id* for BOTH encryption and RLS.

    The one-liner every write/read path calls.

    - Production (``ENCRYPTION_MASTER_KEY`` set): installs the per-tenant AES key
      AND sets the RLS GUC via ``set_tenant_context``.
    - Dev (no master key): encryption is fail-open per ``EncryptedString``, but
      the RLS GUC is STILL set — without it the ``tenant_isolation`` policy would
      hide every tenant-scoped row. Encryption fail-open does NOT imply RLS
      fail-open; the two are independent and RLS is enforced in dev too.

    If the master key is somehow missing in production, ``EncryptedString``
    fails CLOSED (``app_env != "development"`` raises), never silent plaintext.
    """
    if settings.encryption_master_key:
        await set_tenant_context(session, tenant_id, provision=provision)
    else:
        await _set_rls_guc(session, tenant_id)
