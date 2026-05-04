"""Tests for daily digest email generation.

Tests the DigestService class methods including stat gathering and SLA breach detection.
"""

import pytest
from datetime import datetime, timedelta, timezone

from sequor.digest.service import _after_cutoff


class TestAfterCutoff:
    """_after_cutoff correctly identifies timestamps after a cutoff."""

    def test_after_cutoff_returns_true(self):
        cutoff = datetime(2026, 5, 1, tzinfo=timezone.utc)
        dt = datetime(2026, 5, 2, tzinfo=timezone.utc)
        assert _after_cutoff(dt, cutoff) is True

    def test_before_cutoff_returns_false(self):
        cutoff = datetime(2026, 5, 2, tzinfo=timezone.utc)
        dt = datetime(2026, 5, 1, tzinfo=timezone.utc)
        assert _after_cutoff(dt, cutoff) is False

    def test_none_returns_false(self):
        cutoff = datetime(2026, 5, 1, tzinfo=timezone.utc)
        assert _after_cutoff(None, cutoff) is False

    def test_naive_datetime_treated_as_utc(self):
        cutoff = datetime(2026, 5, 1, tzinfo=timezone.utc)
        dt = datetime(2026, 5, 2)
        assert _after_cutoff(dt, cutoff) is True
