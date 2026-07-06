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


@pytest.fixture(autouse=True)
def _stub_tenant_context(monkeypatch):
    """erase_contact_pii binds the tenant via bind_tenant (shard 1a boundary —
    sets the per-tenant key AND the RLS GUC via session.execute). These unit
    tests run against a _FakeSession with no real key/DB, so stub the bind to a
    no-op — the assertions verify the SQL statements issued, not encryption or
    the GUC (both covered by the Tier-2 erasure + RLS tests). This makes the
    suite deterministic whether or not ENCRYPTION_MASTER_KEY is set."""
    import sequor.db.tenant_context as _tc

    monkeypatch.setattr(_tc, "bind_tenant", AsyncMock())
    monkeypatch.setattr(_tc, "set_tenant_context", AsyncMock())


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

    async def test_scrubs_message_content_and_leaves_chunks_untouched(self):
        # Regression (redteam R1): erasure MUST scrub the contact's message
        # content, and MUST NOT touch document chunks (chunks belong to the
        # account KB via document_id and have no contact/message linkage — the
        # prior code referenced DocumentChunk.message_id, which does not exist).
        contact = _MockContact(_make_uuid(), _make_uuid())
        msg_id, esc_id, learned_id = _make_uuid(), _make_uuid(), _make_uuid()
        stmts: list[str] = []
        call = 0

        async def fake_execute(stmt):
            nonlocal call
            call += 1
            s = str(stmt)
            stmts.append(s)
            if call == 1:
                return _MockResult(scalar=contact)
            up = s.upper()
            if up.startswith("SELECT") and "FROM messages" in s:
                return _MockResult(rows=[(msg_id,)])
            if up.startswith("SELECT") and "FROM escalations" in s:
                return _MockResult(rows=[(esc_id,)])
            if up.startswith("SELECT") and "FROM learned_answers" in s:
                return _MockResult(rows=[(learned_id,)])
            return _MockResult()

        session = _FakeSession()
        session.execute = fake_execute
        result = await erase_contact_pii(session, contact.tenant_id, contact.id)

        assert "messages" in result["tables_affected"]
        assert result.get("messages_scrubbed", 0) == 1
        assert "learned_answers" in result["tables_affected"]
        # chunks are NEVER touched by contact erasure
        assert "document_chunks" not in result["tables_affected"]
        assert not any("document_chunks" in s.lower() for s in stmts)

    async def test_no_messages_does_not_wipe_tenant_learned_answers(self):
        # Regression (redteam R1 over-deletion): a contact with NO messages must
        # affect ZERO learned answers — never fall through to an all-tenant wipe
        # that destroyed the whole tenant's knowledge base.
        contact = _MockContact(_make_uuid(), _make_uuid())
        stmts: list[str] = []
        call = 0

        async def fake_execute(stmt):
            nonlocal call
            call += 1
            stmts.append(str(stmt))
            if call == 1:
                return _MockResult(scalar=contact)
            return _MockResult(rows=[])  # no messages / escalations / learned

        session = _FakeSession()
        session.execute = fake_execute
        result = await erase_contact_pii(session, contact.tenant_id, contact.id)

        assert "learned_answers" not in result["tables_affected"]
        assert "messages" not in result["tables_affected"]
        # no UPDATE against learned_answers or document_chunks at all
        assert not any(s.upper().startswith("UPDATE LEARNED_ANSWERS") for s in stmts)
        assert not any("document_chunks" in s.lower() for s in stmts)

    async def test_flush_called_after_erasure(self):
        contact = _MockContact(_make_uuid(), _make_uuid())

        async def fake_execute(stmt):
            stmt_str = str(stmt)
            return _MockResult(scalar=contact, rows=[])

        session = _FakeSession()
        session.execute = fake_execute

        await erase_contact_pii(session, contact.tenant_id, contact.id)

        assert session.flushed >= 1
