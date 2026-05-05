"""Unit tests for sequor.db.audit — audit trail helper.

Verifies that the audit() function correctly creates AuditEntry
records with all required fields.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from sequor.db.audit import audit
from sequor.db.models import AuditEntry, DoerType, RecipientType


class FakeSession:
    """Minimal async session mock that tracks added objects."""

    def __init__(self):
        self.added: list = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass


@pytest.fixture
def session():
    return FakeSession()


def _make_uuid():
    return uuid.uuid4()


class TestAudit:
    async def test_creates_audit_entry_with_required_fields(self, session):
        tenant_id = _make_uuid()
        doer_id = _make_uuid()
        recipient_id = _make_uuid()

        entry = await audit(
            session,
            tenant_id=tenant_id,
            action="message.classified",
            doer_type="ai_agent",
            doer_id=doer_id,
            recipient_type="contact",
            recipient_id=recipient_id,
        )

        assert isinstance(entry, AuditEntry)
        assert entry.tenant_id == tenant_id
        assert entry.action_type == "message.classified"
        assert entry.doer_type == "ai_agent"
        assert entry.doer_id == doer_id
        assert entry.recipient_type == "contact"
        assert entry.recipient_id == recipient_id
        assert entry.occurred_at is not None
        assert entry.id is not None

    async def test_audit_entry_added_to_session(self, session):
        await audit(
            session,
            tenant_id=_make_uuid(),
            action="escalation.created",
            doer_type="system",
            doer_id=_make_uuid(),
            recipient_type="backup_contact",
            recipient_id=_make_uuid(),
        )

        assert len(session.added) == 1
        assert isinstance(session.added[0], AuditEntry)

    async def test_optional_message_id(self, session):
        message_id = _make_uuid()
        entry = await audit(
            session,
            tenant_id=_make_uuid(),
            action="message.replied",
            doer_type="backup_contact",
            doer_id=_make_uuid(),
            recipient_type="contact",
            recipient_id=_make_uuid(),
            message_id=message_id,
        )

        assert entry.message_id == message_id

    async def test_optional_metadata(self, session):
        meta = {"category": "routine", "confidence": 0.95}
        entry = await audit(
            session,
            tenant_id=_make_uuid(),
            action="message.classified",
            doer_type="ai_agent",
            doer_id=_make_uuid(),
            recipient_type="contact",
            recipient_id=_make_uuid(),
            metadata=meta,
        )

        assert entry.metadata_ == meta

    async def test_flush_called(self, session):
        flush_count = 0
        original_flush = session.flush

        async def counting_flush():
            nonlocal flush_count
            flush_count += 1
            await original_flush()

        session.flush = counting_flush

        await audit(
            session,
            tenant_id=_make_uuid(),
            action="test.action",
            doer_type="system",
            doer_id=_make_uuid(),
            recipient_type="system",
            recipient_id=_make_uuid(),
        )

        assert flush_count == 1

    async def test_different_actions_distinct(self, session):
        e1 = await audit(
            session,
            tenant_id=_make_uuid(),
            action="escalation.created",
            doer_type="system",
            doer_id=_make_uuid(),
            recipient_type="backup_contact",
            recipient_id=_make_uuid(),
        )
        e2 = await audit(
            session,
            tenant_id=_make_uuid(),
            action="escalation.resolved",
            doer_type="backup_contact",
            doer_id=_make_uuid(),
            recipient_type="contact",
            recipient_id=_make_uuid(),
        )

        assert e1.action_type != e2.action_type
        assert e1.id != e2.id
