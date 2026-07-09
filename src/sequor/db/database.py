from __future__ import annotations

"""Async database engine and table management."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from sequor.config import settings

_engine: Optional[AsyncEngine] = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")
        _engine = create_async_engine(url, echo=settings.debug)
    return _engine


async def init_db() -> None:
    from sequor.db.base import Base
    from sequor.db.models import (  # noqa: F401 — register all models
        Account,
        AuditEntry,
        BackupContact,
        ChannelConsent,
        Classification,
        Contact,
        Document,
        DocumentChunk,
        Escalation,
        LearnedAnswer,
        Message,
        RAGRetrieval,
        Response,
        RoutingOutcome,
        Tenant,
    )
    from sequor.db.encryption_keys import TenantEncryptionKey  # noqa: F401 — register table

    engine = get_engine()
    async with engine.begin() as conn:
        from sqlalchemy import text

        # Enable pgvector extension before creating tables
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(Base.metadata.create_all)

        # Migration: add email_blind_index column if missing (backfill for existing accounts)
        result = await conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'backup_contacts' AND column_name = 'email_blind_index'
            """
            )
        )
        if result.fetchone() is None:
            await conn.execute(
                text("ALTER TABLE backup_contacts ADD COLUMN email_blind_index VARCHAR(64)")
            )

        # R7-01 (shard 1e): add accounts.password_hash if missing. create_all is
        # CREATE TABLE IF NOT EXISTS, so it never ALTERs an existing table — a dev
        # test DB created before this column landed would otherwise lack it and every
        # signup INSERT would fail. The Alembic migration
        # (e1d2c3b4a506_separate_owner_login_from_backup_contact) is the prod artifact;
        # this self-heal keeps the create_all test loop green. Mirrors the
        # email_blind_index self-heal above.
        result = await conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'accounts' AND column_name = 'password_hash'
            """
            )
        )
        if result.fetchone() is None:
            await conn.execute(text("ALTER TABLE accounts ADD COLUMN password_hash VARCHAR(255)"))

        # A2 tenant isolation: enable RLS + the tenant_isolation policy on every
        # tenant-scoped table and create the cross-tenant lookup functions
        # (db.rls). Idempotent — safe on every bootstrap. Mirrored by the
        # enable_rls_tenant_isolation Alembic migration for production deploys.
        from sequor.db.rls import apply_rls_and_policies

        await apply_rls_and_policies(conn)


async def drop_all(*, force: bool = False) -> None:
    if not force:
        raise RuntimeError(
            "drop_all() refused — pass force=True to acknowledge " "data loss is irreversible"
        )
    from sequor.db.base import Base
    from sequor.db.models import (  # noqa: F401
        Account,
        AuditEntry,
        BackupContact,
        ChannelConsent,
        Classification,
        Contact,
        Document,
        DocumentChunk,
        Escalation,
        LearnedAnswer,
        Message,
        RAGRetrieval,
        Response,
        RoutingOutcome,
        Tenant,
    )
    from sequor.db.encryption_keys import TenantEncryptionKey  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


# get_tenant_session (per-tenant search_path schema switching) was removed in
# shard 1c — tenant isolation is now DB-enforced via Row-Level Security on the
# shared schema (db.rls), not per-tenant PostgreSQL schemas. The helper had zero
# callers; see DEVIATIONS §A2.
