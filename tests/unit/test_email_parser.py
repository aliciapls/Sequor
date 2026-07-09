from __future__ import annotations

"""Tests for inbound email parser and InboundEmailProcessor."""

import uuid

import pytest

from sequor.db.models import MessageChannel, MessageDirection
from sequor.email.inbound import InboundEmailProcessor
from sequor.email.parser import InboundEmail, parse_sendgrid_payload, strip_quoted_reply


def _make_uuid():
    return str(uuid.uuid4())


class FakeExpress:
    def __init__(self, storage: dict | None = None):
        self.storage: dict[str, dict[str, dict]] = storage or {}

    async def bind_tenant(self, tenant_id) -> None:
        """No-op stand-in for SessionCrud.bind_tenant (unit tests run without a master key)."""

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


class TestParseSendgridPayload:
    def test_parses_basic_fields(self):
        payload = {
            "from": "Alice <alice@example.com>",
            "to": "coverage@acme.com",
            "subject": "Question about invoice",
            "text": "What is my balance?",
            "headers": "Message-ID: <msg123@mail>\nIn-Reply-To: <parent@mail>",
        }

        result = parse_sendgrid_payload(payload)

        assert result.from_email == "alice@example.com"
        assert result.from_name == "Alice"
        assert result.to_email == "coverage@acme.com"
        assert result.subject == "Question about invoice"
        assert result.body_text == "What is my balance?"
        assert result.message_id == "<msg123@mail>"
        assert result.in_reply_to == "<parent@mail>"

    def test_detects_reply(self):
        payload = {
            "from": "Bob <bob@test.com>",
            "to": "coverage@acme.com",
            "subject": "Re: Question",
            "text": "Here is my answer",
            "headers": "Message-ID: <reply123@mail>\nIn-Reply-To: <original@mail>",
        }

        result = parse_sendgrid_payload(payload)
        assert result.is_reply is True

    def test_non_reply_has_no_thread(self):
        payload = {
            "from": "Carol <carol@test.com>",
            "to": "coverage@acme.com",
            "subject": "New inquiry",
            "text": "Hello, I have a question.",
            "headers": "Message-ID: <new123@mail>",
        }

        result = parse_sendgrid_payload(payload)
        assert result.is_reply is False

    def test_extracts_html_body(self):
        payload = {
            "from": "Dan <dan@test.com>",
            "to": "coverage@acme.com",
            "subject": "HTML email",
            "text": "Plain text version",
            "html": "<p>HTML version</p>",
            "headers": "Message-ID: <html123@mail>",
        }

        result = parse_sendgrid_payload(payload)
        assert result.body_html == "<p>HTML version</p>"
        assert result.body_text == "Plain text version"

    def test_extracts_escalation_id_from_references(self):
        esc_id = str(uuid.uuid4())
        payload = {
            "from": "Eve <eve@test.com>",
            "to": "coverage@acme.com",
            "subject": "Re: Escalation",
            "text": "Reply content",
            "headers": (
                f"Message-ID: <reply@mail>\n" f"References: <escalation-{esc_id}@sequor.coverage>"
            ),
        }

        result = parse_sendgrid_payload(payload)
        assert result.escalation_id == esc_id


class TestStripQuotedReply:
    def test_strips_gmail_quote(self):
        text = (
            "Here is my answer\n"
            "\nOn Mon, Jan 1, 2026 at 10:00 AM Bob wrote:\n"
            "> Original question"
        )
        result = strip_quoted_reply(text)
        assert result == "Here is my answer"

    def test_strips_outlook_quote(self):
        text = (
            "My response\n" "\n-----Original Message-----\n" "From: Bob\nTo: Alice\nSubject: Hello"
        )
        result = strip_quoted_reply(text)
        assert result == "My response"

    def test_preserves_no_quote(self):
        text = "Just a plain message with no quotes."
        result = strip_quoted_reply(text)
        assert result == text

    def test_strips_signature_separator(self):
        text = "My response\n-- \nSent from my phone"
        result = strip_quoted_reply(text)
        assert result == "My response"


class TestInboundEmailProcessor:
    async def test_creates_message_from_payload(self):
        tenant_id = _make_uuid()
        account_id = _make_uuid()

        storage = {
            "Account": {
                account_id: {
                    "id": account_id,
                    "tenant_id": tenant_id,
                    "name": "Acme",
                    "email_address": "coverage@acme.com",
                    "owner_email": "owner@acme.com",
                }
            },
            "Contact": {},
            "Message": {},
        }
        db = FakeExpress(storage)
        processor = InboundEmailProcessor(db)

        payload = {
            "from": "Alice <alice@example.com>",
            "to": "coverage@acme.com",
            "subject": "Question",
            "text": "What is my balance?",
            "headers": "Message-ID: <msg-001@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)

        assert result["status"] == "created"
        assert result["is_reply"] is False

        messages = list(storage["Message"].values())
        assert len(messages) == 1
        assert messages[0]["body_text"] == "What is my balance?"
        assert messages[0]["direction"] == MessageDirection.inbound.value
        assert messages[0]["channel"] == MessageChannel.email.value

    async def test_creates_contact_if_new(self):
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
            "subject": "Hello",
            "text": "First message",
            "headers": "Message-ID: <msg-002@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)

        contacts = list(storage["Contact"].values())
        assert len(contacts) == 1
        assert contacts[0]["email"] == "new@example.com"
        assert contacts[0]["name"] == "New Person"

    async def test_reuses_existing_contact(self):
        tenant_id = _make_uuid()
        account_id = _make_uuid()
        contact_id = _make_uuid()

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
            "Message": {},
        }
        db = FakeExpress(storage)
        processor = InboundEmailProcessor(db)

        payload = {
            "from": "Alice <alice@example.com>",
            "to": "coverage@acme.com",
            "subject": "Follow-up",
            "text": "Second message",
            "headers": "Message-ID: <msg-003@mail>",
        }

        await processor.process_sendgrid_payload(payload)

        contacts = list(storage["Contact"].values())
        assert len(contacts) == 1

    async def test_returns_no_account_for_unknown_to(self):
        db = FakeExpress({"Account": {}, "Contact": {}, "Message": {}})
        processor = InboundEmailProcessor(db)

        payload = {
            "from": "Someone <someone@example.com>",
            "to": "unknown@nowhere.com",
            "subject": "Hello",
            "text": "Message",
            "headers": "Message-ID: <msg-004@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)
        assert result["status"] == "no_account"

    async def test_links_reply_to_parent_message(self):
        tenant_id = _make_uuid()
        account_id = _make_uuid()
        parent_id = _make_uuid()

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
                    "external_message_id": "<original@mail>",
                }
            },
        }
        db = FakeExpress(storage)
        processor = InboundEmailProcessor(db)

        payload = {
            "from": "Alice <alice@example.com>",
            "to": "coverage@acme.com",
            "subject": "Re: Question",
            "text": "Here is my reply",
            "headers": "Message-ID: <reply@mail>\nIn-Reply-To: <original@mail>",
        }

        result = await processor.process_sendgrid_payload(payload)

        messages = list(storage["Message"].values())
        reply = [m for m in messages if m["id"] != parent_id][0]
        assert reply["in_reply_to_id"] == parent_id
        assert result["is_reply"] is True
