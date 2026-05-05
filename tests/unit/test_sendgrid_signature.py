"""Unit tests for SendGrid Inbound Parse webhook signature verification.

Verifies ECDSA signature verification using the cryptography library.
"""

import base64

import pytest

from sequor.email.inbound import _verify_sendgrid_signature


class TestSendGridSignatureVerification:
    """ECDSA webhook signature verification."""

    def test_returns_false_when_key_not_configured(self, monkeypatch):
        """If SENDGRID_WEBHOOK_VERIFICATION_KEY is empty, reject."""
        monkeypatch.setattr(
            "sequor.email.inbound.settings.sendgrid_webhook_verification_key",
            "",
        )
        assert _verify_sendgrid_signature("body", "sig") is False

    def test_returns_false_on_invalid_signature(self, monkeypatch):
        """Invalid signature should return False, not raise."""
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        pub_der = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        monkeypatch.setattr(
            "sequor.email.inbound.settings.sendgrid_webhook_verification_key",
            base64.b64encode(pub_der).decode(),
        )

        wrong_sig = base64.b64encode(b"not-a-valid-signature").decode()
        assert _verify_sendgrid_signature("test body", wrong_sig) is False

    def test_valid_signature_passes(self, monkeypatch):
        """A properly signed body should verify successfully."""
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes, serialization

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        pub_der = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        monkeypatch.setattr(
            "sequor.email.inbound.settings.sendgrid_webhook_verification_key",
            base64.b64encode(pub_der).decode(),
        )

        body = "test webhook payload"
        signature = private_key.sign(
            body.encode("utf-8"),
            ec.ECDSA(hashes.SHA256()),
        )
        sig_b64 = base64.b64encode(signature).decode()

        assert _verify_sendgrid_signature(body, sig_b64) is True

    def test_returns_false_on_malformed_key(self, monkeypatch):
        """Malformed public key should return False, not raise."""
        monkeypatch.setattr(
            "sequor.email.inbound.settings.sendgrid_webhook_verification_key",
            base64.b64encode(b"not-a-valid-key").decode(),
        )
        assert _verify_sendgrid_signature("body", "sig") is False

    def test_returns_false_on_malformed_signature(self, monkeypatch):
        """Malformed signature should return False, not raise."""
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        pub_der = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        monkeypatch.setattr(
            "sequor.email.inbound.settings.sendgrid_webhook_verification_key",
            base64.b64encode(pub_der).decode(),
        )
        assert _verify_sendgrid_signature("body", "not-base64!!!") is False
