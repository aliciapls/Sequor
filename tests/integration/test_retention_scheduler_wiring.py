"""Tier-2 wiring test for the RetentionPurgeScheduler lifecycle (shard 1d).

The purge LOGIC (``run_retention_purge_once``) is covered by
``test_retention_purge.py``; this file exercises the scheduler CLASS itself —
the ``create_retention_scheduler`` factory gate, ``start``/``_tick``/``stop``
lifecycle — which ``facade-manager-detection.md`` Rule 1 + ``orphan-detection.md``
Rule 2 require for a manager-shape class wired into the app lifespan.

``run_retention_purge_once`` is monkeypatched to a no-op so the test does not
depend on a real purge tick (the lifecycle is what's under test, not the DB);
the DB only needs to be reachable so ``get_engine()`` constructs cleanly.
"""

from __future__ import annotations

import asyncio

import pytest

from sequor.config import settings
from sequor.db.retention import (
    RetentionPurgeScheduler,
    create_retention_scheduler,
)


@pytest.mark.asyncio
async def test_factory_returns_none_when_disabled(monkeypatch):
    """With retention_purge_enabled=False the factory returns None without
    constructing or starting a scheduler — the unit-test TestClient path must
    not spawn a background task."""
    monkeypatch.setattr(settings, "retention_purge_enabled", False)
    scheduler = await create_retention_scheduler()
    assert scheduler is None


@pytest.mark.asyncio
async def test_factory_starts_live_task_and_stop_cleans_up(monkeypatch):
    """With the flag enabled the factory returns a scheduler whose start() has
    spawned a live asyncio task; _tick invokes run_retention_purge_once; stop()
    cancels the task and clears the handle."""
    monkeypatch.setattr(settings, "retention_purge_enabled", True)

    tick_calls: list = []

    async def _fake_purge(engine=None, **kwargs):
        tick_calls.append(True)
        return []

    monkeypatch.setattr("sequor.db.retention.run_retention_purge_once", _fake_purge)

    # Long interval so only the immediate first tick fires during the test.
    scheduler = await create_retention_scheduler(interval_seconds=600)
    try:
        assert scheduler is not None
        assert scheduler._task is not None
        assert not scheduler._task.done(), "scheduler task must be live after start"
        # Let the first _tick run (the loop ticks once before the first sleep).
        await asyncio.sleep(0.1)
        assert len(tick_calls) >= 1, "the loop must invoke run_retention_purge_once on start"
    finally:
        await scheduler.stop()
    assert scheduler._task is None, "stop() must clear the task handle"


@pytest.mark.asyncio
async def test_start_when_already_running_is_a_noop_warning(monkeypatch):
    """A second start() on a running scheduler logs + does not spawn a second
    task (the guard against double-start)."""
    monkeypatch.setattr(settings, "retention_purge_enabled", True)
    monkeypatch.setattr(
        "sequor.db.retention.run_retention_purge_once",
        lambda *a, **k: asyncio.sleep(0, result=[]),  # type: ignore[misc]
    )
    scheduler = RetentionPurgeScheduler(interval_seconds=600)
    try:
        await scheduler.start()
        first_task = scheduler._task
        await scheduler.start()  # second start — must not replace the task
        assert scheduler._task is first_task, "double-start must not spawn a second task"
    finally:
        await scheduler.stop()
