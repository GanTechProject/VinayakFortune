"""MCP gateway policy — per-workspace allow/deny + per-call checks.

Per Architect #6 §8 (Doc 12 §6 L86-94 + §7 L90-93 + §8 L97-100).

For every call the gateway verifies:
1. Authn: agent's identity (user/workspace token); server identity (mTLS).
2. Authz: does this user/workspace have permission for this tool?
3. Per-tool allow/deny per workspace.
4. Per-resource scope (e.g. opportunity:read).
5. Per-call policy (e.g. no PII to external APIs).
6. Rate limit (per tool, per workspace, per run).
7. Cost budget (per workspace, per run; gates against RunState.budget.cost_usd).

A failed check returns 429 or 429 + retry_after (Doc 12 §8 L100).
"""

from __future__ import annotations

import re
from typing import Protocol

from services.agent_runtime.app.contracts.tool_manifest import ToolManifest


class PolicyViolation(Exception):
    """Raised when a per-call policy check fails (Doc 12 §6-§8)."""

    def __init__(self, code: str, message: str, retry_after_s: int | None = None) -> None:
        self.code = code
        self.message = message
        self.retry_after_s = retry_after_s
        super().__init__(message)


# Naive PII regexes (the production implementation calls a PII detector
# service; the regex is a defensive in-process filter).
_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    re.compile(r"\b\d{16}\b"),  # credit card (no separators)
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),  # email
]


def detect_pii(text: str) -> bool:
    """Return True if the text contains a PII pattern.

    Per Doc 12 §7 L91-95: PII in input to an external API is rejected.
    """
    return any(p.search(text) for p in _PII_PATTERNS)


class ToolRegistry(Protocol):
    """Minimal interface for the manifest registry the gateway looks up.

    The production implementation pulls from plugin-svc.
    """

    def get(self, tool_id: str) -> ToolManifest | None: ...


class RateLimiter(Protocol):
    """Per-tool, per-workspace, per-run rate limiter.

    Returns True if the call is allowed; False if rate-limited.
    """

    def allow(self, tool_id: str, workspace_id: str, run_id: str) -> bool: ...


class CostGate(Protocol):
    """Per-workspace, per-run cost budget gate.

    Returns True if the call is allowed (cost_usd is within budget).
    """

    def allow(self, workspace_id: str, run_id: str, cost_usd: float) -> bool: ...


class WorkspacePolicy(Protocol):
    """Per-workspace allow/deny on a tool."""

    def is_allowed(self, tool_id: str, workspace_id: str) -> bool: ...


class AllowAllPolicy:
    """Default policy: allow every tool for every workspace."""

    def is_allowed(self, tool_id: str, workspace_id: str) -> bool:
        return True


class NoOpRateLimiter:
    """Default rate limiter: never rate-limits."""

    def allow(self, tool_id: str, workspace_id: str, run_id: str) -> bool:
        return True


class NoOpCostGate:
    """Default cost gate: never blocks."""

    def allow(self, workspace_id: str, run_id: str, cost_usd: float) -> bool:
        return True


__all__ = [
    "AllowAllPolicy",
    "CostGate",
    "NoOpCostGate",
    "NoOpRateLimiter",
    "PolicyViolation",
    "RateLimiter",
    "ToolRegistry",
    "WorkspacePolicy",
    "detect_pii",
]
