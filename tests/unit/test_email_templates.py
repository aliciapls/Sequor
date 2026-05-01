"""Unit tests for email template functions — pure, no mocking."""

import uuid

from sequor.email.templates import (
    build_digest_email,
    build_digest_subject,
    build_escalation_email,
    build_escalation_subject,
    build_return_summary_email,
    build_return_summary_subject,
    build_weekly_recap_email,
    build_weekly_recap_subject,
)

ESCALATION_ID = str(uuid.uuid4())


def _escalation_data(**overrides):
    defaults = {
        "escalation_id": ESCALATION_ID,
        "contact_name": "Jane Smith",
        "contact_channel": "email",
        "received_at": "2026-05-01 10:00 UTC",
        "ai_attempted": "RAG lookup — no matching document found",
        "confidence_score": 0.45,
        "confidence_category": "low",
        "original_message_body": "What is the refund policy for annual plans?",
        "escalation_deadline": "2026-05-01 14:00 UTC",
        "backup_name": "Bob Johnson",
        "suggested_response": None,
        "org_name": "Acme Corp",
        "one_line_summary": "Refund policy question from client",
    }
    defaults.update(overrides)
    return defaults


def _digest_data(**overrides):
    defaults = {
        "account_name": "Acme Corp",
        "date": "2026-05-01",
        "ai_handled_count": 15,
        "rag_resolved_count": 10,
        "learned_answers_count": 5,
        "pending_count": 3,
        "oldest_unresolved_hours": 2.5,
        "escalated_count": 1,
        "breached_count": 0,
        "new_knowledge_count": 2,
        "new_knowledge_topics": ["refund policy", "pricing tiers"],
        "org_name": "Acme Corp",
    }
    defaults.update(overrides)
    return defaults


def _weekly_data(**overrides):
    defaults = {
        "account_name": "Acme Corp",
        "date_range": "Apr 25 – May 1",
        "total_messages": 100,
        "ai_auto_resolved": 75,
        "human_resolved": 20,
        "pending": 5,
        "ai_accuracy_pct": 92.0,
        "top_topics": ["pricing", "refund", "shipping", "hours", "location"],
        "knowledge_new": 8,
        "knowledge_total": 45,
        "avg_ai_response_minutes": 3.0,
        "avg_human_response_hours": 2.5,
        "org_name": "Acme Corp",
    }
    defaults.update(overrides)
    return defaults


def _return_data(**overrides):
    defaults = {
        "account_name": "Acme Corp",
        "date_range": "Apr 28 – May 1",
        "total_received": 50,
        "auto_resolved": 40,
        "backup_resolved": 8,
        "still_pending": 2,
        "pending_items": [
            {"summary": "Refund policy question from Jane", "urgency": "high"},
            {"summary": "Shipping inquiry from Tom", "urgency": "medium"},
        ],
        "new_answers_learned": 6,
        "org_name": "Acme Corp",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Escalation email
# ---------------------------------------------------------------------------


class TestEscalationEmail:
    def test_subject_format(self):
        data = _escalation_data()
        subject = build_escalation_subject(data)
        assert subject.startswith("[UNRESOLVED]")
        assert "Ref: " in subject
        assert ESCALATION_ID[:8] in subject

    def test_text_contains_client_info(self):
        html, text = build_escalation_email(_escalation_data())
        assert "Jane Smith" in text
        assert "email" in text

    def test_text_contains_confidence(self):
        html, text = build_escalation_email(_escalation_data())
        assert "45%" in text
        assert "low" in text

    def test_text_contains_original_message(self):
        html, text = build_escalation_email(_escalation_data())
        assert "refund policy for annual plans" in text

    def test_text_contains_escalation_deadline(self):
        html, text = build_escalation_email(_escalation_data())
        assert "2026-05-01 14:00 UTC" in text

    def test_text_contains_backup_name(self):
        html, text = build_escalation_email(_escalation_data())
        assert "Bob Johnson" in text

    def test_text_contains_reply_instruction(self):
        html, text = build_escalation_email(_escalation_data())
        assert "Reply to this email" in text

    def test_suggested_response_present_when_provided(self):
        data = _escalation_data(suggested_response="Our refund policy is 30 days.")
        html, text = build_escalation_email(data)
        assert "Our refund policy is 30 days" in text
        assert "suggested response" in text.lower()

    def test_no_suggested_response_when_none(self):
        html, text = build_escalation_email(_escalation_data())
        assert "AI suggested response" not in text

    def test_html_is_valid_markup(self):
        html, text = build_escalation_email(_escalation_data())
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert "Jane Smith" in html

    def test_consent_notice_included(self):
        html, text = build_escalation_email(_escalation_data())
        assert "AI assistant" in html
        assert "HUMAN" in html


# ---------------------------------------------------------------------------
# Digest email
# ---------------------------------------------------------------------------


class TestDigestEmail:
    def test_subject_format(self):
        subject = build_digest_subject(_digest_data())
        assert "[COVERAGE DIGEST]" in subject
        assert "2026-05-01" in subject

    def test_text_contains_ai_handled_count(self):
        html, text = build_digest_email(_digest_data())
        assert "15" in text
        assert "AI handled automatically" in text

    def test_text_contains_rag_resolved(self):
        html, text = build_digest_email(_digest_data())
        assert "Resolved by RAG: 10" in text

    def test_text_contains_pending_count(self):
        html, text = build_digest_email(_digest_data())
        assert "Pending your response: 3" in text

    def test_text_contains_oldest_unresolved(self):
        html, text = build_digest_email(_digest_data())
        assert "2.5 hours ago" in text

    def test_text_oldest_unresolved_none(self):
        data = _digest_data(oldest_unresolved_hours=None)
        html, text = build_digest_email(data)
        assert "N/A" in text

    def test_text_contains_breached_sla(self):
        html, text = build_digest_email(_digest_data(breached_count=2))
        assert "Breached SLA: 2" in text

    def test_text_lists_knowledge_topics(self):
        html, text = build_digest_email(_digest_data())
        assert "refund policy" in text
        assert "pricing tiers" in text

    def test_zero_pending_shows_zero(self):
        data = _digest_data(pending_count=0)
        html, text = build_digest_email(data)
        assert "Pending your response: 0" in text

    def test_consent_notice_included(self):
        html, text = build_digest_email(_digest_data())
        assert "AI assistant" in html


# ---------------------------------------------------------------------------
# Weekly recap
# ---------------------------------------------------------------------------


class TestWeeklyRecapEmail:
    def test_subject_format(self):
        subject = build_weekly_recap_subject(_weekly_data())
        assert "[WEEKLY RECAP]" in subject
        assert "Apr 25" in subject

    def test_text_contains_total_messages(self):
        html, text = build_weekly_recap_email(_weekly_data())
        assert "Messages this week: 100" in text

    def test_text_contains_ai_percentage(self):
        html, text = build_weekly_recap_email(_weekly_data())
        assert "75%" in text

    def test_text_contains_human_percentage(self):
        html, text = build_weekly_recap_email(_weekly_data())
        assert "20%" in text

    def test_text_contains_ai_accuracy(self):
        html, text = build_weekly_recap_email(_weekly_data())
        assert "92%" in text
        assert "client acceptance" in text

    def test_text_lists_top_topics(self):
        html, text = build_weekly_recap_email(_weekly_data())
        assert "pricing" in text
        assert "refund" in text

    def test_top_topics_capped_at_five(self):
        data = _weekly_data(
            top_topics=["a", "b", "c", "d", "e", "f", "g"]
        )
        html, text = build_weekly_recap_email(data)
        assert text.count("\n - ") <= 5 or "f" not in text.split("Most common")[1][:100]

    def test_text_contains_knowledge_growth(self):
        html, text = build_weekly_recap_email(_weekly_data())
        assert "8 new answers" in text
        assert "45 total" in text

    def test_text_contains_response_times(self):
        html, text = build_weekly_recap_email(_weekly_data())
        assert "3 minutes (AI)" in text
        assert "2.5 hours (human)" in text

    def test_consent_notice_included(self):
        html, text = build_weekly_recap_email(_weekly_data())
        assert "AI assistant" in html


# ---------------------------------------------------------------------------
# Return summary
# ---------------------------------------------------------------------------


class TestReturnSummaryEmail:
    def test_subject_format(self):
        subject = build_return_summary_subject(_return_data())
        assert "[OOO COMPLETE]" in subject

    def test_text_contains_totals(self):
        html, text = build_return_summary_email(_return_data())
        assert "Messages received: 50" in text
        assert "Auto-resolved by AI: 40" in text
        assert "Resolved by backup: 8" in text
        assert "Still pending: 2" in text

    def test_text_lists_pending_items(self):
        html, text = build_return_summary_email(_return_data())
        assert "Refund policy question from Jane" in text
        assert "Shipping inquiry from Tom" in text

    def test_zero_pending_items(self):
        data = _return_data(still_pending=0, pending_items=[])
        html, text = build_return_summary_email(data)
        assert "Still pending: 0" in text
        assert "(none)" in text

    def test_text_contains_new_answers_learned(self):
        html, text = build_return_summary_email(_return_data())
        assert "6 new answers" in text

    def test_html_contains_pending_table(self):
        html, text = build_return_summary_email(_return_data())
        assert "Refund policy question from Jane" in html
        assert "high" in html

    def test_consent_notice_included(self):
        html, text = build_return_summary_email(_return_data())
        assert "AI assistant" in html
