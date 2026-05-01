"""No hardcoded secrets guardrail test.

Ensures config defaults are empty strings (secrets must come from .env).
If someone accidentally hardcodes a key, this test catches it.
"""

from sequor.config import Settings


def test_stripe_defaults_are_empty():
    s = Settings(_env_file=None, database_url="postgresql://localhost/test")
    assert s.stripe_api_key == ""
    assert s.stripe_webhook_secret == ""
    assert s.stripe_starter_price_id == ""


def test_sendgrid_default_is_empty():
    s = Settings(_env_file=None, database_url="postgresql://localhost/test")
    assert s.sendgrid_api_key == ""
