# hello-world

Sample service for the VentureMiner AI monorepo. Closes AC-1.1 of [issue #4](../../issues/4).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service info (used by smoke tests) |
| GET | `/healthz` | Liveness probe (REQ-PLAT-0010) |
| GET | `/readyz` | Readiness probe (REQ-PLAT-0010) |

## Local dev

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Test (RED-first)
pytest app/

# Lint
ruff check app/

# Run
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
docker build -t hello-world .
docker run --rm -p 8000:8000 hello-world
curl http://localhost:8000/healthz  # {"status":"ok"}
```

## Source documents

- Document 02 (TRD) §2.1 — Python 3.12 + FastAPI baseline (we use 3.11 for the sample; services move to 3.12 once the monorepo template is in).
- Document 08-Engineering/26 (Coding Standards) — service structure.
- Document 00-Governance §3.3 — required sections (Goal, Source documents, etc.) live in the issue, not the README.
