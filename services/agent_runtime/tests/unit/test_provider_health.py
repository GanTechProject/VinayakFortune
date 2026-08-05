"""Unit tests for ProviderHealth event-window pruning (Bugfix C)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.agent_runtime.app.workflows import model_router
from services.agent_runtime.app.workflows.model_router import (
    Provider,
    ProviderHealth,
)


class _FakeDatetime:
    """A datetime class whose `now` returns a controllable timestamp."""

    now_value: datetime = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None) -> datetime:
        return cls.now_value


@pytest.fixture
def fake_clock(monkeypatch):
    _FakeDatetime.now_value = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(model_router, "datetime", _FakeDatetime)


def test_provider_health_prunes_old_events(fake_clock) -> None:
    """Bugfix C: record() drops events older than the window — no unbounded growth."""
    health = ProviderHealth(window_s=30)
    t0 = _FakeDatetime.now_value

    for _ in range(100):
        health.record(Provider.ANTHROPIC, True)

    # Advance well past the 30s window, then record one more event.
    _FakeDatetime.now_value = t0 + timedelta(seconds=40)
    health.record(Provider.ANTHROPIC, True)

    events = health._events[Provider.ANTHROPIC]
    assert len(events) == 1
    assert events[0][1] is True


def test_provider_health_status_with_mixed_timing(fake_clock) -> None:
    """Bugfix C: status() computes the success rate over the current window."""
    health = ProviderHealth(window_s=30)
    t0 = _FakeDatetime.now_value

    # 90 successes at t0, 10 failures at t0+20s.
    for _ in range(90):
        health.record(Provider.ANTHROPIC, True)
    _FakeDatetime.now_value = t0 + timedelta(seconds=20)
    for _ in range(10):
        health.record(Provider.ANTHROPIC, False)

    # t0+25s: window is [t0-5s, t0+25s] → all 100 events → 90% → down.
    _FakeDatetime.now_value = t0 + timedelta(seconds=25)
    status = health.status(Provider.ANTHROPIC)
    assert status.ok is False
    assert status.opus_ok is False

    # t0+45s: window is [t0+15s, t0+45s] → only the 10 failures → 0% → down.
    _FakeDatetime.now_value = t0 + timedelta(seconds=45)
    status = health.status(Provider.ANTHROPIC)
    assert status.ok is False

    # t0+55s: window is [t0+25s, t0+55s] → no events → healthy (default).
    _FakeDatetime.now_value = t0 + timedelta(seconds=55)
    status = health.status(Provider.ANTHROPIC)
    assert status.ok is True
    assert status.opus_ok is True
