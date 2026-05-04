from __future__ import annotations

"""Tests for DigestService."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from sequor.db.models import ContactTier, EscalationStatus
from sequor.digest.service import DigestService


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


class FakeEmailSender:
    def __init__(self):
        self.sent: list[dict] = []

    async def send_email(self, **kwargs) -> str:
        self.sent.append(kwargs)
        return "fake-msg-id"


def _setup_storage():
    tenant_id = _make_uuid()
    account_id = _make_uuid()
    backup_id = _make_uuid()

    storage = {
        "Tenant": {tenant_id: {"id": tenant_id, "name": "Test Org"}},
        "Account": {
            account_id: {
                "id": account_id,
                "tenant_id": tenant_id,
                "name": "Test Account",
            }
        },
        "BackupContact": {
            backup_id: {
                "id": backup_id,
                "account_id": account_id,
                "tier": ContactTier.primary.value,
                "active": True,
                "name": "Primary Backup",
                "email": "backup@test.com",
            }
        },
        "Escalation": {},
        "Response": {},
        "LearnedAnswer": {},
    }
    return storage, tenant_id, account_id


class TestDigestService:
    async def test_send_digest_sends_email(self):
        storage, tenant_id, account_id = _setup_storage()
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = DigestService(db, email)

        result = await service.send_digest(
            uuid.UUID(tenant_id), uuid.UUID(account_id)
        )

        assert result is not None
        assert result["sent_to"] == "backup@test.com"
        assert len(email.sent) == 1
        assert "[COVERAGE DIGEST]" in email.sent[0]["subject"]

    async def test_send_digest_includes_stats(self):
        storage, tenant_id, account_id = _setup_storage()

        esc_id = _make_uuid()
        storage["Escalation"][esc_id] = {
            "id": esc_id,
            "tenant_id": tenant_id,
            "assigned_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "status": EscalationStatus.pending.value,
        }

        resp_id = _make_uuid()
        storage["Response"][resp_id] = {
            "id": resp_id,
            "tenant_id": tenant_id,
            "was_auto_sent": True,
            "sent_at": datetime.now(timezone.utc) - timedelta(hours=1),
        }

        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = DigestService(db, email)

        await service.send_digest(uuid.UUID(tenant_id), uuid.UUID(account_id))

        body_text = email.sent[0]["body_text"]
        assert "AI handled automatically: 1" in body_text
        assert "Pending your response: 1" in body_text

    async def test_send_digest_skips_no_backup(self):
        storage, tenant_id, account_id = _setup_storage()
        storage["BackupContact"] = {}

        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = DigestService(db, email)

        result = await service.send_digest(
            uuid.UUID(tenant_id), uuid.UUID(account_id)
        )

        assert result is None
        assert len(email.sent) == 0

    async def test_send_all_accounts_sends_per_account(self):
        storage, tenant_id, account_id = _setup_storage()

        account_id_2 = _make_uuid()
        backup_id_2 = _make_uuid()
        storage["Account"][account_id_2] = {
            "id": account_id_2,
            "tenant_id": tenant_id,
            "name": "Second Account",
        }
        storage["BackupContact"][backup_id_2] = {
            "id": backup_id_2,
            "account_id": account_id_2,
            "tier": ContactTier.primary.value,
            "active": True,
            "name": "Backup 2",
            "email": "backup2@test.com",
        }

        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = DigestService(db, email)

        results = await service.send_all_accounts(uuid.UUID(tenant_id))

        assert len(results) == 2
        assert len(email.sent) == 2

    async def test_send_all_tenants(self):
        storage, tenant_id, account_id = _setup_storage()
        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = DigestService(db, email)

        results = await service.send_all_tenants()

        assert len(results) == 1

    async def test_send_digest_includes_breached_count(self):
        storage, tenant_id, account_id = _setup_storage()

        esc_id = _make_uuid()
        storage["Escalation"][esc_id] = {
            "id": esc_id,
            "tenant_id": tenant_id,
            "assigned_at": datetime.now(timezone.utc) - timedelta(hours=6),
            "status": EscalationStatus.expired.value,
            "resolved_at": datetime.now(timezone.utc) - timedelta(hours=1),
        }

        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = DigestService(db, email)

        await service.send_digest(uuid.UUID(tenant_id), uuid.UUID(account_id))

        body_text = email.sent[0]["body_text"]
        assert "Breached SLA: 1" in body_text

    async def test_send_digest_includes_learned_answers(self):
        storage, tenant_id, account_id = _setup_storage()

        la_id = _make_uuid()
        storage["LearnedAnswer"][la_id] = {
            "id": la_id,
            "tenant_id": tenant_id,
            "account_id": account_id,
            "question_text": "How do I reset my password?",
            "answer_text": "Click the reset link on the login page.",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
        }

        db = FakeExpress(storage)
        email = FakeEmailSender()
        service = DigestService(db, email)

        await service.send_digest(uuid.UUID(tenant_id), uuid.UUID(account_id))

        body_text = email.sent[0]["body_text"]
        assert "New knowledge learned: 1" in body_text
        assert "reset my password" in body_text
