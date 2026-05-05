"""Unit tests for escalation resolution via inbound email reply.

Tests InboundEmailProcessor._try_resolve_escalation and the full
escalation resolution flow when a reply matches an active escalation.
"""

import uuid
from datetime import datetime, timezone

import pytest

from sequor.db.models import EscalationStatus, MessageChannel, MessageDirection
from sequor.email.inbound import InboundEmailProcessor


def _make_uuid():
    return str(uuid.uuid4())


class FakeExpress:
    """Fake DataFlow express for testing."""

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


class TestEscalationResolutionViaReply:
    """When an inbound email replies to an escalated message, the escalation
    should be automatically resolved."""

    async def test_reply_resolves_pending_escalation(self):
        tenant_id = _make_uuid()
        account_id = _make_uuid()
        parent_id = _make_uuid()
        escalation_id = _make_uuid()
        contact_id = _make_uuid()
        backup_id = _make_uuid()

        storage = {
            "Account": {
                account_id: {
                    "id": account_id,
                    "tenant_id": tenant_id,
                    "email_address": "coverage@acme.com",
                }
            },
            "Contact": {
                contact_id: {
                    "id": contact_id,
                    "tenant_id": tenant_id,
                    "email": "alice@example.com",
                    "name": "Alice",
                }
            },
            "BackupContact": {
                backup_id: {
                    "id": backup_id,
                    "tenant_id": tenant_id,
                    "email": "alice@example.com",
                    "name": "Alice Backup",
                }
            },
            "Message": {
                parent_id: {
                    "id": parent_id,
                    "tenant_id": tenant_id,
                    "external_message_id": "<original@mail>",
                }
            },
            "Escalation": {
                escalation_id: {
                    "id": escalation_id,
                    "tenant_id": tenant_id,
                    "account_id": account_id,
                    "message_id": parent_id,
                    "backup_contact_id": backup_id,
                    "status": EscalationStatus.pending.value,
                    "tier": 1,
                    "priority": "high",
                }
            },
        }
        db = FakeExpress(storage)
        processor = InboundEmailProcessor(db)

        payload = {
            "from": "Alice <alice@example.com>",
            "to": "coverage@acme.com",
            "subject": "Re: Escalation",
            "text": "Here is my reply to resolve this",
            "headers": "Message-ID: <reply@mail>\nIn-Reply-To: <original@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)

        assert result["status"] == "created"
        assert result["escalation_resolved"] is True

        # Verify escalation was updated to resolved
        esc = storage["Escalation"][escalation_id]
        assert esc["status"] == EscalationStatus.resolved.value
        assert esc["resolved_at"] is not None
        assert "reply to resolve" in esc["resolution_summary"]

    async def test_reply_resolves_acknowledged_escalation(self):
        tenant_id = _make_uuid()
        account_id = _make_uuid()
        parent_id = _make_uuid()
        escalation_id = _make_uuid()
        backup_id = _make_uuid()

        storage = {
            "Account": {
                account_id: {
                    "id": account_id,
                    "tenant_id": tenant_id,
                    "email_address": "coverage@acme.com",
                }
            },
            "Contact": {},
            "BackupContact": {
                backup_id: {
                    "id": backup_id,
                    "tenant_id": tenant_id,
                    "email": "bob@example.com",
                    "name": "Bob",
                }
            },
            "Message": {
                parent_id: {
                    "id": parent_id,
                    "tenant_id": tenant_id,
                    "external_message_id": "<parent-msg@mail>",
                }
            },
            "Escalation": {
                escalation_id: {
                    "id": escalation_id,
                    "tenant_id": tenant_id,
                    "account_id": account_id,
                    "message_id": parent_id,
                    "backup_contact_id": backup_id,
                    "status": EscalationStatus.acknowledged.value,
                }
            },
        }
        db = FakeExpress(storage)
        processor = InboundEmailProcessor(db)

        payload = {
            "from": "Bob <bob@example.com>",
            "to": "coverage@acme.com",
            "subject": "Re: Urgent",
            "text": "My response to the escalation",
            "headers": "Message-ID: <reply2@mail>\nIn-Reply-To: <parent-msg@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)

        assert result["escalation_resolved"] is True
        esc = storage["Escalation"][escalation_id]
        assert esc["status"] == EscalationStatus.resolved.value

    async def test_reply_does_not_resolve_already_resolved(self):
        tenant_id = _make_uuid()
        account_id = _make_uuid()
        parent_id = _make_uuid()
        escalation_id = _make_uuid()

        storage = {
            "Account": {
                account_id: {
                    "id": account_id,
                    "tenant_id": tenant_id,
                    "email_address": "coverage@acme.com",
                }
            },
            "Contact": {},
            "Message": {
                parent_id: {
                    "id": parent_id,
                    "tenant_id": tenant_id,
                    "external_message_id": "<resolved-parent@mail>",
                }
            },
            "Escalation": {
                escalation_id: {
                    "id": escalation_id,
                    "tenant_id": tenant_id,
                    "message_id": parent_id,
                    "status": EscalationStatus.resolved.value,
                }
            },
        }
        db = FakeExpress(storage)
        processor = InboundEmailProcessor(db)

        payload = {
            "from": "Carol <carol@example.com>",
            "to": "coverage@acme.com",
            "subject": "Re: Done",
            "text": "Another reply",
            "headers": "Message-ID: <reply3@mail>\nIn-Reply-To: <resolved-parent@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)

        assert result["escalation_resolved"] is False

    async def test_no_escalation_for_non_reply(self):
        tenant_id = _make_uuid()
        account_id = _make_uuid()

        storage = {
            "Account": {
                account_id: {
                    "id": account_id,
                    "tenant_id": tenant_id,
                    "email_address": "coverage@acme.com",
                }
            },
            "Contact": {},
            "Message": {},
        }
        db = FakeExpress(storage)
        processor = InboundEmailProcessor(db)

        payload = {
            "from": "New Person <new@example.com>",
            "to": "coverage@acme.com",
            "subject": "Fresh message",
            "text": "Not a reply",
            "headers": "Message-ID: <fresh@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)

        assert result["escalation_resolved"] is False

    async def test_resolution_summary_truncated_at_500_chars(self):
        tenant_id = _make_uuid()
        account_id = _make_uuid()
        parent_id = _make_uuid()
        escalation_id = _make_uuid()
        backup_id = _make_uuid()

        storage = {
            "Account": {
                account_id: {
                    "id": account_id,
                    "tenant_id": tenant_id,
                    "email_address": "coverage@acme.com",
                }
            },
            "Contact": {},
            "BackupContact": {
                backup_id: {
                    "id": backup_id,
                    "tenant_id": tenant_id,
                    "email": "dave@example.com",
                    "name": "Dave",
                }
            },
            "Message": {
                parent_id: {
                    "id": parent_id,
                    "tenant_id": tenant_id,
                    "external_message_id": "<long-parent@mail>",
                }
            },
            "Escalation": {
                escalation_id: {
                    "id": escalation_id,
                    "tenant_id": tenant_id,
                    "account_id": account_id,
                    "message_id": parent_id,
                    "backup_contact_id": backup_id,
                    "status": EscalationStatus.pending.value,
                }
            },
        }
        db = FakeExpress(storage)
        processor = InboundEmailProcessor(db)

        long_reply = "x" * 1000
        payload = {
            "from": "Dave <dave@example.com>",
            "to": "coverage@acme.com",
            "subject": "Re: Long",
            "text": long_reply,
            "headers": "Message-ID: <reply4@mail>\nIn-Reply-To: <long-parent@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)
        assert result["escalation_resolved"] is True

        esc = storage["Escalation"][escalation_id]
        assert len(esc["resolution_summary"]) <= 500
