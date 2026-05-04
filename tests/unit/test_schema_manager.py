"""Unit tests for sequor.db.schema_manager."""

import pytest

from sequor.db.schema_manager import (
    IdentifierError,
    tenant_id_to_schema,
    validate_identifier,
)


class TestValidateIdentifier:
    def test_valid_name(self):
        validate_identifier("tenant_abc123")

    def test_valid_underscore_name(self):
        validate_identifier("_private")

    def test_rejects_sql_injection(self):
        with pytest.raises(IdentifierError):
            validate_identifier('users"; DROP TABLE customers; --')

    def test_rejects_spaces(self):
        with pytest.raises(IdentifierError):
            validate_identifier("has space")

    def test_rejects_starts_with_digit(self):
        with pytest.raises(IdentifierError):
            validate_identifier("123abc")

    def test_rejects_over_63_chars(self):
        with pytest.raises(IdentifierError, match="63-char limit"):
            validate_identifier("a" * 64)

    def test_rejects_exactly_63_passes(self):
        validate_identifier("a" * 63)

    def test_rejects_non_string(self):
        with pytest.raises(IdentifierError, match="must be a string"):
            validate_identifier(123)

    def test_rejects_special_chars(self):
        with pytest.raises(IdentifierError):
            validate_identifier("name;DROP")

    def test_rejects_hyphen(self):
        with pytest.raises(IdentifierError):
            validate_identifier("has-hyphen")

    def test_accepts_max_length(self):
        validate_identifier("t" * 63)

    def test_rejects_empty(self):
        with pytest.raises(IdentifierError):
            validate_identifier("")


class TestTenantIdToSchema:
    def test_converts_uuid(self):
        schema = tenant_id_to_schema("550e8400-e29b-41d4-a716-446655440000")
        assert schema == "tenant_550e8400e29b41d4a716446655440000"

    def test_deterministic(self):
        uid = "550e8400-e29b-41d4-a716-446655440000"
        assert tenant_id_to_schema(uid) == tenant_id_to_schema(uid)

    def test_different_uuids_different_schemas(self):
        a = tenant_id_to_schema("550e8400-e29b-41d4-a716-446655440000")
        b = tenant_id_to_schema("660e8400-e29b-41d4-a716-446655440001")
        assert a != b

    def test_accepts_uuid_object(self):
        from uuid import UUID
        uid = UUID("550e8400-e29b-41d4-a716-446655440000")
        schema = tenant_id_to_schema(uid)
        assert schema.startswith("tenant_")
        assert len(schema) == 39  # "tenant_" (7) + 32 hex chars
