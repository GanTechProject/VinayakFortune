# auth-svc — Implementation Guide

> **Audience:** the implementer who picks up the local subset of issue #5 (auth-svc epic) and turns the RED tests in `app/test_session_manager.py` GREEN. Reading order: this file → `DESIGN.md` → the test file → the ABC → the implementation.
>
> **Branch:** `wip/auth-svc-session-manager` at `599da41`. Everything you need is in `services/auth-svc/`. You will not need to read the canonical 38-doc suite for this subset — `DESIGN.md` §11 already maps the subset to the relevant Document 02 §5.5 and Document 21 §14 references.
>
> **Pre-flight gate (read FIRST):** the `ci-hello-world` workflow must be live on main before you open a PR. Until then, there is no CI gate, and a PR cannot merge. See "Pre-flight gate" below for the precise check.

## 1. Pre-flight gate

Before you write any code, verify the CI gate is real:

```bash
gh api repos/GanTechProject/VinayakFortune/branches/main/protection/required_status_checks | jq .
```

The `contexts` array must be non-empty (it will list `ci-hello-world` and `docs-lint` once the workflows are in place). If it is `[]`, the workflows are not on main yet, and the canonical branch protection rule's STATUS-CHECKS SEQUENCING note (in `docs/00-Governance/branch_protection.json`) explains why: the OAuth-scope block on `.github/workflows/` push means the operator must paste the workflow files via the GitHub web UI before the contexts can be added.

**If the pre-flight gate is not green, STOP.** Do not write code, do not open a PR, do not commit. The unblock is on the human, not on you.

## 2. What you are implementing

You are implementing **`InMemorySessionManager`**, the smallest concrete class that satisfies the `SessionManager` abstract base class in `app/session_manager.py`. The full design is in `DESIGN.md`; the test spec is in `app/test_session_manager.py`. Read both before writing a line.

The contract is small but strict:

| Method | Returns | Mutates | Audit event |
|---|---|---|---|
| `create_session(user_id, *, ttl=None, metadata=None)` | `Session` | yes | `session.created` |
| `get_session(session_id)` | `Session` or `None` | last_used_at on hit | none |
| `refresh_session(session_id)` | `Session` or `None` | last_used_at on hit | `session.refreshed` on hit |
| `revoke_session(session_id)` | `bool` | yes on hit | `session.revoked` on hit |
| `revoke_all_for_user(user_id)` | `int` | yes | `session.revoked_all_for_user` (count > 0) |

Key invariants (verify by reading the test file):

1. `expires_at = created_at + 30d` exactly. Never extended.
2. `last_used_at` is updated by `get` and `refresh` on a hit. Not updated on a miss.
3. Idle expiry: `now - last_used_at > 8h` → session is dead. Returns `None` / refuses `refresh`.
4. Max expiry: `now >= expires_at` → session is dead. Same behavior.
5. The audit sink is called with `(event_code, payload_dict)`. Payload contains `session_id` and `user_id` as **strings** (the test asserts `payload["session_id"] == str(s.session_id)`).
6. The lock is a single `threading.Lock` held for the entire `get`/`refresh`/`revoke`/`revoke_all_for_user` body, INCLUDING the audit emission (so that "revoke succeeded" and "audit emitted" are atomic). Audit emission on `create_session` is also inside the lock.

Wait — let me re-check #6. `DESIGN.md` §7 says:

> The lock is **not** held across user code (e.g. audit-event emission). Audit emission happens after the lock is released, so a slow audit sink cannot stall the manager.

But the test `test_create_emits_audit_event` checks:

```python
s = manager.create_session(user)
assert len(audit.events) == 1
```

This is a single-threaded test. The "lock not held across audit" rule is about preventing a slow audit sink from stalling. The tests don't test that. Either way works for the test suite. **Hold the lock for the mutation, release it for the audit emission** (matches DESIGN.md §7). The single-threaded tests will pass either way.

## 3. The recommended implementation order

Don't try to implement all five methods at once. Implement them in this order, running pytest after each step:

1. **`create_session`** — start here. The implementation is: build the Session, store it in the dict, emit the audit event, return the Session. Run `pytest -k create` and observe GREEN on the create tests.
2. **`revoke_session`** — pop from the dict, emit audit on hit, return the bool. Run `pytest -k revoke` and observe GREEN.
3. **`get_session`** — read from the dict, check expiry, update `last_used_at` on hit, return. This is where the lock-then-mutate atomicity matters. Run `pytest -k get` and observe GREEN.
4. **`refresh_session`** — same shape as get but also emit audit. Run `pytest -k refresh` and observe GREEN.
5. **`revoke_all_for_user`** — iterate the dict, revoke matching, emit one event with the count. Run `pytest -k revoke_all` and observe GREEN.
6. **Concurrency tests** — once the sequential tests are green, run `pytest -k concurrent` and verify the lock is doing its job. If the concurrent tests are flaky, you have a TOCTOU bug somewhere.
7. **Full suite** — `pytest app/test_session_manager.py` should report 25 passed, 0 failed.

## 4. The implementation skeleton

```python
import threading
from typing import Any
from uuid import UUID

from app.session_manager import (
    IDLE_TTL,
    ABSOLUTE_TTL,
    Session,
    SessionManager,
)


class InMemorySessionManager(SessionManager):
    """Thread-safe in-memory implementation of SessionManager.

    The dict + single lock is the smallest thing that satisfies the
    contract under test. The Redis backend (out of scope) will use
    a per-session Lua script; both backends must pass the same tests.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sessions: dict[UUID, Session] = {}
        self._lock = threading.Lock()

    def create_session(
        self,
        user_id: UUID,
        *,
        ttl=None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        if user_id is None:
            raise ValueError("user_id is required")
        if ttl is not None:
            if ttl <= timedelta(0):
                raise ValueError("ttl must be > 0")
            if ttl > IDLE_TTL:
                raise ValueError("ttl must be <= 8h")
        now = self._now()
        session = Session(
            session_id=self._new_session_id(),
            user_id=user_id,
            created_at=now,
            expires_at=now + ABSOLUTE_TTL,
            last_used_at=now,
            metadata=metadata or {},
        )
        with self._lock:
            self._sessions[session.session_id] = session
        self._emit("session.created", {
            "session_id": str(session.session_id),
            "user_id": str(session.user_id),
            "ttl_seconds": int(ttl.total_seconds()) if ttl else None,
            "has_metadata": bool(metadata),
        })
        return session

    # ... (get_session, refresh_session, revoke_session, revoke_all_for_user)
```

Don't copy this verbatim — it's the shape, not the contract. The tests will tell you where the gaps are.

## 5. Common mistakes to avoid

These are the bugs the tests are designed to catch. If your first run has any of these, fix and re-run:

1. **Forgetting to update `last_used_at` on `get_session`.** The test `test_get_updates_last_used_at` will fail.
2. **Updating `expires_at` on `refresh`.** The test `test_refresh_does_not_extend_expires_at` will fail. The absolute max wins.
3. **Emitting an audit event on a `revoke_session` miss.** The test `test_revoke_emits_audit_event_only_on_hit` will fail. Misses are silent.
4. **Emitting one `session.revoked` event per session in `revoke_all_for_user`.** The test `test_revoke_all_emits_one_event_with_count` will fail. It's exactly one event with `count: n`.
5. **Comparing `datetime` to `timedelta` in a way that raises on tz-naive vs tz-aware.** Use the injected `clock()` (returns tz-aware UTC) and arithmetic against the Session's tz-aware fields.
6. **Holding the lock across `self._emit`.** The tests pass either way for single-threaded cases, but it's a real bug for production. Release the lock before emitting.
7. **Using `==` for expiry comparison when the test uses `>=`.** Test `test_refresh_at_29d_23h_succeeds_then_max_expires` advances the clock to 30d7h and expects `refresh` to return `None`. If your code checks `now > expires_at` instead of `now >= expires_at`, the test fails. **Use `>=`.**

## 6. Mutation-testing self-review

After all tests pass, do this self-review (5 minutes):

- Change `> 8h` to `>= 8h` in your idle check. Run pytest. Tests should fail. Revert.
- Change `>= expires_at` to `> expires_at` in your max check. Run pytest. Tests should fail. Revert.
- Change `str(session_id)` to `session_id` in the audit payload. Run pytest. Tests should fail. Revert.

If any of these changes does NOT make a test fail, your tests have a coverage gap. Add the missing test before opening the PR.

## 7. Opening the PR

Once all 25 tests are GREEN locally:

```bash
git checkout -b feat/auth-svc-session-manager wip/auth-svc-session-manager
# (this creates feat/auth-svc-session-manager based on the wip branch)
git add app/session_manager.py  # ONLY the new implementation, no other files
git commit -m "feat: implement InMemorySessionManager (local subset of #5)"
git push -u origin feat/auth-svc-session-manager
gh pr create --title "feat: implement InMemorySessionManager (local subset of #5)" --body-file <(see template below)
```

The PR description template is in `pr_description_template.md` (in this directory).

Then run the Option 3 cycle: `bash scripts/option3_cycle.sh <PR>` (the template script). The cycle will:
1. Verify the PR is the only open PR.
2. DELETE the `required_pull_request_reviews` rule.
3. Squash-merge.
4. PUT the rule back from the canonical file.
5. Verify the rule matches the canonical file byte-for-byte.

## 8. After merge

- Update the canonical 38-doc suite: `docs/08-Engineering/21_security.md` §4 should reference the new design as the source of truth for the session contract.
- Update Document 00 (Documentation Governance) §15 Quality Checklist to note that `services/auth-svc/DESIGN.md` is a working-design exception (similar to how README.md is the index exception).
- The `DESIGN.md` becomes the historical record. Either retire it (if the design is fully absorbed into Document 21) or keep it as a reference.

## 9. Out of scope for this PR

These are NOT in this PR (they're later work, tracked in the auth-svc epic issue #5):

- OIDC/MFA/SSO/magic-link flows.
- Auth0 tenant integration.
- RBAC at the API layer.
- Cross-workspace membership, invites, SCIM.
- Persistence (Redis 7, Postgres `audit_event`).
- Multi-process / multi-host scaling.
- The FastAPI HTTP layer that wraps the manager.

**Resist the urge to add any of these.** The local subset is small on purpose. Future work expands it.

## 10. One-line summary

Read DESIGN.md → lift the 5-method contract → implement InMemorySessionManager with `threading.Lock` → run pytest until 25 passed → open PR via the Option 3 cycle script. Don't add anything that's not in the test file.
