"""Unit tests for Stripe webhook signature verification and idempotency."""

import pytest
import stripe as real_stripe
from unittest.mock import patch
from uuid import uuid4

from sequor.billing.service import (
    is_event_processed,
    mark_event_processed,
    verify_webhook_signature,
)


class TestWebhookSignatureVerification:
    def test_raises_if_no_secret_configured(self):
        with patch("sequor.config.settings.stripe_webhook_secret", ""):
            with pytest.raises(ValueError, match="STRIPE_WEBHOOK_SECRET"):
                verify_webhook_signature(b"{}", "")

    def test_raises_on_invalid_signature(self):
        with patch("sequor.config.settings.stripe_webhook_secret", "whsec_test"):
            with patch.object(real_stripe.Webhook, "construct_event") as mock_construct:
                mock_construct.side_effect = real_stripe.error.SignatureVerificationError(
                    "bad sig", "t=123,v1=bad"
                )
                with pytest.raises(ValueError, match="signature verification failed"):
                    verify_webhook_signature(b"{}", "t=123,v1=bad")

    def test_returns_event_on_valid_signature(self):
        with patch("sequor.config.settings.stripe_webhook_secret", "whsec_test"):
            mock_event = {"id": "evt_123", "type": "checkout.session.completed"}
            with patch.object(real_stripe.Webhook, "construct_event", return_value=mock_event):
                result = verify_webhook_signature(b"{}", "t=123,v1=good")
                assert result["id"] == "evt_123"


class TestWebhookIdempotency:
    def test_new_event_is_not_processed(self):
        assert is_event_processed("evt_never_seen") is False

    def test_processed_event_is_detected(self):
        event_id = f"evt_test_{uuid4()}"
        mark_event_processed(event_id)
        assert is_event_processed(event_id) is True

    def test_mark_then_check(self):
        event_id = f"evt_{uuid4()}"
        assert is_event_processed(event_id) is False
        mark_event_processed(event_id)
        assert is_event_processed(event_id) is True
