"""Unit tests for the Budget contract (Architect #6 §4.2).

Per Architect #6 §13 test_001..test_010 (state-management subset):
- test_008: budget_tokens_enforced_pre_node
- test_009: budget_wall_clock_enforced_pre_node
- test_010: budget_cost_usd_enforced_via_mcp_gateway
"""

from __future__ import annotations

from decimal import Decimal

from services.agent_runtime.app.contracts.budget import (
    Budget,
    BudgetExceededError,
    RunType,
    budget_for_run_type,
)


def test_budget_for_run_type_discovery_standard() -> None:
    """Doc 08 §9 L165-173: Discovery Standard is 250k tokens / 90s."""
    b = budget_for_run_type(RunType.DISCOVERY_STANDARD)
    assert b.tokens == 250_000
    assert b.wall_clock_s == 90


def test_budget_for_run_type_validation_quick() -> None:
    """Doc 08 §9 L165-173: Validation Quick is 50k tokens / 30s."""
    b = budget_for_run_type(RunType.VALIDATION_QUICK)
    assert b.tokens == 50_000
    assert b.wall_clock_s == 30


def test_budget_for_run_type_validation_deep() -> None:
    """Doc 08 §9 L165-173: Validation Deep is 1.2M tokens / 30 min."""
    b = budget_for_run_type(RunType.VALIDATION_DEEP)
    assert b.tokens == 1_200_000
    assert b.wall_clock_s == 30 * 60


def test_budget_for_run_type_full_report() -> None:
    """Doc 08 §9 L165-173: Full report is 1M tokens / 8 min."""
    b = budget_for_run_type(RunType.FULL_REPORT)
    assert b.tokens == 1_000_000
    assert b.wall_clock_s == 8 * 60


def test_budget_has_tokens_remaining() -> None:
    b = Budget(tokens=1000, wall_clock_s=60, tool_calls=10, cost_usd=Decimal("1.00"))
    assert b.has_tokens_remaining(0) is True
    assert b.has_tokens_remaining(999) is True
    assert b.has_tokens_remaining(1000) is False


def test_budget_has_wall_clock_remaining() -> None:
    b = Budget(tokens=1000, wall_clock_s=60, tool_calls=10, cost_usd=Decimal("1.00"))
    assert b.has_wall_clock_remaining(0) is True
    assert b.has_wall_clock_remaining(59) is True
    assert b.has_wall_clock_remaining(60) is False


def test_budget_has_tool_calls_remaining() -> None:
    b = Budget(tokens=1000, wall_clock_s=60, tool_calls=10, cost_usd=Decimal("1.00"))
    assert b.has_tool_calls_remaining(0) is True
    assert b.has_tool_calls_remaining(9) is True
    assert b.has_tool_calls_remaining(10) is False


def test_budget_has_cost_remaining() -> None:
    b = Budget(tokens=1000, wall_clock_s=60, tool_calls=10, cost_usd=Decimal("1.00"))
    assert b.has_cost_remaining(Decimal("0.00")) is True
    assert b.has_cost_remaining(Decimal("0.99")) is True
    assert b.has_cost_remaining(Decimal("1.00")) is False


def test_budget_exceeded_error_carries_dimension() -> None:
    err = BudgetExceededError("tokens", 1000, 1000)
    assert err.dimension == "tokens"
    assert err.used == 1000
    assert err.cap == 1000
    assert "budget_exceeded" in str(err)
    assert "tokens" in str(err)
