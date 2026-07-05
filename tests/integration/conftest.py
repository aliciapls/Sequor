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


@pytest.fixture(autouse=True)
async def _clean_db():
    """Ensure the schema exists and every data table is empty before each test."""
    engine = get_engine()
    # Idempotent: creates tables + pgvector extension if missing.
    await init_db()
    async with engine.begin() as conn:
        # Drop any per-tenant schemas left by prior signup tests. The signup flow
        # provisions a `tenant_<uuid>` schema per tenant; Base.metadata.drop_all
        # only touches `public`, so these accumulate and their columns pin shared
        # enum types (ownership_type), breaking a later drop_all(). CASCADE clears
        # them fully. (These schemas are the isolation mechanism A2/RLS replaces.)
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
