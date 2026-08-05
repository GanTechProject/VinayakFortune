"""RunState — the keystone cross-service typed state.

Per Architect #6 §4.3 (Doc 08 §5 L113-124, verbatim):
    run_id: UUID
    workspace_id: UUID
    user_id: UUID
    goal: str
    plan: Plan
    evidence: list[Evidence]
    scratchpad: dict
    budget: Budget
    history: list[Step]
    outputs: dict

Invariants (Doc 08 §5 L126-129):
- evidence is the only authoritative store; specialists append to it.
- scratchpad is ephemeral; not persisted.
- history is append-only and replayable.
- budget is enforced by the orchestrator; over-budget calls fail.

Q-6.4 (conductor-ratified): scratchpad is per-specialist (NOT shared).
Cross-specialist data sharing goes through RunState, not scratchpad.

TOCTOU: evidence and history are append-only via add_evidence /
append_step which acquire a per-run asyncio lock (Architect #6 §6).
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, PrivateAttr

from services.agent_runtime.app.contracts.budget import Budget
from services.agent_runtime.app.contracts.evidence import Evidence
from services.agent_runtime.app.contracts.plan import Plan
from services.agent_runtime.app.contracts.step import Step


class RunState(BaseModel):
    """The runtime state of a single agent run (Doc 08 §5 L113-124)."""

    run_id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    user_id: UUID
    goal: str
    plan: Plan
    evidence: list[Evidence] = Field(default_factory=list)
    scratchpad: dict = Field(default_factory=dict)
    budget: Budget
    history: list[Step] = Field(default_factory=list)
    outputs: dict = Field(default_factory=dict)

    # Per-run asyncio lock for TOCTOU-safe appends (Architect #6 §6).
    _append_lock: asyncio.Lock = PrivateAttr(default_factory=asyncio.Lock)

    model_config = {"arbitrary_types_allowed": True}

    async def add_evidence(self, evidence: Evidence) -> None:
        """Append-only evidence writer. Per-run lock serializes (Architect #6 §6)."""
        async with self._append_lock:
            self.evidence.append(evidence)

    async def append_step(self, step: Step) -> None:
        """Append-only history writer. Per-run lock serializes (Architect #6 §6)."""
        async with self._append_lock:
            self.history.append(step)

    async def write_output(self, key: str, value: object) -> None:
        """Write to outputs. Only callable at the terminal node (Architect #6 §6)."""
        async with self._append_lock:
            self.outputs[key] = value

    def fresh_specialist_scratchpad(self) -> dict:
        """Q-6.4: each specialist gets a fresh scratchpad (NOT shared, §6).

        Cross-specialist data sharing goes through RunState, not scratchpad.
        """
        return {}

    def merge_specialist_scratchpad(self, specialist_scratchpad: dict) -> None:
        """Q-6.4: the specialist writes back its deltas to the RunState scratchpad.

        The orchestrator decides which keys to keep; the default is shallow merge.
        """
        self.scratchpad.update(specialist_scratchpad)


__all__ = ["RunState"]
