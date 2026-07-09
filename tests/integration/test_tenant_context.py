"""Tier-2 tests for the tenant-context boundary (shard 1a).

Exercises `set_tenant_context` against real PostgreSQL: it must install the
per-tenant encryption key AND set the transaction-local RLS GUC, and the GUC
must NOT leak past the transaction (the pool-safety invariant RLS relies on).
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.database import get_engine
from sequor.db.encrypted_column import get_tenant_key
from sequor.db.tenant_context import reset_key_manager, set_tenant_context


@pytest.mark.asyncio
async def test_set_tenant_context_installs_key_and_guc():
    """The helper provisions the tenant key and sets app.current_tenant."""
    reset_key_manager()
    tenant_id = uuid.uuid4()
    async with AsyncSession(get_engine()) as session:
        key = await set_tenant_context(session, tenant_id, provision=True)

        # Encryption half: key installed in the context var.
        assert len(key) == 32
        assert get_tenant_key() == key

        # RLS half: GUC readable within the same transaction.
        result = await session.execute(text("SELECT current_setting('app.current_tenant', true)"))
        assert result.scalar() == str(tenant_id)


@pytest.mark.asyncio
async def test_guc_is_transaction_local_not_pool_leaking():
    """The GUC is SET LOCAL — it clears on commit and cannot leak to the next
    checkout of a pooled connection (the invariant RLS isolation depends on)."""
    reset_key_manager()
    tenant_id = uuid.uuid4()
    async with AsyncSession(get_engine()) as session:
        await set_tenant_context(session, tenant_id, provision=True)
        await session.commit()  # transaction ends → SET LOCAL cleared

        # A statement in the NEW (post-commit) transaction must not see it.
        result = await session.execute(text("SELECT current_setting('app.current_tenant', true)"))
        assert result.scalar() in ("", None)


@pytest.mark.asyncio
async def test_load_existing_key_is_stable_across_calls():
    """A second context bind for the same tenant returns the same key (LRU cache
    via the shared KeyManager singleton), not a fresh random key."""
    reset_key_manager()
    tenant_id = uuid.uuid4()
    async with AsyncSession(get_engine()) as session:
        provisioned = await set_tenant_context(session, tenant_id, provision=True)
        await session.commit()
    async with AsyncSession(get_engine()) as session:
        loaded = await set_tenant_context(session, tenant_id, provision=False)
    assert loaded == provisioned
