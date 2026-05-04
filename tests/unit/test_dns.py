"""Tests for DNS record generation and verification logic."""

import pytest
from unittest.mock import patch, MagicMock

from sequor.dns.service import (
    generate_dns_records,
    verify_dns_records,
    _check_spf,
    _check_dkim,
    _check_dmarc,
)


class TestGenerateDNSRecords:
    """generate_dns_records returns SPF, DKIM, DMARC records."""

    def test_returns_three_records(self):
        records = generate_dns_records("acme.com")
        assert len(records) == 3

    def test_spf_record(self):
        records = generate_dns_records("acme.com")
        spf = records[0]
        assert spf["type"] == "TXT"
        assert spf["host"] == "acme.com"
        assert "v=spf1" in spf["value"]
        assert "sequor" in spf["value"]

    def test_dkim_record(self):
        records = generate_dns_records("acme.com")
        dkim = records[1]
        assert dkim["type"] == "CNAME"
        assert "sequor._domainkey.acme.com" == dkim["host"]
        assert "sequor" in dkim["value"]

    def test_dmarc_record(self):
        records = generate_dns_records("acme.com")
        dmarc = records[2]
        assert dmarc["type"] == "TXT"
        assert "_dmarc.acme.com" == dmarc["host"]
        assert "v=DMARC1" in dmarc["value"]

    def test_custom_selector(self):
        records = generate_dns_records("acme.com", selector="custom")
        dkim = records[1]
        assert "custom._domainkey.acme.com" == dkim["host"]

    def test_each_record_has_description(self):
        records = generate_dns_records("acme.com")
        for r in records:
            assert "description" in r
            assert len(r["description"]) > 0


class TestVerifyDNSRecords:
    """verify_dns_records checks live DNS for required records."""

    @patch("sequor.dns.service._check_dmarc", return_value=True)
    @patch("sequor.dns.service._check_dkim", return_value=True)
    @patch("sequor.dns.service._check_spf", return_value=True)
    def test_all_verified(self, mock_spf, mock_dkim, mock_dmarc):
        result = verify_dns_records("acme.com")
        assert result["verified"] is True
        assert result["errors"] == []
        assert len(result["records"]) == 3

    @patch("sequor.dns.service._check_dmarc", return_value=True)
    @patch("sequor.dns.service._check_dkim", return_value=False)
    @patch("sequor.dns.service._check_spf", return_value=True)
    def test_partial_failure(self, mock_spf, mock_dkim, mock_dmarc):
        result = verify_dns_records("acme.com")
        assert result["verified"] is False
        assert "DKIM" in result["errors"]

    @patch("sequor.dns.service._check_dmarc", return_value=False)
    @patch("sequor.dns.service._check_dkim", return_value=False)
    @patch("sequor.dns.service._check_spf", return_value=False)
    def test_none_verified(self, mock_spf, mock_dkim, mock_dmarc):
        result = verify_dns_records("acme.com")
        assert result["verified"] is False
        assert len(result["errors"]) == 3


class TestIndividualDNSChecks:
    """Unit tests for individual DNS check helpers with mocked resolver."""

    @patch("sequor.dns.service.dns.resolver.resolve")
    def test_spf_found(self, mock_resolve):
        mock_rdata = MagicMock()
        mock_rdata.to_text.return_value = '"v=spf1 include:mail.sequor.app ~all"'
        mock_resolve.return_value = [mock_rdata]
        assert _check_spf("acme.com") is True

    @patch("sequor.dns.service.dns.resolver.resolve")
    def test_spf_missing(self, mock_resolve):
        mock_rdata = MagicMock()
        mock_rdata.to_text.return_value = '"v=spf1 include:other.provider ~all"'
        mock_resolve.return_value = [mock_rdata]
        assert _check_spf("acme.com") is False

    @patch("sequor.dns.service.dns.resolver.resolve")
    def test_spf_nxdomain(self, mock_resolve):
        import dns.resolver
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        assert _check_spf("nonexistent.test") is False

    @patch("sequor.dns.service.dns.resolver.resolve")
    def test_dkim_found(self, mock_resolve):
        mock_rdata = MagicMock()
        mock_rdata.target = "sequor.domainkey.mail.sequor.app."
        mock_resolve.return_value = [mock_rdata]
        assert _check_dkim("acme.com", "sequor") is True

    @patch("sequor.dns.service.dns.resolver.resolve")
    def test_dkim_missing(self, mock_resolve):
        import dns.resolver
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        assert _check_dkim("acme.com", "sequor") is False

    @patch("sequor.dns.service.dns.resolver.resolve")
    def test_dmarc_found(self, mock_resolve):
        mock_rdata = MagicMock()
        mock_rdata.to_text.return_value = '"v=DMARC1; p=none;"'
        mock_resolve.return_value = [mock_rdata]
        assert _check_dmarc("acme.com") is True

    @patch("sequor.dns.service.dns.resolver.resolve")
    def test_dmarc_missing(self, mock_resolve):
        import dns.resolver
        mock_resolve.side_effect = dns.resolver.NoAnswer()
        assert _check_dmarc("acme.com") is False
