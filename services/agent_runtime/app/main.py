"""Agent-runtime FastAPI bootstrap (Doc 02 §4.1 L177).

Per Architect #6 §3:
- FastAPI for the REST surface
- LangGraph 0.2.x as the orchestrator runtime
- Postgres 16 via the `agent` schema (TRD Doc 02 §5.2 L219)
- NATS JetStream for cross-process events (Doc 08 §6 L131-141)
- Temporal worker for crash-safe orchestration (Doc 02 §4.1 L187)
"""

from __future__ import annotations

from fastapi import FastAPI

from services.agent_runtime.app.agents.manifest import ALL_AGENT_IDS
from services.agent_runtime.app.api.events import router as runs_router


def create_app() -> FastAPI:
    """Build the FastAPI app."""
    app = FastAPI(
        title="agent-runtime",
        version="0.1.0",
        description="AI-plane orchestrator (Architect #6 BAND-3-DESIGN).",
    )
    app.include_router(runs_router)

    @app.get("/")
    async def root() -> dict[str, object]:
        return {
            "service": "agent-runtime",
            "version": "0.1.0",
            "agents": list(ALL_AGENT_IDS),
        }

    return app


app = create_app()


__all__ = ["app", "create_app"]
