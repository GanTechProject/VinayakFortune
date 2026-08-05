"""Unit tests for the default specialist (Bugfix A)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from services.agent_runtime.app.contracts.budget import RunType, budget_for_run_type
from services.agent_runtime.app.contracts.plan import DiscoveryPlan
from services.agent_runtime.app.contracts.run_state import RunState
from services.agent_runtime.app.contracts.step import Step
from services.agent_runtime.app.workflows.specialists import (
    Dimension,
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


@pytest.mark.asyncio
async def test_default_specialist_returns_valid_step() -> None:
    """Bugfix A: default_specialist must not raise; step.started_at is a datetime."""
    state = _new_state()
    dim = Dimension(name="market", agent_id="AGT-RSRCH-MARKET")
    result = await default_specialist(state, dim)
    assert result.step.started_at is not None
    assert isinstance(result.step.started_at, datetime)
    assert result.step.run_id == state.run_id
    assert result.step.node_name == "specialist.market"


@pytest.mark.asyncio
async def test_default_specialist_with_existing_history() -> None:
    """Bugfix A: a prior step with finished_at=None must not break the run."""
    state = _new_state()
    prior = Step(
        step_id=uuid4(),
        run_id=state.run_id,
        agent_id="AGT-RSRCH-MARKET",
        node_name="specialist.prev",
        started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
        finished_at=None,
    )
    await state.append_step(prior)
    dim = Dimension(name="market", agent_id="AGT-RSRCH-MARKET")
    result = await default_specialist(state, dim)
    assert result.step.started_at is not None
    assert isinstance(result.step.started_at, datetime)
    assert result.step.node_name == "specialist.market"
