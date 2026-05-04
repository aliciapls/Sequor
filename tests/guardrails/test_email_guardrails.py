"""Guardrail tests for the email module — no secrets, protocol compliance."""

import pytest

from sequor.email.sender import SendGridEmailSender
from sequor.protocols import EmailSender


class TestEmailSecrets:
    def test_sender_rejects_empty_key(self):
        with pytest.raises(ValueError, match="SENDGRID_API_KEY"):
            SendGridEmailSender(api_key="", from_domain="test.com", rate_limit_per_minute=10)


class TestProtocolCompliance:
    def test_sender_implements_email_sender_protocol(self):
        sender = SendGridEmailSender(
            api_key="SG.test",
            from_domain="test.com",
            rate_limit_per_minute=10,
        )
        assert isinstance(sender, EmailSender)
        assert hasattr(sender, "send_email")
        assert callable(sender.send_email)

    def test_all_templates_return_dual_format(self):
        from sequor.email.templates import (
            build_digest_email,
            build_escalation_email,
            build_return_summary_email,
            build_weekly_recap_email,
        )

        esc_data = {
            "escalation_id": "abc12345-6789",
            "contact_name": "Test",
            "contact_channel": "email",
            "received_at": "2026-05-01",
            "ai_attempted": "RAG",
            "confidence_score": 0.5,
            "confidence_category": "moderate",
            "original_message_body": "Hello",
            "escalation_deadline": "2026-05-01",
            "backup_name": "Backup",
            "suggested_response": None,
            "org_name": "Test",
            "one_line_summary": "Test summary",
        }
        html, text = build_escalation_email(esc_data)
        assert isinstance(html, str) and isinstance(text, str)
        assert len(html) > 0 and len(text) > 0

        digest_data = {
            "account_name": "Test",
            "date": "2026-05-01",
            "ai_handled_count": 0,
            "rag_resolved_count": 0,
            "learned_answers_count": 0,
            "pending_count": 0,
            "oldest_unresolved_hours": None,
            "escalated_count": 0,
            "breached_count": 0,
            "new_knowledge_count": 0,
            "new_knowledge_topics": [],
            "org_name": "Test",
        }
        html, text = build_digest_email(digest_data)
        assert isinstance(html, str) and isinstance(text, str)

        weekly_data = {
            "account_name": "Test",
            "date_range": "May 1",
            "total_messages": 0,
            "ai_auto_resolved": 0,
            "human_resolved": 0,
            "pending": 0,
            "ai_accuracy_pct": 0.0,
            "top_topics": [],
            "knowledge_new": 0,
            "knowledge_total": 0,
            "avg_ai_response_minutes": 0.0,
            "avg_human_response_hours": 0.0,
            "org_name": "Test",
        }
        html, text = build_weekly_recap_email(weekly_data)
        assert isinstance(html, str) and isinstance(text, str)

        return_data = {
            "account_name": "Test",
            "date_range": "May 1",
            "total_received": 0,
            "auto_resolved": 0,
            "backup_resolved": 0,
            "still_pending": 0,
            "pending_items": [],
            "new_answers_learned": 0,
            "org_name": "Test",
        }
        html, text = build_return_summary_email(return_data)
        assert isinstance(html, str) and isinstance(text, str)
