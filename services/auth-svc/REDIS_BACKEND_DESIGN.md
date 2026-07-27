# Redis 7 SessionManager Backend — Design

| Field          | Value                                                      |
| -------------- | ---------------------------------------------------------- |
| Status         | Design (Phase C, step 2; issue #5 AC-2.4)                  |
| Target branch  | `wip/auth-svc-redis-session-manager`                       |
| Test contract  | `services/auth-svc/app/test_session_manager.py` (38 tests) |
| Base commit    | `4a0ea1a` (PR #49 squash)                                  |
| Sibling docs   | `DESIGN.md` §1, §5; `IMPLEMENTATION_GUIDE.md`              |
| Test-fixture   | `IMPLEMENTATION_REDIS_TESTING.md` (sibling)                |

## 1. Goal

Replace the in-memory `SessionManager` implementation with a Redis 7 backend that passes the **same 38-test contract** that `InMemorySessionManager` already passes — without modifying the test bodies. This is Phase C step 2 of the auth-svc roadmap and satisfies issue #5 AC-2.4 (Redis-backed sessions).

The TTL semantics, audit event contract, and method signatures are fixed by `services/auth-svc/app/session_manager.py` (`Session` model, `SessionManager` ABC) and exercised by `services/auth-svc/app/test_session_manager.py`. The pre-existing `DESIGN.md` §1 defines the TTL semantics; §2 defines the audit event contract; §5 is the interface contract (and §5's `SessionManager` docstring notes "the Redis backend (out of scope) will use a per-session Lua script"). This document is the **how** for the Redis backend.

## 2. Scope

**In scope:**

- A new `RedisSessionManager` class in `services/auth-svc/app/redis_session_manager.py`, implementing the same `SessionManager` ABC.
- A Redis 7–compatible storage model (Hash + Set, no Streams, no Modules).
- Lua-scripted atomicity for the five mutating operations.
- Test-fixture rewiring so the existing 38 tests run against both backends.
- A CI matrix in `ci-hello-world.yml` so both backends are exercised on every PR.

**Out of scope:**

- **Production Redis provisioning.** Issue #4 AC-1.4 (config:production) owns the docker-compose / Helm / managed-Redis decision. This design assumes a `REDIS_URL` env var.
- **Multi-DC replication, active-active, Redis Cluster mode.** Single Redis 7 instance assumed.
- **KeyDB / DragonflyDB compatibility.** Redis 7 only. Their RESP compatibility is not validated.
- **Password rotation / OAuth-token–based auth to Redis.** Plain `REDIS_URL` for now; TLS only as a deployment-level concern.
- **Async client.** The ABC is sync; we use sync `redis.Redis`. Async is a follow-up.
- **A background sweeper for stale `auth_svc:session:*` keys.** Cleanup is reactive (on `get_session`).

## 3. Storage model

Two key patterns, both prefixed `auth_svc:` (so a single Redis instance can be shared with other services in dev without collision; the prefix is a constant, not configurable per-doc to keep the contract crisp).

### 3.1 `auth_svc:session:{session_id}` — Hash

Per-session record. Hash, not JSON string, because future extensions (e.g., `device_fingerprint`, `last_ip`) need field-level reads without re-serializing the whole record.

| Field          | Redis type | Source                                            |
| -------------- | ---------- | ------------------------------------------------- |
| `user_id`      | string     | `str(user_id)` on create                          |
| `created_at`   | string     | ISO 8601 UTC, microsecond precision               |
| `expires_at`   | string     | ISO 8601 UTC (from `created_at + ABSOLUTE_TTL`)   |
| `last_used_at` | string     | ISO 8601 UTC, updated on `refresh`                |
| `metadata`     | string     | JSON-encoded `dict[str, Any]`, default `{}`       |

**Why metadata as a JSON-encoded string, not a sub-hash.** Metadata is opaque to the server and rarely inspected; it's read whole and written whole. Atomicity per-field is not a requirement. A sub-hash would multiply the field count and the HSET round-trips with no payoff; a JSON string is one HSET / HGET pair and round-trips cleanly through `json.loads`.

### 3.2 `auth_svc:user_sessions:{user_id}` — Set of session_id strings

Per-user index of live session IDs. Used by `revoke_all_for_user` (SMEMBERS) and kept in sync via SADD on create / SREM on revoke / get-time DEL.

**Why a Set, not a Hash or a Sorted Set.** A Set gives O(1) SADD / SREM / SISMEMBER with no ordering requirement. A Sorted Set would imply we care about ordering (we don't). A Hash would imply we care about per-session fields (we already have the per-session Hash for that — the user-index is a membership index only).

### 3.3 TTL semantics: max-of-members

`auth_svc:user_sessions:{user_id}` has no fixed TTL. Instead, on every SADD (inside `create_session_lua`), the script computes the **max of the set's members' `expires_at`** and re-EXPIREs the set to that. This avoids orphaned user sets outliving all their sessions (e.g., a user whose only session expired between SADD and the next op).

## 4. TTL semantics under Redis primitives

### 4.1 Max (absolute) TTL — `EXPIREAT`

Set `EXPIREAT auth_svc:session:{sid} <unix_seconds(created_at + ABSOLUTE_TTL)>`.

**Critical detail: the absolute timestamp comes from the injected clock, not Redis's wall-clock.** `test_clock_injection_determines_expiry` requires that advancing the injected clock past `expires_at` returns `None` on the next call, even if the test runs faster than Redis's key-expiry callback. The Python wrapper passes `unix_seconds(created_at + ABSOLUTE_TTL)` as an ARGV to the Lua; the Lua sets `EXPIREAT` to that exact value. Redis's own clock is irrelevant for correctness.

The Python-side `is_max_expired` check is the load-bearing one; the Redis EXPIREAT is defense-in-depth and a cleanup mechanism.

### 4.2 Idle TTL — do NOT use Redis EXPIRE

The idle check is **a Python-side `>` comparison** between `(now - last_used_at)` and `idle_ttl`. We do not call `EXPIRE` on every refresh because:

- It would race with the injected clock. If the test runs faster than Redis's TTL callback, the test's `is_idle_expired` would say "not expired" while Redis has already evicted the key — inconsistent states.
- The injected clock is the source of truth. The contract is `now() - last_used_at > idle_ttl` where `now()` is the injected clock.
- The absolute EXPIREAT is the only ceiling; idle is a soft, clock-driven check.

**Cleanup of stale keys.** No background sweeper. `get_session` and `refresh_session` perform the `is_max_expired` check via the injected clock; if `now >= expires_at`, the Lua DELs the key and SREMs from the user-index. The Redis EXPIREAT is the last-resort cleanup if the service is down for >30d.

### 4.3 User-index TTL — max-of-members

See §3.3. The `create_session_lua` script:

1. SADD the new session_id to the user-set.
2. SMEMBERS the user-set.
3. For each session_id, `HMGET auth_svc:session:{sid} expires_at`.
4. Compute `max_expires_at = max(...)`.
5. `EXPIREAT auth_svc:user_sessions:{user_id} unix_seconds(max_expires_at)`.

All inside one Lua call, so atomic with the SADD.

## 5. Concurrency model

Five Lua scripts, each registered via `redis.Redis.register_script(...)` so the SHA is cached and subsequent calls use EVALSHA. The Python wrapper passes the clock-driven deltas as ARGV; the Lua only does integer comparisons and one round-trip.

**Why Lua over WATCH/MULTI/EXEC.** Simpler reasoning (one atomic block per op), no retry loop on contention, and the `is_idle_expired` / `is_max_expired` checks are conditional on the read, which is awkward to express in WATCH/MULTI. Lua scripts also run server-side atomically, which is what we want for the user-index TTL recompute.

### 5.1 `create_session_lua`

```lua
-- KEYS[1] = auth_svc:session:{session_id}
-- KEYS[2] = auth_svc:user_sessions:{user_id}
-- ARGV[1] = user_id (string)
-- ARGV[2] = created_at (ISO 8601)
-- ARGV[3] = expires_at (ISO 8601)
-- ARGV[4] = last_used_at (ISO 8601)
-- ARGV[5] = metadata (JSON string)
-- ARGV[6] = absolute_expires_unix (int, for the session key EXPIREAT)
-- ARGV[7] = session_id (string, for SADD into the user-set)

if redis.call('EXISTS', KEYS[1]) == 1 then
  return redis.error_reply('session_exists')
end

redis.call('HSET', KEYS[1],
  'user_id', ARGV[1],
  'created_at', ARGV[2],
  'expires_at', ARGV[3],
  'last_used_at', ARGV[4],
  'metadata', ARGV[5]
)
redis.call('EXPIREAT', KEYS[1], ARGV[6])

redis.call('SADD', KEYS[2], ARGV[7])
-- (User-set TTL recompute is a separate script `recompute_user_set_ttl_lua`
--  called from the Python wrapper after create, not from inside this Lua.
--  See §5.6. Keeping it separate keeps create_session_lua single-purpose.)

return 'ok'
```

### 5.2 `get_session_lua`

```lua
-- KEYS[1] = auth_svc:session:{session_id}
-- KEYS[2] = auth_svc:user_sessions:{user_id}  -- used for SREM on expiry
-- ARGV[1] = now_iso (ISO 8601)
-- ARGV[2] = now_unix (int, seconds since epoch)
-- ARGV[3] = idle_ttl_seconds (int)
-- ARGV[4] = last_used_at_unix (int, for the idle check; pre-read in Python)
-- ARGV[5] = expires_at_unix (int, for the max check; pre-read in Python)
-- ARGV[6] = session_id (string, for SREM)
-- ARGV[7] = user_id (string, for SREM)

local data = redis.call('HGETALL', KEYS[1])
if #data == 0 then
  return nil
end

-- Idle: strict >  (matches in-memory backend's _is_idle_expired)
-- Max:  >=       (matches in-memory backend's _is_max_expired)
local is_idle_expired = (ARGV[2] - ARGV[4]) > ARGV[3]
local is_max_expired  = (ARGV[2] >= ARGV[5])

if is_idle_expired or is_max_expired then
  redis.call('DEL', KEYS[1])
  redis.call('SREM', KEYS[2], ARGV[6])
  return nil
end

-- Update last_used_at to now (this is the read AND the refresh, in one call)
redis.call('HSET', KEYS[1], 'last_used_at', ARGV[1])
return data  -- returns [k1, v1, k2, v2, ...]
```

The Python wrapper inspects the returned flat list, rebuilds the `Session` model, and returns it. Audit is **not** emitted here — `get_session` never emits (per the contract).

### 5.3 `refresh_session_lua`

Identical to `get_session_lua` in behavior, but the Python wrapper emits `session.refreshed` audit after the script returns. (We could collapse `get` and `refresh` into one script with a `mode` ARGV, but the audit asymmetry means the Python wrapper is the right place to branch.)

### 5.4 `revoke_session_lua`

```lua
-- KEYS[1] = auth_svc:session:{session_id}
-- KEYS[2] = auth_svc:user_sessions:{user_id}
-- ARGV[1] = session_id
-- ARGV[2] = user_id

local existed = redis.call('DEL', KEYS[1])
redis.call('SREM', KEYS[2], ARGV[1])
return existed  -- 1 if existed, 0 if not
```

The Python wrapper emits `session.revoked` audit only if `existed == 1` (matches `test_revoke_emits_audit_event_only_on_hit`).

### 5.5 `revoke_all_for_user_lua`

```lua
-- KEYS[1] = auth_svc:user_sessions:{user_id}
-- ARGV[1] = key_prefix = 'auth_svc:session:'

local members = redis.call('SMEMBERS', KEYS[1])
local count = 0
for _, sid in ipairs(members) do
  if redis.call('DEL', ARGV[1] .. sid) == 1 then
    count = count + 1
  end
end
redis.call('DEL', KEYS[1])
return count
```

The Python wrapper emits `session.revoked_all_for_user` audit only if `count > 0` (matches `test_revoke_all_emits_one_event_with_count`).

### 5.6 `recompute_user_set_ttl_lua`

```lua
-- KEYS[1] = auth_svc:user_sessions:{user_id}
-- ARGV[1] = key_prefix = 'auth_svc:session:'

local members = redis.call('SMEMBERS', KEYS[1])
if #members == 0 then
  redis.call('DEL', KEYS[1])
  return 0
end

local max_expires_unix = 0
for _, sid in ipairs(members) do
  local expires_at = redis.call('HGET', ARGV[1] .. sid, 'expires_at')
  if expires_at then
    -- expires_at is ISO 8601; we ALSO need a sibling pre-computed unix-seconds.
    -- Better: store expires_at_unix in the session Hash too, alongside the ISO.
    -- The Python wrapper writes both fields on create, and the Lua reads the unix one.
    -- (See §3.1 — add `expires_at_unix` to the Hash schema.)
    local unix = tonumber(expires_at_unix)
    if unix and unix > max_expires_unix then
      max_expires_unix = unix
    end
  end
end

if max_expires_unix > 0 then
  redis.call('EXPIREAT', KEYS[1], max_expires_unix)
end
return max_expires_unix
```

**Note on the implementation choice for the recompute.** Storing both `expires_at` (ISO 8601) and `expires_at_unix` (integer seconds) in the session Hash avoids string parsing in Lua. The Python wrapper computes `unix_seconds(created_at + ABSOLUTE_TTL)` and writes both fields on create.

## 6. Audit emission

Audit is **always post-script**, never inside the Lua. The Python wrapper:

1. Computes the ARGV from the injected clock.
2. Calls the Lua script.
3. Inspects the return value.
4. Emits the audit event with the right `event_code` and payload (using `str(session_id)` and `str(user_id)`).

**Why.** Audit is observability; the script's atomicity is correctness. Coupling the audit sink's I/O into the Lua would:

- Couple the script to the audit sink's latency (Lua holds the Redis main thread).
- Make the audit contract dependent on Redis being healthy (the sink might be a remote HTTP endpoint that times out).
- Break the symmetry with `InMemorySessionManager`, which does audit post-mutex.

The contract is: the script is the source of truth for **state changes**; the audit sink is the source of truth for **observability**. They are linked by the wrapper, not by the script.

## 7. Parity requirement

| ABC method                  | Lua script              | Audit code                   | Returns  |
| --------------------------- | ----------------------- | ---------------------------- | -------- |
| `create_session(user_id, *, ttl, metadata)` | `create_session_lua` (+ `recompute_user_set_ttl_lua`) | `session.created` (post) | `Session`; raises `ValueError` on bad `ttl` / `None` user_id |
| `get_session(session_id)`   | `get_session_lua`       | (none)                       | `Session` or `None` |
| `refresh_session(session_id)` | `get_session_lua` (or `refresh_session_lua`) | `session.refreshed` (post, only on hit) | `Session` or `None` |
| `revoke_session(session_id)` | `revoke_session_lua`   | `session.revoked` (post, only on hit) | `bool` (True iff existed) |
| `revoke_all_for_user(user_id)` | `revoke_all_for_user_lua` | `session.revoked_all_for_user` (post, only if count > 0) | `int` (count) |

Parity invariants the implementer must preserve:

- `ValueError` for `create_session` if `user_id is None`, `ttl <= timedelta(0)`, or `ttl > self._idle_ttl`. Raise in Python before the script call.
- `Session` model's `created_at`, `expires_at`, `last_used_at` are tz-aware UTC. The Redis side stores ISO 8601 with the `+00:00` suffix; the Python wrapper parses with `datetime.fromisoformat` and asserts `tzinfo is not None`.
- Audit payload uses `str(session_id)` and `str(user_id)`, not the UUID objects. The tests assert the string form.
- Strict `>` for idle, `>=` for max. Tested by `test_get_returns_none_for_idle_expired` and `test_get_returns_none_for_max_expired`.

## 8. Implementation surface

### 8.1 Created

- `services/auth-svc/app/redis_session_manager.py` — the new `RedisSessionManager` class, ~350 lines. One method per ABC method, plus a `_load_scripts()` helper that registers the six Lua scripts via `self._redis.register_script(...)`.
- `services/auth-svc/REDIS_BACKEND_DESIGN.md` — this document.
- `services/auth-svc/IMPLEMENTATION_REDIS_TESTING.md` — sibling, the test-fixture strategy.
- `services/auth-svc/app/conftest.py` — the `redis_container`, `redis_client`, and `_redis_flush` fixtures.

### 8.2 Edited

- `services/auth-svc/pyproject.toml` — add `redis>=5.0` to `dependencies`; add `testcontainers[redis]>=4.8` to `optional-dependencies.dev`.
- `services/auth-svc/requirements.txt` — add `redis>=5.0` (the file is not auto-derived from `pyproject.toml`; it's a literal pip req file).
- `services/auth-svc/requirements-dev.txt` — add `testcontainers[redis]>=4.8`.
- `services/auth-svc/Dockerfile` — add a comment block documenting `REDIS_URL`. No `apt-get install redis-tools`; Redis is external.
- `services/auth-svc/app/test_session_manager.py` — **only the `manager` fixture at lines 70–82.** One permitted exception to the no-test-edit rule. The fixture reads `AUTH_SVC_BACKEND` env var and returns `RedisSessionManager` when `"redis"`. Test bodies stay untouched.
- `.github/workflows/ci-hello-world.yml` — add a NEW `test-auth-svc` job (not a matrix entry on the existing `test-lint-build` job, which runs against `services/hello-world/`). The new job installs `services/auth-svc` deps, sets `AUTH_SVC_BACKEND` per matrix entry, and runs pytest + ruff.

## 9. Open questions (architect's hypotheses)

1. **Sync or async client? — Hypothesis: sync `redis.Redis` from `redis-py`.** Justify: matches the sync ABC, no async test infrastructure exists, `redis-py` async is a separate import (`redis.asyncio`). The implementer can change to async if they find a reason.
2. **Date arithmetic in Lua vs Python? — Hypothesis: pre-computed deltas as ARGV.** Lua's integer arithmetic on Unix timestamps is fine, but Python-side computation keeps the Lua scripts thin and lets the Python wrapper hold the clock-injection contract. Pass `now_unix`, `idle_ttl_seconds`, `absolute_ttl_seconds` as ARGV.
3. **User-index TTL: max-of-members or none? — Hypothesis: max of members' `expires_at`, refreshed atomically on every SADD.** See §3.3 and §5.6.
4. **EXISTS guard in `create_session_lua`? — Hypothesis: keep it.** Paranoid; session_id is `uuid4()` so a collision is astronomical, but the guard makes the script self-contained.
5. **Production Redis client config? — Hypothesis: out of scope; `REDIS_URL` env-var-driven.** The `RedisSessionManager.__init__` accepts a `redis.Redis` instance OR builds one from `REDIS_URL`. Production deployment is issue #4 AC-1.4.

## 10. Cross-references

- `DESIGN.md` §1 — TTL semantics.
- `DESIGN.md` §2 — audit event contract.
- `DESIGN.md` §5 — the `SessionManager` ABC docstring ("the Redis backend (out of scope) will use a per-session Lua script").
- `IMPLEMENTATION_GUIDE.md` — repo-wide implementation conventions.
- `services/auth-svc/app/session_manager.py:43-66` — the `SessionManager` ABC.
- `services/auth-svc/app/test_session_manager.py:8-13` — the contract header docstring.
- `services/auth-svc/app/test_session_manager.py:70-82` — the `manager` fixture (the one permitted edit).
- `services/auth-svc/app/test_session_manager.py:84-518` — the 38 tests.

## 11. Operational notes

- **Connection pooling.** The `RedisSessionManager.__init__` accepts a `redis.Redis` instance. The factory (`__init__` without an instance) builds `redis.Redis.from_url(REDIS_URL, decode_responses=True)`. `decode_responses=True` keeps the wrapper's typing simple (strings, not bytes).
- **Connection failures.** Let `redis.exceptions.ConnectionError` propagate. The ABC does not promise retry; the caller (FastAPI dependency) handles retries.
- **Key prefix.** Hard-coded `auth_svc:`. If a future multi-tenant deployment needs per-tenant prefixes, that's a `RedisSessionManager(prefix=...)` constructor arg — out of scope here.

## 12. Failure modes

- **Redis is down.** `create_session` raises; `get_session` returns `None` (or raises, depending on the wrapper's choice — the in-memory backend raises; match it). Audit emission is best-effort and does not fail the operation.
- **Lua script returns nil unexpectedly.** Treat as `None` from the ABC method. Do not retry inside the wrapper.
- **Clock injection corrupted.** If the injected clock returns a `datetime` without `tzinfo`, the wrapper raises `ValueError` before the script call. Matches the in-memory backend's behavior.

## 13. Rollout plan

- **Phase 1 (this PR).** Add `RedisSessionManager`, fixture rewiring, CI matrix. No production deployment.
- **Phase 2 (issue #4 AC-1.4).** Production Redis provisioning, `REDIS_URL` injection via the deployment platform, monitoring (Redis-side key-space notifications are out of scope; service-side metrics are the observability path).
- **Phase 3 (future).** Multi-DC replication, async client, key-space-notification-driven idle sweeper.
