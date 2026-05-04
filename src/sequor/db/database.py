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

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
