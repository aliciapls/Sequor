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
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'backup_contacts' AND column_name = 'email_blind_index'
            """)
        )
        if result.fetchone() is None:
            await conn.execute(text(
                "ALTER TABLE backup_contacts ADD COLUMN email_blind_index VARCHAR(64)"
            ))


async def drop_all(*, force: bool = False) -> None:
    if not force:
        raise RuntimeError(
            "drop_all() refused — pass force=True to acknowledge "
            "data loss is irreversible"
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


from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def get_tenant_session(tenant_id):
    """Yield a session with search_path set to the tenant's schema."""
    from sequor.db.schema_manager import tenant_id_to_schema, validate_identifier

    engine = get_engine()
    schema_name = tenant_id_to_schema(tenant_id)
    validate_identifier(schema_name)  # defense-in-depth
    async with AsyncSession(engine) as session:
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))
        yield session
