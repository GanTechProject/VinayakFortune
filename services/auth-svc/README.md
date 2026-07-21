# auth-svc

Auth service for the VentureMiner AI platform. See [DESIGN.md](DESIGN.md) for the design rationale, the local-subset scope, and the RED test spec that the in-memory `SessionManager` must satisfy.

## What this is

The local subset of the auth-svc epic (issue #5). It contains:

- `app/session_manager.py` — the `SessionManager` abstract base class (the contract every backend must satisfy) and the `Session` Pydantic model. The `InMemorySessionManager` concrete class is added by the implementer to make the RED tests in `test_session_manager.py` pass GREEN.
- `app/test_session_manager.py` — the RED test spec, lifted from DESIGN.md §10.
- `pyproject.toml`, `requirements.txt`, `requirements-dev.txt` — the Python package metadata, matching the `services/hello-world/` convention.
- `Dockerfile` — placeholder for the FastAPI service that wraps the manager.

## What this is NOT

The full auth-svc epic has 15 acceptance criteria (issue #5). The local subset covers AC-2.4 (TTL contract) and AC-2.6 (audit-emission contract) at the *interface* level — the in-memory backend satisfies them under test, but the production deploys to Redis 7 (Document 02 §5.5) and Postgres `audit_event` (Document 21 §14). See DESIGN.md §2 for the full out-of-scope list.

## Local dev

```bash
cd services/auth-svc
python -m venv .venv
.venv/bin/activate          # or .venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
pytest                      # RED — InMemorySessionManager not yet implemented
```

## Layout

```
services/auth-svc/
├── DESIGN.md                  # the design (working doc, not part of the canonical 38-doc suite)
├── README.md                  # this file
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── .dockerignore
└── app/
    ├── __init__.py
    ├── session_manager.py     # the ABC + the (future) InMemorySessionManager
    └── test_session_manager.py  # the RED test spec
```

## Status

- Branch: `wip/auth-svc-session-manager` (working branch, not a PR).
- Tests: RED by construction (imports `InMemorySessionManager` which doesn't exist yet).
- Next: implementer adds `InMemorySessionManager` to `app/session_manager.py`, runs pytest until GREEN, then opens a PR.
