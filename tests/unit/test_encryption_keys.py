"""Unit tests for sequor.db.encryption_keys."""

import os
from base64 import b64encode
from uuid import uuid4

import pytest

from sequor.db.encryption_keys import KeyManager


def _make_master_key() -> str:
    return b64encode(os.urandom(32)).decode("ascii")


class TestKeyManagerInit:
    def test_valid_master_key(self):
        km = KeyManager(_make_master_key())
        assert km is not None

    def test_empty_master_key_raises(self):
        with pytest.raises(ValueError, match="not set"):
            KeyManager("")

    def test_wrong_length_raises(self):
        with pytest.raises(ValueError, match="32 bytes"):
            KeyManager(b64encode(b"short").decode())


class TestGenerateAndEncrypt:
    def test_generate_returns_32_bytes(self):
        km = KeyManager(_make_master_key())
        key = km.generate_tenant_key()
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_encrypt_decrypt_roundtrip(self):
        km = KeyManager(_make_master_key())
        raw = km.generate_tenant_key()
        encrypted = km.encrypt_tenant_key(raw)
        assert isinstance(encrypted, str)
        decrypted = km.decrypt_tenant_key(encrypted)
        assert decrypted == raw

    def test_different_keys_produce_different_ciphertext(self):
        km = KeyManager(_make_master_key())
        raw = km.generate_tenant_key()
        enc1 = km.encrypt_tenant_key(raw)
        enc2 = km.encrypt_tenant_key(raw)
        assert enc1 != enc2  # random nonce

    def test_wrong_master_key_fails(self):
        km1 = KeyManager(_make_master_key())
        km2 = KeyManager(_make_master_key())
        raw = km1.generate_tenant_key()
        encrypted = km1.encrypt_tenant_key(raw)
        with pytest.raises(Exception):
            km2.decrypt_tenant_key(encrypted)


class TestCache:
    def test_cache_returns_same_key(self):
        km = KeyManager(_make_master_key())
        tid = uuid4()
        raw = os.urandom(32)
        encrypted = km.encrypt_tenant_key(raw)
        # Manually put in cache
        km._cache[tid] = raw
        km._cache.move_to_end(tid)
        # Verify cache hit works
        cached = km._cache_get(tid)
        assert cached == raw

    def test_cache_evicts_at_max(self):
        km = KeyManager(_make_master_key())
        for i in range(1001):
            km._cache_put(uuid4(), os.urandom(32))
        assert len(km._cache) <= 1000
