"""Unit tests for the Plan union (Q-6.3)."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from services.agent_runtime.app.contracts.plan import (
    DiscoveryPlan,
    Plan,
    ReportPlan,
    ValidationPlan,
)

_plan_adapter = TypeAdapter(Plan)


def test_discovery_plan_validates() -> None:
    p = DiscoveryPlan(sources=["doc1"], queries=["q1"], expected_yield=10)
    assert p.plan_type == "discovery"
    assert p.sources == ["doc1"]
    assert p.queries == ["q1"]
    assert p.expected_yield == 10


def test_validation_plan_validates() -> None:
    p = ValidationPlan(dimensions=["market", "comp"], rubric_version="v1.0")
    assert p.plan_type == "validation"
    assert p.dimensions == ["market", "comp"]
    assert p.rubric_version == "v1.0"
    assert p.min_confidence == 0.7
    assert p.force_deep is False


def test_report_plan_validates() -> None:
    p = ReportPlan(template_id="tpl-board-v1", sections=["summary", "appendix"])
    assert p.plan_type == "report"
    assert p.template_id == "tpl-board-v1"
    assert p.sections == ["summary", "appendix"]
    assert p.include_appendix is True


def test_plan_union_discriminator_discovery() -> None:
    payload = {"plan_type": "discovery", "sources": ["a"], "queries": ["b"], "expected_yield": 5}
    p = _plan_adapter.validate_python(payload)
    assert isinstance(p, DiscoveryPlan)


def test_plan_union_discriminator_validation() -> None:
    payload = {"plan_type": "validation", "dimensions": ["market"], "rubric_version": "v1.0"}
    p = _plan_adapter.validate_python(payload)
    assert isinstance(p, ValidationPlan)


def test_plan_union_discriminator_report() -> None:
    payload = {"plan_type": "report", "template_id": "tpl", "sections": ["a"]}
    p = _plan_adapter.validate_python(payload)
    assert isinstance(p, ReportPlan)


def test_plan_union_unknown_plan_type_rejected() -> None:
    payload = {"plan_type": "unknown_type", "sources": [], "queries": [], "expected_yield": 0}
    with pytest.raises(ValidationError):
        _plan_adapter.validate_python(payload)


def test_plan_union_serializes_plan_type_field() -> None:
    """Each variant surfaces its plan_type field for cross-service typing."""
    p = DiscoveryPlan(sources=[], queries=[], expected_yield=0)
    dumped = p.model_dump()
    assert dumped["plan_type"] == "discovery"
