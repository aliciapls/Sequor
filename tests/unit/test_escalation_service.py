"""Unit tests for EscalationService — mocked DataFlow + email sender."""

import uuid
from datetime import datetime, timezone

import pytest

from sequor.db.models import EscalationPriority, EscalationStatus
from sequor.escalation.service import (
    BackupNotFoundError,
    EscalationError,
    EscalationNotFoundError,
    EscalationService,
)


def _make_uuid():
    return str(uuid.uuid4())


class FakeExpress:
    """Fake DataFlow express for testing EscalationService."""

    def __init__(self, storage: dict | None = None):
        self.storage: dict[str, dict[str, dict]] = storage or {}
        self.created: list[tuple] = []
        self.updated: list[tuple] = []
        self.emails_sent: list[dict] = []

    def _ensure_model(self, model: str) -> None:
        if model not in self.storage:
            self.storage[model] = {}

    async def read(self, model: str, id: str) -> dict | None:
        self._ensure_model(model)
        return self.storage[model].get(id)

    async def list(
        self,
        model: str,
        filter: dict | None = None,
    ) -> list[dict]:
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
        self.created.append((model, id, record))
        return record

    async def update(self, model: str, id: str, data: dict) -> dict:
        self._ensure_model(model)
        record = self.storage[model].get(id, {})
        updated = {**record, **data, "id": id}
        self.storage[model][id] = updated
        self.updated.append((model, id, updated))
        return updated


class FakeEmailSender:
    """Fake EmailSender for testing EscalationService."""

    def __init__(self):
        self.sent: list[dict] = []
        self.should_fail = False

    async def send_email(self, **kwargs) -> str:
        if self.should_fail:
            raise RuntimeError("Fake send failure")
        self.sent.append(kwargs)
        return "fake-msg-id-123"

    async def send_escalation_email(self, **kwargs) -> str:
        if self.should_fail:
            raise RuntimeError("Fake escalation send failure")
        self.sent.append({"method": "send_escalation_email", **kwargs})
        return "fake-escalation-msg-id"


ACCOUNT_ID = _make_uuid()
MESSAGE_ID = _make_uuid()
TENANT_ID = _make_uuid()
BACKUP_ID = _make_uuid()
CONTACT_ID = _make_uuid()
ESCALATION_ID = _make_uuid()


def _setup_storage(express: FakeExpress) -> None:
    express.storage["Account"] = {
        ACCOUNT_ID: {
            "id": ACCOUNT_ID,
            "name": "Acme Corp",
            "escalation_sla_hours": 4,
        }
    }
    express.storage["Message"] = {
        MESSAGE_ID: {
            "id": MESSAGE_ID,
            "contact_id": CONTACT_ID,
            "channel": "email",
            "body_text": "What is your refund policy?",
            "received_at": datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
        }
    }
    express.storage["Contact"] = {
        CONTACT_ID: {
            "id": CONTACT_ID,
            "name": "Jane Smith",
            "email": "jane@example.com",
        }
    }
    express.storage["BackupContact"] = {
        BACKUP_ID: {
            "id": BACKUP_ID,
            "account_id": ACCOUNT_ID,
            "name": "Bob Johnson",
            "email": "bob@acme.com",
            "tier": "primary",
            "active": True,
        }
    }


class TestCreateEscalation:
    @pytest.fixture
    def service(self):
        express = FakeExpress()
        _setup_storage(express)
        email = FakeEmailSender()
        return EscalationService(express, email), express, email

    async def test_creates_escalation_record(self, service):
        svc, express, _ = service
        result = await svc.create_escalation(
            message_id=uuid.UUID(MESSAGE_ID),
            tenant_id=uuid.UUID(TENANT_ID),
            account_id=uuid.UUID(ACCOUNT_ID),
            priority=EscalationPriority.high,
            ai_summary="Refund policy question",
            routing_reason="Low confidence — AI could not answer reliably",
            suggested_response="Our refund policy is...",
        )
        assert result["tier"] == 1
        assert result["status"] == EscalationStatus.pending.value
        assert result["priority"] == EscalationPriority.high.value
        assert result["backup_contact_id"] == BACKUP_ID

    async def test_sends_escalation_email(self, service):
        svc, express, email = service
        await svc.create_escalation(
            message_id=uuid.UUID(MESSAGE_ID),
            tenant_id=uuid.UUID(TENANT_ID),
            account_id=uuid.UUID(ACCOUNT_ID),
            priority=EscalationPriority.high,
            ai_summary="Refund policy question",
            routing_reason="Low confidence",
            suggested_response="Our refund policy is...",
        )
        assert len(email.sent) == 1
        assert email.sent[0]["to"] == "bob@acme.com"
        assert "escalation_id" in email.sent[0]

    async def test_raises_when_no_backup_found(self, service):
        svc, express, _ = service
        express.storage["BackupContact"] = {}
        with pytest.raises(BackupNotFoundError):
            await svc.create_escalation(
                message_id=uuid.UUID(MESSAGE_ID),
                tenant_id=uuid.UUID(TENANT_ID),
                account_id=uuid.UUID(ACCOUNT_ID),
                priority=EscalationPriority.high,
                ai_summary="Test",
                routing_reason="Test",
            )

    async def test_raises_when_account_not_found(self, service):
        svc, express, _ = service
        express.storage["Account"] = {}
        with pytest.raises(EscalationError, match="Account.*not found"):
            await svc.create_escalation(
                message_id=uuid.UUID(MESSAGE_ID),
                tenant_id=uuid.UUID(TENANT_ID),
                account_id=uuid.UUID(ACCOUNT_ID),
                priority=EscalationPriority.high,
                ai_summary="Test",
                routing_reason="Test",
            )


class TestResolveEscalation:
    @pytest.fixture
    def service_with_escalation(self):
        express = FakeExpress()
        _setup_storage(express)
        express.storage["Escalation"] = {
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
        email = FakeEmailSender()
        return EscalationService(express, email), express, email

    async def test_resolves_escalation(self, service_with_escalation):
        svc, express, _ = service_with_escalation
        result = await svc.resolve_escalation(
            escalation_id=uuid.UUID(ESCALATION_ID),
            resolution_summary="Sent refund policy details.",
        )
        assert result["status"] == EscalationStatus.resolved.value
        assert result["resolution_summary"] == "Sent refund policy details."
        assert result["resolved_at"] is not None

    async def test_resolve_raises_not_found(self, service_with_escalation):
        svc, express, _ = service_with_escalation
        with pytest.raises(EscalationNotFoundError):
            await svc.resolve_escalation(
                escalation_id=uuid.uuid4(),
                resolution_summary="Done.",
            )


class TestAcknowledgeEscalation:
    @pytest.fixture
    def service_with_escalation(self):
        express = FakeExpress()
        _setup_storage(express)
        express.storage["Escalation"] = {
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
        email = FakeEmailSender()
        return EscalationService(express, email), express

    async def test_acknowledges_escalation(self, service_with_escalation):
        svc, express = service_with_escalation
        result = await svc.acknowledge_escalation(
            escalation_id=uuid.UUID(ESCALATION_ID),
        )
        assert result["status"] == EscalationStatus.acknowledged.value
        assert result["acknowledged_at"] is not None


class TestCheckContradiction:
    @pytest.fixture
    def service_with_ai_reply(self):
        express = FakeExpress()
        _setup_storage(express)
        express.storage["Escalation"] = {
            ESCALATION_ID: {
                "id": ESCALATION_ID,
                "message_id": MESSAGE_ID,
            }
        }
        express.storage["Response"] = {
            _make_uuid(): {
                "message_id": MESSAGE_ID,
                "was_auto_sent": True,
                "content": "Our refund policy is 30 days.",
            }
        }
        email = FakeEmailSender()
        return EscalationService(express, email), express

    async def test_detects_ai_auto_reply(self, service_with_ai_reply):
        svc, _ = service_with_ai_reply
        result = await svc.check_contradiction(
            escalation_id=uuid.UUID(ESCALATION_ID),
            proposed_reply_summary="Refund policy information",
        )
        assert result is True

    async def test_no_contradiction_when_no_auto_reply(self):
        express = FakeExpress()
        _setup_storage(express)
        express.storage["Escalation"] = {
            ESCALATION_ID: {"id": ESCALATION_ID, "message_id": MESSAGE_ID}
        }
        express.storage["Response"] = {}
        email = FakeEmailSender()
        svc = EscalationService(express, email)
        result = await svc.check_contradiction(
            escalation_id=uuid.UUID(ESCALATION_ID),
            proposed_reply_summary="Refund policy information",
        )
        assert result is False


class TestEscalateToSecondTier:
    @pytest.fixture
    def service_with_second_tier(self):
        express = FakeExpress()
        _setup_storage(express)
        second_tier_id = _make_uuid()
        express.storage["BackupContact"][second_tier_id] = {
            "id": second_tier_id,
            "account_id": ACCOUNT_ID,
            "name": "Carol Manager",
            "email": "carol@acme.com",
            "tier": "second_tier",
            "active": True,
        }
        express.storage["Escalation"] = {
            ESCALATION_ID: {
                "id": ESCALATION_ID,
                "tenant_id": TENANT_ID,
                "message_id": MESSAGE_ID,
                "backup_contact_id": BACKUP_ID,
                "tier": 1,
                "status": EscalationStatus.pending.value,
                "priority": EscalationPriority.high.value,
                "ai_summary": "Refund question",
                "routing_reason": "Low confidence",
            }
        }
        email = FakeEmailSender()
        return EscalationService(express, email), express, email, second_tier_id

    async def test_creates_tier_two_escalation(self, service_with_second_tier):
        svc, express, _, second_tier_id = service_with_second_tier
        result = await svc.escalate_to_second_tier(
            escalation_id=uuid.UUID(ESCALATION_ID),
        )
        assert result["tier"] == 2
        assert result["status"] == EscalationStatus.pending.value
        assert result["backup_contact_id"] == second_tier_id

    async def test_sends_email_to_second_tier(self, service_with_second_tier):
        svc, express, email, _ = service_with_second_tier
        await svc.escalate_to_second_tier(
            escalation_id=uuid.UUID(ESCALATION_ID),
        )
        assert len(email.sent) == 1
        assert email.sent[0]["to"] == "carol@acme.com"

    async def test_raises_when_no_second_tier_backup(self):
        express = FakeExpress()
        _setup_storage(express)
        express.storage["Escalation"] = {
            ESCALATION_ID: {
                "id": ESCALATION_ID,
                "message_id": MESSAGE_ID,
                "tenant_id": TENANT_ID,
                "backup_contact_id": BACKUP_ID,
                "priority": EscalationPriority.high.value,
            }
        }
        # Remove second tier
        for k in list(express.storage.get("BackupContact", {}).keys()):
            pass
        express.storage["BackupContact"] = {
            BACKUP_ID: {
                "id": BACKUP_ID,
                "account_id": ACCOUNT_ID,
                "name": "Bob",
                "email": "bob@acme.com",
                "tier": "primary",
                "active": True,
            }
        }
        email = FakeEmailSender()
        svc = EscalationService(express, email)
        with pytest.raises(BackupNotFoundError):
            await svc.escalate_to_second_tier(escalation_id=uuid.UUID(ESCALATION_ID))
