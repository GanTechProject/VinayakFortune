"""Verifier — 2-strike auto-skip + surface (Q-6.7).

Per Architect #6 §5 + DRIFT-6.7:
- The 2-strike rule is sourced from Doc 08 §8 L157 + Doc 15 §7 L94.
- Do NOT re-prompt the user on the second strike.
- After 2 consecutive rejections on the same node, mark the dimension
  `unverified` and surface.

NOTE: DRIFT-6.7 corrects the prior cite "Doc 17 §3" — the verifier
2-strike rule is NOT in Doc 17 §3 (Report Generation assembly pipeline).
Use Doc 08 §8 L157 + Doc 15 §7 L94 only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VerifierDecision(str, Enum):
    OK = "ok"
    RETRY = "retry"
    UNVERIFIED = "unverified"  # 2-strike: auto-skip + surface


@dataclass
class VerifierState:
    """Per-node strike counter (per-run, per-node)."""

    strikes: dict[str, int]

    def record(self, node_name: str) -> None:
        self.strikes[node_name] = self.strikes.get(node_name, 0) + 1

    def verdict(self, node_name: str) -> VerifierDecision:
        n = self.strikes.get(node_name, 0)
        if n >= 2:
            return VerifierDecision.UNVERIFIED
        if n == 1:
            return VerifierDecision.RETRY
        return VerifierDecision.OK


def should_auto_skip(strikes: int) -> bool:
    """Q-6.7: 2 consecutive failures → auto-skip + surface (Doc 15 §7 L94)."""
    return strikes >= 2


__all__ = [
    "VerifierDecision",
    "VerifierState",
    "should_auto_skip",
]
