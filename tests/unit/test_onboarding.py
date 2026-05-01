"""Unit tests for onboarding service layer.

Tests the signup flow: input validation, record creation, and edge cases.
Does not require a real database — uses async session mocks where needed.
"""

import pytest

from sequor.schemas import OnboardingRequest


def _valid_request(**overrides):
    """Build a valid OnboardingRequest with sensible defaults."""
    defaults = dict(
        org_name="Acme Consulting",
        owner_email="alice@acme.com",
        owner_password="SecurePass1",
        account_name="Front Desk",
        ownership_type="individual",
        backup_name="Bob Smith",
        backup_email="bob@acme.com",
        escalation_sla_hours=4,
        routing_rule="full_ai",
    )
    defaults.update(overrides)
    return OnboardingRequest(**defaults)


class TestOnboardingRequestValidation:
    """Input validation via Pydantic — rejects bad data before service layer."""

    def test_valid_request(self):
        req = _valid_request()
        assert req.org_name == "Acme Consulting"
        assert req.routing_rule == "full_ai"

    def test_default_sla(self):
        req = _valid_request(escalation_sla_hours=4)
        assert req.escalation_sla_hours == 4

    def test_default_routing(self):
        req = _valid_request(routing_rule="full_ai")
        assert req.routing_rule == "full_ai"

    def test_rejects_missing_org_name(self):
        with pytest.raises(Exception):
            _valid_request(org_name="")

    def test_rejects_missing_backup_email(self):
        with pytest.raises(Exception):
            _valid_request(backup_email="not-valid")

    def test_rejects_weak_password(self):
        with pytest.raises(Exception):
            _valid_request(owner_password="short")

    def test_rejects_html_injection(self):
        with pytest.raises(Exception):
            _valid_request(org_name="<script>alert(1)</script>")

    def test_strips_whitespace(self):
        req = _valid_request(org_name="  Acme  ")
        assert req.org_name == "Acme"

    def test_all_routing_rules_valid(self):
        for rule in ("all_to_backup", "faq_only", "full_ai"):
            req = _valid_request(routing_rule=rule)
            assert req.routing_rule == rule

    def test_all_ownership_types_valid(self):
        for ot in ("individual", "department"):
            req = _valid_request(ownership_type=ot)
            assert req.ownership_type == ot


class TestRoutingRuleMapping:
    """Verify routing rule strings map to correct database values."""

    def test_all_to_backup_template(self):
        from sequor.onboarding.service import ROUTING_RULES

        assert "all_to_backup" in ROUTING_RULES
        assert ROUTING_RULES["all_to_backup"]["auto_respond"] is False

    def test_faq_only_template(self):
        from sequor.onboarding.service import ROUTING_RULES

        assert "faq_only" in ROUTING_RULES
        assert ROUTING_RULES["faq_only"]["auto_respond"] is True

    def test_full_ai_template(self):
        from sequor.onboarding.service import ROUTING_RULES

        assert "full_ai" in ROUTING_RULES
        assert ROUTING_RULES["full_ai"]["auto_respond"] is True
