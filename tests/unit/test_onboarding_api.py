"""Tests for onboarding API endpoint.

Tests the form submission endpoint including validation, error handling,
and the signup page serving. Uses FastAPI TestClient — no real HTTP server needed.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from sequor.onboarding.app import app

    return TestClient(app)


def _valid_payload(**overrides):
    defaults = dict(
        org_name="Test Org",
        owner_email="owner@testorg.com",
        owner_password="SecurePass1",
        account_name="Front Desk",
        ownership_type="individual",
        backup_name="Backup Person",
        backup_email="backup@testorg.com",
        escalation_sla_hours=4,
        routing_rule="full_ai",
    )
    defaults.update(overrides)
    return defaults


class TestSignupPage:
    """GET / serves the signup form."""

    def test_returns_html(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "Sequor" in res.text

    def test_contains_form(self, client):
        res = client.get("/")
        assert "<form" in res.text
        assert 'name="org_name"' in res.text
        assert 'name="owner_email"' in res.text
        assert 'name="backup_email"' in res.text


class TestSignupEndpointValidation:
    """POST /api/v1/onboarding rejects invalid input."""

    def test_rejects_missing_fields(self, client):
        res = client.post("/api/v1/onboarding", json={})
        assert res.status_code == 422

    def test_rejects_invalid_email(self, client):
        res = client.post("/api/v1/onboarding", json=_valid_payload(owner_email="not-valid"))
        assert res.status_code == 422

    def test_rejects_html_in_org_name(self, client):
        res = client.post(
            "/api/v1/onboarding", json=_valid_payload(org_name="<script>alert(1)</script>")
        )
        assert res.status_code == 422

    def test_rejects_weak_password(self, client):
        res = client.post("/api/v1/onboarding", json=_valid_payload(owner_password="short"))
        assert res.status_code == 422

    def test_rejects_invalid_routing_rule(self, client):
        res = client.post(
            "/api/v1/onboarding", json=_valid_payload(routing_rule="custom_rule")
        )
        assert res.status_code == 422

    def test_rejects_sla_out_of_range(self, client):
        res = client.post("/api/v1/onboarding", json=_valid_payload(escalation_sla_hours=0))
        assert res.status_code == 422
