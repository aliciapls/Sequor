"""Lightweight CRUD adapter wrapping AsyncSession for services that use
the db_express pattern (list/create/read/update with model name strings).
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Map model name strings to their ORM classes.
_MODEL_MAP: dict[str, type] = {}

# Fields that must never be set via create/update (mass assignment protection).
_PROTECTED_FIELDS = frozenset({"id", "created_at", "updated_at"})


def _get_model(name: str) -> type:
    if not _MODEL_MAP:
        from sequor.db import models as m

        for attr in dir(m):
            cls = getattr(m, attr)
            if isinstance(cls, type) and hasattr(cls, "__tablename__"):
                _MODEL_MAP[cls.__tablename__] = cls
                _MODEL_MAP[attr] = cls
    if name not in _MODEL_MAP:
        raise ValueError(f"Unknown model: {name}")
    return _MODEL_MAP[name]


class SessionCrud:
    """Provides list/create/read/update over AsyncSession using model name strings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._session_inner = session

    async def bind_tenant(self, tenant_id: Any) -> None:
        """Bind this session to a tenant for encrypted-column access.

        A1 (encryption) + A2 (RLS GUC) both derive from the tenant, so one call
        installs the per-tenant key in the context var ``EncryptedString`` reads
        and sets the ``app.current_tenant`` GUC on the current transaction.
        No-op when ``ENCRYPTION_MASTER_KEY`` is unset (local dev fail-open) per
        ``tenant_context.bind_tenant``.

        Services that receive a ``SessionCrud`` via injection (inbound/escalation/
        digest) call this once the tenant is known — typically right after account
        resolution and before the first encrypted-column write/read.
        """
        from sequor.db.tenant_context import bind_tenant as _bind_tenant

        await _bind_tenant(self._session, tenant_id)

    async def list(self, model_name: str, filters: dict[str, Any] | None = None) -> list[dict]:
        model = _get_model(model_name)
        stmt = select(model)
        if filters:
            for key, value in filters.items():
                col = getattr(model, key, None)
                if col is not None:
                    stmt = stmt.where(col == value)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [_orm_to_dict(row) for row in rows]

    async def create(self, model_name: str, data: dict[str, Any]) -> dict[str, Any]:
        model = _get_model(model_name)
        safe = {k: v for k, v in data.items() if hasattr(model, k) and k not in _PROTECTED_FIELDS}
        unknown = [k for k in data if not hasattr(model, k)]
        if unknown:
            logger.warning("crud.create_unknown_fields", model=model_name, fields=unknown)
        obj = model(**safe)
        self._session.add(obj)
        await self._session.flush()
        return _orm_to_dict(obj)

    async def read(self, model_name: str, record_id: str) -> dict[str, Any] | None:
        model = _get_model(model_name)
        stmt = select(model).where(model.id == uuid.UUID(record_id))
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _orm_to_dict(row) if row else None

    async def update(
        self, model_name: str, record_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        model = _get_model(model_name)
        stmt = select(model).where(model.id == uuid.UUID(record_id))
        result = await self._session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            return None
        for key, value in data.items():
            if key in _PROTECTED_FIELDS:
                continue
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self._session.flush()
        return _orm_to_dict(obj)

    async def raw_execute(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute raw SQL and return rows as plain dicts (column-name keyed).

        Use for projections that MUST bypass ORM materialization — notably
        resolving a tenant/account by a NON-encrypted key when the same row has
        ``EncryptedString`` columns whose ``process_result_value`` would
        fail-close during an ORM load before the tenant key is set (inbound
        webhook account resolution; mirrors ``onboarding.app.auth_login``).
        Read-only by contract. ``sql`` is a literal in the calling service,
        never user input; values are bound via ``params``.
        """
        result = await self._session.execute(text(sql), params or {})
        return [dict(row) for row in result.mappings().all()]


def _orm_to_dict(obj: Any) -> dict[str, Any]:
    """Convert an ORM object to a plain dict."""
    result: dict[str, Any] = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name, None)
        # Enum members expose ``.value``; extract so the dict carries the scalar
        # enum value, not the member. ``getattr``-with-default returns ``val``
        # itself when no ``value`` attribute exists (plain str/int/datetime/None).
        val = getattr(val, "value", val)
        result[col.name] = val
    return result
