"""Input validation guardrail tests.

These tests enforce that all user-facing inputs are validated before
reaching the database. If a validation rule is removed or weakened,
these tests fail.
"""

import pytest
from pydantic import ValidationError

from sequor.schemas import (
    ContactErasureRequest,
    DocumentUploadRequest,
    OnboardingRequest,
)


class TestOnboardingValidation:
    """Onboarding form rejects invalid input."""

    def test_valid_onboarding(self):
        req = OnboardingRequest(
            org_name="Acme Consulting",
            owner_email="alice@acme.com",
            owner_password="SecurePass1",
            account_name="Main Account",
            ownership_type="individual",
            backup_name="Bob",
            backup_email="bob@acme.com",
        )
        assert req.org_name == "Acme Consulting"

    def test_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(
                org_name="Acme",
                owner_email="not-an-email",
                owner_password="SecurePass1",
                account_name="Main",
                ownership_type="individual",
                backup_name="Bob",
                backup_email="bob@acme.com",
            )

    def test_rejects_short_password(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(
                org_name="Acme",
                owner_email="alice@acme.com",
                owner_password="short",
                account_name="Main",
                ownership_type="individual",
                backup_name="Bob",
                backup_email="bob@acme.com",
            )

    def test_rejects_password_without_uppercase(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(
                org_name="Acme",
                owner_email="alice@acme.com",
                owner_password="lowercase1",
                account_name="Main",
                ownership_type="individual",
                backup_name="Bob",
                backup_email="bob@acme.com",
            )

    def test_rejects_password_without_digit(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(
                org_name="Acme",
                owner_email="alice@acme.com",
                owner_password="NoDigitsHere",
                account_name="Main",
                ownership_type="individual",
                backup_name="Bob",
                backup_email="bob@acme.com",
            )

    def test_rejects_html_in_org_name(self):
        with pytest.raises(ValidationError, match="HTML"):
            OnboardingRequest(
                org_name="<script>alert('xss')</script>",
                owner_email="alice@acme.com",
                owner_password="SecurePass1",
                account_name="Main",
                ownership_type="individual",
                backup_name="Bob",
                backup_email="bob@acme.com",
            )

    def test_rejects_html_in_backup_name(self):
        with pytest.raises(ValidationError, match="HTML"):
            OnboardingRequest(
                org_name="Acme",
                owner_email="alice@acme.com",
                owner_password="SecurePass1",
                account_name="Main",
                ownership_type="individual",
                backup_name="<img src=x onerror=alert(1)>",
                backup_email="bob@acme.com",
            )

    def test_rejects_invalid_ownership_type(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(
                org_name="Acme",
                owner_email="alice@acme.com",
                owner_password="SecurePass1",
                account_name="Main",
                ownership_type="corporation",
                backup_name="Bob",
                backup_email="bob@acme.com",
            )

    def test_rejects_invalid_routing_rule(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(
                org_name="Acme",
                owner_email="alice@acme.com",
                owner_password="SecurePass1",
                account_name="Main",
                ownership_type="individual",
                backup_name="Bob",
                backup_email="bob@acme.com",
                routing_rule="custom_rule",
            )

    def test_rejects_sla_out_of_range(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(
                org_name="Acme",
                owner_email="alice@acme.com",
                owner_password="SecurePass1",
                account_name="Main",
                ownership_type="individual",
                backup_name="Bob",
                backup_email="bob@acme.com",
                escalation_sla_hours=0,
            )

    def test_strips_whitespace_from_names(self):
        req = OnboardingRequest(
            org_name="  Acme  ",
            owner_email="alice@acme.com",
            owner_password="SecurePass1",
            account_name="  Main  ",
            ownership_type="individual",
            backup_name="  Bob  ",
            backup_email="bob@acme.com",
        )
        assert req.org_name == "Acme"
        assert req.account_name == "Main"
        assert req.backup_name == "Bob"


class TestDocumentUploadValidation:
    """Document upload rejects dangerous filenames."""

    def test_valid_upload(self):
        req = DocumentUploadRequest(document_type="faq", filename="prices.pdf")
        assert req.filename == "prices.pdf"

    def test_rejects_path_traversal(self):
        with pytest.raises(ValidationError, match="Invalid filename"):
            DocumentUploadRequest(document_type="faq", filename="../etc/passwd")

    def test_rejects_backslash_traversal(self):
        with pytest.raises(ValidationError, match="Invalid filename"):
            DocumentUploadRequest(document_type="faq", filename="..\\windows\\system32")

    def test_rejects_html_in_filename(self):
        with pytest.raises(ValidationError, match="HTML"):
            DocumentUploadRequest(document_type="faq", filename="<script>.pdf")

    def test_rejects_invalid_document_type(self):
        with pytest.raises(ValidationError):
            DocumentUploadRequest(document_type="executable", filename="file.pdf")


class TestErasureRequestValidation:
    """Erasure requires explicit confirmation."""

    def test_rejects_unconfirmed_erasure(self):
        with pytest.raises(ValidationError, match="explicit confirmation"):
            ContactErasureRequest(contact_id="abc", confirmed=False)

    def test_accepts_confirmed_erasure(self):
        req = ContactErasureRequest(contact_id="abc", confirmed=True)
        assert req.confirmed is True
