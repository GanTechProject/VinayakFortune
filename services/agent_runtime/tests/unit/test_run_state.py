"""Unit tests for RunState (Architect #6 §4.3).

Per Architect #6 §13 test_001..test_006 (state-management subset).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.agent_runtime.app.contracts.budget import RunType, budget_for_run_type
from services.agent_runtime.app.contracts.evidence import Evidence
from services.agent_runtime.app.contracts.plan import DiscoveryPlan
from services.agent_runtime.app.contracts.run_state import RunState
from services.agent_runtime.app.contracts.step import CostRecord, Step


def _new_state() -> RunState:
    return RunState(
        workspace_id=uuid4(),
        user_id=uuid4(),
        goal="test",
        plan=DiscoveryPlan(sources=[], queries=["q"], expected_yield=10),
        budget=budget_for_run_type(RunType.VALIDATION_QUICK),
    )


def _new_evidence() -> Evidence:
    return Evidence(
        claim="claim",
        citations=[],
        freshness="live",
        confidence="high",
        snippet="snippet",
        source_url="https://example.com",
        captured_at=__import__("datetime").datetime(2026, 7, 28, tzinfo=__import__("datetime").timezone.utc),
        agent_id="AGT-RSRCH-MARKET",
        step_id=uuid4(),
    )


def _new_step(state: RunState) -> Step:
    return Step(
        step_id=uuid4(),
        run_id=state.run_id,
        agent_id="AGT-RSRCH-MARKET",
        node_name="specialist.market",
        started_at=__import__("datetime").datetime(2026, 7, 28, tzinfo=__import__("datetime").timezone.utc),
        cost=CostRecord(provider="anthropic", model="claude-sonnet-4.5"),
    )


@pytest.mark.asyncio
async def test_run_state_initializes_with_budget_for_run_type() -> None:
    """Per Doc 08 §9 L165-173: budget is loaded from the run-type table."""
    s = _new_state()
    assert s.budget.tokens == 50_000  # Validation Quick
    assert s.evidence == []
    assert s.history == []
    assert s.budget.cost_usd == Decimal("0.50")


@pytest.mark.asyncio
async def test_run_state_evidence_is_append_only_via_method() -> None:
    """Per Doc 08 §5 L126: evidence is the only authoritative store; specialists append."""
    s = _new_state()
    e = _new_evidence()
    await s.add_evidence(e)
    assert len(s.evidence) == 1
    assert s.evidence[0] == e


@pytest.mark.asyncio
async def test_run_state_history_is_append_only_via_method() -> None:
    """Per Doc 08 §5 L128: history is append-only and replayable."""
    s = _new_state()
    step = _new_step(s)
    await s.append_step(step)
    assert len(s.history) == 1
    assert s.history[0] == step


@pytest.mark.asyncio
async def test_run_state_scratchpad_is_ephemeral() -> None:
    """Per Doc 08 §5 L127: scratchpad is ephemeral; not persisted."""
    s = _new_state()
    assert s.scratchpad == {}


@pytest.mark.asyncio
async def test_run_state_outputs_write_only_at_terminal() -> None:
    """Per Architect #6 §6: outputs is written once at the terminal node."""
    s = _new_state()
    await s.write_output("report", {"sections": ["market", "comp"]})
    assert s.outputs["report"] == {"sections": ["market", "comp"]}


@pytest.mark.asyncio
async def test_run_state_concurrent_appends_are_serialized() -> None:
    """Per Architect #6 §6: per-run asyncio lock serializes evidence/appends."""
    import asyncio
    s = _new_state()

    async def add_ten() -> None:
        for _ in range(10):
            await s.add_evidence(_new_evidence())

    await asyncio.gather(*(add_ten() for _ in range(5)))
    assert len(s.evidence) == 50


@pytest.mark.asyncio
async def test_run_state_fresh_specialist_scratchpad_is_empty() -> None:
    """Per Q-6.4: each specialist gets a fresh scratchpad (not shared)."""
    s = _new_state()
    sp = s.fresh_specialist_scratchpad()
    assert sp == {}
    # Mutating the fresh scratchpad does NOT mutate the RunState's.
    sp["x"] = 1
    assert s.scratchpad == {}


@pytest.mark.asyncio
async def test_run_state_merge_specialist_scratchpad() -> None:
    """Per Q-6.4: the specialist writes back its deltas to the RunState scratchpad."""
    s = _new_state()
    sp = s.fresh_specialist_scratchpad()
    sp["market_size"] = 1_000_000_000
    s.merge_specialist_scratchpad(sp)
    assert s.scratchpad["market_size"] == 1_000_000_000
