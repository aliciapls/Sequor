"""PDPA compliance guardrail tests.

These tests enforce the compliance contract. Every feature that touches
personal data must pass these tests. If any test fails, the feature
is not compliant and must not ship.
"""

import pytest

from sequor.compliance import (
    CONSENT_NOTICE,
    OPT_OUT_KEYWORDS,
    build_consent_notice,
    is_opt_out,
)


class TestConsentNotice:
    """The consent notice must appear in every first auto-reply."""

    def test_consent_notice_is_nonempty(self):
        assert len(CONSENT_NOTICE) > 0

    def test_consent_notice_mentions_ai(self):
        assert "AI assistant" in CONSENT_NOTICE

    def test_consent_notice_mentions_opt_out(self):
        assert "HUMAN" in CONSENT_NOTICE

    def test_consent_notice_mentions_processing(self):
        assert "processed" in CONSENT_NOTICE

    def test_build_consent_notice_includes_org_name(self):
        notice = build_consent_notice("Acme Consulting")
        assert "Acme Consulting" in notice


class TestOptOutDetection:
    """HUMAN/STOP keywords must trigger immediate opt-out."""

    def test_human_exact_match(self):
        assert is_opt_out("HUMAN") is True

    def test_human_lowercase(self):
        assert is_opt_out("human") is True

    def test_human_mixed_case(self):
        assert is_opt_out("Human") is True

    def test_human_with_trailing_whitespace(self):
        assert is_opt_out("  HUMAN  ") is True

    def test_human_with_additional_text(self):
        assert is_opt_out("HUMAN I want to speak to someone") is True

    def test_stop_keyword(self):
        assert is_opt_out("STOP") is True

    def test_normal_message_is_not_opt_out(self):
        assert is_opt_out("What are your opening hours?") is False

    def test_empty_message_is_not_opt_out(self):
        assert is_opt_out("") is False

    def test_human_embedded_in_word_is_not_opt_out(self):
        """'humanity' should NOT trigger opt-out — it's a different word from HUMAN."""
        assert is_opt_out("humanity") is False
        assert is_opt_out("I study humanity") is False


class TestPIIErasure:
    """Erasure must remove all personally identifiable information.

    These tests exercise the compliance module constants.
    The integration test (erasing a contact and verifying DB state)
    lives in tests/guardrails/test_erasure_integration.py.
    """

    def test_pii_fields_listed(self):
        from sequor.compliance import PII_FIELDS

        assert "email" in PII_FIELDS
        assert "phone" in PII_FIELDS
        assert "name" in PII_FIELDS

    def test_erasure_replaces_name_with_erased(self):
        from sequor.compliance import ERASURE_NULL_FIELDS

        assert ERASURE_NULL_FIELDS["name"] == "[erased]"
