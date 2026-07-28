"""RED test spec for the SessionManager.

This file ships the FAILING tests against the SessionManager interface,
exercising the Redis 7 backend (`RedisSessionManager` in
`app/redis_session_manager.py`). It is the 39th test file — a byte-identical
copy of `app/test_session_manager.py` with the single substitution
`manager` -> `redis_manager` in the fixture parameter and body references,
plus a one-line import of `RedisSessionManager`. The 38 test bodies
themselves are byte-identical to the in-memory suite; the contract they
express is the SessionManager ABC contract, not any backend-specific
behavior. A Redis regression surfaces as failures in THIS file, not
collapsed into a parametrized suite.

The tests are written against the public interface of SessionManager
(create_session, get_session, refresh_session, revoke_session,
revoke_all_for_user) so any future backend (Redis, Postgres) must
satisfy the same tests.

See DESIGN.md §10 and REDIS_BACKEND_DESIGN.md for the rationale and
the per-test contract.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.redis_session_manager import RedisSessionManager
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
        self._now = start or datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

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
def redis_manager(clock: FakeClock, audit: CollectingAuditSink, redis_client) -> SessionManager:
    """The Redis-backed SessionManager under test.

    CRITICAL clock + TTL design:
    - Session fields (created_at, expires_at, last_used_at) are populated from
      the FAKE clock — deterministic for assertions.
    - Redis EXPIREAT is set to unix_seconds(fake_now + ABSOLUTE_TTL) — a
      real wall-clock value, but derived FROM the fake clock, not from Redis's
      own clock. So advancing the fake clock past expires_at trips
      RedisSessionManager's Python-side is_max_expired check (and the Lua's
      (now_unix >= expires_at_unix) check) regardless of how fast Redis's
      expiration callback runs.
    - Idle TTL is NOT applied via Redis EXPIRE (per REDIS_BACKEND_DESIGN.md
      §4.2); it is a Python-side (now - last_used_at) > idle_ttl comparison
      using the fake clock. No Redis key is EXPIREd on idle.

    The 8h idle / 30d max semantics hold under both clocks: assertions
    (test_clock_injection_determines_expiry) are against the fake clock;
    Redis-side cleanup (defense in depth) is against wall time derived
    from the fake clock.
    """
    return RedisSessionManager(
        clock=clock,
        audit_sink=audit,
        redis_client=redis_client,
        idle_ttl=IDLE_TTL,
        absolute_ttl=ABSOLUTE_TTL,
    )


# ---------------------------------------------------------------------------
# §10.1 create_session
# ---------------------------------------------------------------------------


def test_create_returns_session_with_unique_id(redis_manager: SessionManager) -> None:
    user = uuid4()
    s1 = redis_manager.create_session(user)
    s2 = redis_manager.create_session(user)
    assert isinstance(s1, Session)
    assert isinstance(s2, Session)
    assert s1.session_id != s2.session_id
    assert s1.user_id == user
    assert s2.user_id == user


def test_create_sets_expires_at_30d_from_created_at(redis_manager: SessionManager, clock: FakeClock) -> None:
    s = redis_manager.create_session(uuid4())
    assert s.expires_at - s.created_at == timedelta(days=30)
    assert s.last_used_at == s.created_at


def test_create_with_custom_ttl_caps_idle_window(redis_manager: SessionManager) -> None:
    """Passing ttl=5m produces a session whose idle window (without refresh) is 5m."""
    user = uuid4()
    s = redis_manager.create_session(user, ttl=timedelta(minutes=5))
    # expires_at is still 30d (absolute max is unaffected by the initial ttl)
    assert s.expires_at - s.created_at == timedelta(days=30)
    # but the idle window is 5m, so after 5m+1s the session is idle-expired
    # (this is enforced by get/refresh, not stored on the Session — see test_get_returns_none_for_idle_expired)


def test_create_rejects_ttl_zero(redis_manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        redis_manager.create_session(uuid4(), ttl=timedelta(seconds=0))


def test_create_rejects_ttl_above_8h(redis_manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        redis_manager.create_session(uuid4(), ttl=timedelta(hours=9))


def test_create_rejects_negative_ttl(redis_manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        redis_manager.create_session(uuid4(), ttl=timedelta(seconds=-1))


def test_create_rejects_none_user_id(redis_manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        redis_manager.create_session(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# §10.2 get_session
# ---------------------------------------------------------------------------


def test_get_returns_none_for_unknown_id(redis_manager: SessionManager) -> None:
    assert redis_manager.get_session(uuid4()) is None


def test_get_returns_session_for_valid_id(redis_manager: SessionManager) -> None:
    s = redis_manager.create_session(uuid4())
    fetched = redis_manager.get_session(s.session_id)
    assert fetched is not None
    assert fetched.session_id == s.session_id
    assert fetched.user_id == s.user_id


def test_get_updates_last_used_at(redis_manager: SessionManager, clock: FakeClock) -> None:
    s = redis_manager.create_session(uuid4())
    initial_last_used = s.last_used_at
    clock.advance(timedelta(minutes=1))
    fetched = redis_manager.get_session(s.session_id)
    assert fetched is not None
    assert fetched.last_used_at > initial_last_used


def test_get_returns_none_for_idle_expired(redis_manager: SessionManager, clock: FakeClock) -> None:
    s = redis_manager.create_session(uuid4())
    clock.advance(IDLE_TTL + timedelta(seconds=1))
    assert redis_manager.get_session(s.session_id) is None


def test_get_returns_none_for_max_expired(redis_manager: SessionManager, clock: FakeClock) -> None:
    s = redis_manager.create_session(uuid4())
    clock.advance(ABSOLUTE_TTL + timedelta(seconds=1))
    assert redis_manager.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.3 refresh_session
# ---------------------------------------------------------------------------


def test_refresh_updates_last_used_at(redis_manager: SessionManager, clock: FakeClock) -> None:
    s = redis_manager.create_session(uuid4())
    initial = s.last_used_at
    clock.advance(timedelta(minutes=30))
    refreshed = redis_manager.refresh_session(s.session_id)
    assert refreshed is not None
    assert refreshed.last_used_at > initial


def test_refresh_does_not_extend_expires_at(redis_manager: SessionManager, clock: FakeClock) -> None:
    s = redis_manager.create_session(uuid4())
    original_expires = s.expires_at
    clock.advance(timedelta(hours=2))
    refreshed = redis_manager.refresh_session(s.session_id)
    assert refreshed is not None
    assert refreshed.expires_at == original_expires


def test_refresh_returns_none_for_unknown_id(redis_manager: SessionManager) -> None:
    assert redis_manager.refresh_session(uuid4()) is None


def test_refresh_returns_none_for_idle_expired(redis_manager: SessionManager, clock: FakeClock) -> None:
    s = redis_manager.create_session(uuid4())
    clock.advance(IDLE_TTL + timedelta(seconds=1))
    assert redis_manager.refresh_session(s.session_id) is None


def test_refresh_returns_none_for_max_expired(redis_manager: SessionManager, clock: FakeClock) -> None:
    s = redis_manager.create_session(uuid4())
    clock.advance(ABSOLUTE_TTL + timedelta(seconds=1))
    assert redis_manager.refresh_session(s.session_id) is None


def test_refresh_after_29d_still_succeeds(redis_manager: SessionManager, clock: FakeClock) -> None:
    """A session near its absolute max is still refreshable as long as the idle window is fresh.

    An actively-used session (refreshed every 7h, well under the 8h
    idle TTL) reaches t = 29d with idle = 1h (fresh) and 1d before
    expires_at. The test asserts that refresh at t = 29d succeeds,
    proving the absolute max does NOT fire prematurely while the
    idle window is fresh.
    """
    s = redis_manager.create_session(uuid4())
    # Target the moment the loop should settle at: 29d - 1h after created_at.
    # Compute relative to the session's created_at so the FakeClock's
    # start (2026-01-01 12:00 UTC) is irrelevant — we navigate by deltas.
    target = s.created_at + timedelta(days=29) - timedelta(hours=1)
    # Refresh every 7h, clamping the final step so the loop lands EXACTLY
    # at clock = created_at + 29d - 1h, where last_used = clock and idle = 0.
    while clock() < target:
        next_step = min(timedelta(hours=7), target - clock())
        clock.advance(next_step)
        refreshed = redis_manager.refresh_session(s.session_id)
        assert refreshed is not None  # sanity: all intervening refreshes succeed
    # Now at clock = created_at + 29d - 1h, last_used = clock, idle = 0.
    # Advance 1h: clock = created_at + 29d, idle = 1h (fresh), now < expires_at.
    clock.advance(timedelta(hours=1))
    refreshed = redis_manager.refresh_session(s.session_id)
    assert refreshed is not None
    assert refreshed.last_used_at == clock()


def test_refresh_at_29d_23h_succeeds_then_max_expires(redis_manager: SessionManager, clock: FakeClock) -> None:
    """At 29d23h (idle fresh), refresh succeeds. After 8h more, max-expiry kicks in.

    An actively-used session reaches t = 29d23h with idle = 1h
    (fresh) and 1h before expires_at. Refresh succeeds at this
    state. After advancing another 8h, now = 30d7h > expires_at,
    so the absolute max fires and both refresh and get return None.
    """
    s = redis_manager.create_session(uuid4())
    # Refresh every 7h up to just before expires_at, keeping the idle window fresh.
    while clock() + timedelta(hours=7) < s.expires_at - timedelta(hours=1):
        clock.advance(timedelta(hours=7))
        refreshed = redis_manager.refresh_session(s.session_id)
        assert refreshed is not None  # sanity: all intervening refreshes succeed
    # Advance 1h so the next refresh has idle = 1h (fresh) and is 1h before expires_at.
    clock.advance(timedelta(hours=1))
    refreshed = redis_manager.refresh_session(s.session_id)
    assert refreshed is not None
    # After the refresh, last_used_at = 29d23h. Advance 8h: now = 30d7h, past expires_at.
    clock.advance(timedelta(hours=8))
    assert redis_manager.refresh_session(s.session_id) is None
    assert redis_manager.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.4 revoke_session
# ---------------------------------------------------------------------------


def test_revoke_returns_true_for_existing_session(redis_manager: SessionManager) -> None:
    s = redis_manager.create_session(uuid4())
    assert redis_manager.revoke_session(s.session_id) is True


def test_revoke_returns_false_for_unknown_id(redis_manager: SessionManager) -> None:
    assert redis_manager.revoke_session(uuid4()) is False


def test_revoke_is_idempotent(redis_manager: SessionManager) -> None:
    s = redis_manager.create_session(uuid4())
    assert redis_manager.revoke_session(s.session_id) is True
    assert redis_manager.revoke_session(s.session_id) is False  # second call: not found


def test_revoke_makes_get_return_none(redis_manager: SessionManager) -> None:
    s = redis_manager.create_session(uuid4())
    redis_manager.revoke_session(s.session_id)
    assert redis_manager.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.5 revoke_all_for_user
# ---------------------------------------------------------------------------


def test_revoke_all_returns_count(redis_manager: SessionManager) -> None:
    user_a = uuid4()
    user_b = uuid4()
    for _ in range(3):
        redis_manager.create_session(user_a)
    redis_manager.create_session(user_b)
    assert redis_manager.revoke_all_for_user(user_a) == 3
    # user_b's session is untouched
    assert redis_manager.revoke_all_for_user(user_b) == 1


def test_revoke_all_for_user_with_no_sessions_returns_zero(redis_manager: SessionManager) -> None:
    assert redis_manager.revoke_all_for_user(uuid4()) == 0


def test_revoke_all_does_not_affect_other_users(redis_manager: SessionManager) -> None:
    user_a = uuid4()
    user_b = uuid4()
    s_a = redis_manager.create_session(user_a)
    s_b = redis_manager.create_session(user_b)
    redis_manager.revoke_all_for_user(user_a)
    assert redis_manager.get_session(s_a.session_id) is None
    assert redis_manager.get_session(s_b.session_id) is not None


# ---------------------------------------------------------------------------
# §10.6 Concurrency
# ---------------------------------------------------------------------------


def test_concurrent_create_produces_unique_ids(redis_manager: SessionManager) -> None:
    """10 threads × 100 creates = 1000 sessions, all with distinct session_ids."""
    n_threads = 10
    per_thread = 100
    user = uuid4()
    results: list[Session] = []
    results_lock = threading.Lock()

    def worker() -> None:
        local: list[Session] = []
        for _ in range(per_thread):
            local.append(redis_manager.create_session(user))
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


def test_concurrent_refresh_is_atomic(redis_manager: SessionManager, clock: FakeClock) -> None:
    """Concurrent refreshes on the same session must not corrupt it."""
    s = redis_manager.create_session(uuid4())
    n_threads = 10
    barrier = threading.Barrier(n_threads)

    def worker() -> None:
        barrier.wait()
        redis_manager.refresh_session(s.session_id)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Session still exists and is well-formed
    fetched = redis_manager.get_session(s.session_id)
    assert fetched is not None
    assert fetched.expires_at - fetched.created_at == timedelta(days=30)
    assert fetched.last_used_at <= clock()


def test_concurrent_revoke_and_get(redis_manager: SessionManager) -> None:
    """Racing revoke and get on the same session: no thread sees a 'ghost' session
    that was already revoked. (Both outcomes — get returns the session because
    revoke hasn't completed yet, or get returns None because revoke won — are
    correct under the contract; the assertion is the session is gone after the
    dust settles.)"""
    s = redis_manager.create_session(uuid4())
    n_threads = 20
    barrier = threading.Barrier(n_threads)

    # Pre-assign roles per thread (one revoker, the rest getters).
    def revoker() -> None:
        barrier.wait()
        redis_manager.revoke_session(s.session_id)

    def getter() -> None:
        barrier.wait()
        redis_manager.get_session(s.session_id)  # may return the session or None; both correct

    threads: list[threading.Thread] = []
    for i in range(n_threads):
        target = revoker if i == 0 else getter
        threads.append(threading.Thread(target=target))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # After the dust settles, the session must be revoked
    assert redis_manager.get_session(s.session_id) is None


# ---------------------------------------------------------------------------
# §10.7 Audit emission
# ---------------------------------------------------------------------------


def test_create_emits_audit_event(redis_manager: SessionManager, audit: CollectingAuditSink) -> None:
    user = uuid4()
    s = redis_manager.create_session(user)
    assert len(audit.events) == 1
    code, payload = audit.events[0]
    assert code == "session.created"
    assert payload["session_id"] == str(s.session_id)
    assert payload["user_id"] == str(user)


def test_revoke_emits_audit_event_only_on_hit(redis_manager: SessionManager, audit: CollectingAuditSink) -> None:
    # miss does not emit
    redis_manager.revoke_session(uuid4())
    assert audit.events == []
    # hit emits
    s = redis_manager.create_session(uuid4())
    audit.events.clear()
    redis_manager.revoke_session(s.session_id)
    assert len(audit.events) == 1
    code, payload = audit.events[0]
    assert code == "session.revoked"
    assert payload["session_id"] == str(s.session_id)


def test_revoke_all_emits_one_event_with_count(redis_manager: SessionManager, audit: CollectingAuditSink) -> None:
    user = uuid4()
    for _ in range(3):
        redis_manager.create_session(user)
    audit.events.clear()
    n = redis_manager.revoke_all_for_user(user)
    assert n == 3
    # Exactly one event for the bulk revoke (not one per session)
    revoke_all_events = [e for e in audit.events if e[0] == "session.revoked_all_for_user"]
    assert len(revoke_all_events) == 1
    assert revoke_all_events[0][1]["count"] == 3
    assert revoke_all_events[0][1]["user_id"] == str(user)


def test_refresh_emits_audit_event_only_on_hit(redis_manager: SessionManager, audit: CollectingAuditSink) -> None:
    redis_manager.refresh_session(uuid4())  # miss
    assert audit.events == []
    s = redis_manager.create_session(uuid4())
    audit.events.clear()
    redis_manager.refresh_session(s.session_id)  # hit
    assert len(audit.events) == 1
    assert audit.events[0][0] == "session.refreshed"


def test_get_does_not_emit_audit_event(redis_manager: SessionManager, audit: CollectingAuditSink) -> None:
    s = redis_manager.create_session(uuid4())
    audit.events.clear()
    redis_manager.get_session(s.session_id)
    redis_manager.get_session(s.session_id)
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


def test_metadata_is_stored_and_returned(redis_manager: SessionManager) -> None:
    md = {"ip": "10.0.0.1", "user_agent": "curl/8.0"}
    s = redis_manager.create_session(uuid4(), metadata=md)
    fetched = redis_manager.get_session(s.session_id)
    assert fetched is not None
    assert fetched.metadata == md


def test_metadata_defaults_to_empty_dict(redis_manager: SessionManager) -> None:
    s = redis_manager.create_session(uuid4())
    assert s.metadata == {}


# ---------------------------------------------------------------------------
# Sanity: the abstract class itself cannot be instantiated
# ---------------------------------------------------------------------------


def test_session_manager_is_abstract() -> None:
    """SessionManager is an ABC; you cannot instantiate it directly."""
    with pytest.raises(TypeError):
        SessionManager()  # type: ignore[abstract]
