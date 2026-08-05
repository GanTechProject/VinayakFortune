"""Step — append-only history entry (Doc 08 §5 L122).

Per Architect #6 §4.4 (operational minimum derived from Doc 08 §5 L128
"append-only and replayable" + Doc 08 §10 L182 "Replay: production
traces can be replayed with new code to compare" + TRD L219
`agent_tool_call` table).

Q-6.1 (conductor-ratified): Step carries `cost: CostRecord` (full
provider + tokens + tool cost) — not a simpler token count.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

Severity = Literal["info", "warning", "error", "fatal"]


class ToolCallRef(BaseModel):
    """Reference to an agent_tool_call row (TRD L219)."""

    tool_id: str  # MCP tool manifest ID
    invocation_id: UUID
    latency_ms: int = Field(ge=0)
    cost_usd: Decimal = Field(ge=Decimal(0))


class CostRecord(BaseModel):
    """Per-step cost record (Doc 07 §8.3).

    Captures the full provider+token+tool cost. Q-6.1: required for
    replay + monthly calibration regression (Architect #6 §13 test_046,
    test_047).
    """

    provider: str = "unknown"  # "anthropic", "openai", "internal"
    model: str = "unknown"  # "claude-sonnet-4.5", "gpt-4o", "llama-3.1-405b"
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    tool_cost_usd: Decimal = Field(default=Decimal(0))
    llm_cost_usd: Decimal = Field(default=Decimal(0))

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def total_cost_usd(self) -> Decimal:
        return self.llm_cost_usd + self.tool_cost_usd


class ErrorRecord(BaseModel):
    """A structured error record (Architect #6 §10)."""

    error_code: str  # BUDGET_EXHAUSTED, PROVIDER_DOWN, etc.
    severity: Severity
    retryable: bool
    message: str  # PII-redacted
    remediation_hint: str | None = None


class Step(BaseModel):
    """An append-only history entry for a run.

    Per Doc 08 §5 L122 (`history: list[Step]`) and Architect #6 §4.4.
    """

    step_id: UUID  # unique per append
    run_id: UUID  # foreign key to RunState.run_id
    agent_id: str  # who performed this step (e.g. "AGT-RSRCH-MARKET")
    node_name: str  # LangGraph node name
    started_at: datetime
    finished_at: datetime | None = None  # null until terminal
    inputs: dict = Field(default_factory=dict)  # PII-redacted at MCP boundary
    outputs: dict = Field(default_factory=dict)  # PII-redacted
    tool_calls: list[ToolCallRef] = Field(default_factory=list)
    cost: CostRecord = Field(default_factory=CostRecord)
    error: ErrorRecord | None = None

    model_config = {"frozen": False}  # mutated only by orchestrator on finish


__all__ = ["CostRecord", "ErrorRecord", "Severity", "Step", "ToolCallRef"]
