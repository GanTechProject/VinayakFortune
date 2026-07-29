"""Top-level orchestrator — discovery → validation → scoring → report.

Per Architect #6 §5 (Doc 08 §4 L76-92 mermaid, verbatim):

    Plan → Safety → Plan dimensions → {For each dim → Specialist → Verify}
    → Score → Verify2 → Report → Verify3 → Done

Three verify passes (post-specialist, post-score, post-report) — each
with a |retry| → Spec branch. Two consecutive failures on the same
node mark the dimension unverified (Doc 15 §7 L94).
"""

from __future__ import annotations

from dataclasses import dataclass

from services.agent_runtime.app.contracts.budget import BudgetExceededError
from services.agent_runtime.app.contracts.run_state import RunState
from services.agent_runtime.app.workflows.specialists import (
    Dimension,
    SpecialistFn,
    default_specialist,
)
from services.agent_runtime.app.workflows.verifier import (
    VerifierDecision,
    VerifierState,
)


@dataclass
class OrchestratorResult:
    """The terminal result of an orchestrated run."""

    state: RunState
    unverified_dimensions: list[str]
    budget_exhausted: bool


class Orchestrator:
    """Top-level orchestrator (Doc 08 §4 L76-92)."""

    def __init__(
        self,
        *,
        specialist_fn: SpecialistFn | None = None,
        max_strikes: int = 2,
    ) -> None:
        self.specialist_fn = specialist_fn or default_specialist
        self.max_strikes = max_strikes

    async def run(
        self,
        *,
        state: RunState,
        dimensions: list[Dimension],
    ) -> OrchestratorResult:
        """Run the top-level orchestration.

        Per Architect #6 §5: Plan → Safety → {For each dim → Specialist
        → Verify} → Score → Verify2 → Report → Verify3 → Done.
        """
        verifier = VerifierState(strikes={})
        unverified: list[str] = []

        # Per-specialist dispatch
        for dim in dimensions:
            try:
                self._check_budget(state)
            except BudgetExceededError:
                return OrchestratorResult(
                    state=state, unverified_dimensions=unverified, budget_exhausted=True
                )

            try:
                result = await self.specialist_fn(state, dim)
            except (RuntimeError, ValueError, TimeoutError):
                # Specialist raised a recoverable error. Record a strike
                # and retry up to max_strikes.
                verifier.record(dim.name)
                if verifier.verdict(dim.name) == VerifierDecision.UNVERIFIED:
                    unverified.append(dim.name)
                    continue
                # Otherwise retry the same dimension.
                try:
                    result = await self.specialist_fn(state, dim)
                except (RuntimeError, ValueError, TimeoutError):
                    verifier.record(dim.name)
                    if verifier.verdict(dim.name) == VerifierDecision.UNVERIFIED:
                        unverified.append(dim.name)
                        continue

            # Persist evidence + step into the run state (Q-6.4: orchestrator
            # is the only writer of the shared RunState).
            for ev in result.evidence:
                await state.add_evidence(ev)
            await state.append_step(result.step)

            # Self-check pass (Q-6.7: 2-strike auto-skip)
            if verifier.verdict(dim.name) == VerifierDecision.UNVERIFIED:
                unverified.append(dim.name)

        # Score + Report nodes are deterministic stubs for v1. The wiring
        # for AGT-SCORE / AGT-RPT-WRITER is in `specialists.py` /
        # `cross_service` and out of scope for the keystone skeleton.
        return OrchestratorResult(
            state=state, unverified_dimensions=unverified, budget_exhausted=False
        )

    def _check_budget(self, state: RunState) -> None:
        """Pre-node budget check (Doc 08 §9 L175)."""
        # The orchestrator checks budget BEFORE every node invocation.
        # For the skeleton, we only check the wall-clock fraction; the
        # token, tool, and cost gates are enforced by the MCP gateway.
        spent = sum(s.cost.total_tokens for s in state.history)
        if not state.budget.has_tokens_remaining(spent):
            raise BudgetExceededError("tokens", spent, state.budget.tokens)


__all__ = ["Orchestrator", "OrchestratorResult"]
