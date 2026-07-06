"""Shared integration-test fixtures.

Tier-2 tests run against a real PostgreSQL (pgvector) instance. Unlike Tier-1
unit tests they share a persistent database, so without per-test isolation one
test's rows leak into the next (e.g. a second signup with the same owner email
raises DuplicateEmailError). This autouse fixture gives every integration test a
clean slate by truncating all data tables before it runs — satisfying
`.claude/rules/testing.md` § "Isolated: ... tests MUST NOT affect each other".

Schema (not data) is created once via init_db(); truncation is fast and keeps
the schema in place across tests.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from sequor.db.database import get_engine, init_db
from sequor.db.encrypted_column import set_tenant_key
from sequor.db.tenant_context import reset_key_manager


@pytest.fixture(autouse=True)
async def _reset_tenant_key():
    """Clear the per-tenant encryption state around every integration test.

    Two surfaces, both process-global, both MUST reset or tests contaminate
    each other order-dependently (the Wave-1 holistic redteam found the suite
    was not reproducibly green — flaky failures across 1b/1d/1e/1f tests traced
    to this):

    - ``set_tenant_key(None)`` — the per-tenant AES-key contextvar that
      ``EncryptedString`` reads. pytest-asyncio's per-test loop isolates
      contextvars, but a few tests deliberately set None to assert fail-close;
      this makes the hygiene explicit.
    - ``reset_key_manager()`` — the process-wide ``KeyManager`` singleton
      (``tenant_context._key_manager``) with its LRU per-tenant key cache. Tests
      that swap the master key (fail-close/provisioning assertions) left a
      singleton built against the OLD master key, so a later test's
      ``bind_tenant`` resolved a stale key and decrypted wrong / failed. Only
      ~5 of 12 integration files reset it locally; centralizing it here removes
      the order-dependence.
    """
    set_tenant_key(None)
    reset_key_manager()
    yield
    set_tenant_key(None)
    reset_key_manager()


@pytest.fixture(autouse=True)
async def _clean_db():
    """Ensure the schema exists and every data table is empty before each test."""
    engine = get_engine()
    # Idempotent: creates tables + pgvector extension if missing.
    await init_db()
    async with engine.begin() as conn:
        # Drop any per-tenant schemas left by prior signup tests on this shared
        # PG instance. Shard 1c RETIRED the schema-per-tenant mechanism (signup
        # no longer provisions `tenant_<uuid>` schemas; isolation is now
        # DB-enforced via RLS on the shared schema — see db.rls), but this loop
        # remains as defensive cleanup for schemas created by older test runs
        # before the retirement: Base.metadata.drop_all only touches `public`,
        # so without this they accumulate and their columns pin shared enum
        # types (ownership_type), breaking a later drop_all(). CASCADE clears
        # them fully. A no-op on any 1c-or-later DB.
        tenant_schemas = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name LIKE 'tenant\\_%'"
            )
        )
        for (schema_name,) in tenant_schemas.fetchall():
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

        rows = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = [r[0] for r in rows.fetchall()]
        if tables:
            quoted = ", ".join(f'"{t}"' for t in tables)
            # RESTART IDENTITY resets sequences; CASCADE follows FKs so order
            # doesn't matter. One statement = one round trip.
            await conn.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    yield
