"""Model routing tests (Architect #6 §13 test_027..test_031)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from services.agent_runtime.app.workflows.model_router import (
    DEFAULT_HEALTH,
    Provider,
    ProviderHealth,
    ProviderStatus,
    ProviderUnavailableError,
    route_model,
)


@pytest.fixture
def health():
    return ProviderHealth()


def test_routing_rubric_weight_0_8_routes_to_opus(health: ProviderHealth) -> None:
    """Per Q-6.5: rubric_weight >= 0.8 AND anthropic.opus_ok → Opus 4."""
    choice = route_model(
        node_name="synthesize",
        rubric_weight=0.85,
        latency_budget_ms=30_000,
        cost_remaining_usd=Decimal("1.00"),
    )
    assert choice.is_opus is True
    assert choice.provider == Provider.ANTHROPIC


def test_routing_low_latency_budget_routes_to_sonnet_fast_lane() -> None:
    """Per Q-6.5: latency_budget_ms < 5000 → Sonnet 4.5 fast lane."""
    choice = route_model(
        node_name="retrieve",
        rubric_weight=0.5,
        latency_budget_ms=2000,
        cost_remaining_usd=Decimal("1.00"),
    )
    assert choice.model_id == "claude-sonnet-4.5"
    assert choice.max_tokens == 2048


def test_routing_low_cost_remaining_routes_to_sonnet_fast_lane() -> None:
    """Per Q-6.5: cost_remaining_usd < 0.05 → Sonnet 4.5 fast lane."""
    choice = route_model(
        node_name="retrieve",
        rubric_weight=0.5,
        latency_budget_ms=30_000,
        cost_remaining_usd=Decimal("0.01"),
    )
    assert choice.model_id == "claude-sonnet-4.5"
    assert choice.max_tokens == 2048


def test_routing_anthropic_down_routes_to_gpt4o_fallback() -> None:
    """Per Q-6.5: anthropic down → GPT-4o fallback."""
    health = {
        Provider.ANTHROPIC: ProviderStatus(ok=False, opus_ok=False),
        Provider.OPENAI: ProviderStatus(ok=True),
    }
    choice = route_model(
        node_name="synthesize",
        rubric_weight=0.5,
        latency_budget_ms=30_000,
        cost_remaining_usd=Decimal("1.00"),
        provider_health=health,
    )
    assert choice.is_fallback is True
    assert choice.model_id == "gpt-4o"


def test_routing_both_providers_down_raises_provider_unavailable() -> None:
    """Per Doc 08 §8 L160: two providers down → abort."""
    health = {
        Provider.ANTHROPIC: ProviderStatus(ok=False),
        Provider.OPENAI: ProviderStatus(ok=False),
    }
    with pytest.raises(ProviderUnavailableError):
        route_model(
            node_name="synthesize",
            rubric_weight=0.5,
            latency_budget_ms=30_000,
            cost_remaining_usd=Decimal("1.00"),
            provider_health=health,
        )


def test_provider_health_30s_sliding_window_below_95_pct_marks_down() -> None:
    """Per Doc 07 §9 L218: below 95% success over 30s → ok=False."""
    health = ProviderHealth()
    for _ in range(100):
        health.record(Provider.ANTHROPIC, False)
    status = health.status(Provider.ANTHROPIC)
    assert status.ok is False
    assert status.opus_ok is False


def test_provider_health_window_above_95_pct_marks_ok() -> None:
    health = ProviderHealth()
    for _ in range(95):
        health.record(Provider.ANTHROPIC, True)
    for _ in range(5):
        health.record(Provider.ANTHROPIC, False)
    status = health.status(Provider.ANTHROPIC)
    assert status.ok is True


def test_default_health_is_healthy() -> None:
    """A provider with no recorded events is considered healthy."""
    status = DEFAULT_HEALTH.status(Provider.ANTHROPIC)
    assert status.ok is True
    assert status.opus_ok is True
