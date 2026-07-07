"""Regression tests for /redteam Round-5 findings + accretion gaps.

Tier 1 (no live Postgres): each test either exercises a branch that runs before
DB access, or mocks the async DB layer so the endpoint's name-resolution and
error-handling paths run without a real connection.

Covers:
- R5-02 — WhatsApp webhook verify-token constant-time compare + reject-on-mismatch.
- G3    — 500 handlers MUST NOT leak exception text / tracebacks into the response.
- G2    — the live keyphrase/mappings endpoints resolve `select`/`desc` (the R2
          NameError fix); a behavioral guard, not a source-grep.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from sequor.auth import create_access_token_for_operator
from sequor.config import settings
from sequor.onboarding.app import app


@pytest.fixture
def client():
    return TestClient(app)


def _session_cookie(role: str = "operator") -> dict:
    token = create_access_token_for_operator(
        operator_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000002",
        account_id="00000000-0000-0000-0000-000000000003",
        name="Test Op",
        email="op@example.com",
        role=role,
    )
    return {"sequor_session": token}


# ---------------------------------------------------------------------------
# R5-02 — WhatsApp webhook verify-token: constant-time compare, reject mismatch
# ---------------------------------------------------------------------------


class TestR5WhatsAppVerifyToken:
    def test_wrong_token_rejected(self, client, monkeypatch):
        monkeypatch.setattr(settings, "whatsapp_verify_token", "the-real-token")
        resp = client.get(
            "/api/v1/whatsapp/inbound",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "12345",
            },
        )
        assert resp.status_code == 403
        # The challenge MUST NOT be echoed when the token is wrong.
        assert "12345" not in resp.text

    def test_correct_token_echoes_challenge(self, client, monkeypatch):
        monkeypatch.setattr(settings, "whatsapp_verify_token", "the-real-token")
        resp = client.get(
            "/api/v1/whatsapp/inbound",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "the-real-token",
                "hub.challenge": "echo-me-42",
            },
        )
        assert resp.status_code == 200
        assert resp.text.strip() == "echo-me-42"

    def test_verify_uses_constant_time_compare(self):
        """The verify path must use hmac.compare_digest, not a plain != oracle."""
        import inspect
        import sequor.onboarding.app as appmod

        src = inspect.getsource(appmod.whatsapp_webhook_verify)
        assert "compare_digest" in src, "verify-token compare must be constant-time"


# ---------------------------------------------------------------------------
# G3 — 500 handlers MUST NOT leak exception text / tracebacks
# ---------------------------------------------------------------------------

_LEAK_MARKER = "LEAKMARKER_TRACEBACK_SENTINEL_9f8e7d"


class TestR5NoTracebackLeak:
    def test_500_body_excludes_exception_text(self, client):
        """When an endpoint's internals raise, the 500 body is generic — the
        exception message / traceback never reaches the caller (R1 fix guard)."""
        with patch(
            "sequor.ai.ingestion.DocumentIngester.ingest",
            new_callable=AsyncMock,
            side_effect=RuntimeError(_LEAK_MARKER),
        ):
            resp = client.post(
                "/api/v1/onboarding/upload",
                data={
                    "tenant_id": str(uuid4()),
                    "account_id": str(uuid4()),
                    "document_type": "faq",
                },
                files={"file": ("kb.txt", b"hello world", "text/plain")},
            )
        assert resp.status_code == 500
        assert _LEAK_MARKER not in resp.text
        assert "Internal server error" in resp.text


# ---------------------------------------------------------------------------
# G2 — keyphrase/mappings endpoints resolve select/desc (R2 NameError fix)
# ---------------------------------------------------------------------------


class _FakeResult:
    def all(self):
        return []


class _FakeSession:
    """Minimal async-context-manager DB session double: lets the endpoint run
    its real `select(...).join(...).order_by(desc(...))` construction (so an
    unimported name raises NameError) without a live Postgres connection."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, *a, **k):
        return _FakeResult()

    async def commit(self):
        return None


class TestR5KeyphraseNameResolution:
    def test_keyphrase_mappings_get_resolves_names(self, client, monkeypatch):
        # Mock the DB layer the endpoint imports in-function.
        import sequor.db.database as dbmod
        import sqlalchemy.ext.asyncio as sa_async

        monkeypatch.setattr(dbmod, "get_engine", lambda: object())
        monkeypatch.setattr(sa_async, "AsyncSession", lambda *a, **k: _FakeSession())

        resp = client.get("/api/v1/portal/keyphrase/mappings", cookies=_session_cookie())
        # 200 + empty list proves select/desc/join/order_by all resolved —
        # an unimported name would have raised NameError -> 500.
        assert resp.status_code == 200
        assert resp.json() == {"mappings": []}
