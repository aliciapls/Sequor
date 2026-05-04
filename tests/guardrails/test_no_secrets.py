"""No hardcoded secrets guardrail test.

Ensures config defaults are empty strings (secrets must come from .env).
If someone accidentally hardcodes a key, this test catches it.
"""

from sequor.config import Settings

_SECRET_KEYS = [
    "STRIPE_API_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_STARTER_PRICE_ID",
    "SENDGRID_API_KEY",
]


def test_stripe_defaults_are_empty(monkeypatch):
    for key in _SECRET_KEYS[:3]:
        monkeypatch.delenv(key, raising=False)
    s = Settings(_env_file=None, database_url="postgresql://localhost/test")
    assert s.stripe_api_key == ""
    assert s.stripe_webhook_secret == ""
    assert s.stripe_starter_price_id == ""


def test_sendgrid_default_is_empty(monkeypatch):
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
    s = Settings(_env_file=None, database_url="postgresql://localhost/test")
    assert s.sendgrid_api_key == ""
