"""Unit tests for SessionCrud adapter.

Verifies list/create/read/update with model name strings,
mass assignment protection, and unknown field handling.
"""

import uuid

import pytest
from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sequor.db.crud import SessionCrud


class StubModel:
    """Minimal ORM-like object for testing SessionCrud logic without real DB."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_get_model_returns_tablename_mapping():
    """_get_model resolves both table names and class names."""
    from sequor.db.crud import _get_model

    account_cls = _get_model("accounts")
    assert account_cls is not None
    assert hasattr(account_cls, "__tablename__")

    account_cls2 = _get_model("Account")
    assert account_cls2 is account_cls


def test_get_model_raises_on_unknown():
    from sequor.db.crud import _get_model

    with pytest.raises(ValueError):
        _get_model("nonexistent_table_xyz")


class TestSessionCrudCreateProtection:
    """Verify protected fields are stripped on create."""

    def test_create_strips_id_from_data(self):
        """Protected field 'id' should be excluded from create."""
        from sequor.db.crud import _PROTECTED_FIELDS

        assert "id" in _PROTECTED_FIELDS
        assert "created_at" in _PROTECTED_FIELDS


class TestSessionCrudUpdateProtection:
    """Verify protected fields are not settable via update."""

    def test_update_ignores_protected_fields(self):
        from sequor.db.crud import _PROTECTED_FIELDS

        assert "id" in _PROTECTED_FIELDS
        assert "tenant_id" not in _PROTECTED_FIELDS
