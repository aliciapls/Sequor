"""Tests for DNS setup API endpoints."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from sequor.onboarding.app import app
    return TestClient(app)


class TestDNSRecordsEndpoint:
    """GET /api/v1/dns/records returns DNS instructions."""

    @patch("sequor.onboarding.app.generate_dns_records")
    def test_returns_records(self, mock_gen, client):
        mock_gen.return_value = [
            {"type": "TXT", "host": "acme.com", "value": "v=spf1 include:mail.sequor.app ~all", "description": "SPF"},
        ]
        res = client.get("/api/v1/dns/records", params={"domain": "acme.com"})
        assert res.status_code == 200
        body = res.json()
        assert body["domain"] == "acme.com"
        assert len(body["records"]) == 1

    def test_rejects_missing_domain(self, client):
        res = client.get("/api/v1/dns/records")
        assert res.status_code == 422

    def test_rejects_invalid_domain(self, client):
        res = client.get("/api/v1/dns/records", params={"domain": "notadomain"})
        assert res.status_code == 422


class TestDNSVerifyEndpoint:
    """GET /api/v1/dns/verify checks DNS records."""

    @patch("sequor.onboarding.app.verify_dns_records")
    def test_returns_verification_result(self, mock_verify, client):
        mock_verify.return_value = {
            "verified": True,
            "records": [
                {"type": "SPF", "host": "acme.com", "verified": True},
            ],
            "errors": [],
        }
        res = client.get("/api/v1/dns/verify", params={"domain": "acme.com"})
        assert res.status_code == 200
        body = res.json()
        assert body["verified"] is True

    def test_rejects_missing_domain(self, client):
        res = client.get("/api/v1/dns/verify")
        assert res.status_code == 422
