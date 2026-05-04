"""Unit tests for SLA deadline calculation and breach detection."""

from datetime import datetime, timedelta, timezone

import pytest

from sequor.escalation.sla import (
    calculate_deadline,
    is_breached,
    time_until_deadline,
)


class TestCalculateDeadline:
    def test_adds_hours(self):
        assigned = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        deadline = calculate_deadline(assigned, sla_hours=4)
        assert deadline == datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)

    def test_naive_datetime_treated_as_utc(self):
        assigned = datetime(2026, 5, 1, 10, 0, 0)
        deadline = calculate_deadline(assigned, sla_hours=4)
        assert deadline == datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)

    def test_zero_hours(self):
        assigned = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        deadline = calculate_deadline(assigned, sla_hours=0)
        assert deadline == datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)


class TestIsBreached:
    def test_not_breached_before_deadline(self):
        deadline = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 5, 1, 13, 0, 0, tzinfo=timezone.utc)
        assert is_breached(deadline, now) is False

    def test_breached_after_deadline(self):
        deadline = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 5, 1, 15, 0, 0, tzinfo=timezone.utc)
        assert is_breached(deadline, now) is True

    def test_naive_now_treated_as_utc(self):
        deadline = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 5, 1, 15, 0, 0)
        assert is_breached(deadline, now) is True

    def test_naive_deadline_treated_as_utc(self):
        deadline = datetime(2026, 5, 1, 14, 0, 0)
        now = datetime(2026, 5, 1, 15, 0, 0, tzinfo=timezone.utc)
        assert is_breached(deadline, now) is True

    def test_exactly_at_deadline_not_breached(self):
        deadline = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        assert is_breached(deadline, now) is False

    def test_defaults_to_now(self):
        deadline = datetime.now(timezone.utc) - timedelta(hours=1)
        assert is_breached(deadline) is True


class TestTimeUntilDeadline:
    def test_positive_before_deadline(self):
        deadline = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
        delta = time_until_deadline(deadline, now)
        assert delta == timedelta(hours=2)

    def test_negative_after_deadline(self):
        deadline = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 5, 1, 16, 0, 0, tzinfo=timezone.utc)
        delta = time_until_deadline(deadline, now)
        assert delta == timedelta(hours=-2)

    def test_zero_at_deadline(self):
        deadline = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
        delta = time_until_deadline(deadline, now)
        assert delta == timedelta(0)
