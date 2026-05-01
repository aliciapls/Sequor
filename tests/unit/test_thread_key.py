"""Unit tests for thread key derivation."""

from sequor.escalation.thread_key import (
    derive_thread_key,
    extract_topic,
    normalize_email,
    normalize_phone,
)


class TestNormalizeEmail:
    def test_lowercases(self):
        assert normalize_email("Alice@Example.COM") == "alice@example.com"

    def test_strips_whitespace(self):
        assert normalize_email("  alice@example.com  ") == "alice@example.com"

    def test_preserves_email_local_part(self):
        assert normalize_email("alice+tag@example.com") == "alice+tag@example.com"


class TestNormalizePhone:
    def test_removes_nondigits(self):
        assert normalize_phone("+1 (555) 123-4567") == "15551234567"

    def test_empty_phone(self):
        assert normalize_phone("") == ""

    def test_already_digits(self):
        assert normalize_phone("5551234567") == "5551234567"


class TestExtractTopic:
    def test_returns_first_five_significant_words(self):
        body = "Hello can you please tell me what is the refund policy for annual plans"
        assert extract_topic(body) == "refund policy annual plans"

    def test_filters_stop_words(self):
        body = "please can you tell me the refund policy"
        assert extract_topic(body) == "refund policy"

    def test_filters_short_words(self):
        body = "hi I need help with my order number 12345"
        assert "hi" not in extract_topic(body)
        assert "I" not in extract_topic(body)
        assert "my" not in extract_topic(body)

    def test_empty_body(self):
        assert extract_topic("") == ""
        assert extract_topic("a an the is are") == ""

    def test_less_than_five_words(self):
        body = "what is the refund policy"
        assert extract_topic(body) == "refund policy"

    def test_punctuation_stripped(self):
        body = "Hello, what is the refund policy? I need help!"
        topic = extract_topic(body)
        assert "Hello," not in topic
        assert "policy?" not in topic


class TestDeriveThreadKey:
    def test_same_inputs_produce_same_key(self):
        key1 = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone=None,
            message_body="What is the refund policy?",
        )
        key2 = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone=None,
            message_body="What is the refund policy?",
        )
        assert key1 == key2

    def test_different_email_produces_different_key(self):
        key1 = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone=None,
            message_body="What is the refund policy?",
        )
        key2 = derive_thread_key(
            contact_email="bob@example.com",
            contact_phone=None,
            message_body="What is the refund policy?",
        )
        assert key1 != key2

    def test_different_topic_produces_different_key(self):
        key1 = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone=None,
            message_body="What is the refund policy?",
        )
        key2 = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone=None,
            message_body="What are your business hours?",
        )
        assert key1 != key2

    def test_email_normalized(self):
        key1 = derive_thread_key(
            contact_email="Alice@Example.COM",
            contact_phone=None,
            message_body="Refund question",
        )
        key2 = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone=None,
            message_body="Refund question",
        )
        assert key1 == key2

    def test_phone_used_when_email_absent(self):
        key1 = derive_thread_key(
            contact_email=None,
            contact_phone="+1 555-123-4567",
            message_body="Refund question",
        )
        key2 = derive_thread_key(
            contact_email=None,
            contact_phone="15551234567",
            message_body="Refund question",
        )
        assert key1 == key2

    def test_email_preferred_over_phone(self):
        key1 = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone="+1 555-123-4567",
            message_body="Refund question",
        )
        key2 = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone="15551234567",
            message_body="Refund question",
        )
        assert key1 == key2

    def test_unknown_when_neither_provided(self):
        key1 = derive_thread_key(
            contact_email=None,
            contact_phone=None,
            message_body="Refund question",
        )
        key2 = derive_thread_key(
            contact_email=None,
            contact_phone=None,
            message_body="Refund question",
        )
        assert key1 == key2

    def test_returns_sha256_hex(self):
        key = derive_thread_key(
            contact_email="alice@example.com",
            contact_phone=None,
            message_body="Refund question",
        )
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)
