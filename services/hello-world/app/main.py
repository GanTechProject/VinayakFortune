"""hello-world service.

The minimum service for AC-1.1: builds, lints, tests, and runs in Docker.
Three endpoints: `/` (info), `/healthz` (REQ-PLAT-0010), `/readyz` (REQ-PLAT-0010).
"""
from fastapi import FastAPI

app = FastAPI(
    title="hello-world",
    version="0.1.0",
    description="Sample service for the VentureMiner AI monorepo (AC-1.1).",
)


@app.get("/")
def root() -> dict:
    """Service info — used by the smoke test to confirm the deploy landed."""
    return {
        "message": "hello from ventureminer-ai",
        "service": "hello-world",
        "version": "0.1.0",
    }


@app.get("/healthz")
def healthz() -> dict:
    """Liveness probe (REQ-PLAT-0010). Always 200 if the process is up."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict:
    """Readiness probe (REQ-PLAT-0010). 200 if the service can serve traffic."""
    return {"ready": True}
