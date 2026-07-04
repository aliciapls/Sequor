"""Regression tests for sequor.auth JWT signing/verification.

Guards the redteam Round-1 CRITICAL: the JWT path used a world-known constant
fallback secret ("dev-secret-change-in-production") when JWT_SECRET was unset,
with no production gate — anyone could forge an admin token for any tenant.
The fix fails CLOSED outside development.
"""

import pytest

import sequor.auth as auth
from sequor.config import settings


@pytest.fixture
def restore_settings():
    orig_env, orig_secret = settings.app_env, settings.jwt_secret
    yield
    settings.app_env, settings.jwt_secret = orig_env, orig_secret


def _payload(**over):
    base = {
        "operator_id": "op-1",
        "tenant_id": "tenant-1",
        "account_id": "acct-1",
        "name": "T",
        "email": "t@example.com",
        "role": "operator",
    }
    base.update(over)
    return base


class TestJwtFailClosed:
    def test_prod_without_secret_refuses_to_sign(self, restore_settings):
        settings.app_env = "production"
        settings.jwt_secret = ""
        with pytest.raises(RuntimeError, match="JWT_SECRET is unset"):
            auth.create_access_token(_payload())

    def test_prod_without_secret_refuses_to_decode(self, restore_settings):
        settings.app_env = "production"
        settings.jwt_secret = ""
        with pytest.raises(RuntimeError, match="JWT_SECRET is unset"):
            auth.decode_token("any.token.value")

    def test_staging_without_secret_also_refuses(self, restore_settings):
        # Any non-"development" app_env must fail closed, not just production.
        settings.app_env = "staging"
        settings.jwt_secret = ""
        with pytest.raises(RuntimeError):
            auth.create_access_token(_payload())

    def test_dev_without_secret_still_works(self, restore_settings):
        settings.app_env = "development"
        settings.jwt_secret = ""
        tok = auth.create_access_token(_payload(role="admin"))
        assert auth.decode_token(tok)["role"] == "admin"

    def test_prod_with_real_secret_round_trips(self, restore_settings):
        settings.app_env = "production"
        settings.jwt_secret = "x" * 40
        tok = auth.create_access_token(_payload(tenant_id="t-9"))
        assert auth.decode_token(tok)["tenant_id"] == "t-9"

    def test_token_signed_with_other_secret_is_rejected(self, restore_settings):
        # A token forged under the OLD constant fallback must not verify once a
        # real secret is configured.
        settings.app_env = "production"
        settings.jwt_secret = "real-production-secret-at-least-32-bytes-long"
        from jose import jwt

        forged = jwt.encode(
            _payload(role="admin"), "dev-secret-change-in-production", algorithm=auth.ALGORITHM
        )
        assert auth.decode_token(forged) is None
