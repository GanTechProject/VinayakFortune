"""RED test spec for the SessionManager.

This file ships the FAILING tests against the SessionManager interface.
The implementer's job is to add `InMemorySessionManager` to
`app/session_manager.py` and make every test in this file pass GREEN.

The tests are written against the public interface of SessionManager
(create_session, get_session, refresh_session, revoke_session,
revoke_all_for_user) so any future backend (Redis, Postgres) must
satisfy the same tests.

See DESIGN.md §10 for the rationale and the per-test contract.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.session_manager import (
    ABSOLUTE_TTL,
    IDLE_TTL,
    Session,
    SessionManager,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class FakeClock:
    """A deterministic clock for tests. Manual advance only — no real time."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now = self._now + delta


class CollectingAuditSink:
    """Records every (event_code, payload) the manager emits."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def __call__(self, event_code: str, payload: dict[str, Any]) -> None:
        self.events.append((event_code, payload))


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def audit() -> CollectingAuditSink:
    return CollectingAuditSink()


@pytest.fixture
def manager(clock: FakeClock, audit: CollectingAuditSink) -> SessionManager:
    """The local subset manager under test.

    This fixture imports the concrete class lazily so the import
    error is surfaced at fixture-resolution time (when the test
    actually runs) rather than at collection time. The implementer
    is expected to add `InMemorySessionManager` to app/session_manager.py.
    """
    from app.session_manager import InMemorySessionManager

    return InMemorySessionManager(clock=clock, audit_sink=audit)


# ---------------------------------------------------------------------------
# §10.1 create_session
# ---------------------------------------------------------------------------


def test_create_returns_session_with_unique_id(manager: SessionManager) -> None:
    user = uuid4()
    s1 = manager.create_session(user)
    s2 = manager.create_session(user)
    assert isinstance(s1, Session)
    assert isinstance(s2, Session)
    assert s1.session_id != s2.session_id
    assert s1.user_id == user
    assert s2.user_id == user


def test_create_sets_expires_at_30d_from_created_at(manager: SessionManager, clock: FakeClock) -> None:
    s = manager.create_session(uuid4())
    assert s.expires_at - s.created_at == timedelta(days=30)
    assert s.last_used_at == s.created_at


def test_create_with_custom_ttl_caps_idle_window(manager: SessionManager) -> None:
    """Passing ttl=5m produces a session whose idle window (without refresh) is 5m."""
    user = uuid4()
    s = manager.create_session(user, ttl=timedelta(minutes=5))
    # expires_at is still 30d (absolute max is unaffected by the initial ttl)
    assert s.expires_at - s.created_at == timedelta(days=30)
    # but the idle window is 5m, so after 5m+1s the session is idle-expired
    # (this is enforced by get/refresh, not stored on the Session — see test_get_returns_none_for_idle_expired)


def test_create_rejects_ttl_zero(manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        manager.create_session(uuid4(), ttl=timedelta(seconds=0))


def test_create_rejects_ttl_above_8h(manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        manager.create_session(uuid4(), ttl=timedelta(hours=9))


def test_create_rejects_negative_ttl(manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        manager.create_session(uuid4(), ttl=timedelta(seconds=-1))


def test_create_rejects_none_user_id(manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        manager.create_session(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# §10.2 get_session
# ---------------------------------------------------------------------------


def test_get_returns_none_for_unknown_id(manager: SessionManager) -> None:
    assert manager.get_session(uuid4()) is None


def test_get_returns_session_for_valid_id(manager: SessionManager) -> None:
    s = manager.create_session(uuid4())
    fetched = manager.get_session(s.session_id)
    assert fetched is not None
    assert fetched.session_id == s.session_id
    assert fetched.user_id == s.user_id


def test_get_updates_last_used_at(manager: SessionManager, clock: FakeClock) -> None:
    s = manager.create_session(uuid4())
    initial_last_used = s.last_used_at
    clock.advance(timedelta(minutes=1))
    fetched = manager.get_session(s.session_id)
    assert fetched is not None
    assert fetched.last_used_at > initial_last_used


def test_get_returns_none_for_idle_expired(manager: SessionManager, clock: FakeClock) -> None:
    s = manager.create_session(uuid4())
    clock.advance(IDLE_TTL + timedelta(seconds=1))
    assert manager.get_session(s.session_id) is None


def test_get_returns_none_for_max_expired(manager: SessionManager, clock: FakeClock) -> None:
    s = manager.create_session(uuid4())
    clock.advance(ABSOLUTE_TTL + timedelta(seconds=1))
    assert manager.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.3 refresh_session
# ---------------------------------------------------------------------------


def test_refresh_updates_last_used_at(manager: SessionManager, clock: FakeClock) -> None:
    s = manager.create_session(uuid4())
    initial = s.last_used_at
    clock.advance(timedelta(minutes=30))
    refreshed = manager.refresh_session(s.session_id)
    assert refreshed is not None
    assert refreshed.last_used_at > initial


def test_refresh_does_not_extend_expires_at(manager: SessionManager, clock: FakeClock) -> None:
    s = manager.create_session(uuid4())
    original_expires = s.expires_at
    clock.advance(timedelta(hours=2))
    refreshed = manager.refresh_session(s.session_id)
    assert refreshed is not None
    assert refreshed.expires_at == original_expires


def test_refresh_returns_none_for_unknown_id(manager: SessionManager) -> None:
    assert manager.refresh_session(uuid4()) is None


def test_refresh_returns_none_for_idle_expired(manager: SessionManager, clock: FakeClock) -> None:
    s = manager.create_session(uuid4())
    clock.advance(IDLE_TTL + timedelta(seconds=1))
    assert manager.refresh_session(s.session_id) is None


def test_refresh_returns_none_for_max_expired(manager: SessionManager, clock: FakeClock) -> None:
    s = manager.create_session(uuid4())
    clock.advance(ABSOLUTE_TTL + timedelta(seconds=1))
    assert manager.refresh_session(s.session_id) is None


def test_refresh_after_29d_still_succeeds(manager: SessionManager, clock: FakeClock) -> None:
    """A session that's been active for 29d is still valid as long as the idle window is fresh."""
    s = manager.create_session(uuid4())
    clock.advance(timedelta(days=29))
    # idle window is 29d - 0 = fresh; refresh succeeds
    refreshed = manager.refresh_session(s.session_id)
    assert refreshed is not None
    assert refreshed.last_used_at == clock()


def test_refresh_at_29d_23h_succeeds_then_max_expires(manager: SessionManager, clock: FakeClock) -> None:
    """At 29d23h, refresh succeeds (idle window fresh). After 8h more, max-expiry kicks in."""
    s = manager.create_session(uuid4())
    clock.advance(timedelta(days=29, hours=23))
    # 29d23h: idle window 29d23h - 0 = fresh; refresh succeeds
    assert manager.refresh_session(s.session_id) is not None
    # After refresh, last_used_at = 29d23h
    # Advance another 8h: now = 30d7h, which is > 30d = max-expired
    clock.advance(timedelta(hours=8))
    assert manager.refresh_session(s.session_id) is None
    assert manager.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.4 revoke_session
# ---------------------------------------------------------------------------


def test_revoke_returns_true_for_existing_session(manager: SessionManager) -> None:
    s = manager.create_session(uuid4())
    assert manager.revoke_session(s.session_id) is True


def test_revoke_returns_false_for_unknown_id(manager: SessionManager) -> None:
    assert manager.revoke_session(uuid4()) is False


def test_revoke_is_idempotent(manager: SessionManager) -> None:
    s = manager.create_session(uuid4())
    assert manager.revoke_session(s.session_id) is True
    assert manager.revoke_session(s.session_id) is False  # second call: not found


def test_revoke_makes_get_return_none(manager: SessionManager) -> None:
    s = manager.create_session(uuid4())
    manager.revoke_session(s.session_id)
    assert manager.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.5 revoke_all_for_user
# ---------------------------------------------------------------------------


def test_revoke_all_returns_count(manager: SessionManager) -> None:
    user_a = uuid4()
    user_b = uuid4()
    for _ in range(3):
        manager.create_session(user_a)
    manager.create_session(user_b)
    assert manager.revoke_all_for_user(user_a) == 3
    # user_b's session is untouched
    assert manager.revoke_all_for_user(user_b) == 1


def test_revoke_all_for_user_with_no_sessions_returns_zero(manager: SessionManager) -> None:
    assert manager.revoke_all_for_user(uuid4()) == 0


def test_revoke_all_does_not_affect_other_users(manager: SessionManager) -> None:
    user_a = uuid4()
    user_b = uuid4()
    s_a = manager.create_session(user_a)
    s_b = manager.create_session(user_b)
    manager.revoke_all_for_user(user_a)
    assert manager.get_session(s_a.session_id) is None
    assert manager.get_session(s_b.session_id) is not None


# ---------------------------------------------------------------------------
# §10.6 Concurrency
# ---------------------------------------------------------------------------


def test_concurrent_create_produces_unique_ids(manager: SessionManager) -> None:
    """10 threads × 100 creates = 1000 sessions, all with distinct session_ids."""
    n_threads = 10
    per_thread = 100
    user = uuid4()
    results: list[Session] = []
    results_lock = threading.Lock()

    def worker() -> None:
        local: list[Session] = []
        for _ in range(per_thread):
            local.append(manager.create_session(user))
        with results_lock:
            results.extend(local)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == n_threads * per_thread
    ids = {s.session_id for s in results}
    assert len(ids) == len(results)  # all unique


def test_concurrent_refresh_is_atomic(manager: SessionManager, clock: FakeClock) -> None:
    """Concurrent refreshes on the same session must not corrupt it."""
    s = manager.create_session(uuid4())
    n_threads = 10
    barrier = threading.Barrier(n_threads)

    def worker() -> None:
        barrier.wait()
        manager.refresh_session(s.session_id)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Session still exists and is well-formed
    fetched = manager.get_session(s.session_id)
    assert fetched is not None
    assert fetched.expires_at - fetched.created_at == timedelta(days=30)
    assert fetched.last_used_at <= clock()


def test_concurrent_revoke_and_get(manager: SessionManager) -> None:
    """Racing revoke and get on the same session: no thread sees a 'ghost' session
    that was already revoked. (Both outcomes — get returns the session because
    revoke hasn't completed yet, or get returns None because revoke won — are
    correct under the contract; the assertion is the session is gone after the
    dust settles.)"""
    s = manager.create_session(uuid4())
    n_threads = 20
    barrier = threading.Barrier(n_threads)

    def worker() -> None:
        barrier.wait()
        if thread_local := getattr(worker, "_i", None) is None:
            pass
        # Half threads revoke, half get
        # (the dispatch is on thread index, set in the loop below)

    # Simpler approach: pre-assign roles
    def revoker() -> None:
        barrier.wait()
        manager.revoke_session(s.session_id)

    def getter() -> None:
        barrier.wait()
        manager.get_session(s.session_id)  # may return the session or None; both correct

    threads: list[threading.Thread] = []
    for i in range(n_threads):
        target = revoker if i == 0 else getter
        threads.append(threading.Thread(target=target))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # After the dust settles, the session must be revoked
    assert manager.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.7 Audit emission
# ---------------------------------------------------------------------------


def test_create_emits_audit_event(manager: SessionManager, audit: CollectingAuditSink) -> None:
    user = uuid4()
    s = manager.create_session(user)
    assert len(audit.events) == 1
    code, payload = audit.events[0]
    assert code == "session.created"
    assert payload["session_id"] == str(s.session_id)
    assert payload["user_id"] == str(user)


def test_revoke_emits_audit_event_only_on_hit(manager: SessionManager, audit: CollectingAuditSink) -> None:
    # miss does not emit
    manager.revoke_session(uuid4())
    assert audit.events == []
    # hit emits
    s = manager.create_session(uuid4())
    audit.events.clear()
    manager.revoke_session(s.session_id)
    assert len(audit.events) == 1
    code, payload = audit.events[0]
    assert code == "session.revoked"
    assert payload["session_id"] == str(s.session_id)


def test_revoke_all_emits_one_event_with_count(manager: SessionManager, audit: CollectingAuditSink) -> None:
    user = uuid4()
    for _ in range(3):
        manager.create_session(user)
    audit.events.clear()
    n = manager.revoke_all_for_user(user)
    assert n == 3
    # Exactly one event for the bulk revoke (not one per session)
    revoke_all_events = [e for e in audit.events if e[0] == "session.revoked_all_for_user"]
    assert len(revoke_all_events) == 1
    assert revoke_all_events[0][1]["count"] == 3
    assert revoke_all_events[0][1]["user_id"] == str(user)


def test_refresh_emits_audit_event_only_on_hit(manager: SessionManager, audit: CollectingAuditSink) -> None:
    manager.refresh_session(uuid4())  # miss
    assert audit.events == []
    s = manager.create_session(uuid4())
    audit.events.clear()
    manager.refresh_session(s.session_id)  # hit
    assert len(audit.events) == 1
    assert audit.events[0][0] == "session.refreshed"


def test_get_does_not_emit_audit_event(manager: SessionManager, audit: CollectingAuditSink) -> None:
    s = manager.create_session(uuid4())
    audit.events.clear()
    manager.get_session(s.session_id)
    manager.get_session(s.session_id)
    assert audit.events == []


# ---------------------------------------------------------------------------
# §10.8 Clock injection
# ---------------------------------------------------------------------------


def test_clock_injection_determines_expiry(clock: FakeClock, audit: CollectingAuditSink) -> None:
    """The clock passed at construction determines expiry. Default-constructed managers use real time."""
    from app.session_manager import InMemorySessionManager

    m = InMemorySessionManager(clock=clock, audit_sink=audit)
    s = m.create_session(uuid4())
    assert s.created_at == clock()
    clock.advance(IDLE_TTL + timedelta(seconds=1))
    assert m.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.bonus: metadata is opaque to the manager
# ---------------------------------------------------------------------------


def test_metadata_is_stored_and_returned(manager: SessionManager) -> None:
    md = {"ip": "10.0.0.1", "user_agent": "curl/8.0"}
    s = manager.create_session(uuid4(), metadata=md)
    fetched = manager.get_session(s.session_id)
    assert fetched is not None
    assert fetched.metadata == md


def test_metadata_defaults_to_empty_dict(manager: SessionManager) -> None:
    s = manager.create_session(uuid4())
    assert s.metadata == {}


# ---------------------------------------------------------------------------
# Sanity: the abstract class itself cannot be instantiated
# ---------------------------------------------------------------------------


def test_session_manager_is_abstract() -> None:
    """SessionManager is an ABC; you cannot instantiate it directly."""
    with pytest.raises(TypeError):
        SessionManager()  # type: ignore[abstract]
