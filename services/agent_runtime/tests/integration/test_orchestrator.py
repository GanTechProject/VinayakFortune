"""Orchestrator integration tests (Architect #6 §5 + §13 test_016..test_020)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from services.agent_runtime.app.contracts.budget import (
    Budget,
    RunType,
    budget_for_run_type,
)
from services.agent_runtime.app.contracts.evidence import Evidence
from services.agent_runtime.app.contracts.plan import DiscoveryPlan
from services.agent_runtime.app.contracts.run_state import RunState
from services.agent_runtime.app.contracts.step import CostRecord, Step
from services.agent_runtime.app.workflows.orchestrator import Orchestrator
from services.agent_runtime.app.workflows.specialists import (
    Dimension,
    SpecialistResult,
    default_specialist,
)


def _new_state() -> RunState:
    return RunState(
        workspace_id=uuid4(),
        user_id=uuid4(),
        goal="test",
        plan=DiscoveryPlan(sources=[], queries=["q"], expected_yield=10),
        budget=budget_for_run_type(RunType.VALIDATION_QUICK),
    )


def _evidence() -> Evidence:
    return Evidence(
        claim="claim",
        citations=[],
        freshness="live",
        confidence="high",
        snippet="snippet",
        source_url="https://example.com",
        captured_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
        agent_id="AGT-RSRCH-MARKET",
        step_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_orchestrator_dispatches_all_dimensions() -> None:
    """Per Architect #6 §5: For each dim → Specialist → Verify → Score → Report."""
    state = _new_state()
    dims = [Dimension(name="market", agent_id="AGT-RSRCH-MARKET"), Dimension(name="comp", agent_id="AGT-RSRCH-COMP")]

    async def specialist(state: RunState, dim: Dimension) -> SpecialistResult:
        step = Step(
            step_id=uuid4(),
            run_id=state.run_id,
            agent_id=dim.agent_id,
            node_name=f"specialist.{dim.name}",
            started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
            cost=CostRecord(provider="anthropic", model="claude-sonnet-4.5"),
        )
        return SpecialistResult(
            evidence=[_evidence()],
            tool_calls=1,
            cost=step.cost,
            step=step,
        )

    orch = Orchestrator(specialist_fn=specialist)
    result = await orch.run(state=state, dimensions=dims)
    assert len(state.history) == 2
    assert len(state.evidence) == 2
    assert result.unverified_dimensions == []
    assert result.budget_exhausted is False


@pytest.mark.asyncio
async def test_verifier_2strike_marks_dimension_unverified() -> None:
    """Per Q-6.7: 2 consecutive failures → auto-skip + surface (Doc 15 §7 L94)."""
    state = _new_state()
    dims = [Dimension(name="market", agent_id="AGT-RSRCH-MARKET")]

    async def failing_specialist(state: RunState, dim: Dimension) -> SpecialistResult:
        raise RuntimeError("specialist failure")

    orch = Orchestrator(specialist_fn=failing_specialist)
    result = await orch.run(state=state, dimensions=dims)
    assert "market" in result.unverified_dimensions


@pytest.mark.asyncio
async def test_orchestrator_returns_budget_exhausted_when_over_budget() -> None:
    """Per Architect #6 §10: Cost budget exceeded → Stop run; surface partial result."""
    state = _new_state()
    # Pre-fill history with cost equal to the budget.
    from services.agent_runtime.app.contracts.step import CostRecord, Step

    state.history.append(
        Step(
            step_id=uuid4(),
            run_id=state.run_id,
            agent_id="some-agent",
            node_name="pre",
            started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
            cost=CostRecord(
                provider="anthropic",
                model="claude-sonnet-4.5",
                input_tokens=state.budget.tokens,
                output_tokens=0,
            ),
        )
    )

    dims = [Dimension(name="market", agent_id="AGT-RSRCH-MARKET")]

    async def specialist(state: RunState, dim: Dimension) -> SpecialistResult:
        step = Step(
            step_id=uuid4(),
            run_id=state.run_id,
            agent_id=dim.agent_id,
            node_name=f"specialist.{dim.name}",
            started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
            cost=CostRecord(provider="anthropic", model="claude-sonnet-4.5"),
        )
        return SpecialistResult(evidence=[], tool_calls=0, cost=step.cost, step=step)

    orch = Orchestrator(specialist_fn=specialist)
    result = await orch.run(state=state, dimensions=dims)
    assert result.budget_exhausted is True


@pytest.mark.asyncio
async def test_orchestrator_wall_clock_budget_exceeded() -> None:
    """Bugfix D: _check_budget enforces wall-clock; wall_clock_s=0 fails any run."""
    state = RunState(
        workspace_id=uuid4(),
        user_id=uuid4(),
        goal="test",
        plan=DiscoveryPlan(sources=[], queries=["q"], expected_yield=10),
        budget=Budget(
            tokens=99_999_999,
            wall_clock_s=0,
            tool_calls=9_999_999,
            cost_usd=Decimal("9999"),
        ),
    )
    dims = [Dimension(name="market", agent_id="AGT-RSRCH-MARKET")]

    async def slow_specialist(state: RunState, dim: Dimension) -> SpecialistResult:
        await asyncio.sleep(0.01)
        step = Step(
            step_id=uuid4(),
            run_id=state.run_id,
            agent_id=dim.agent_id,
            node_name=f"specialist.{dim.name}",
            started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
            cost=CostRecord(provider="anthropic", model="claude-sonnet-4.5"),
        )
        return SpecialistResult(evidence=[], tool_calls=0, cost=step.cost, step=step)

    orch = Orchestrator(specialist_fn=slow_specialist)
    result = await orch.run(state=state, dimensions=dims)
    assert result.budget_exhausted is True


@pytest.mark.asyncio
async def test_default_specialist_produces_nonempty_result() -> None:
    """Bugfix A: the fixed default_specialist yields evidence and no unverified dims."""
    state = _new_state()
    dims = [
        Dimension(name="market", agent_id="AGT-RSRCH-MARKET"),
        Dimension(name="comp", agent_id="AGT-RSRCH-COMP"),
    ]
    orch = Orchestrator(specialist_fn=default_specialist)
    result = await orch.run(state=state, dimensions=dims)
    assert result.unverified_dimensions == []
    assert len(state.evidence) == 2
    assert len(state.history) == 2
