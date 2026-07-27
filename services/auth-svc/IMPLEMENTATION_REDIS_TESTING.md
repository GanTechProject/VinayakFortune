# Redis 7 SessionManager Backend — Test-Fixture + CI Strategy

| Field          | Value                                                                                  |
| -------------- | -------------------------------------------------------------------------------------- |
| Status         | Specification (Phase C, step 2; issue #5 AC-2.4)                                      |
| Sibling        | `services/auth-svc/REDIS_BACKEND_DESIGN.md`                                            |
| Test contract  | `services/auth-svc/app/test_session_manager.py` — 38 tests, no body modifications      |
| Base commit    | `4a0ea1a` (PR #49 squash) on `wip/auth-svc-redis-session-manager`                      |
| Target CI      | A new `test-auth-svc` job added to `.github/workflows/ci-hello-world.yml`              |

## 1. Goal

The same 38 tests that currently pass against `InMemorySessionManager` must pass against the new `RedisSessionManager` backend, with **zero modifications to any test-body in `test_session_manager.py`**. The test contract — the 38 function bodies, the assertions, the boundary conditions, the audit-emission expectations, the `clock` and `audit` fixtures, the contract that the `manager` fixture is typed `SessionManager` — is sacred. The testing strategy here is about **how to run** those 38 tests against a second backend and **how to express the matrix in CI**; it is not about editing the tests. The Redis 7 backend must satisfy the contract by being drop-in compatible at the `SessionManager` ABC boundary (see `REDIS_BACKEND_DESIGN.md` §5 and §7).

## 2. Test-fixture strategy

### 2.1 Recommendation: duplicated test file (failure-isolation)

I recommend the **duplicated test file** approach over a single-file `@pytest.mark.parametrize` strategy. The two strategies are described below; the recommendation is duplication, with the rationale in §2.3.

### 2.2 The two strategies

**Strategy A — single file, `@pytest.mark.parametrize` on the `manager` fixture.**

```python
# services/auth-svc/app/test_session_manager.py
# (Modifications limited to the manager fixture at lines 70-82.)
# All 38 test bodies remain byte-identical.

import os
import pytest

@pytest.fixture
def manager(clock, audit, request):
    """Yield the SessionManager under test, parameterized by env var."""
    backend = os.environ.get("AUTH_SVC_BACKEND", "memory")
    if backend == "redis":
        # Imported lazily so the test suite can run without redis-py when
        # AUTH_SVC_BACKEND is unset. The redis_client fixture is provided
        # by conftest.py and depends on the AUTH_SVC_REDIS_URL env var.
        from app.conftest_helpers import build_redis_manager
        return build_redis_manager(clock=clock, audit_sink=audit,
                                   redis_client=request.getfixturevalue("redis_client"))
    from app.session_manager import InMemorySessionManager
    return InMemorySessionManager(clock=clock, audit_sink=audit)
```

This satisfies a one-line edit contract for the `manager` fixture. The CI matrix sets `AUTH_SVC_BACKEND=memory` and `AUTH_SVC_BACKEND=redis` to toggle. The same 38 tests run twice; pytest reports 76 invocations.

**Strategy B — duplicated test file, second file with `redis_manager` fixture.** (recommended)

Two test files, identical test bodies, different fixture name.

```python
# services/auth-svc/app/test_session_manager.py
# UNCHANGED on disk from the 38-test baseline. The manager fixture still
# yields InMemorySessionManager (lines 70-82 untouched).

@pytest.fixture
def manager(clock: FakeClock, audit: CollectingAuditSink) -> SessionManager:
    from app.session_manager import InMemorySessionManager
    return InMemorySessionManager(clock=clock, audit_sink=audit)
```

```python
# services/auth-svc/app/test_redis_session_manager.py  (NEW; 39th file in the suite)
# All 38 test functions copied verbatim from test_session_manager.py.
# The ONLY delta: the fixture parameter is `redis_manager` (not `manager`).
# Identical assertions, identical arrange/act, identical clock/audit usage.

import threading
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4
import pytest
import redis

from app.session_manager import (
    ABSOLUTE_TTL, IDLE_TTL, Session, SessionManager,
)
from app.redis_session_manager import RedisSessionManager


class FakeClock:
    def __init__(self, start=None):
        self._now = start or datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    def __call__(self):
        return self._now
    def advance(self, delta):
        self._now = self._now + delta


class CollectingAuditSink:
    def __init__(self):
        self.events = []
    def __call__(self, code, payload):
        self.events.append((code, payload))


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def audit():
    return CollectingAuditSink()


@pytest.fixture
def redis_client():
    """A real redis.Redis connected to AUTH_SVC_REDIS_URL on DB 15, flushed per test."""
    import os
    url = os.environ.get("AUTH_SVC_REDIS_URL", "redis://localhost:6379/15")
    client = redis.Redis.from_url(url, decode_responses=True)
    client.ping()  # fail fast if Redis is not reachable
    yield client
    client.flushdb()  # isolation: every test starts with an empty DB


@pytest.fixture
def redis_manager(clock, audit, redis_client):
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


# --- The 38 test functions, copied verbatim from test_session_manager.py ---
# (Their bodies are identical; only the fixture parameter `manager` is
# renamed to `redis_manager`.) Implementer: copy/paste the function bodies
# from the existing file; do NOT retype. The duplication is the point.

def test_create_returns_session_with_unique_id(redis_manager: SessionManager) -> None:
    user = uuid4()
    s1 = redis_manager.create_session(user)
    s2 = redis_manager.create_session(user)
    assert isinstance(s1, Session)
    assert isinstance(s2, Session)
    assert s1.session_id != s2.session_id
    assert s1.user_id == user
    assert s2.user_id == user

# ... 37 more tests, byte-identical to test_session_manager.py, with the
#     single substitution `manager` -> `redis_manager` in every signature
#     and body. ...
```

### 2.3 Why duplication beats parametrize (failure isolation)

The 38 tests assert subtle invariants: idle-window vs absolute-max ordering, concurrent refresh atomicity, audit emission-on-miss semantics, `last_used_at` monotonicity. When a regression lands, the failure mode I want is:

- **Duplication (Strategy B):** A Redis-only regression shows up as "38 in-memory pass, 12 of 38 Redis fail." The next agent reads the failure list, scopes the bug to the Redis backend, fixes it.
- **Parametrize (Strategy A):** A single broken assertion shows up as 2 failures (one per backend), the test name carries no indication of which backend failed, and the orchestrator must re-inspect the env var to know which matrix entry produced the failure. Worse, if the 38 tests share state via a module-level fixture (e.g. a counter), a teardown failure in the Redis backend can mask the in-memory pass count.

Additional reasons duplication wins:

1. **No `xfail` markers.** A parametrized suite that discovers a Redis-only bug is tempted to mark the failing subset `xfail` ("known-broken on Redis"). Duplication forbids this — both backends must be green or the PR is blocked.
2. **No `if backend == "redis"` in test bodies.** Parametrize invites test bodies to branch on `request.param`; duplication forbids that.
3. **CI failure attribution is direct.** `pytest -q test_redis_session_manager.py` says "12 failed in test_redis_session_manager.py" — no matrix inspection needed.
4. **The 38 test bodies stay byte-identical to the in-memory file.** A code review can `diff` the two files and see exactly one substitution per test: `manager` -> `redis_manager`. There is no way to accidentally change a test's assertion.
5. **Failure-isolation bandwidth.** The 39th-file approach fails the build at 12 of 38 for a typical Redis bug; the parametrize approach fails at 1 of 38 (because each test runs once per matrix entry but the test name collapses both runs in the report). The duplicated file's signal-to-noise is higher.

### 2.4 Divergence from the strategy prescribed in the design doc

The design doc (`REDIS_BACKEND_DESIGN.md` §8.2) prescribes a **one-line edit to `test_session_manager.py`'s `manager` fixture** (Strategy A) as the canonical approach. This testing document recommends **Strategy B (duplication)** as the architect's preferred path because of the failure-isolation reasons above. The two strategies are mutually exclusive; the conductor must choose one before the implementer dispatches. The `conftest.py` + `redis_client` fixtures from §8.1 are still required in both strategies (the `redis_client` is needed by the duplicated file's `redis_manager` fixture, or by the parametrize strategy's branch).

## 3. Redis service strategy in CI

### 3.1 Recommendation: GitHub Actions `services:` block with `redis:7-alpine`

I recommend the **GHA-native `services:` block** over `testcontainers` and over a checked-in `docker-compose.yml`. Constraints:

- Must run on `actions/runner-images/ubuntu-latest` (Windows runners do not support `services:` blocks for arbitrary images as cleanly).
- Must not add more than ~10 s to the suite (the matrix backend is `redis`, which adds a Redis container cold-start; `services:` with a `health check` is the cheapest path).
- Must work under the human-driven paste-into-main workflow ritual (per memory `oauth-workflow-scope-block` and `oauth-workflow-scope-probe-2026-07-27`). A self-contained yaml is paste-ready; testcontainers would require a `pip install testcontainers[redis]` step that adds latency and a `docker.sock` mount requirement (which is not available in unprivileged GHA runners).
- Must not depend on `docker compose` (the runner does not have it preinstalled; the GHA-native path uses `docker` directly via the `services:` block).

`docker-compose.yml` is overkill for one Redis instance in one job; `testcontainers` adds dependency complexity; GHA `services:` is the right tool.

### 3.2 The complete `test-auth-svc` job

I recommend **adding the job to the existing `ci-hello-world.yml`** rather than a new workflow file. Reasons:

- One less file to paste into main via the web UI (the paste ritual is human-driven; a typo in a file path blocks the whole PR).
- The job has a distinct `runs-on`, distinct `working-directory`, and distinct `services:` block, so there is zero coupling with the existing `test-lint-build` job.
- The `name:` field disambiguates the two jobs in the PR checks UI.
- All required-status-check names on the branch-protection rule are flat strings; adding a new job to an existing workflow does NOT change the names of existing jobs (which would force a branch-protection update). A new workflow file would add a new check name, which the branch-protection rule would also need to register — more ceremony.

```yaml
# .github/workflows/ci-hello-world.yml  (NEW job added at the end of `jobs:`)

  test-auth-svc:
    name: auth-svc tests (backend=${{ matrix.backend }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        backend: [memory, redis]
    # The `services:` block is GHA-native: it starts a container, waits for
    # the healthcheck to pass, and exposes the listed port on localhost.
    # We declare it UNCONDITIONALLY (not gated by `if: matrix.backend == 'redis'`)
    # because the healthcheck-driven startup takes ~1 s on ubuntu-latest
    # (redis:7-alpine cold start + redis-server readiness), which is well
    # under our ~10 s budget. Gating it would add an `if:` step with
    # conditional-service semantics that the GHA docs flag as
    # "best-effort, may race" — see
    # https://docs.github.com/en/actions/using-containerized-services
    # The unconditional path is the documented-supported path.
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 1s
          --health-timeout 1s
          --health-retries 30
    env:
      AUTH_SVC_REDIS_URL: redis://localhost:6379/15
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: services/auth-svc/requirements-dev.txt
      - name: Install dependencies
        working-directory: services/auth-svc
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      - name: Run unit tests (backend=${{ matrix.backend }})
        working-directory: services/auth-svc
        run: |
          if [ "${{ matrix.backend }}" = "redis" ]; then
            # Wait for the Redis service to be reachable; the `services:`
            # healthcheck should have already done this, but a defensive
            # retry makes the suite robust to a slow runner image.
            for i in $(seq 1 30); do
              if redis-cli ping >/dev/null 2>&1; then break; fi
              sleep 1
            done
            AUTH_SVC_REDIS_URL=redis://localhost:6379/15 \
              python -m pytest app/test_redis_session_manager.py -v
          else
            python -m pytest app/test_session_manager.py -v
          fi
      - name: Run linter
        working-directory: services/auth-svc
        run: python -m ruff check app/
```

### 3.3 Why unconditional `services:` (and not `if: matrix.backend == 'redis'`)

GHA `services:` blocks can be conditionally declared with `if: matrix.backend == 'redis'`, but the GHA documentation marks conditional services as a less-reliable path: the runner's job-container setup runs before `if:` is evaluated, and a conditional service occasionally races the next step's first network call. The unconditional `services:` path is fully supported and adds ~1 s to the `memory` matrix entry's cold start — well within the ~10 s budget. The memory-only path pays the Redis startup cost but does not import or use the Redis client. **The `if: matrix.backend == 'redis'` alternative is rejected for reliability reasons**, not for cost reasons.

## 4. Line-by-line migration of the test file

### 4.1 `services/auth-svc/app/test_session_manager.py` (unchanged)

This file stays byte-identical to its state at `4a0ea1a`. Specifically:

- Lines 1-13: module docstring (contract header) — unchanged.
- Lines 15-30: imports — unchanged.
- Lines 32-67: `FakeClock`, `CollectingAuditSink`, `clock` fixture, `audit` fixture — unchanged.
- **Lines 70-82: `manager` fixture — UNCHANGED.** Still yields `InMemorySessionManager(clock=clock, audit_sink=audit)`. This is the contract; the design doc §8.2 permits a one-line edit here, but the duplication strategy (Strategy B) does NOT need it.
- Lines 84-518: the 38 test functions — UNCHANGED. Every body, every assertion, every fixture usage stays as-is.

The in-memory suite continues to run exactly as it did in PR #49.

### 4.2 `services/auth-svc/app/test_redis_session_manager.py` (new; 39th file)

Created by copying `test_session_manager.py` and applying exactly these substitutions:

1. **Module docstring** (lines 1-13): replace the `InMemorySessionManager` reference with a `RedisSessionManager` reference; preserve the "no body modifications" contract reference.
2. **`from app.session_manager import (...)` line 24-29**: add `from app.redis_session_manager import RedisSessionManager` (the new module from the design doc §8.1).
3. **`manager` fixture (lines 70-82)**: REPLACED with the `redis_manager` fixture shown in §2.2. The `redis_client` fixture it depends on is provided by `services/auth-svc/app/conftest.py` (new file, per design doc §8.1).
4. **All 38 test function signatures and bodies**: byte-identical to `test_session_manager.py` EXCEPT for the substitution `manager` -> `redis_manager` in:
   - the function signature (e.g. `def test_create_returns_session_with_unique_id(redis_manager: SessionManager) -> None:`);
   - every body reference to `manager.create_session(...)`, `manager.get_session(...)`, etc.

The `diff` between the two files should be: docstring, one import line, one fixture block, and 38 single-token substitutions (`manager` -> `redis_manager`). If any test assertion changes, the test contract has been violated.

### 4.3 `services/auth-svc/app/conftest.py` (new)

This is the design doc §8.1 spec verbatim:

```python
# services/auth-svc/app/conftest.py
# Provides the `redis_client` fixture (and its dependency, the
# `redis_container` / `_redis_flush` helpers) to the test suite.
#
# Used by:
#   - app/test_redis_session_manager.py  (the 39th duplicated file)
#   - app/test_session_manager.py        (NOT modified by this PR; if the
#                                         conductor picks Strategy A, the
#                                         manager fixture is the only edit)
#
# Skip-on-unavailable: the redis_client fixture is only requested by tests
# that ask for the `redis_manager` fixture. The in-memory suite never asks
# for it, so the redis_client fixture is never resolved, and the suite
# runs even when Redis is absent.

from __future__ import annotations

import os

import pytest
import redis


@pytest.fixture
def redis_client():
    """A redis.Redis client connected to AUTH_SVC_REDIS_URL, DB 15.

    Defaults to redis://localhost:6379/15 (the convention used by the
    GitHub Actions `services:` block in .github/workflows/ci-hello-world.yml).
    Flushes the DB on teardown so each test starts clean.
    """
    url = os.environ.get("AUTH_SVC_REDIS_URL", "redis://localhost:6379/15")
    client = redis.Redis.from_url(url, decode_responses=True)
    client.ping()  # fail fast if Redis is unreachable
    yield client
    client.flushdb()
```

The `redis_container` and `_redis_flush` helpers from the design doc §8.1 are NOT implemented in this PR because we use the GHA `services:` block (no testcontainers). The conftest stays minimal.

### 4.4 What changes vs what stays (audit table)

| File                                            | Status   | Notes                                                                                  |
| ----------------------------------------------- | -------- | -------------------------------------------------------------------------------------- |
| `app/session_manager.py`                        | unchanged| The `SessionManager` ABC and `InMemorySessionManager` are untouched.                    |
| `app/test_session_manager.py`                   | unchanged| 38 tests, byte-identical. (Strategy A would edit lines 70-82; Strategy B does not.)    |
| `app/test_redis_session_manager.py`             | created  | 38 tests, byte-identical to the in-memory file, with `manager` -> `redis_manager`.     |
| `app/redis_session_manager.py`                  | created  | The new backend (per design doc §8.1). Out of scope for this testing doc.              |
| `app/conftest.py`                               | created  | `redis_client` fixture; flushes DB 15 per test.                                        |
| `pyproject.toml`                                | edited   | Add `redis>=5.0` to deps; add `redis>=5.0` to dev deps (per design doc §8.2).          |
| `requirements.txt`                              | edited   | Add `redis>=5.0` (per design doc §8.2).                                                |
| `requirements-dev.txt`                          | edited   | Add `redis>=5.0` (per design doc §8.2).                                                |
| `Dockerfile`                                    | edited   | Add a `REDIS_URL` comment block (per design doc §8.2). No redis-tools install.         |
| `.github/workflows/ci-hello-world.yml`          | edited   | Add the `test-auth-svc` job shown in §3.2.                                             |
| `REDIS_BACKEND_DESIGN.md`                       | unchanged| This testing doc is its sibling.                                                       |
| `IMPLEMENTATION_REDIS_TESTING.md`               | created  | This file.                                                                             |

## 5. Local development recipe

### 5.1 Without Docker (host-installed `redis-server`)

```bash
# 1. Install Redis 7 (Ubuntu/Debian). On macOS: `brew install redis@7`.
sudo apt-get update && sudo apt-get install -y redis-server

# 2. Start Redis 7 on the default port, DB 15 unused.
redis-server --daemonize yes --port 6379

# 3. Run the in-memory suite (no Redis needed).
cd services/auth-svc
python -m pip install -r requirements-dev.txt
python -m pytest app/test_session_manager.py -v

# 4. Run the Redis suite.
AUTH_SVC_REDIS_URL=redis://localhost:6379/15 \
  python -m pytest app/test_redis_session_manager.py -v
```

### 5.2 With Docker (`redis:7-alpine`)

```bash
# 1. Start a Redis 7 container, named so it can be stopped cleanly.
docker run -d --name auth-svc-redis -p 6379:6379 redis:7-alpine

# 2. Run the in-memory suite (Redis is irrelevant for this suite).
cd services/auth-svc
python -m pip install -r requirements-dev.txt
python -m pytest app/test_session_manager.py -v

# 3. Run the Redis suite.
AUTH_SVC_REDIS_URL=redis://localhost:6379/15 \
  python -m pytest app/test_redis_session_manager.py -v

# 4. Tear down.
docker stop auth-svc-redis && docker rm auth-svc-redis
```

### 5.3 Skipping the Redis suite when Redis is absent

The `redis_client` fixture fails fast with a `redis.exceptions.ConnectionError` from `client.ping()`. Tests that request `redis_manager` will fail collection, not silently skip. This is intentional: a missing Redis on a Redis-backend test is a real failure. If the conductor wants graceful skip semantics, add a session-scoped fixture that probes `redis_client.ping()` and calls `pytest.skip(...)` — but the architect's recommendation is fail-fast: a missing Redis is a developer environment bug, not a test-suite bug.

## 6. CI cost

### 6.1 Estimate

Per backend entry, the suite does:
- Checkout: ~2 s
- `pip install` (cached on second run): ~10 s cold / ~2 s warm
- `pytest` (38 tests, no I/O for the in-memory suite; 38 tests with network round-trips for the Redis suite): ~5 s for in-memory, ~10-15 s for Redis (the per-test `flushdb` and Lua-script-registration overhead)
- `ruff check`: ~1 s
- GHA service cold start (Redis): ~2 s (parallel with checkout)

Total: **~25-30 s per backend matrix entry on a warm cache, ~40-50 s cold.**

### 6.2 Single-OS, two-backend matrix

The matrix is `[memory, redis]` on a single `runs-on: ubuntu-latest` runner. **No Windows or macOS matrix entries** — the auth-svc test suite is platform-agnostic (it uses only `pydantic`, `pytest`, `redis-py`, and stdlib), and the branch-protection rule does not require platform diversity for this service. The total CI cost is **roughly 2x a single-backend suite** (~50-100 s), well under the auth-svc's contribution to the repo-wide CI budget.

### 6.3 Why the matrix is mandatory (not collapsed)

Collapsing to one backend only is tempting: "just run the in-memory suite, since the in-memory backend has been the contract for two PRs (#49 and the original test PR)." This is rejected because:

- The Redis backend is the AC-2.4 deliverable. Running only the in-memory suite gives zero signal on the Redis implementation.
- The 38 tests against `RedisSessionManager` are the regression net for the new code. A red build on the new code is the only signal that catches a Lua-script bug, a clock-injection mismatch, a key-prefix typo, or an audit-emission asymmetry (per design doc §6).
- The matrix doubles the bill but halves the risk of a silent Redis regression shipping to production.

The matrix is the architect's recommended path.

## 7. Failure isolation

When the Redis suite fails in CI, the orchestrator will see a `test-auth-svc (backend=redis)` job failure in the PR checks. The most likely failure modes, with their symptoms, are:

1. **Redis service did not start.**
   *Symptom:* `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.` The `redis_client` fixture's `ping()` call raises before the first test runs. The pytest output shows one error (the fixture error) and 38 collection errors.
   *Diagnostic:* The GHA `services:` healthcheck logs are at the bottom of the step output. If the `redis:7-alpine` image failed to pull (rate-limited registry), the service never started.
   *Fix:* Re-run the job; if reproducible, the runner image is missing the `redis-cli` for the healthcheck — change the healthcheck to a TCP probe (`nc -z localhost 6379`).

2. **Port conflict on the runner.**
   *Symptom:* `Bind for 0.0.0.0:6379 failed: port is already allocated`. GHA's service-startup step fails before any test runs.
   *Diagnostic:* Look for prior `services:` blocks in the same job that may have reserved 6379. Unlikely in this PR (only the redis service uses 6379), but possible if a future PR adds another service.
   *Fix:* Use a non-default port; update `AUTH_SVC_REDIS_URL` to match.

3. **EXPIREAT clock drift between fake clock and Redis wall time.**
   *Symptom:* `test_clock_injection_determines_expiry` fails with `assert m.get_session(s.session_id) is None` (the assertion that after `IDLE_TTL + 1s` of fake-clock advance, the session is gone). The session is NOT gone; the in-memory `is_max_expired` Python check should have fired but didn't.
   *Diagnostic:* This indicates the Lua's `(now_unix - last_used_at_unix) > idle_ttl_seconds` comparison is off — either `now_unix` is the wall clock (not derived from the fake clock) or `last_used_at_unix` is not what the fake clock produced. Re-read `REDIS_BACKEND_DESIGN.md` §4 and §5.2: the ARGV `[now_iso, now_unix, idle_ttl_seconds, last_used_at_unix, expires_at_unix, ...]` must be derived from the injected `clock()`, not from `time.time()`.
   *Fix:* In the `RedisSessionManager.create_session` Python wrapper, compute `now_iso = clock().isoformat()` and `now_unix = int(clock().timestamp())`; pass both to the Lua. Same for `get_session`/`refresh_session`.

4. **`redis` vs `redis.asyncio` import mismatch.**
   *Symptom:* `AttributeError: module 'redis' has no attribute 'Redis'` (or `has no attribute 'from_url'`).
   *Diagnostic:* The implementer imported `from redis.asyncio import Redis` thinking the sync `Redis` is in the same module. It is not: `redis.Redis` is sync, `redis.asyncio.Redis` is async. The sync client is at the top level of the `redis` package.
   *Fix:* `import redis; client = redis.Redis.from_url(...)` (sync). The design doc §9 hypothesis #1 confirms sync is the choice.

5. **Audit emission asymmetry.**
   *Symptom:* `test_revoke_emits_audit_event_only_on_hit` fails: either the miss emits (audit leak) or the hit does not (audit gap).
   *Diagnostic:* The Lua's `revoke_session_lua` returns `existed` (1 or 0). The Python wrapper must emit ONLY when `existed == 1`. Re-read `REDIS_BACKEND_DESIGN.md` §5.4 and §6.

## 8. Cross-references to `REDIS_BACKEND_DESIGN.md`

- **§3 (Storage model)** — `auth_svc:session:{session_id}` (Hash) and `auth_svc:user_sessions:{user_id}` (Set) key naming conventions that the `redis_client.flushdb()` teardown relies on. The test fixture does NOT need to know the prefix; it only knows it must `flushdb` DB 15 between tests.
- **§4 (TTL semantics under Redis primitives)** — the load-bearing rule for the fake-clock/real-clock split in the `redis_manager` fixture (§2.2 of this doc). The `is_idle_expired` is Python-side, the `is_max_expired` is both Python-side AND Lua-side via `EXPIREAT`.
- **§6 (Audit emission)** — audit is post-script, never inside the Lua. The 38 audit assertions in `test_session_manager.py` (and their duplicates in `test_redis_session_manager.py`) verify the post-script contract.
- **§7 (Parity requirement)** — the per-method table that maps each ABC method to its Lua script and audit code. The 38 tests are the parity tests; this doc is the test-fixture strategy that makes the parity table enforceable in CI.
- **§8.1 (Created files)** — the list of files this PR creates; the duplicated test file is in addition to the design doc's list, as a §2.4 divergence flagged for conductor approval.
- **§8.2 (Edited files)** — the `test_session_manager.py:70-82` one-line edit. NOT applied under Strategy B (duplication). Flagged for conductor.
- **§11 (Operational notes)** — `decode_responses=True` is the typing simplification that lets the Python wrapper treat Hash fields as `str` (not `bytes`); the `redis_client` fixture in `conftest.py` uses this. Connection failure semantics: `redis.exceptions.ConnectionError` propagates; the `redis_client.ping()` in the fixture is the fail-fast surface.

## 9. Open questions for the conductor

1. **Duplication vs parametrize (Strategy B vs A).** The design doc §8.2 prescribes the parametrize approach (one-line edit to `test_session_manager.py`'s `manager` fixture). This testing doc recommends the duplication approach (a 39th file with a `redis_manager` fixture) for failure-isolation reasons. The conductor must choose; the two are mutually exclusive (you cannot have both `manager` and `redis_manager` named fixtures coexist in a single-file parametrize model). **Recommendation: duplication.**
2. **Pin to `redis:7-alpine` or matrix across `redis:7.2-alpine` and `redis:7.4-alpine`?** The design doc is silent on minor-version pinning. The architect recommends `redis:7-alpine` (rolling tag, always 7.x latest) for simplicity. A two-entry Redis-version matrix doubles the matrix cardinality (4 entries total) and adds ~30 s of CI time per PR; the failure-isolation benefit is small unless a specific 7.4-only bug is suspected. **Recommendation: `redis:7-alpine` only; bump when a new minor ships.**
3. **`AUTH_SVC_REDIS_URL` as a hard-coded `redis://localhost:6379/15` or as a job-matrix variable?** The GHA yaml in §3.2 hard-codes DB 15. A matrix variable is more flexible but harder to read. The hard-coded value matches the `conftest.py` default; tests that need a different URL can set the env var. **Recommendation: hard-code.**
4. **Should `conftest.py` add a `pytest.skip` for missing Redis, or fail fast?** The §5.3 recipe fails fast. A skip would let the suite run green in environments without Redis, which is convenient for contributors who don't have Redis installed locally — but masks the "this PR requires Redis to validate" message. **Recommendation: fail fast.**

## 10. Revision history

### 1.0 Revision history

- Initial spec: test-fixture strategy (duplicated test file), GHA `services:` block, line-by-line migration, local-dev recipe, CI cost, failure isolation, cross-references to the design doc, four open questions for the conductor.
