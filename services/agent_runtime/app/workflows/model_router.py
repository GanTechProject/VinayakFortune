"""Model routing — per-call AD-004 model selection.

Per Architect #6 §9 (Doc 07 §7.2 L162-171, verbatim):
- Default: Anthropic Claude Sonnet 4.5 for routine work
- High-stakes: Opus 4 for board reports
- Fallback: OpenAI GPT-4o for tool failures
- Per-call selection based on rubric_weight, latency_budget, cost_budget,
  provider_health

Q-6.5 (conductor-ratified): rubric_weight >= 0.8 → Opus;
cost_remaining_usd < 0.05 → fast lane; anthropic-down → GPT-4o fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum


class Provider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    INTERNAL = "internal"


@dataclass(frozen=True)
class ModelChoice:
    """The result of a routing decision."""

    provider: Provider
    model_id: str
    max_tokens: int
    temperature: float

    @property
    def is_opus(self) -> bool:
        return self.model_id == "claude-opus-4"

    @property
    def is_fallback(self) -> bool:
        return self.provider == Provider.OPENAI


@dataclass(frozen=True)
class ProviderStatus:
    """30s sliding-window health (Doc 07 §9 L218)."""

    ok: bool
    opus_ok: bool = True
    last_update: datetime = None

    def __post_init__(self) -> None:
        if self.last_update is None:
            object.__setattr__(self, "last_update", datetime.now(tz=timezone.utc))
        # If the provider is down, opus is also down (Doc 07 §9 L218).
        if not self.ok:
            object.__setattr__(self, "opus_ok", False)


class ProviderHealth:
    """30s sliding-window success-rate signal per provider."""

    def __init__(self, threshold: float = 0.95, window_s: int = 30) -> None:
        self.threshold = threshold
        self.window_s = window_s
        self._events: dict[Provider, list[tuple[datetime, bool]]] = {
            p: [] for p in Provider
        }

    def record(self, provider: Provider, success: bool) -> None:
        self._events[provider].append((datetime.now(tz=timezone.utc), success))

    def status(self, provider: Provider) -> ProviderStatus:
        now = datetime.now(tz=timezone.utc)
        cutoff = now - timedelta(seconds=self.window_s)
        events = [s for t, s in self._events[provider] if t >= cutoff]
        if not events:
            return ProviderStatus(ok=True)
        success_rate = sum(events) / len(events)
        ok = success_rate >= self.threshold
        # Opus availability tracks overall: if the provider is down, opus is down.
        return ProviderStatus(ok=ok, opus_ok=ok)


DEFAULT_HEALTH = ProviderHealth()


def route_model(
    *,
    node_name: str,
    rubric_weight: float,
    latency_budget_ms: int,
    cost_remaining_usd: Decimal,
    provider_health: dict[Provider, ProviderStatus] | None = None,
) -> ModelChoice:
    """Per-call routing decision (Doc 07 §7.2 L162-171).

    Q-6.5 thresholds:
    - rubric_weight >= 0.8 AND anthropic.opus_ok → Opus 4
    - latency_budget_ms < 5000 OR cost_remaining_usd < 0.05 → Sonnet 4.5 fast lane
    - anthropic down → GPT-4o fallback
    - default → Sonnet 4.5
    """
    health = provider_health or {p: DEFAULT_HEALTH.status(p) for p in Provider}
    anthropic_status = health.get(Provider.ANTHROPIC) or DEFAULT_HEALTH.status(Provider.ANTHROPIC)
    openai_status = health.get(Provider.OPENAI) or DEFAULT_HEALTH.status(Provider.OPENAI)

    # Fast lane: low latency OR low cost remaining
    if latency_budget_ms < 5000 or cost_remaining_usd < Decimal("0.05"):
        return ModelChoice(
            provider=Provider.ANTHROPIC,
            model_id="claude-sonnet-4.5",
            max_tokens=2048,
            temperature=0.2,
        )

    # High-stakes: rubric_weight >= 0.8 AND anthropic Opus OK
    if rubric_weight >= 0.8 and anthropic_status.ok and anthropic_status.opus_ok:
        return ModelChoice(
            provider=Provider.ANTHROPIC,
            model_id="claude-opus-4",
            max_tokens=4096,
            temperature=0.3,
        )

    # Anthropic down → GPT-4o fallback
    if not anthropic_status.ok:
        if not openai_status.ok:
            raise ProviderUnavailableError("both providers down")
        return ModelChoice(
            provider=Provider.OPENAI,
            model_id="gpt-4o",
            max_tokens=4096,
            temperature=0.3,
        )

    # Default
    return ModelChoice(
        provider=Provider.ANTHROPIC,
        model_id="claude-sonnet-4.5",
        max_tokens=4096,
        temperature=0.3,
    )


class ProviderUnavailableError(Exception):
    """Raised when both providers are down (Doc 08 §8 L160)."""


__all__ = [
    "DEFAULT_HEALTH",
    "ModelChoice",
    "Provider",
    "ProviderHealth",
    "ProviderStatus",
    "ProviderUnavailableError",
    "route_model",
]
