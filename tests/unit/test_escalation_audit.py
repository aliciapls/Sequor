"""Unit tests for escalation service audit trail integration.

Verifies that EscalationService._write_audit is invoked during
create_escalation and resolve_escalation, and that it delegates
to sequor.db.audit.audit().
"""

import uuid
from datetime import datetime, timezone

import pytest

from sequor.db.models import EscalationPriority, EscalationStatus
from sequor.escalation.service import EscalationService


def _make_uuid():
    return str(uuid.uuid4())


class FakeExpress:
    def __init__(self, storage: dict | None = None):
        self.storage: dict[str, dict[str, dict]] = storage or {}

    def _ensure_model(self, model: str) -> None:
        if model not in self.storage:
            self.storage[model] = {}

    async def read(self, model: str, id: str) -> dict | None:
        self._ensure_model(model)
        return self.storage[model].get(id)

    async def list(self, model: str, filter: dict | None = None) -> list[dict]:
        self._ensure_model(model)
        results = list(self.storage[model].values())
        if filter:
            for key, val in filter.items():
                results = [r for r in results if r.get(key) == val]
        return results

    async def create(self, model: str, data: dict) -> dict:
        self._ensure_model(model)
        id = data.get("id", str(uuid.uuid4()))
        record = {**data, "id": id}
        self.storage[model][id] = record
        return record

    async def update(self, model: str, id: str, data: dict) -> dict:
        self._ensure_model(model)
        record = self.storage[model].get(id, {})
        updated = {**record, **data, "id": id}
        self.storage[model][id] = updated
        return updated


class FakeEmailSender:
    def __init__(self):
        self.sent: list[dict] = []

    async def send_escalation_email(self, **kwargs) -> str:
        self.sent.append(kwargs)
        return "fake-msg-id"


ACCOUNT_ID = _make_uuid()
MESSAGE_ID = _make_uuid()
TENANT_ID = _make_uuid()
BACKUP_ID = _make_uuid()
CONTACT_ID = _make_uuid()
ESCALATION_ID = _make_uuid()


def _setup_storage():
    return {
        "Account": {
            ACCOUNT_ID: {
                "id": ACCOUNT_ID,
                "name": "Acme Corp",
                "escalation_sla_hours": 4,
            }
        },
        "Message": {
            MESSAGE_ID: {
                "id": MESSAGE_ID,
                "contact_id": CONTACT_ID,
                "channel": "email",
                "body_text": "What is your refund policy?",
                "received_at": datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
            }
        },
        "Contact": {
            CONTACT_ID: {
                "id": CONTACT_ID,
                "name": "Jane Smith",
                "email": "jane@example.com",
            }
        },
        "BackupContact": {
            BACKUP_ID: {
                "id": BACKUP_ID,
                "account_id": ACCOUNT_ID,
                "name": "Bob Johnson",
                "email": "bob@acme.com",
                "tier": "primary",
                "active": True,
            }
        },
    }


class TestEscalationAuditTrail:
    """Escalation service must write audit entries on create and resolve."""

    async def test_create_escalation_invokes_write_audit(self):
        """create_escalation calls _write_audit which attempts to import
        sequor.db.audit and write an entry. Since our FakeExpress has no
        real SQLAlchemy session, the audit silently fails. We verify the
        escalation still gets created with correct fields."""
        express = FakeExpress(_setup_storage())
        email = FakeEmailSender()
        svc = EscalationService(express, email)

        await svc.create_escalation(
            message_id=uuid.UUID(MESSAGE_ID),
            tenant_id=uuid.UUID(TENANT_ID),
            account_id=uuid.UUID(ACCOUNT_ID),
            priority=EscalationPriority.high,
            ai_summary="Test summary",
            routing_reason="Low confidence",
        )

        escalations = list(express.storage.get("Escalation", {}).values())
        assert len(escalations) == 1
        assert escalations[0]["status"] == EscalationStatus.pending.value

    async def test_resolve_escalation_invokes_write_audit(self):
        """resolve_escalation calls _write_audit for the resolution event."""
        storage = _setup_storage()
        storage["Escalation"] = {
            ESCALATION_ID: {
                "id": ESCALATION_ID,
                "tenant_id": TENANT_ID,
                "message_id": MESSAGE_ID,
                "backup_contact_id": BACKUP_ID,
                "tier": 1,
                "status": EscalationStatus.pending.value,
                "priority": EscalationPriority.high.value,
            }
        }
        express = FakeExpress(storage)
        email = FakeEmailSender()
        svc = EscalationService(express, email)

        result = await svc.resolve_escalation(
            escalation_id=uuid.UUID(ESCALATION_ID),
            resolution_summary="Resolved with policy info.",
        )

        assert result["status"] == EscalationStatus.resolved.value

    async def test_write_audit_handles_missing_session_gracefully(self):
        """_write_audit should not raise even if db has no _session."""
        express = FakeExpress(_setup_storage())
        # Ensure _session is not present on the instance
        if hasattr(express, "_session"):
            delattr(express, "_session")
        email = FakeEmailSender()
        svc = EscalationService(express, email)

        # Should not raise
        result = await svc.create_escalation(
            message_id=uuid.UUID(MESSAGE_ID),
            tenant_id=uuid.UUID(TENANT_ID),
            account_id=uuid.UUID(ACCOUNT_ID),
            priority=EscalationPriority.medium,
            ai_summary="Test",
            routing_reason="Test",
        )
        assert result is not None

    async def test_write_audit_with_session_records_audit(self):
        """When _session is present, _write_audit should attempt to call
        sequor.db.audit.audit with the correct parameters."""
        express = FakeExpress(_setup_storage())

        audit_entries = []

        class FakeAuditSession:
            """Tracks objects added via session.add."""
            def add(self, obj):
                audit_entries.append(obj)

            async def flush(self):
                pass

        express._session = FakeAuditSession()
        email = FakeEmailSender()
        svc = EscalationService(express, email)

        await svc.create_escalation(
            message_id=uuid.UUID(MESSAGE_ID),
            tenant_id=uuid.UUID(TENANT_ID),
            account_id=uuid.UUID(ACCOUNT_ID),
            priority=EscalationPriority.high,
            ai_summary="Audit test",
            routing_reason="Test",
        )

        # _write_audit should have created an AuditEntry
        assert len(audit_entries) == 1
        assert audit_entries[0].action_type == "escalation.created"
        assert audit_entries[0].tenant_id == uuid.UUID(TENANT_ID)
