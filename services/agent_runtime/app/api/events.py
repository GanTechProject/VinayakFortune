"""Public REST API — FastAPI (Doc 02 §4.1 L177).

Per Architect #6 §7:
- POST /runs           — start a new run
- GET  /runs/{id}      — fetch the current RunState
- DELETE /runs/{id}    — cancel a run
- GET  /healthz        — liveness probe
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from services.agent_runtime.app.contracts.budget import RunType, budget_for_run_type
from services.agent_runtime.app.contracts.plan import DiscoveryPlan
from services.agent_runtime.app.contracts.run_state import RunState

router = APIRouter()


# In-process run store (v1 stub; production uses Postgres + Temporal).
_RUN_STORE: dict[UUID, RunState] = {}


class RunRequest(BaseModel):
    """The inbound RunRequest (Doc 09 §3)."""

    goal: str
    workspace_id: UUID
    user_id: UUID
    run_type: RunType = RunType.VALIDATION_STANDARD
    plan: DiscoveryPlan | None = None


class RunResponse(BaseModel):
    """The outbound RunResponse."""

    run_id: UUID
    status: str
    created_at: datetime

    @classmethod
    def from_state(cls, state: RunState) -> RunResponse:
        return cls(
            run_id=state.run_id,
            status="running",
            created_at=datetime.now(tz=timezone.utc),
        )


@router.post("/runs", status_code=status.HTTP_201_CREATED, response_model=RunResponse)
async def create_run(req: RunRequest) -> RunResponse:
    """Start a new agent run (Doc 09 §3)."""
    if req.plan is None:
        req.plan = DiscoveryPlan(sources=[], queries=[req.goal], expected_yield=10)
    state = RunState(
        run_id=uuid4(),
        workspace_id=req.workspace_id,
        user_id=req.user_id,
        goal=req.goal,
        plan=req.plan,
        budget=budget_for_run_type(req.run_type),
    )
    _RUN_STORE[state.run_id] = state
    return RunResponse.from_state(state)


@router.get("/runs/{run_id}", response_model=RunState)
async def get_run(run_id: UUID) -> RunState:
    """Fetch the current RunState."""
    state = _RUN_STORE.get(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return state


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def cancel_run(run_id: UUID) -> Response:
    """Cancel a running run."""
    state = _RUN_STORE.get(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    # The orchestrator picks up the cancel on the next node boundary.
    _RUN_STORE.pop(run_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe (Doc 08 §6 L139)."""
    return {"status": "ok", "service": "agent-runtime"}


__all__ = ["RunRequest", "RunResponse", "router"]
