from __future__ import annotations

"""SLA deadline calculation and breach detection."""

from datetime import datetime, timedelta, timezone


def calculate_deadline(
    assigned_at: datetime,
    sla_hours: int,
) -> datetime:
    """Return the escalation deadline = assigned_at + sla_hours.

    If assigned_at is timezone-naive, it is treated as UTC.
    The returned deadline is timezone-aware (UTC).
    """
    if assigned_at.tzinfo is None:
        assigned_at = assigned_at.replace(tzinfo=timezone.utc)
    return assigned_at + timedelta(hours=sla_hours)


def is_breached(deadline: datetime, now: datetime | None = None) -> bool:
    """Return True if the deadline has already passed.

    If now is timezone-naive, it is treated as UTC.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    return now > deadline


def time_until_deadline(
    deadline: datetime,
    now: datetime | None = None,
) -> timedelta:
    """Return timedelta until deadline.

    Negative value means the deadline has been breached.
    If now is timezone-naive, it is treated as UTC.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    return deadline - now
