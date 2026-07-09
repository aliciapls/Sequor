from __future__ import annotations

"""Tests for SLAScheduler and EscalationService.process_breached_escalation."""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from sequor.db.models import (
    ContactTier,
    EscalationPriority,
    EscalationStatus,
)
from sequor.escalation.scheduler import SLAScheduler
from sequor.escalation.service import (
    BackupNotFoundError,
    EscalationService,
)


def _make_uuid():
    return str(uuid.uuid4())


class FakeExpress:
    """Fake DataFlow express for testing."""

    def __init__(self, storage: dict | None = None):
        self.storage: dict[str, dict[str, dict]] = storage or {}

    async def bind_tenant(self, tenant_id) -> None:
        """No-op stand-in for SessionCrud.bind_tenant (unit tests run without a master key)."""

    async def commit(self) -> None:
        """No-op stand-in for SessionCrud.commit (per-tenant boundary; in-memory fake has no txn)."""

    async def rollback(self) -> None:
        """No-op stand-in for SessionCrud.rollback (in-memory fake has no txn to roll back)."""

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
    """Fake email sender for testing."""

    def __init__(self):
        self.sent: list[dict] = []

    async def send_email(self, **kwargs) -> str:
        self.sent.append(kwargs)
        return "fake-msg-id"

    async def send_escalation_email(self, **kwargs) -> str:
        self.sent.append(kwargs)
        return "fake-msg-id"


def _setup_storage_with_breach(
    tier: int = 1,
    status: str = EscalationStatus.pending.value,
    hours_ago: int = 5,
    sla_hours: int = 4,
    has_second_tier: bool = True,
):
    """Create storage with an escalation that is past its SLA deadline."""
    tenant_id = _make_uuid()
    account_id = _make_uuid()
    primary_backup_id = _make_uuid()
    second_tier_backup_id = _make_uuid() if has_second_tier else None
    message_id = _make_uuid()
    escalation_id = _make_uuid()

    storage = {
        "Tenant": {tenant_id: {"id": tenant_id, "name": "Test Tenant"}},
        "Account": {
            account_id: {
                "id": account_id,
                "name": "Test Account",
                "escalation_sla_hours": sla_hours,
            }
        },
        "BackupContact": {
            primary_backup_id: {
                "id": primary_backup_id,
                "account_id": account_id,
                "tier": ContactTier.primary.value,
                "active": True,
                "name": "Primary Backup",
                "email": "primary@test.com",
            },
        },
        "Message": {
            message_id: {
                "id": message_id,
                "contact_id": _make_uuid(),
                "body_text": "Test message",
                "channel": "email",
                "received_at": datetime.now(timezone.utc) - timedelta(hours=hours_ago),
            }
        },
        "Escalation": {
            escalation_id: {
                "id": escalation_id,
                "tenant_id": tenant_id,
                "message_id": message_id,
                "backup_contact_id": primary_backup_id,
                "tier": tier,
                "status": status,
                "priority": EscalationPriority.high.value,
                "assigned_at": datetime.now(timezone.utc) - timedelta(hours=hours_ago),
            }
        },
        "Contact": {},
    }

    if has_second_tier and second_tier_backup_id:
        storage["BackupContact"][second_tier_backup_id] = {
            "id": second_tier_backup_id,
            "account_id": account_id,
            "tier": ContactTier.second_tier.value,
            "active": True,
            "name": "Second Tier Backup",
            "email": "secondary@test.com",
        }

    return storage, escalation_id, tenant_id


class TestProcessBreachedEscalation:
    async def test_tier1_breach_escalates_to_tier2(self):
        storage, esc_id, _ = _setup_storage_with_breach(tier=1, has_second_tier=True)
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)

        escalation = storage["Escalation"][esc_id]
        result = await service.process_breached_escalation(escalation)

        assert result["new_status"] == EscalationStatus.expired.value
        assert result["tier_2_id"] is not None
        assert len(email.sent) == 2  # tier-2 email + reminder to primary

    async def test_tier1_breach_marks_original_expired(self):
        storage, esc_id, _ = _setup_storage_with_breach(tier=1)
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)

        await service.process_breached_escalation(storage["Escalation"][esc_id])

        updated = storage["Escalation"][esc_id]
        assert updated["status"] == EscalationStatus.expired.value
        assert updated["resolved_at"] is not None

    async def test_tier1_breach_sends_reminder_to_primary(self):
        storage, esc_id, _ = _setup_storage_with_breach(tier=1)
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)

        await service.process_breached_escalation(storage["Escalation"][esc_id])

        reminder = [s for s in email.sent if "SLA BREACHED" in s.get("subject", "")]
        assert len(reminder) == 1
        assert reminder[0]["to"] == "primary@test.com"

    async def test_tier2_breach_marks_expired_no_further_escalation(self):
        storage, esc_id, _ = _setup_storage_with_breach(tier=2)
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)

        result = await service.process_breached_escalation(storage["Escalation"][esc_id])

        assert result["new_status"] == EscalationStatus.expired.value
        assert result["tier_2_id"] is None
        assert len(email.sent) == 0

    async def test_skips_already_processed(self):
        storage, esc_id, _ = _setup_storage_with_breach(status=EscalationStatus.resolved.value)
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)

        result = await service.process_breached_escalation(storage["Escalation"][esc_id])

        assert result["status"] == "skipped"
        assert len(email.sent) == 0

    async def test_tier1_breach_without_second_tier_backup(self):
        storage, esc_id, _ = _setup_storage_with_breach(tier=1, has_second_tier=False)
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)

        result = await service.process_breached_escalation(storage["Escalation"][esc_id])

        assert result["new_status"] == EscalationStatus.expired.value
        assert result["tier_2_id"] is None
        updated = storage["Escalation"][esc_id]
        assert updated["status"] == EscalationStatus.expired.value


class TestSLAScheduler:
    async def test_start_creates_task(self):
        db = FakeExpress()
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)
        scheduler = SLAScheduler(service, db, interval_seconds=9999)

        await scheduler.start()
        assert scheduler._task is not None
        assert not scheduler._task.done()
        await scheduler.stop()

    async def test_stop_cancels_task(self):
        db = FakeExpress()
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)
        scheduler = SLAScheduler(service, db, interval_seconds=9999)

        await scheduler.start()
        await scheduler.stop()
        assert scheduler._task is None

    async def test_tick_processes_breached_escalations(self):
        storage, esc_id, tenant_id = _setup_storage_with_breach()
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)
        scheduler = SLAScheduler(service, db, interval_seconds=9999)

        await scheduler._tick()

        updated = storage["Escalation"][esc_id]
        assert updated["status"] == EscalationStatus.expired.value

    async def test_tick_handles_empty_tenant_list(self):
        db = FakeExpress({"Tenant": {}})
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)
        scheduler = SLAScheduler(service, db, interval_seconds=9999)

        await scheduler._tick()
        assert len(email.sent) == 0

    async def test_tick_continues_after_tenant_error(self):
        storage, esc_a, original_tenant_id = _setup_storage_with_breach()
        bad_tenant_id = _make_uuid()

        storage["Tenant"][bad_tenant_id] = {"id": bad_tenant_id, "name": "Bad Tenant"}
        storage["Escalation"][_make_uuid()] = {
            "id": _make_uuid(),
            "tenant_id": bad_tenant_id,
            "message_id": _make_uuid(),
            "backup_contact_id": _make_uuid(),
            "tier": 1,
            "status": EscalationStatus.pending.value,
            "priority": EscalationPriority.high.value,
            "assigned_at": datetime.now(timezone.utc) - timedelta(hours=5),
        }

        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = EscalationService(db, email, config_sla_hours=4)
        scheduler = SLAScheduler(service, db, interval_seconds=9999)

        await scheduler._tick()

        assert storage["Escalation"][esc_a]["status"] == EscalationStatus.expired.value
