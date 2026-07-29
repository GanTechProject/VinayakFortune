"""Unit tests for Step (Architect #6 §4.4)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from services.agent_runtime.app.contracts.step import (
    CostRecord,
    ErrorRecord,
    Step,
    ToolCallRef,
)


def test_step_carries_cost_record_with_provider_tokens_tool_cost() -> None:
    """Q-6.1: Step carries cost: CostRecord (full provider + tokens + tool cost)."""
    step = Step(
        step_id=uuid4(),
        run_id=uuid4(),
        agent_id="AGT-RSRCH-MARKET",
        node_name="specialist.market",
        started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
        cost=CostRecord(
            provider="anthropic",
            model="claude-sonnet-4.5",
            input_tokens=1000,
            output_tokens=500,
            tool_cost_usd=Decimal("0.02"),
            llm_cost_usd=Decimal("0.06"),
        ),
    )
    assert step.cost.provider == "anthropic"
    assert step.cost.model == "claude-sonnet-4.5"
    assert step.cost.input_tokens == 1000
    assert step.cost.output_tokens == 500
    assert step.cost.total_tokens == 1500
    assert step.cost.total_cost_usd == Decimal("0.08")


def test_step_tool_call_refs() -> None:
    """ToolCallRef mirrors agent_tool_call row (TRD L219)."""
    tool = ToolCallRef(
        tool_id="T-MARKET-DATA-FETCHER",
        invocation_id=uuid4(),
        latency_ms=234,
        cost_usd=Decimal("0.02"),
    )
    step = Step(
        step_id=uuid4(),
        run_id=uuid4(),
        agent_id="AGT-RSRCH-MARKET",
        node_name="specialist.market",
        started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
        tool_calls=[tool],
    )
    assert len(step.tool_calls) == 1
    assert step.tool_calls[0].tool_id == "T-MARKET-DATA-FETCHER"


def test_step_error_record() -> None:
    """Step.error is a structured ErrorRecord (Architect #6 §10)."""
    err = ErrorRecord(
        error_code="BUDGET_EXHAUSTED",
        severity="error",
        retryable=False,
        message="tokens exhausted",
        remediation_hint="reduce specialist fan-out",
    )
    step = Step(
        step_id=uuid4(),
        run_id=uuid4(),
        agent_id="AGT-RSRCH-MARKET",
        node_name="specialist.market",
        started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
        error=err,
    )
    assert step.error is not None
    assert step.error.error_code == "BUDGET_EXHAUSTED"
    assert step.error.severity == "error"
    assert step.error.retryable is False


def test_step_finished_at_defaults_to_none() -> None:
    """finished_at is null until terminal (Architect #6 §4.4)."""
    step = Step(
        step_id=uuid4(),
        run_id=uuid4(),
        agent_id="AGT-RSRCH-MARKET",
        node_name="specialist.market",
        started_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
    )
    assert step.finished_at is None
