"""Specialist sub-graph: plan → retrieve → fetch → synthesize → self-check.

Per Architect #6 §5 (Doc 08 §4.1 L99, verbatim):
    plan → retrieve (RAG) → fetch (plugin) → synthesize → self-check

The specialist is a LangGraph sub-graph. Each specialist gets a fresh
scratchpad (Q-6.4). The orchestrator (specialists.py-level) is the
top-level discovery → validation → scoring → report graph.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import uuid4

from services.agent_runtime.app.contracts.evidence import Evidence
from services.agent_runtime.app.contracts.run_state import RunState
from services.agent_runtime.app.contracts.step import CostRecord, Step


@dataclass
class Dimension:
    """One dimension of the run (e.g. market, demand, comp)."""

    name: str
    agent_id: str


@dataclass
class SpecialistResult:
    """The result of a specialist sub-graph execution."""

    evidence: list[Evidence]
    tool_calls: int
    cost: CostRecord
    step: Step


SpecialistFn = Callable[[RunState, Dimension], Awaitable[SpecialistResult]]


async def default_specialist(
    state: RunState, dim: Dimension
) -> SpecialistResult:
    """The default specialist stub.

    Returns a single evidence row and a CostRecord. The LangGraph
    subgraph wires the actual plan → retrieve → fetch → synthesize →
    self-check pipeline; this stub is the deterministic phase-1
    implementation.
    """
    started_at = state.history[-1].finished_at if state.history else None
    step = Step(
        step_id=uuid4(),
        run_id=state.run_id,
        agent_id=dim.agent_id,
        node_name=f"specialist.{dim.name}",
        started_at=started_at,  # type: ignore[arg-type]
        finished_at=None,
        inputs={"dimension": dim.name},
        outputs={"evidence_count": 0},
        cost=CostRecord(
            provider="anthropic",
            model="claude-sonnet-4.5",
            input_tokens=0,
            output_tokens=0,
        ),
    )
    return SpecialistResult(
        evidence=[],
        tool_calls=0,
        cost=step.cost,
        step=step,
    )


__all__ = ["Dimension", "SpecialistFn", "SpecialistResult", "default_specialist"]
