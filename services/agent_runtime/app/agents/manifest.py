"""Per-agent stubs — 17 agents per Doc 09 §20.1 (Doc 08 §3 L57-75).

The per-agent YAML contracts live at `agents/<id>/contract.yaml`; the
Python node signatures live here. Mismatch between YAML and Python is
a startup error (Architect #6 §3).
"""

from __future__ import annotations

# The 17 agents per Doc 09 §20.1 (Doc 08 §3 L57-75).
ALL_AGENT_IDS: tuple[str, ...] = (
    "AGT-ORCH",
    "AGT-DISC-PLANNER",
    "AGT-DISC-CLUSTER",
    "AGT-RSRCH-MARKET",
    "AGT-RSRCH-DEMAND",
    "AGT-RSRCH-COMP",
    "AGT-RSRCH-PRICING",
    "AGT-RSRCH-PERSONA",
    "AGT-RSRCH-WTP",
    "AGT-RSRCH-GTM",
    "AGT-RSRCH-RISK",
    "AGT-SCORE",
    "AGT-RPT-WRITER",
    "AGT-VERIFY",
    "AGT-SAFETY",
    "AGT-PLANNER",
    "AGT-CRITIC",
)


def agent_registry() -> set[str]:
    """The set of agent IDs registered in this build."""
    return set(ALL_AGENT_IDS)


__all__ = ["ALL_AGENT_IDS", "agent_registry"]
