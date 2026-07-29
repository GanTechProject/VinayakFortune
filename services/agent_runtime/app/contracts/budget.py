"""Budget — per-orchestration cost/time/token cap.

Per Architect #6 §4.2 (Doc 08 §9 L165-173, verbatim).

Run-type → budget table (Doc 08 §9 L165-173):
| Run type              | Token budget | Wall-clock budget |
|-----------------------|--------------|-------------------|
| Discovery (Standard)  | 250k         | 90s               |
| Validation (Quick)    | 50k          | 30s               |
| Validation (Standard) | 400k         | 8 min             |
| Validation (Deep)     | 1.2M         | 30 min            |
| One-page brief        | 80k          | 60s               |
| Full report           | 1M           | 8 min             |
| Comparison report     | 600k         | 3 min             |

Enforcement: the orchestrator checks Budget BEFORE every node invocation.
Over-budget calls raise BudgetExceededError and trigger the degrade strategy
(Doc 08 §9 L175). The MCP gateway independently enforces cost_usd and
tool_calls (Doc 12 §8 L98-100).
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class RunType(str, Enum):
    """Run-type enum (per Doc 08 §9 L165-173 table)."""

    DISCOVERY_STANDARD = "discovery_standard"
    VALIDATION_QUICK = "validation_quick"
    VALIDATION_STANDARD = "validation_standard"
    VALIDATION_DEEP = "validation_deep"
    ONE_PAGE_BRIEF = "one_page_brief"
    FULL_REPORT = "full_report"
    COMPARISON_REPORT = "comparison_report"


# Doc 08 §9 L165-173 table (verbatim).
_BUDGET_TABLE: dict[RunType, tuple[int, int, int, Decimal]] = {
    RunType.DISCOVERY_STANDARD: (250_000, 90, 50, Decimal("2.50")),
    RunType.VALIDATION_QUICK: (50_000, 30, 20, Decimal("0.50")),
    RunType.VALIDATION_STANDARD: (400_000, 480, 100, Decimal("4.00")),
    RunType.VALIDATION_DEEP: (1_200_000, 1_800, 200, Decimal("12.00")),
    RunType.ONE_PAGE_BRIEF: (80_000, 60, 30, Decimal("0.80")),
    RunType.FULL_REPORT: (1_000_000, 480, 120, Decimal("10.00")),
    RunType.COMPARISON_REPORT: (600_000, 180, 80, Decimal("6.00")),
}


def budget_for_run_type(run_type: RunType) -> Budget:
    """Return the canonical Budget for the given run type.

    Per Doc 08 §9 L165-173 — the orchestrator loads the budget from this
    table at run-start; never inferred from defaults.
    """
    tokens, wall_clock_s, tool_calls, cost_usd = _BUDGET_TABLE[run_type]
    return Budget(
        tokens=tokens,
        wall_clock_s=wall_clock_s,
        tool_calls=tool_calls,
        cost_usd=cost_usd,
    )


class Budget(BaseModel):
    """Per-orchestration cost/time/token cap (Doc 08 §9 L165-173)."""

    tokens: int = Field(ge=0)  # total token cap (input + output combined)
    wall_clock_s: int = Field(ge=0)  # wall-clock cap, seconds
    tool_calls: int = Field(ge=0)  # MCP-call cap (cross-workspace enforced)
    cost_usd: Decimal  # cost cap, USD; enforced by MCP gateway (Doc 12 §8)

    def has_tokens_remaining(self, used: int) -> bool:
        return used < self.tokens

    def has_wall_clock_remaining(self, used_s: int) -> bool:
        return used_s < self.wall_clock_s

    def has_tool_calls_remaining(self, used: int) -> bool:
        return used < self.tool_calls

    def has_cost_remaining(self, used_usd: Decimal) -> bool:
        return used_usd < self.cost_usd


class BudgetExceededError(Exception):
    """Raised when a pre-node budget check fails (Doc 08 §9 L175)."""

    def __init__(self, dimension: str, used: int | Decimal, cap: int | Decimal) -> None:
        self.dimension = dimension
        self.used = used
        self.cap = cap
        super().__init__(
            f"budget_exceeded: {dimension} used={used} cap={cap}"
        )


__all__ = ["Budget", "BudgetExceededError", "RunType", "budget_for_run_type"]
