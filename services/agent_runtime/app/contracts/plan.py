"""Plan — per-run-type union (Q-6.3).

Per Architect #6 §4.6 and DRIFT-6.3: a generic Plan is a per-run-type
union. Doc 08 §5 L118 says `plan: Plan`; Doc 09 §4 L88 calls the inline
form `DiscoveryPlan`. The conductor ratifies the per-run-type union
pattern via Q-6.3.

Discrimination via RunState.plan_type: Literal[...]; Pydantic uses the
`plan_type` discriminator to select the correct variant at validation
time.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator, Field, Tag


class DiscoveryPlan(BaseModel):
    """Per Architect #6 §4.6 (Doc 09 §4 L88, verbatim)."""

    plan_type: Literal["discovery"] = "discovery"
    sources: list[str]  # source IDs to query
    queries: list[str]  # search queries
    expected_yield: int  # planner's estimate of hits


class ValidationPlan(BaseModel):
    """Per-run-type variant for validation runs."""

    plan_type: Literal["validation"] = "validation"
    dimensions: list[str]  # dimensions to validate (e.g. market, demand, comp)
    rubric_version: str  # which scoring rubric to apply
    min_confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    force_deep: bool = False  # if true, run all specialists in parallel


class ReportPlan(BaseModel):
    """Per-run-type variant for report assembly."""

    plan_type: Literal["report"] = "report"
    template_id: str  # reporting-svc template to render
    sections: list[str]  # sections to include
    include_appendix: bool = True


def _plan_discriminator(v: object) -> str:
    """Pydantic discriminator for the Plan union."""
    if isinstance(v, dict):
        return v.get("plan_type", "discovery")
    return getattr(v, "plan_type", "discovery")


Plan = Annotated[
    Annotated[DiscoveryPlan, Tag("discovery")] | Annotated[ValidationPlan, Tag("validation")] | Annotated[ReportPlan, Tag("report")],
    Discriminator(_plan_discriminator),
]


__all__ = ["DiscoveryPlan", "Plan", "ReportPlan", "ValidationPlan"]
