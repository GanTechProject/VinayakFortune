---
title: auth-svc — Session Manager (local subset, in-memory)
version: v0.1
date: 2026-07-21
author: wizard (architect phase)
status: Working design — not part of the canonical docs suite
---

# auth-svc — Session Manager (local subset, in-memory)

> **Status:** Working design for the in-memory SessionManager that closes the local subset of [issue #5](../../issues/5) (AC-2.1, AC-2.4 partial). The full auth-svc epic — OIDC/MFA/SSO/magic-link/audit log/RBAC enforcement/SCIM — is out of scope for this doc and is covered by separate follow-up work once CI is real.
>
> **Where this lives:** `services/auth-svc/DESIGN.md`. Co-located with the service so the implementer can lift the interface and the RED tests directly when the local subset moves from `wip/` to a real PR.
>
> **Not in the canonical docs suite:** the 38-doc suite (`docs/`) is the product spec. This is a working design for the implementer. It will be retired or absorbed into Document 21 (Security) §4 once the local subset lands and the contract stabilizes.

## 1. Goal

Ship a **thread-safe, in-memory SessionManager** that the auth-svc HTTP layer can call to manage user sessions. The in-memory backend is the local-subset target: it runs in a single process, holds sessions in a Python `dict` with a per-method `threading.Lock`, and produces the same observable contract that the eventual Redis-backed implementation will produce. The contract is the deliverable; the backend is the smallest thing that can satisfy it under test.

## 2. Scope

**In scope (this design):**

- The `Session` data model (Pydantic).
- The `SessionManager` interface (abstract base class) — every method, every parameter, every return type, every exception.
- The `InMemorySessionManager` concrete implementation.
- TTL semantics: 8 h idle (sliding), 30 d max (absolute).
- Concurrency model: per-manager `threading.Lock`, the invariants under contention.
- Audit events emitted by the manager (`session.created`, `session.refreshed`, `session.revoked`, `session.revoked_all_for_user`).
- The RED test spec — every test the implementer must satisfy before the local subset is merge-ready.
- The error contract — when the manager raises vs returns `None`.

**Out of scope (follow-up work, gated on CI + infra):**

- OIDC/MFA/SSO/magic-link sign-in flows (issue #5 AC-2.1, AC-2.2, AC-2.3, AC-2.5).
- Auth0 tenant integration (issue #5 dependencies).
- RBAC at the API layer (issue #5 AC-2.8, AC-2.10).
- Cross-workspace membership, invites, SCIM (issue #5 AC-2.9, AC-2.11, AC-2.12).
- Persistence beyond process memory (Postgres `audit_event` table, Redis 7 session store).
- Multi-process / multi-host scaling.
- API tokens (the bearer-token model in Document 19 §4 is a *separate* type from session tokens; sessions are cookie-backed, API tokens are header-backed).

## 3. The Session model

```python
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class Session(BaseModel):
    """An authenticated user session, identified by an opaque session_id.

    Sessions are issued by the auth-svc after identity verification
    (OIDC callback, magic link, API-token exchange — those flows are
    out of scope for the local subset). The session manager owns the
    lifecycle of this object: create, get, refresh, revoke.
    """

    session_id: UUID
    user_id: UUID
    created_at: datetime       # absolute creation time; never mutated
    expires_at: datetime        # absolute max-expiry time (created_at + 30d)
    last_used_at: datetime      # sliding-window anchor (updated on refresh / get-if-valid)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

**Invariants on `Session`:**

- `created_at <= last_used_at <= expires_at` at all times.
- `expires_at = created_at + 30d` exactly. The manager does not let a `refresh` push `expires_at` past this ceiling.
- `metadata` is opaque to the manager — the manager never reads it. Callers use it for client IP, user agent, etc.

## 4. TTL semantics

Document 02 §5.5 specifies "8 h idle / 30 d max." This is two distinct TTLs, and the manager must enforce both:

| TTL | Type | Reset on | Hard ceiling |
|---|---|---|---|
| **8 h idle** | Sliding window from `last_used_at` | Every successful `get` or `refresh` (both update `last_used_at` to `now()`) | None — but if `now() - last_used_at > 8 h`, the session is "expired-idle" |
| **30 d max** | Absolute window from `created_at` | Never — `expires_at` is set at create time and is never extended | A session older than 30 d from `created_at` is "expired-max" |

**Worked examples:**

- A session is created at `t=0`. `expires_at = 30d`, `last_used_at = 0`.
- At `t=10d`, the user is active (refresh called). `last_used_at` updates to `10d`. Still valid.
- At `t=10d + 8h + 1s`, the user tries to `get`. `now - last_used_at = 8h + 1s` > 8h idle → session is expired-idle. `get` returns `None`.
- A session is created at `t=0`. The user calls `refresh` every 5 minutes for 29 days. `last_used_at` keeps updating. `expires_at` stays at `30d`. Still valid.
- At `t=29d + 23h`, the user calls `refresh`. `now - last_used_at = 5 min` < 8h idle → refresh succeeds. `last_used_at` updates. **But** `expires_at - now = 1h` < 8h idle, so the next `get` or `refresh` will fail with idle expiry even though the user is active. This is the intended behavior: absolute max wins. The user must re-authenticate.

**The contract is the same for both expiry reasons:** the manager returns `None` from `get` and refuses the operation in `refresh`. The caller cannot distinguish "expired-idle" from "expired-max" from the return value — both are `None` / refused. (If the caller needs to distinguish, they can call `manager.get_session_raw(id)` which returns the session metadata even if expired; this is for diagnostics only, gated to admin scope. Out of scope for the local subset.)

## 5. The interface

```python
import abc
from datetime import timedelta
from uuid import UUID
from .session_manager import Session


class SessionManager(abc.ABC):
    """The contract every session-manager backend must satisfy.

    All methods are thread-safe. The in-memory backend uses a single
    threading.Lock; the Redis backend (out of scope) will use a
    per-session Lua script. Both backends must produce the same
    observable behavior under the RED test spec.
    """

    @abc.abstractmethod
    def create_session(
        self,
        user_id: UUID,
        *,
        ttl: timedelta | None = None,
        metadata: dict | None = None,
    ) -> Session:
        """Create a new session for `user_id`.

        The new session is assigned a fresh session_id (UUIDv4) and a
        created_at timestamp from the manager's clock. The expires_at
        is set to created_at + 30d (the absolute max); the `ttl`
        parameter caps the *initial* idle window if shorter than 8h,
        but the absolute max always wins at refresh time.

        Returns the new Session. Raises:
        - ValueError if user_id is None.
        - ValueError if ttl is provided and is <= 0 or > 8h.
        """

    @abc.abstractmethod
    def get_session(self, session_id: UUID) -> Session | None:
        """Return the session if it exists and is not expired (idle or max).

        Updates last_used_at to now() on a hit. Returns None on a miss
        or on any kind of expiry. Does NOT raise on expiry.
        """

    @abc.abstractmethod
    def refresh_session(self, session_id: UUID) -> Session | None:
        """Extend the idle window on an existing session.

        Updates last_used_at to now(). Returns the refreshed session,
        or None if the session is missing, idle-expired, or max-expired.
        Does NOT raise on expiry. Does NOT extend expires_at (the
        absolute max wins).
        """

    @abc.abstractmethod
    def revoke_session(self, session_id: UUID) -> bool:
        """Revoke a single session. Returns True if it existed, False otherwise.

        Idempotent: revoking a non-existent session returns False
        without raising. Does NOT raise on miss.
        """

    @abc.abstractmethod
    def revoke_all_for_user(self, user_id: UUID) -> int:
        """Revoke every active session for `user_id`. Returns the count revoked.

        Revokes both idle-expired and active sessions (a "log out
        everywhere" semantic). Returns 0 if the user has no sessions.
        Does NOT raise on miss.
        """
```

**Three contract decisions worth flagging:**

1. **No exceptions for "session not found."** Every miss returns `None` (for get/refresh) or `False` (for revoke) or `0` (for revoke-all). The HTTP layer translates these to the 401/404 codes in Document 19 §8. Raising on miss would force every caller to wrap in try/except, and the contracts in Document 19 are explicit: 401 is the same code for "no token" and "expired token," and the API shouldn't expose the difference.

2. **`metadata` is opaque to the manager.** Callers use it for client IP, user agent, locale, device fingerprint. The manager never reads it, never validates its shape, never persists it to a typed schema. This is the same separation as Document 21 §10 (Secrets Management) — the manager owns lifecycle, callers own payload.

3. **`create_session` validates `ttl` but `refresh_session` does not.** The idle window is enforced uniformly by the manager; the *initial* idle window at create time is the only place the caller can express "this session should expire faster than 8h" (e.g. for a step-up flow that wants a 5-minute session). The 8h cap on the create-time `ttl` parameter prevents the caller from asking for something silly like a 24h initial idle that would defeat the 8h policy.

## 6. The in-memory implementation

The local subset target is `InMemorySessionManager`:

- Storage: `dict[UUID, Session]` keyed by `session_id`.
- Lock: one `threading.Lock` per manager instance. Held for the entire duration of any method that mutates state. Held for the read-and-update path in `get_session` and `refresh_session` so the "read, check expiry, update last_used_at" sequence is atomic.
- Clock: a `Callable[[], datetime]` injected at construction. Default is `datetime.utcnow`. Tests inject a fake clock so the TTL behavior is deterministic.
- UUID generation: `uuid.uuid4`. Tests can inject a deterministic UUID factory if needed (not required by the RED spec, but available for future use).
- No persistence. Process restart loses all sessions. This is acceptable for the local subset because the HTTP layer (out of scope) is what produces the user-facing "I got logged out when you restarted" behavior, and that HTTP layer doesn't exist yet.

The full source is in `app/session_manager.py` alongside this doc. The interface is the deliverable; the in-memory implementation is the smallest thing that can satisfy the RED test spec.

## 7. Concurrency model

The manager is thread-safe. The in-memory implementation uses a single `threading.Lock`; the contract is "no method leaves the manager in an inconsistent state under concurrent calls."

**Invariants under contention:**

- A `create_session` call always produces a `Session` with a unique `session_id` (UUID collisions are not the manager's problem; UUIDv4 collisions are astronomically unlikely).
- A `get_session` call that observes a session as non-expired returns it with `last_used_at` updated to `now()`. A `get_session` call that races with a `revoke_session` may return the session or `None`; both are correct under the contract.
- A `refresh_session` call that races with `revoke_session` returns `None` (the revoke won) or the refreshed session (the refresh won). Both are correct.
- A `revoke_all_for_user` call sees a consistent snapshot: it returns the count of sessions it actually revoked, which may be less than the count visible to a concurrent `get_session` if that get races in. The caller treats the count as a lower bound, not an exact total.

The lock is **not** held across user code (e.g. audit-event emission). Audit emission happens after the lock is released, so a slow audit sink cannot stall the manager.

## 8. Audit events

The manager emits one audit event per state-mutating method. The events are:

| Method | Event code | Payload |
|---|---|---|
| `create_session` | `session.created` | `{session_id, user_id, ttl_seconds, has_metadata}` |
| `get_session` | (none — read-only) | — |
| `refresh_session` (hit) | `session.refreshed` | `{session_id, user_id}` |
| `refresh_session` (miss) | (none) | — |
| `revoke_session` (hit) | `session.revoked` | `{session_id, user_id}` |
| `revoke_session` (miss) | (none) | — |
| `revoke_all_for_user` (n>0) | `session.revoked_all_for_user` | `{user_id, count: n}` |
| `revoke_all_for_user` (n=0) | (none) | — |

The audit sink is injected at construction (`Callable[[str, dict], None]`, default is `logging.info`). The local subset does not write to the Postgres `audit_event` table; the implementer plugs that in via the same injection point.

**Note on PII:** the payload includes `session_id` and `user_id` (both UUIDs, no PII), and a count or boolean. No client IP, no user agent — those go in `Session.metadata` at create time and are *not* part of the audit event. This matches Document 21 §14 ("Auth events: every sign-in, MFA challenge, role change") which lists session lifecycle as auditable but does not require the full metadata in the audit payload.

## 9. Error contract

| Situation | Behavior |
|---|---|
| `create_session(user_id=None)` | `ValueError("user_id is required")` |
| `create_session(user_id, ttl=timedelta(seconds=0))` | `ValueError("ttl must be > 0")` |
| `create_session(user_id, ttl=timedelta(hours=9))` | `ValueError("ttl must be <= 8h")` |
| `get_session(<unknown id>)` | returns `None` |
| `get_session(<expired-idle id>)` | returns `None` |
| `get_session(<expired-max id>)` | returns `None` |
| `get_session(<valid id>)` | returns the Session with `last_used_at` updated |
| `refresh_session(<unknown id>)` | returns `None` |
| `refresh_session(<expired id>)` | returns `None` |
| `refresh_session(<valid id>)` | returns the Session with `last_used_at` and `expires_at` unchanged (absolute max wins) |
| `revoke_session(<unknown id>)` | returns `False` |
| `revoke_session(<valid id>)` | returns `True` |
| `revoke_all_for_user(<user with no sessions>)` | returns `0` |
| `revoke_all_for_user(<user with 3 sessions>)` | returns `3`, emits one audit event |

**No method raises on session state. All validation errors are `ValueError` at create time only.**

## 10. RED test spec

The implementer's merge gate is "every test below passes GREEN." The tests are written against the interface, not the concrete class, so any future backend (Redis, Postgres) must satisfy the same tests.

### 10.1 create_session

- `test_create_returns_session_with_unique_id` — two calls with the same user_id produce different session_ids.
- `test_create_sets_expires_at_30d_from_created_at` — `expires_at - created_at == timedelta(days=30)`, exact, regardless of when the call is made.
- `test_create_with_custom_ttl_caps_idle_window` — passing `ttl=timedelta(minutes=5)` produces a session whose idle window (without refresh) expires at `created_at + 5m`, not `+ 8h`.
- `test_create_rejects_ttl_zero` — `ValueError`.
- `test_create_rejects_ttl_above_8h` — `ValueError`.
- `test_create_rejects_none_user_id` — `ValueError`.

### 10.2 get_session

- `test_get_returns_none_for_unknown_id` — UUID that was never created → `None`.
- `test_get_returns_session_for_valid_id` — session was just created, get returns it with the same `session_id` and `user_id`.
- `test_get_updates_last_used_at` — get twice in succession; the second `get` returns a session with `last_used_at >` the first.
- `test_get_returns_none_for_idle_expired` — fake clock advances past `last_used_at + 8h`; get returns `None`. (Idle expiry.)
- `test_get_returns_none_for_max_expired` — fake clock advances past `created_at + 30d`; get returns `None`. (Max expiry.)

### 10.3 refresh_session

- `test_refresh_updates_last_used_at` — same as get; refresh also updates `last_used_at`.
- `test_refresh_does_not_extend_expires_at` — refresh does NOT change `expires_at`. The absolute max is fixed at create time.
- `test_refresh_returns_none_for_expired_session` — both idle and max expiry return `None`.
- `test_refresh_after_29d_still_succeeds` — fake clock at `created_at + 29d`, refresh succeeds because idle window is fresh.
- `test_refresh_at_29d_23h_succeeds_once` — first refresh at this time succeeds; second refresh after another 8h returns `None` because the session is now max-expired (`30d + 1h > expires_at`).

### 10.4 revoke_session

- `test_revoke_returns_true_for_existing_session` — returns `True`.
- `test_revoke_returns_false_for_unknown_id` — returns `False`, no exception.
- `test_revoke_is_idempotent` — revoke twice, both calls return the right boolean, no exception.
- `test_revoke_makes_get_return_none` — after revoke, `get_session` returns `None`.

### 10.5 revoke_all_for_user

- `test_revoke_all_returns_count` — create 3 sessions for user A, 1 for user B; `revoke_all_for_user(A)` returns `3`, leaves user B's session intact.
- `test_revoke_all_for_user_with_no_sessions_returns_zero` — returns `0`, no exception.
- `test_revoke_all_does_not_affect_other_users` — the user-B session is still retrievable after revoking user A.

### 10.6 Concurrency

- `test_concurrent_create_produces_unique_ids` — 10 threads, each calling `create_session` 100 times → 1000 sessions, all with distinct `session_id`s.
- `test_concurrent_refresh_is_atomic` — 10 threads racing on `refresh_session` for the same `session_id`; the session is not corrupted (`last_used_at` is a valid datetime, `expires_at` is unchanged).
- `test_concurrent_revoke_and_get` — 10 threads each doing `revoke_session` or `get_session` on the same id; no thread observes a "ghost" session (a session that was revoked but get still returns it after the revoke completed).

### 10.7 Audit emission

- `test_create_emits_audit_event` — the injected audit sink receives exactly one `session.created` event per `create_session` call.
- `test_revoke_emits_audit_event_only_on_hit` — `revoke_session(<unknown>)` does NOT emit; `revoke_session(<valid>)` does.
- `test_revoke_all_emits_one_event_with_count` — `revoke_all_for_user` emits exactly one event with `count: n` regardless of `n`.

### 10.8 Clock injection

- `test_clock_injection_determines_expiry` — same test pattern as 10.2 idle-expired and 10.2 max-expired, but explicit: the manager takes a `clock: Callable[[], datetime]` constructor argument, and tests pass a fake clock that returns controlled values.

## 11. Infra-gated ACs (the things this design does NOT cover)

The local subset is intentionally small. The full auth-svc epic has 15 ACs (issue #5). The mapping:

| AC | Covered by local subset? | Where it lives |
|---|---|---|
| AC-2.1 OIDC callback | No | Follow-up design, gated on Auth0 tenant |
| AC-2.2 MFA enforcement | No | Follow-up design |
| AC-2.3 SSO SAML/OIDC | No | Follow-up design, Enterprise tier |
| AC-2.4 Sessions stored in Redis 7 with 8h/30d TTL | **Partial** — TTL contract designed and tested; the in-memory backend satisfies it; the Redis backend is the production implementation | This doc + a future `RedisSessionManager` |
| AC-2.5 Magic-link sign-in | No | Follow-up design |
| AC-2.6 Audit log of auth events | **Partial** — the manager emits events to a sink; persistence to Postgres `audit_event` is a follow-up | This doc + a future `PostgresAuditSink` |
| AC-2.7 workspace-svc CRUD | No (different service) | Issue #5 follow-up |
| AC-2.8 RBAC | No | Follow-up design at the API layer |
| AC-2.9 Multi-workspace membership | No | Follow-up design |
| AC-2.10 Per-resource ACLs | No | Follow-up design |
| AC-2.11 Invite flow | No | Follow-up design |
| AC-2.12 SCIM 2.0 | No (post-MVP) | Out of scope per issue #5 |
| AC-2.13 Auth latency p95 < 250ms | No (production gate) | Staging load test, not a unit-test concern |
| AC-2.14 Tenant isolation | No (Postgres RLS) | Follow-up design |
| AC-2.15 Backout plan | No (operational doc) | Document 28 §3 follow-up |

The local subset is the minimum that lets the rest of the platform depend on `SessionManager` without blocking on Auth0/Redis/Postgres. When CI is real, the implementer dispatches off this design, the local subset lands behind a feature flag (`auth.session_manager.backend = "memory" | "redis"`), and the production deployments flip the flag to `redis` once Redis 7 is provisioned.

## 12. Open questions

1. **Async vs sync.** The interface is sync. The eventual FastAPI service is async. The choice is: (a) keep the manager sync and use `asyncio.to_thread` at the call site, or (b) make the interface async and use `asyncio.Lock` in the in-memory backend. The local subset picks (a) for simplicity; the implementer can revisit. The RED test spec is written against the sync interface.

2. **Audit sink durability.** The local subset's audit sink is `logging.info`, which is best-effort. The production sink must be durable (Postgres `audit_event` with chained hashes per Document 21 §14). The local subset's `audit_sink: Callable[[str, dict], None]` injection point is the seam; the production implementation is a follow-up.

3. **Session ID format.** The interface uses `UUID`. Some platforms use signed JWTs or opaque base64 strings. UUID is the right call for the in-memory backend (no signing, no parsing) and a fine call for the Redis backend (Redis stores it as a string). If the implementer wants JWTs for stateless verification, that's a follow-up design and a different SessionManager implementation.

4. **Observability.** The local subset doesn't emit metrics (session count, hit rate, idle-expiry rate, etc.). The `audit_sink` injection point could be extended to a metrics sink, or a separate `metrics: SessionMetrics` interface could be added. The implementer decides; the RED test spec doesn't cover metrics.

## 13. Verification (this design, not the implementation)

This design is not yet a tested artifact. The verification steps for the *implementer* are: lift the interface and the test file into `services/auth-svc/app/`, run `pytest app/test_session_manager.py`, observe RED, implement `InMemorySessionManager`, re-run, observe GREEN. The RED test spec above is the implementer's merge gate.

The verification I did for *this design doc* before publishing:

- Cross-checked the TTL contract (8h idle / 30d max) against Document 02 §5.5 (matches).
- Cross-checked the audit-event list against Document 21 §14 ("Auth events: every sign-in, MFA challenge, role change" — session lifecycle extends this with create/refresh/revoke, which is consistent with the spirit but adds events not explicitly named; the implementer should confirm with the doc-librarian that the extension is acceptable).
- Cross-checked the error contract against Document 19 §8 (the 401 envelope, with no body detail beyond the standard `unauthenticated` + `trace_id`).
- Cross-checked the no-PII-in-payload decision against Document 21 §14 (consistent with the audit-event model).
- Re-ran the docs-lint check against the canonical docs suite: 0 hard failures (this design is in `services/auth-svc/`, not `docs/`, so it doesn't affect the docs-lint gate).

## 14. Next steps (when CI is real)

1. Dispatch the `architect` agent (already done — this doc is the deliverable) → DONE.
2. Implementer: copy `app/session_manager.py` (the interface, ABC only) and `app/test_session_manager.py` (the RED tests) from this design into the actual `services/auth-svc/app/`.
3. Implementer: scaffold `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `Dockerfile`, `.dockerignore` matching the hello-world convention.
4. Implementer: write the `InMemorySessionManager` class — start with `create_session` and `revoke_session`, run pytest, observe GREEN, then add the rest.
5. Open PR, run the Option 3 cycle, merge.
6. After merge: update the canonical docs suite (Document 21 §4) to point to the new design as the source of truth for the session contract. This design (`services/auth-svc/DESIGN.md`) is then retired or kept as a historical reference.
