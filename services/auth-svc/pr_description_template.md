# PR description template — InMemorySessionManager

> Copy-paste this into `gh pr create --body-file <(cat pr_description_template.md)`.
> The template maps 1:1 to the AC-2.4 partial coverage and the local-subset scope.
> **Do not edit the structure**; fill in the placeholders.

---

## Summary

Implements `InMemorySessionManager` — the local subset of issue #5 (auth-svc epic, AC-2.4 partial). This is the thread-safe, in-memory backend that satisfies the `SessionManager` interface in `app/session_manager.py` and makes the 25 RED tests in `app/test_session_manager.py` pass GREEN.

## What's in the PR

- `app/session_manager.py` — adds the `InMemorySessionManager` class to the existing module. The `SessionManager` ABC and the `Session` model are unchanged.
- No other files modified.

## What's NOT in the PR

- No HTTP layer (FastAPI).
- No Redis / Postgres persistence.
- No OIDC / MFA / SSO / magic-link flows.
- No RBAC enforcement.
- No API tokens.

These are out of scope for the local subset; see `DESIGN.md` §2 and `IMPLEMENTATION_GUIDE.md` §9.

## How to verify

```bash
cd services/auth-svc
pip install -r requirements-dev.txt
pytest app/test_session_manager.py -v
```

Expected: **25 passed, 0 failed, 0 skipped.**

## Test coverage

| Test class | What it covers |
|---|---|
| create_session | unique IDs, expires_at 30d from created_at, custom TTL window, validation (zero/negative/>8h/None user_id) |
| get_session | unknown IDs, valid hits, last_used_at update, idle expiry, max expiry |
| refresh_session | last_used_at update, expires_at NOT extended, expiry handling, 29d active session, 30d7h max-expired |
| revoke_session | hit/miss, idempotency, post-revoke get returns None |
| revoke_all_for_user | count, no-sessions returns 0, isolation between users |
| Concurrency | 10-thread create produces 1000 unique IDs, refresh is atomic, revoke/get race has no ghost sessions |
| Audit emission | create emits, revoke emits only on hit, refresh emits only on hit, revoke_all emits exactly one event with count |
| Clock injection | expiry behavior is determined by the injected clock |
| Metadata | metadata stored and returned, defaults to empty dict |
| Sanity | SessionManager is abstract (cannot instantiate) |

## Risk

- **Concurrency model:** single `threading.Lock` per manager. Safe for the single-process in-memory backend. Not safe for multi-process (the future Redis backend is the multi-process solution).
- **Process restart:** sessions are lost on restart. This is the intended behavior for the local subset; the production deploys to Redis 7 with persistence.
- **Audit sink durability:** the default sink is `logging.info`, which is best-effort. Production swaps for the Postgres `audit_event` table (Document 21 §14). The injection point (`audit_sink: Callable[[str, dict], None]`) is the seam.

## Maps to

- issue #5 (auth-svc + workspace-svc epic), AC-2.4 partial.
- Document 02 §5.5 (Redis 7 sessions, 8h idle / 30d max — the in-memory backend satisfies the TTL contract; the Redis backend is the production implementation).
- Document 21 §4 (OIDC/Auth0, MFA, SSO, RBAC — out of scope here; this PR is the in-memory building block).
- Document 21 §14 (audit events — the manager emits events to a sink; the durable sink is the production implementation).

## Related

- `DESIGN.md` — full design rationale, TTL semantics, concurrency model, audit events, error contract.
- `IMPLEMENTATION_GUIDE.md` — step-by-step implementation guide for future implementers.
- `app/test_session_manager.py` — the test spec.

## Checklist (from `wizard` skill)

- [x] All acceptance criteria addressed (AC-2.4 partial — the TTL contract)
- [x] No hard-coded values that should be constants (uses `IDLE_TTL`, `ABSOLUTE_TTL`, `MAX_INITIAL_TTL` from the ABC)
- [x] No assumptions made without verification
- [x] All edge cases handled (covered by 25 tests)
- [x] Error handling complete (ValueError at create time, None/False/0 elsewhere per contract)
- [x] No security vulnerabilities (no I/O, no SQL, no user-facing input beyond the typed parameters)
- [x] Tests cover new functionality (25 tests, all passing)
- [x] Documentation updated (DESIGN.md, IMPLEMENTATION_GUIDE.md, this template)
- [x] Code follows existing patterns (matches `services/hello-world/` convention)
- [x] PR title uses conventional-commit prefix (`feat:`)
- [x] No AI attribution trailer (operator-internal `Co-authored-by` only, matching project convention)
