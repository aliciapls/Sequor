"""Unit-tier shared fixtures.

The tenant-context boundary caches a process-wide KeyManager singleton
(`sequor.db.tenant_context._key_manager`). In production that shared LRU key
cache is desirable; in Tier-1 tests it would leak a real (or mocked) KeyManager
from one test into the next. Reset it around every unit test so each test starts
from a clean singleton and its own `@patch(...KeyManager)` is the one used.
"""

import pytest

from sequor.db.tenant_context import reset_key_manager


@pytest.fixture(autouse=True)
def _reset_key_manager_singleton():
    reset_key_manager()
    yield
    reset_key_manager()
