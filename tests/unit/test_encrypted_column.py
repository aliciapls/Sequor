"""Unit tests for sequor.db.encrypted_column."""

import pytest

from sequor.db.encrypted_column import (
    EncryptedString,
    compute_blind_index,
    derive_field_key,
    get_tenant_key,
    set_tenant_key,
)


@pytest.fixture
def tenant_key():
    key = b"\x01" * 32
    set_tenant_key(key)
    yield key
    set_tenant_key(None)


class TestKeyDerivation:
    def test_different_fields_produce_different_keys(self, tenant_key):
        k1 = derive_field_key(tenant_key, "email")
        k2 = derive_field_key(tenant_key, "phone")
        assert k1 != k2
        assert len(k1) == 32
        assert len(k2) == 32

    def test_same_field_same_key(self, tenant_key):
        k1 = derive_field_key(tenant_key, "email")
        k2 = derive_field_key(tenant_key, "email")
        assert k1 == k2

    def test_different_tenant_same_field_different_key(self):
        key_a = b"\x01" * 32
        key_b = b"\x02" * 32
        ka = derive_field_key(key_a, "email")
        kb = derive_field_key(key_b, "email")
        assert ka != kb


class TestBlindIndex:
    def test_deterministic(self, tenant_key):
        h1 = compute_blind_index(tenant_key, "user@example.com")
        h2 = compute_blind_index(tenant_key, "user@example.com")
        assert h1 == h2

    def test_different_values_different_hash(self, tenant_key):
        h1 = compute_blind_index(tenant_key, "alice@example.com")
        h2 = compute_blind_index(tenant_key, "bob@example.com")
        assert h1 != h2

    def test_hex_output_length(self, tenant_key):
        h = compute_blind_index(tenant_key, "test@test.com")
        assert len(h) == 64  # SHA-256 hex = 64 chars

    def test_different_tenant_same_value_different_hash(self):
        key_a = b"\x01" * 32
        key_b = b"\x02" * 32
        ha = compute_blind_index(key_a, "same@example.com")
        hb = compute_blind_index(key_b, "same@example.com")
        assert ha != hb


class TestEncryptedString:
    def test_encrypt_decrypt_roundtrip(self, tenant_key):
        col = EncryptedString(field_name="email")
        plaintext = "user@example.com"
        encrypted = col.process_bind_param(plaintext, dialect=None)
        assert encrypted != plaintext
        decrypted = col.process_result_value(encrypted, dialect=None)
        assert decrypted == plaintext

    def test_none_passthrough(self, tenant_key):
        col = EncryptedString(field_name="email")
        assert col.process_bind_param(None, dialect=None) is None
        assert col.process_result_value(None, dialect=None) is None

    def test_no_tenant_key_raises(self):
        # Regression (redteam R1): fail-closed is sourced from settings.app_env
        # (the single config source), NOT a raw os.environ["APP_ENV"] read that
        # defaulted to "development" and silently wrote plaintext in prod.
        from sequor.config import settings

        orig_env = settings.app_env
        settings.app_env = "production"
        try:
            set_tenant_key(None)
            col = EncryptedString(field_name="email")
            with pytest.raises(RuntimeError, match="tenant key"):
                col.process_bind_param("test@test.com", dialect=None)
            # decrypt path must fail-closed too
            with pytest.raises(RuntimeError, match="tenant key"):
                col.process_result_value("ciphertext", dialect=None)
        finally:
            settings.app_env = orig_env

    def test_dev_mode_allows_no_key(self):
        """In development mode, EncryptedString stores plaintext when no tenant key is set."""
        import os

        orig_env = os.environ.get("APP_ENV")
        os.environ["APP_ENV"] = "development"
        try:
            set_tenant_key(None)
            col = EncryptedString(field_name="email")
            # Should store plaintext in dev mode, not raise
            result = col.process_bind_param("test@test.com", dialect=None)
            assert result == "test@test.com"
        finally:
            if orig_env is None:
                os.environ.pop("APP_ENV", None)
            else:
                os.environ["APP_ENV"] = orig_env

    def test_wrong_key_fails_to_decrypt(self, tenant_key):
        col = EncryptedString(field_name="email")
        encrypted = col.process_bind_param("secret@test.com", dialect=None)
        set_tenant_key(b"\xff" * 32)
        with pytest.raises(Exception):
            col.process_result_value(encrypted, dialect=None)

    def test_different_fields_different_ciphertext(self, tenant_key):
        col_email = EncryptedString(field_name="email")
        col_phone = EncryptedString(field_name="phone")
        enc_email = col_email.process_bind_param("same-value", dialect=None)
        enc_phone = col_phone.process_bind_param("same-value", dialect=None)
        assert enc_email != enc_phone

    def test_cache_ok_true(self):
        assert EncryptedString.cache_ok is True
