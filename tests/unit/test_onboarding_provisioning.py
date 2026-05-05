"""Unit tests for onboarding service encryption key provisioning and schema creation.

Tests that signup() provisions encryption keys and creates tenant schemas,
and handles non-RuntimeError failures gracefully without blocking account creation.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sequor.schemas import OnboardingRequest


# A valid base64-encoded 32-byte key for testing.
TEST_ENCRYPTION_KEY = "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVphYmNkZWY="


def _make_uuid():
    return uuid.uuid4()


def _valid_request(**overrides):
    defaults = dict(
        org_name="Test Org",
        owner_email="owner@testorg.com",
        owner_password="SecurePass1",
        account_name="Front Desk",
        ownership_type="individual",
        backup_name="Backup Person",
        backup_email="backup@testorg.com",
        escalation_sla_hours=4,
        routing_rule="full_ai",
    )
    defaults.update(overrides)
    return OnboardingRequest(**defaults)


class _FakeResult:
    """Simulates SQLAlchemy scalar result."""

    def __init__(self, first_val=None):
        self._first = first_val

    def scalars(self):
        return self

    def first(self):
        return self._first


class _FakeSession:
    """Minimal async session that tracks operations."""

    def __init__(self, existing_account=None):
        self.added = []
        self.committed = False
        self.flushed = 0
        self._existing_account = existing_account

    async def execute(self, stmt):
        # Return mock result for the duplicate email check
        return _FakeResult(first_val=self._existing_account)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flushed += 1

    async def commit(self):
        self.committed = True

    async def connection(self):
        conn = AsyncMock()
        conn.execute = AsyncMock()
        conn.run_sync = AsyncMock()
        return conn


class TestOnboardingEncryptionProvisioning:
    """Tests for encryption key provisioning during signup."""

    @patch("sequor.onboarding.service.send_verification_email", new_callable=AsyncMock)
    @patch("sequor.db.encrypted_column.set_tenant_key")
    @patch("sequor.db.encryption_keys.KeyManager")
    @patch("sequor.config.settings")
    async def test_signup_provisions_encryption_key(
        self, mock_settings, MockKM, mock_set_key, mock_email
    ):
        """signup should call KeyManager.provision_tenant_key when key is configured."""
        from sequor.onboarding.service import signup

        mock_settings.encryption_master_key = TEST_ENCRYPTION_KEY
        mock_settings.sendgrid_api_key = None

        mock_km_instance = MagicMock()
        mock_km_instance.provision_tenant_key = AsyncMock(return_value=b"\x01" * 32)
        MockKM.return_value = mock_km_instance

        session = _FakeSession()
        result = await signup(session, _valid_request())

        assert result["tenant_id"] is not None
        mock_km_instance.provision_tenant_key.assert_called_once()
        mock_set_key.assert_called_once_with(b"\x01" * 32)

    @patch("sequor.onboarding.service.send_verification_email", new_callable=AsyncMock)
    @patch("sequor.config.settings")
    async def test_signup_raises_when_encryption_key_missing(self, mock_settings, mock_email):
        """signup should raise RuntimeError when ENCRYPTION_MASTER_KEY is not set."""
        from sequor.onboarding.service import signup

        mock_settings.encryption_master_key = None

        session = _FakeSession()
        with pytest.raises(RuntimeError, match="ENCRYPTION_MASTER_KEY"):
            await signup(session, _valid_request())

    @patch("sequor.onboarding.service.send_verification_email", new_callable=AsyncMock)
    @patch("sequor.db.encrypted_column.set_tenant_key")
    @patch("sequor.db.encryption_keys.KeyManager")
    @patch("sequor.config.settings")
    async def test_signup_converts_non_runtime_encryption_failure_to_runtime(
        self, mock_settings, MockKM, mock_set_key, mock_email
    ):
        """If KeyManager.provision_tenant_key raises a non-RuntimeError,
        signup re-raises as RuntimeError with a descriptive message."""
        from sequor.onboarding.service import signup

        mock_settings.encryption_master_key = TEST_ENCRYPTION_KEY
        mock_settings.sendgrid_api_key = None

        mock_km_instance = MagicMock()
        mock_km_instance.provision_tenant_key = AsyncMock(
            side_effect=OSError("Disk error during key provisioning")
        )
        MockKM.return_value = mock_km_instance

        session = _FakeSession()
        with pytest.raises(RuntimeError, match="Failed to provision tenant encryption key"):
            await signup(session, _valid_request())

    @patch("sequor.onboarding.service.send_verification_email", new_callable=AsyncMock)
    @patch("sequor.db.encrypted_column.set_tenant_key")
    @patch("sequor.db.encryption_keys.KeyManager")
    @patch("sequor.config.settings")
    async def test_signup_creates_tenant_account_and_backup(
        self, mock_settings, MockKM, mock_set_key, mock_email
    ):
        """Signup must create all three records: tenant, account, backup."""
        from sequor.onboarding.service import signup

        mock_settings.encryption_master_key = TEST_ENCRYPTION_KEY
        mock_settings.sendgrid_api_key = None

        mock_km_instance = MagicMock()
        mock_km_instance.provision_tenant_key = AsyncMock(return_value=b"\x01" * 32)
        MockKM.return_value = mock_km_instance

        session = _FakeSession()
        result = await signup(session, _valid_request())

        # Three objects added: Tenant, Account, BackupContact
        # (plus possible re-adds for linking)
        assert session.flushed >= 3  # tenant flush, account flush, backup flush


class TestOnboardingSchemaProvisioning:
    """Tests for tenant schema creation during signup."""

    @patch("sequor.onboarding.service.send_verification_email", new_callable=AsyncMock)
    @patch("sequor.db.encrypted_column.set_tenant_key")
    @patch("sequor.db.encryption_keys.KeyManager")
    @patch("sequor.config.settings")
    async def test_signup_handles_schema_creation_failure(
        self, mock_settings, MockKM, mock_set_key, mock_email
    ):
        """If create_tenant_schema fails, signup should still complete."""
        from sequor.onboarding.service import signup

        mock_settings.encryption_master_key = TEST_ENCRYPTION_KEY
        mock_settings.sendgrid_api_key = None

        mock_km_instance = MagicMock()
        mock_km_instance.provision_tenant_key = AsyncMock(return_value=b"\x01" * 32)
        MockKM.return_value = mock_km_instance

        session = _FakeSession()
        with patch("sequor.db.schema_manager.create_tenant_schema", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = RuntimeError("Schema creation failed")
            result = await signup(session, _valid_request())

        assert result["tenant_id"] is not None
        assert session.committed is True

    @patch("sequor.onboarding.service.send_verification_email", new_callable=AsyncMock)
    @patch("sequor.config.settings")
    async def test_signup_rejects_duplicate_email(self, mock_settings, mock_email):
        """Signup must reject duplicate owner_email."""
        from sequor.onboarding.service import signup, DuplicateEmailError

        mock_settings.encryption_master_key = TEST_ENCRYPTION_KEY

        existing = MagicMock()
        session = _FakeSession(existing_account=existing)

        with pytest.raises(DuplicateEmailError):
            await signup(session, _valid_request())
