"""Tests for daily digest email generation.

Tests the digest formatting logic and data query structure.
Uses real database for integration tests.
"""

import pytest
from datetime import datetime, timedelta, timezone

from sequor.digest.service import (
    format_digest_email,
    compute_breached_count,
)


class TestDigestFormatting:
    """format_digest_email produces the spec-compliant email body."""

    def test_full_digest(self):
        data = {
            "date": "1 May 2026",
            "account_name": "Front Desk",
            "auto_resolved": 12,
            "resolved_by_rag": 8,
            "resolved_by_learned": 4,
            "pending": 3,
            "oldest_unresolved_hours": 6.5,
            "escalated": 2,
            "breached_sla": 1,
            "learned_count": 2,
            "learned_topics": ["invoice payment terms", "shipping timeline"],
        }
        subject, body = format_digest_email(data)

        assert subject == "[COVERAGE DIGEST] 1 May 2026 — Front Desk"
        assert "AI handled automatically: 12 messages" in body
        assert "Resolved by RAG: 8" in body
        assert "Resolved by learned answers: 4" in body
        assert "Pending your response: 3 items" in body
        assert "Oldest unresolved: 6.5 hours ago" in body
        assert "Escalated to backup: 2 items" in body
        assert "Breached SLA: 1 (need attention)" in body
        assert "New knowledge learned: 2 answers" in body
        assert '"invoice payment terms"' in body
        assert '"shipping timeline"' in body

    def test_zero_counts(self):
        data = {
            "date": "1 May 2026",
            "account_name": "Test Account",
            "auto_resolved": 0,
            "resolved_by_rag": 0,
            "resolved_by_learned": 0,
            "pending": 0,
            "oldest_unresolved_hours": None,
            "escalated": 0,
            "breached_sla": 0,
            "learned_count": 0,
            "learned_topics": [],
        }
        subject, body = format_digest_email(data)

        assert "AI handled automatically: 0 messages" in body
        assert "Pending your response: 0 items" in body
        assert "New knowledge learned: 0 answers" in body
        assert "Oldest unresolved" not in body

    def test_no_learned_topics_shows_count_only(self):
        data = {
            "date": "1 May 2026",
            "account_name": "Acme",
            "auto_resolved": 5,
            "resolved_by_rag": 3,
            "resolved_by_learned": 2,
            "pending": 0,
            "oldest_unresolved_hours": None,
            "escalated": 0,
            "breached_sla": 0,
            "learned_count": 0,
            "learned_topics": [],
        }
        _, body = format_digest_email(data)
        assert "New knowledge learned: 0 answers" in body
        # No topic lines when count is 0
        lines = body.strip().splitlines()
        learned_lines = [l for l in lines if l.strip().startswith('"')]
        assert len(learned_lines) == 0


class TestBreachedSLACount:
    """compute_breached_count identifies escalations past SLA deadline."""

    def test_escalation_past_sla_is_breached(self):
        now = datetime.now(timezone.utc)
        escalations = [
            {"assigned_at": now - timedelta(hours=8), "status": "pending"},
        ]
        sla_hours = 4
        assert compute_breached_count(escalations, sla_hours, now) == 1

    def test_resolved_escalation_not_breached(self):
        now = datetime.now(timezone.utc)
        escalations = [
            {"assigned_at": now - timedelta(hours=8), "status": "resolved"},
        ]
        sla_hours = 4
        assert compute_breached_count(escalations, sla_hours, now) == 0

    def test_within_sla_not_breached(self):
        now = datetime.now(timezone.utc)
        escalations = [
            {"assigned_at": now - timedelta(hours=2), "status": "pending"},
        ]
        sla_hours = 4
        assert compute_breached_count(escalations, sla_hours, now) == 0

    def test_mixed_escalations(self):
        now = datetime.now(timezone.utc)
        escalations = [
            {"assigned_at": now - timedelta(hours=8), "status": "pending"},
            {"assigned_at": now - timedelta(hours=10), "status": "resolved"},
            {"assigned_at": now - timedelta(hours=2), "status": "pending"},
            {"assigned_at": now - timedelta(hours=6), "status": "acknowledged"},
        ]
        sla_hours = 4
        # 8h pending = breached, 10h resolved = not breached,
        # 2h pending = not breached, 6h acknowledged = breached (no resolution)
        assert compute_breached_count(escalations, sla_hours, now) == 2
