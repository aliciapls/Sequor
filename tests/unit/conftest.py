"""Unit-tier shared fixtures.

The tenant-context boundary caches a process-wide KeyManager singleton
(`sequor.db.tenant_context._key_manager`). In production that shared LRU key
cache is desirable; in Tier-1 tests it would leak a real (or mocked) KeyManager
from one test into the next. Reset it around every unit test so each test starts
from a clean singleton and its own `@patch(...KeyManager)` is the one used.

Unit-tier contract: no ENCRYPTION_MASTER_KEY. Several unit fakes (FakeExpress in
the inbound tests, the learning-loop mocks) only implement the no-master-key
code path. A shell that exports ENCRYPTION_MASTER_KEY (e.g. after running the
Tier-2 loop in the same session) would otherwise activate the encryption
branches and the fakes cannot serve them, so the suite would fail when run in
such a shell. Force the no-key regime here so the unit suite is hermetic
regardless of shell env. Tests that genuinely need a key mock
``sequor.config.settings`` itself (test_onboarding_provisioning — signup
re-imports the patched settings) or stub the tenant boundary
(test_compliance_erasure), so they never read the real
``settings.encryption_master_key`` and are unaffected.
"""

import pytest

from sequor.config import settings
from sequor.db.tenant_context import reset_key_manager


@pytest.fixture(autouse=True)
def _reset_key_manager_singleton():
    reset_key_manager()
    yield
    reset_key_manager()


@pytest.fixture(autouse=True)
def _no_encryption_master_key(monkeypatch):
    """Force the unit-tier no-key regime (see module docstring)."""
    monkeypatch.setattr(settings, "encryption_master_key", None)
