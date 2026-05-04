"""Integration tests for SendGridEmailSender — client construction and Mail building."""

import uuid

import pytest

from sequor.email.sender import SendGridEmailSender, _mask_email
from sequor.protocols import EmailSender


class TestSendGridClientConstruction:
    def test_raises_on_empty_api_key(self):
        with pytest.raises(ValueError, match="SENDGRID_API_KEY"):
            SendGridEmailSender(api_key="", from_domain="test.com", rate_limit_per_minute=10)

    def test_client_created_with_valid_key(self):
        sender = SendGridEmailSender(
            api_key="SG.test-key-not-real",
            from_domain="example.com",
            rate_limit_per_minute=10,
        )
        assert sender._client is not None
        assert sender._from_domain == "example.com"

    def test_from_domain_from_parameter(self):
        sender = SendGridEmailSender(
            api_key="SG.test-key",
            from_domain="custom.domain.com",
            rate_limit_per_minute=10,
        )
        assert sender._from_domain == "custom.domain.com"


class TestMailBuilding:
    def test_mail_has_correct_from_address(self):
        sender = SendGridEmailSender(
            api_key="SG.test-key",
            from_domain="acme.com",
            rate_limit_per_minute=60,
        )
        mail = sender._build_mail(
            to="owner@acme.com",
            subject="Test",
            body_html="<p>Hello</p>",
            body_text="Hello",
        )
        mail_json = mail.get()
        assert mail_json["from"]["email"] == "coverage@acme.com"

    def test_mail_has_reply_to(self):
        sender = SendGridEmailSender(
            api_key="SG.test-key",
            from_domain="acme.com",
            rate_limit_per_minute=60,
        )
        mail = sender._build_mail(
            to="owner@acme.com",
            subject="Test",
            body_html="<p>Hello</p>",
            body_text="Hello",
            reply_to="coverage@acme.com",
        )
        mail_json = mail.get()
        assert mail_json["reply_to"]["email"] == "coverage@acme.com"

    def test_mail_has_in_reply_to_header(self):
        sender = SendGridEmailSender(
            api_key="SG.test-key",
            from_domain="acme.com",
            rate_limit_per_minute=60,
        )
        mail = sender._build_mail(
            to="owner@acme.com",
            subject="Re: Test",
            body_html="<p>Reply</p>",
            body_text="Reply",
            in_reply_to="<msg-123@sendgrid.com>",
        )
        mail_json = mail.get()
        assert mail_json["headers"]["In-Reply-To"] == "<msg-123@sendgrid.com>"
        assert mail_json["headers"]["References"] == "<msg-123@sendgrid.com>"

    def test_mail_has_escalation_custom_arg(self):
        sender = SendGridEmailSender(
            api_key="SG.test-key",
            from_domain="acme.com",
            rate_limit_per_minute=60,
        )
        esc_id = str(uuid.uuid4())
        mail = sender._build_mail(
            to="backup@acme.com",
            subject="[UNRESOLVED] Something",
            body_html="<p>Details</p>",
            body_text="Details",
            escalation_id=esc_id,
        )
        mail_json = mail.get()
        assert mail_json["custom_args"]["escalation_id"] == esc_id
        assert mail_json["headers"]["X-Sequor-Escalation-Id"] == esc_id


class TestEmailSenderProtocol:
    def test_sender_satisfies_protocol(self):
        assert isinstance(
            SendGridEmailSender(
                api_key="SG.test",
                from_domain="test.com",
                rate_limit_per_minute=10,
            ),
            EmailSender,
        )


class TestEmailMasking:
    def test_masks_normal_email(self):
        assert _mask_email("alice@example.com") == "a***@example.com"

    def test_masks_short_local(self):
        assert _mask_email("ab@example.com") == "***@example.com"

    def test_handles_no_at(self):
        assert _mask_email("invalid") == "***"
