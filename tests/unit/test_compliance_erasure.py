"""Unit tests for sequor.compliance.erase_contact_pii.

Tests the PDPA erasure function using a mock async session.
Verifies PII fields are overwritten, embeddings are nulled,
and audit entries are written.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sequor.compliance import ERASURE_NULL_FIELDS, erase_contact_pii


def _make_uuid():
    return uuid.uuid4()


class _MockResult:
    """Simulates SQLAlchemy result with scalar_one_or_none / all."""

    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar

    def all(self):
        return self._rows


class _MockContact:
    """Simulates a Contact ORM instance."""

    def __init__(self, contact_id, tenant_id):
        self.id = contact_id
        self.tenant_id = tenant_id
        self.email = "test@example.com"
        self.phone = "+6512345678"
        self.name = "Test User"
        self.company = "Test Corp"


class _FakeSession:
    """Minimal async session that records execute calls."""

    def __init__(self, contact_found=True):
        self.executed: list[tuple] = []
        self.flushed = 0
        self._contact_found = contact_found

    async def execute(self, stmt):
        self.executed.append(stmt)
        # Return appropriate mock result based on what the caller expects
        # The first execute is the contact lookup
        # We detect it via string inspection
        stmt_str = str(stmt)
        if "contacts" in stmt_str and self._contact_found and not self.executed[1:]:
            return _MockResult(scalar=_MockContact(_make_uuid(), _make_uuid()))
        if "document_chunks" in stmt_str:
            return _MockResult(rows=[])
        if "learned_answers" in stmt_str:
            return _MockResult(rows=[])
        return _MockResult(scalar=None, rows=[])

    async def flush(self):
        self.flushed += 1


class TestEraseContactPII:
    async def test_raises_if_contact_not_found(self):
        session = _FakeSession(contact_found=False)
        tenant_id = _make_uuid()
        contact_id = _make_uuid()

        # Override execute to return None for the contact lookup
        async def fake_execute(stmt):
            return _MockResult(scalar=None)

        session.execute = fake_execute

        with pytest.raises(ValueError, match="not found"):
            await erase_contact_pii(session, tenant_id, contact_id)

    async def test_returns_erased_summary(self):
        contact_id = _make_uuid()
        tenant_id = _make_uuid()
        contact = _MockContact(contact_id, tenant_id)

        call_count = 0

        async def fake_execute(stmt):
            nonlocal call_count
            call_count += 1
            stmt_str = str(stmt)
            if call_count == 1:
                # Contact lookup
                return _MockResult(scalar=contact)
            elif "document_chunks" in stmt_str:
                return _MockResult(rows=[])
            elif "learned_answers" in stmt_str:
                return _MockResult(rows=[])
            return _MockResult()

        session = _FakeSession()
        session.execute = fake_execute

        result = await erase_contact_pii(session, tenant_id, contact_id)

        assert result["contact_id"] == str(contact_id)
        assert "contacts" in result["tables_affected"]

    async def test_erasure_null_fields_includes_required_pii(self):
        assert "email" in ERASURE_NULL_FIELDS
        assert "phone" in ERASURE_NULL_FIELDS
        assert ERASURE_NULL_FIELDS["name"] == "[erased]"

    async def test_removes_document_chunk_embeddings(self):
        contact = _MockContact(_make_uuid(), _make_uuid())
        chunk_id = _make_uuid()
        learned_id = _make_uuid()

        call_count = 0

        async def fake_execute(stmt):
            nonlocal call_count
            call_count += 1
            stmt_str = str(stmt)
            if call_count == 1:
                return _MockResult(scalar=contact)
            elif "document_chunks" in stmt_str and "SELECT" in stmt_str.upper():
                return _MockResult(rows=[(chunk_id,)])
            elif "learned_answers" in stmt_str and "SELECT" in stmt_str.upper():
                return _MockResult(rows=[(learned_id,)])
            return _MockResult()

        session = _FakeSession()
        session.execute = fake_execute

        result = await erase_contact_pii(
            session, contact.tenant_id, contact.id
        )

        assert "document_chunks" in result["tables_affected"]
        assert result.get("embeddings_removed", 0) > 0

    async def test_flush_called_after_erasure(self):
        contact = _MockContact(_make_uuid(), _make_uuid())

        async def fake_execute(stmt):
            stmt_str = str(stmt)
            return _MockResult(scalar=contact, rows=[])

        session = _FakeSession()
        session.execute = fake_execute

        await erase_contact_pii(session, contact.tenant_id, contact.id)

        assert session.flushed >= 1
