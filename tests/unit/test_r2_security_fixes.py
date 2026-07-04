"""Regression tests for /redteam Round-2 security/correctness fixes.

These exercise the branches that reject BEFORE any database access, so they run
without live Postgres (Tier 1). The DB-dependent positive paths are covered by
the integration suite.
"""

import pytest
from fastapi.testclient import TestClient

from sequor.auth import create_access_token_for_operator
from sequor.onboarding.app import app


@pytest.fixture
def client():
    return TestClient(app)


def _session_cookie(role: str) -> dict:
    token = create_access_token_for_operator(
        operator_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000002",
        account_id="00000000-0000-0000-0000-000000000003",
        name="Test Op",
        email="op@example.com",
        role=role,
    )
    return {"sequor_session": token}


def test_admin_backfill_requires_auth(client):
    # r2-security M4: unauthenticated caller is rejected before any tenant iteration.
    resp = client.post("/api/v1/admin/backfill-blind-indexes")
    assert resp.status_code == 401


def test_admin_backfill_rejects_non_admin(client):
    # r2-security M4: an authenticated but non-admin operator cannot trigger the
    # cross-tenant migration op.
    resp = client.post(
        "/api/v1/admin/backfill-blind-indexes",
        cookies=_session_cookie("operator"),
    )
    assert resp.status_code == 403
