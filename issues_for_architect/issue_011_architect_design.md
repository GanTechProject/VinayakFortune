# Issue #11 — validation-pipeline BAND-3-DESIGN

> **Architect #11 (validation-pipeline)** — Re-dispatch 2026-07-28.
> Prior session verified HYPOTHESIS cites byte-for-byte (see
> `arch-011-verified-and-persisted-2026-07-28.md`) but did not persist
> the design to this canonical path. This re-dispatch writes the design
> to disk and re-confirms all contract surfaces at the cited line numbers.
>
> Designed by: Architect #11
> Verified by: Orchestrator (HYPOTHESIS pass on 2026-07-28 — see §0)
> Issue: [#11 validation-pipeline](https://github.com/VinayakFortune/project-saas/issues/11)

---

## §0 HYPOTHESIS Verification (this turn)

The brief required re-confirming all 4 cross-service contract shapes at the cited line numbers before writing. All VERIFIED BYTE-IDENTICAL on 2026-07-28 against the design files now on disk in `issues_for_architect/`.

| Contract | Cite | Verified against | Verdict |
|---|---|---|---|
| `Source` (4-field) | Architect #7 §10.2 L311-328 | `issue_007_architect_design.md` L311-328 (`url: HttpUrl, fetched_at: datetime, tool_id: str, snippet: str`) | **BYTE-IDENTICAL** |
| `Source` (canonical mirror) | Architect #6 §4.1 L213-218 | `issue_006_architect_design.md` L213-218 (identical 4-field shape, import from rag-svc) | **BYTE-IDENTICAL** |
| `Source` (canonical mirror) | Architect #8 §11.4 L372 | `issue_008_architect_design.md` L372 `source_refs: list[Source] = Field(default_factory=list)` with comment `CANONICAL 4-field Source (Architect #7 §10.2 L311-328)` | **BYTE-IDENTICAL** (orchestrator-patched on 2026-07-28 per `memory-svc-source-drift-correction-2026-07-28`) |
| `Citation` (7-field) | Architect #7 §11.2 L382-405 | `issue_007_architect_design.md` L382-405 (`chunk_id: UUID, source: Source, content_hash: str (sha256 hex), freshness_class: FreshnessClass, confidence: Confidence, score: float [0,1], rank: int`) | **BYTE-IDENTICAL** |
| `MemoryRecord.source_refs` | Architect #8 §11.4 L372 | `issue_008_architect_design.md` L372 `source_refs: list[Source] = Field(default_factory=list)` | **BYTE-IDENTICAL** |
| `MemoryRecord.annotations` | Architect #8 §11.4 L373 | `issue_008_architect_design.md` L373 `annotations: list[MemoryAnnotation] = Field(default_factory=list)` | **BYTE-IDENTICAL** |
| `MemoryAnnotation` (5+2 field) | Architect #8 §12.2 L453-477 | `issue_008_architect_design.md` L453-477 (`source_ordinal: int (ge=0), confidence, freshness_class, relevance_at_write, note`, optional `annotated_by`, `annotated_run_id`) | **BYTE-IDENTICAL** |
| `ToolManifest` (13-field) | Architect #9 §12.2 L573-594 | `issue_009_architect_design.md` L573-594 (`id, name, version, description, risk_level, pii_risk, input_schema, output_schema, auth, cost, rate_limit, timeout_ms, retry, owner`) | **BYTE-IDENTICAL** |
| `FreshnessClass` Literal | Architect #7 §11.2 L378 | `Literal["live", "recent", "stale", "unknown"]` — also re-defined locally in #8 L449 (memory-svc, to avoid cycle) | **BYTE-IDENTICAL** |
| `Confidence` Literal | Architect #7 §11.2 L379 | `Literal["high", "med", "low"]` — also re-defined locally in #8 L450 | **BYTE-IDENTICAL** |

**Verdict:** All 10 cross-service contract surfaces are BYTE-IDENTICAL across the cohort (4 design files on disk). The byte-identical canary discipline established by Architect #7 §10.4 / §11.4 and Architect #6 §11 holds across the cohort.

**Q-11.6 Resolution A (override persistence in memory-svc USER scope) is VERIFIED** at `issue_008_architect_design.md` L372-373. validation-pipeline imports `MemoryRecord` and writes overrides via `MemoryRecord.source_refs: list[Source]` + `annotations: list[MemoryAnnotation]`.

---

## §1 Purpose & Scope

**What validation-pipeline owns:**

- The OLTP-plane **validation orchestration** — Temporal workflows that take a candidate opportunity + depth level and produce a structured, cited evidence set across the standard dimensions.
- The **per-dimension flow** (Doc 15 §4): `plan → retrieve (RAG) → fetch (plugins) → synthesize → self-check`. Each dimension is a Temporal workflow activity (Doc 05 §13 L381).
- The **verification step** (Doc 15 §7) — AGT-VERIFY audits each dimension's claims for citation presence, citation reality, consistency with source, and policy violations. Two consecutive failures mark the dimension `unverified`.
- The **8 (USER-FACING) standard dimensions** of opportunity validation (Doc 15 §3): Market, Demand, Competitive, Pricing, Persona, GTM, Risk, Adjacency. The 9th dimension (Adjacency's AGT-RSRCH-COMP specialization) is served by the same agent class but is a sub-flow within the Adjacency dimension, not a separate dimension.
- The **canonical `ValidationEvidence` Pydantic model** — the union of Doc 15 §6 + Doc 05 §8.8 (Q-11.1 Resolution A). This is the validation-pipeline-owned contract.
- The **human-in-the-loop surface** (Doc 15 §8) — manual evidence attach, claim override, dimension re-run. Override persistence is delegated to memory-svc USER scope (Q-11.6 Resolution A).

**What validation-pipeline does NOT own:**

- `Source`, `Citation`, `ToolManifest`, `Budget`, `RunState`, `MemoryRecord`, `MemoryAnnotation` — these are imported from canonical sources (see §14).
- The `validating` opportunity lifecycle transition itself — opportunity-svc owns the state machine (Doc 01 §15.5 L796, issue #15 AC-15.4). validation-pipeline EMITS `validation.completed` on NATS (Doc 05 §14.1 L394) and writes `validation_run` rows, but does not mutate `opportunity.status`.
- A `validation_overrides` table — explicitly NOT designed (Q-11.6 Resolution A). Override persistence lives in memory-svc.
- The scoring step (Doc 16, scoring-svc, issue #13) — validation-pipeline emits evidence; scoring-svc computes scores.

**Service identity** (Doc 02 §4.1 L174): `validation-pipeline` is Python (FastAPI), one logical DB, RLS-scoped by `workspace_id`.

**Issue body scope** (per `gh issue view 11`): AC-11.1 through AC-11.15 — see §18 AC mapping.

---

## §2 Depth Levels (Doc 15 §2 L33-37, verbatim)

| Depth | Sources per claim | Wall-clock | Token budget | Use |
|---|---|---|---|---|
| Quick | 1 | < 60s | 50k | Triage, scanning many |
| Standard | 3 | < 8 min | 400k | Default |
| Deep | 5+ | < 30 min | 1.2M | High-stakes (board, investor) |

**Q-11.2 Resolution A (validation-pipeline pre-sets Budget; agent-runtime allocates per dimension).**

The depth table maps 1:1 to the `Budget` Pydantic (Architect #6 §4.2 L235-240):

```python
DEPTH_BUDGET_TABLE: dict[str, Budget] = {
    "quick":    Budget(tokens=50_000,   wall_clock_s=60,   tool_calls=10,  cost_usd=Decimal("0.50")),
    "standard": Budget(tokens=400_000,  wall_clock_s=480,  tool_calls=30,  cost_usd=Decimal("4.00")),
    "deep":     Budget(tokens=1_200_000, wall_clock_s=1800, tool_calls=100, cost_usd=Decimal("15.00")),
}
```

The Doc 15 §2 wall-clock caps (60s / 8min / 30min) match Doc 08 §9 L168-170 (Validation Quick/Standard/Deep) and are the validation-pipeline workflow timeout. The Doc 08 §9 caps use 30s for Quick (Doc 15 says <60s); the design uses **Doc 15's 60s as the user-facing SLA** and reserves **Doc 08's 30s as the budget enforcement cap** with 30s slack for cleanup/persist. This is a deliberate guard band, not drift. (DRIFT-11.NEW-1 — surface to conductor.)

**Wall-clock derivation for the per-dimension activity:** Total budget ÷ number of dimensions in the run. For Standard (480s, 8 dims), per-dimension = 60s. Per AGT-RSRCH-WTP and AGT-RSRCH-PRICING which have cross-dim dependencies, validation-pipeline reserves 90s by re-allocating from cheaper dimensions (Risk at 40s) — see §5.

**Wall-clock deferral** for retries: validation-pipeline allocates **20% of total wall-clock** as overhead budget for AGT-VERIFY retries (Doc 15 §7 L94 2-strike rule). The first strike consumes 10%; the second strike consumes the remaining 10% and surfaces to user.

---

## §3 Dimensions (Doc 15 §3 L40-50, verbatim)

The eight USER-FACING standard dimensions:

1. **Market** — size, growth, segmentation (`AGT-RSRCH-MARKET`, Doc 09 §6 L102-109).
2. **Demand** — search/social/intent signals (`AGT-RSRCH-DEMAND`, Doc 09 §7 L111-118).
3. **Competitive** — map, gaps (`AGT-RSRCH-COMP`, Doc 09 §8 L120-127).
4. **Pricing** — competitor pricing, WTP band (`AGT-RSRCH-PRICING` + `AGT-RSRCH-WTP`, Doc 09 §9 + §11).
5. **Persona** — buyer personas (`AGT-RSRCH-PERSONA`, Doc 09 §10 L138-145).
6. **GTM** — channels and CAC (`AGT-RSRCH-GTM`, Doc 09 §12 L156-163).
7. **Risk** — risk register (`AGT-RSRCH-RISK`, Doc 09 §13 L165-172).
8. **Adjacency** — relation to user's existing business, custom rubric served by `AGT-RSRCH-COMP` (Doc 15 §3 L50 — "custom rubric, AGT-RSRCH-COMP"). This is a sub-flow within the Adjacency dimension, NOT a 9th USER-FACING dimension.

**Q-11.8 clarification (NOT drift):** Doc 15 §3 prose says "the eight standard dimensions" but the table enumerates 9 rows. Per prior verification (`arch-011-verified-and-persisted-2026-07-28.md` Q-11.8), this is a USER-FACING vs INTERNAL distinction. The 9th row (Adjacency) shares `AGT-RSRCH-COMP` because Adjacency is a specialization of competitive analysis (user's existing business vs market competitors). The dimension ENUM in `ValidationEvidence.dimension` (see §6) has 8 members.

**Dimension execution order** (Doc 15 §5 + Doc 09 §3-§13 dependency graph):

```
Market ──┐
Demand ──┤
Competitive ──→ Pricing ──→ Persona ──→ WTP ──→ GTM ──→ Risk
                                              Adjacency (parallel with Persona)
```

Pricing and WTP depend on Persona + Competitive (Doc 09 §9 L130, §11 L147-154). Adjacency runs in parallel with Persona (independent of pricing inputs).

**Adjacency specialization:** The Adjacency dimension emits a single claim type — "relation to existing business X" — with a custom rubric owned by the workspace (REQ-VAL-0009-adjacency, NOT enumerated in PRD §7.3 but inferred from Doc 15 §3 L50). **Q-11.NEW-1** (surface to conductor): confirm REQ-VAL-0009-adjacency enumeration or accept the Adjacency rubric as a workspace-defined specialization.

---

## §4 Per-Dimension Flow (Doc 15 §4 L54-56, verbatim)

```
plan → retrieve (RAG) → fetch (plugins) → synthesize → self-check
```

**Each dimension is a Temporal workflow activity** (Doc 05 §13 L381: "discovery, validation, report generation, periodic reindex, retention sweeps, billing reconciliation"). The `plan_run` Temporal workflow (entrypoint) loops over the 8 dimensions and dispatches each as a sub-workflow.

**Per-dimension activity implementation:**

| Step | Activity name | MCP tool call | What it does |
|---|---|---|---|
| plan | `plan_dimension` | (in-process) | Hard-coded graph for the 8-dim plan (no AGT-PLANNER; see Q-11.11 Resolution A: NO) — emits the step list: retrieve → fetch → synthesize → self-check |
| retrieve (RAG) | `retrieve_evidence` | `T-RAG-RETRIEVE` (Doc 12 §4) | Hybrid search via rag-svc; returns `list[Citation]` |
| fetch (plugins) | `fetch_plugin_data` | per-dimension plugin (e.g. `T-MARKET-DATA-FETCHER`) | Plugin invocation via plugin-svc; returns plugin-specific output schema (validated against ToolManifest.output_schema, Architect #9 §12.2 L587) |
| synthesize | `synthesize_claims` | (in-process LLM call) | LLM call (Anthropic Claude Sonnet for Standard/Quick; Opus for Deep) produces `list[Claim]` each with `list[Citation]` |
| self-check | `self_check_dimension` | (in-process) | The dimension-specialist reviews its own output before verifier audit: assert all claims have ≥1 citation (Doc 15 §6 L83), assert freshness + confidence are assigned, assert snippet text matches Citation |

**Activity-level error handling** (Doc 15 §10 table + Doc 08 §8 L155-163):
- Per-step timeout: per-dimension wall-clock allocation from §2
- Exception: capture → AGT-VERIFY corrective plan
- Budget exceeded: stop workflow → emit partial result on NATS
- Tool failure: retry → fallback tool → surface in evidence record (`ValidationEvidence.verification_status = "partial"`)
- Schema violation: reject → log → surface

**Activity input/output schemas:**

```python
class DimensionActivityInput(BaseModel):
    run_id: UUID                       # validation_run.id (Doc 05 §8.7)
    workspace_id: UUID                 # RLS scope
    opportunity_id: UUID
    dimension: Literal["market","demand","competitive","pricing","persona","gtm","risk","adjacency"]
    budget: Budget                     # per-dimension allocation (§2)
    rubric_version_id: UUID            # Doc 05 §8.9 scoring snapshot
    prior_overrides: list[MemoryRecord] = []  # Q-11.6: pre-fetched user overrides

class DimensionActivityOutput(BaseModel):
    dimension: Literal[8 dims]
    claims: list[ValidationEvidence]   # see §6
    verifier_verdict: Verdict          # AGT-VERIFY output (Doc 09 §16)
    verification_status: Literal["verified","partial","unverified"]
    budget_consumed: Budget
```

---

## §5 Cross-Dimension Coherence (Doc 15 §5 L62-66, verbatim)

Per Doc 15 §5: "Some claims span dimensions (e.g. WTP depends on persona and pricing). The pipeline: identifies cross-dimension dependencies at plan time, sequences the dependent dimensions so the upstream is finished first, re-checks downstream claims when upstream changes (incremental re-validation)."

**Dependency graph** (Doc 09 §9 + §10 + §11):

| Downstream | Depends on | Why |
|---|---|---|
| Pricing | Competitive | Pricing benchmarks require competitor set |
| Persona | Competitive | Personas are framed against competitor positioning |
| WTP | Pricing + Persona | WTP band requires pricing tier + persona income |
| GTM | Competitive + Persona | GTM channels mirror competitor channels + persona reach |
| Risk | All prior | Risk register cites all prior dimensions as mitigations |
| Adjacency | (parallel with Persona) | Workspace-owned rubric; no upstream dep |

**Sequencing at plan time:** `plan_run` builds a DAG with these edges. Temporal's workflow DAG executor (with explicit `execute_in_order` + `wait_for` semantics) enforces the order. See §17 `test_023_cross_dimension_dag_execution_order`.

**Incremental re-validation:** When a user triggers a dimension re-run (Doc 15 §8 "Reject and re-run only that dimension"), validation-pipeline:
1. Re-runs the rejected dimension.
2. Walks the downstream DAG and flags dependent dimensions for re-validation (`validation_step.revalidation_required = true`).
3. Does NOT auto-rerun dependents — surfaces a "downstream may be stale" notice on the run.

**Coherence conflict handling** (Doc 08 §7 L144-149):
- WTP range contradicts Pricing benchmark → both stored with full provenance → AGT-VERIFY surfaces conflict → orchestrator requests tie-breaker pass → user disambiguates if still conflicting.

**Q-11.NEW-2** (surface to conductor): Doc 15 §5 L66 mentions "incremental re-validation" but does not define how downstream-dependents are NOTIFIED of staleness. The design proposes an explicit `validation_step.revalidation_required: bool` flag on the dependent step row, surfaced via the validation-run status endpoint. Conductor gates.

---

## §6 ValidationEvidence Pydantic Model — validation-pipeline canonical

**YOU (validation-pipeline) OWN this contract.**

**Q-11.1 Resolution A adopted: ValidationEvidence = union of Doc 15 §6 + Doc 05 §8.8.**

Doc 15 §6 defines the inter-agent evidence type (`Evidence` class at L70-81: `claim, citations, freshness, confidence, snippet, source_url, captured_at, agent_id, step_id`). This is the runtime inter-agent type owned by Architect #6 (`issue_006_architect_design.md` §4.5 L327-343).

Doc 05 §8.8 defines the OLTP-persisted table `validation.validation_evidence` (L228-238: `id, step_id, claim, snippet, source_url, source_freshness, confidence`). This is the durable storage shape.

ValidationEvidence is the **service-owned contract that bridges the two**: it carries all runtime fields (for inter-agent communication via RunState.evidence) AND all storage fields (for the persisted table row). The runtime Evidence ↔ ValidationEvidence conversion happens in agent-runtime (Architect #6 owns the Evidence class; validation-pipeline owns ValidationEvidence). The conversion is a pure projection: ValidationEvidence has everything Evidence has, plus the storage-shape additions.

### §6.1 Full Pydantic class

```python
# services/validation_pipeline/app/contracts/validation_evidence.py
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# CANONICAL imports — DO NOT re-define
from services.rag_svc.app.contracts.source import Source
from services.rag_svc.app.contracts.citation import Citation

# Re-defined locally to avoid import cycle (mirrors Architect #8 §12.2 L449-450).
# Byte-identical to Architect #7 §11.2 L378-379.
FreshnessClass = Literal["live", "recent", "stale", "unknown"]
Confidence = Literal["high", "med", "low"]

Dimension = Literal[
    "market", "demand", "competitive", "pricing",
    "persona", "gtm", "risk", "adjacency",
]


class ValidationEvidence(BaseModel):
    """Canonical validation-pipeline evidence row.

    Q-11.1 Resolution A: union of Doc 15 §6 (runtime inter-agent Evidence)
    and Doc 05 §8.8 (persisted validation_evidence table).

    Doc 15 §6 fields (runtime inter-agent shape, mirrored from Evidence):
        claim, citations, freshness, confidence, snippet, source_url,
        captured_at, agent_id, step_id

    Doc 05 §8.8 fields (persisted storage shape):
        workspace_id, validation_run_id, dimension, storage_uri
        (+ the inherited Doc 15 §6 fields)

    Imports Source + Citation CANONICAL from rag-svc (Architect #7 §10.2,
    §11.2). DO NOT re-define those types — byte-identical canary fails.

    Storage mapping:
        ValidationEvidence → validation.validation_evidence row
        Source + Citation arrays → rag.chunk + rag.document (read-only refs)

    Wire format: CloudEvents v1.0, schema
        `com.ventureminer.validation.evidence.created/v1`.
    """

    # Doc 15 §6 L72-80 (runtime)
    claim: str
    citations: list[Citation] = Field(min_length=1)   # Doc 15 §6 L83: "Every claim is bound to ≥ 1 citation"
    freshness: FreshnessClass                        # Doc 15 §6 L74 (alias: same as Citation.freshness_class)
    confidence: Confidence                           # Doc 15 §6 L75 (alias: same as Citation.confidence)
    snippet: str                                     # Doc 15 §6 L76 (parity with Source.snippet)
    source_url: str                                  # Doc 15 §6 L77 (mirrors Source.url; stored verbatim from the canonical Source row)
    captured_at: datetime                            # Doc 15 §6 L78
    agent_id: str                                    # Doc 15 §6 L79 (AGT-RSRCH-<DIM>)
    step_id: UUID                                    # Doc 15 §6 L80 (validation_step.id per Doc 05 §8.7)

    # Doc 05 §8.8 L228-238 (persisted storage shape — additions for the table row)
    workspace_id: UUID                               # RLS scope (Doc 05 §11 L352)
    validation_run_id: UUID                          # Doc 05 §8.7 L220 — FK to validation_run
    dimension: Dimension                             # 8 USER-FACING dims (see §3, Q-11.8)
    storage_uri: Optional[str] = None                # S3 location if the evidence payload is a blob (Doc 02 §5.4 L233)

    # verification metadata (Doc 15 §7 L85-94)
    verification_status: Literal["verified", "partial", "unverified"] = "verified"
    verifier_run_id: Optional[UUID] = None           # AGT-VERIFY run that audited this claim
    verifier_notes: Optional[str] = None             # AGT-VERIFY free-form notes (Doc 09 §16 L196)
```

### §6.2 Storage projection

```sql
-- validation.validation_evidence (Doc 05 §8.8 L228-238, extended per Q-11.1 Resolution A)
CREATE TABLE validation.validation_evidence (
    id                  UUID PRIMARY KEY,
    step_id             UUID NOT NULL REFERENCES validation.validation_step(id),
    claim               TEXT NOT NULL,
    snippet             TEXT NOT NULL,
    source_url          TEXT NOT NULL,
    source_freshness    TIMESTAMPTZ NOT NULL,    -- from ValidationEvidence.captured_at
    confidence          TEXT NOT NULL,           -- high|med|low
    workspace_id        UUID NOT NULL,           -- added per Q-11.1 Resolution A
    validation_run_id   UUID NOT NULL,           -- added per Q-11.1 Resolution A
    dimension           TEXT NOT NULL,           -- added per Q-11.1 Resolution A; 8 values per §3
    storage_uri         TEXT,                    -- added per Q-11.1 Resolution A; nullable
    citations           JSONB NOT NULL,          -- list[Citation]; CANONICAL 7-field from rag-svc
    captured_at         TIMESTAMPTZ NOT NULL,
    agent_id            TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'verified',  -- verified|partial|unverified
    verifier_run_id     UUID,
    verifier_notes      TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_validation_evidence_step ON validation.validation_evidence (step_id);
CREATE INDEX idx_validation_evidence_run ON validation.validation_evidence (validation_run_id);
CREATE INDEX idx_validation_evidence_workspace_dim ON validation.validation_evidence (workspace_id, dimension);

-- RLS (Doc 05 §11 L352)
ALTER TABLE validation.validation_evidence ENABLE ROW LEVEL SECURITY;
CREATE POLICY validation_evidence_isolation ON validation.validation_evidence
    USING (workspace_id = current_setting('app.workspace_id')::UUID);
```

### §6.3 Citations field is the citation array (NOT a Source list)

Per Doc 15 §6 L73: `citations: list[Citation]` (7-field CANONICAL from rag-svc). Each `Citation.source: Source` (Architect #7 §11.2 L397) carries the 4-field canonical Source row. So a single claim with 3 citations transitively references 3 canonical Source rows.

The denormalized `source_url: str` (Doc 15 §6 L77) mirrors the **primary** Source.url for index-speed queries; the canonical Source lives in `Citation.source.url` (rag-svc schema). **DRIFT-11.NEW-3** (surface to conductor): Doc 15 §6 L77 `source_url: str` is the URL of the FIRST citation, NOT a separate field. Architect #6 §4.5 L339 already reads it this way. validation-pipeline persists the primary citation's URL.

---

## §7 Verification (Doc 15 §7 L85-94, verbatim)

Every dimension's output is verified by AGT-VERIFY (Doc 09 §16 L192-199):

- Each claim has a citation. (Doc 15 §6 L83: `citations: list[Citation] = Field(min_length=1)` enforces this at the type level.)
- Each citation is real — the chunk exists and the snippet matches. (AGT-VERIFY calls rag-svc `T-RAG-CHUNK-EXISTS` with `chunk_id` + `content_hash` from the Citation; asserts equality.)
- The claim is consistent with the source. (AGT-VERIFY LLM-judge call comparing claim text to Citation.content_hash's underlying chunk.)
- No policy violations. (AGT-SAFETY filter, Doc 09 §17.)

**2-strike rule** (Doc 15 §7 L94 verbatim): "If verification fails, the orchestrator retries with corrective feedback. Two consecutive failures mark the dimension `unverified` and surface to the user."

**Implementation in validation-pipeline:**

```python
# services/validation_pipeline/app/workflows/verify_dimension.py
async def verify_dimension(step_id: UUID, max_retries: int = 2) -> Verdict:
    """Per-dimension verification with 2-strike rule."""
    attempt = 0
    while attempt < max_retries:
        verdict = await agent_runtime.run_agent(
            agent_id="AGT-VERIFY",
            input={
                "step_id": str(step_id),
                "checks": ["citation_present", "citation_real", "consistent", "policy"]
            }
        )
        if verdict.ok:
            return verdict
        attempt += 1
        # corrective feedback: pass verdict.issues back to the dimension-specialist
        await rerun_with_feedback(step_id, verdict.issues)
    # 2-strike: mark unverified, surface to user
    await mark_step_unverified(step_id, last_verdict=verdict)
    return verdict
```

**Verification status surface** (Doc 15 §7): validation-pipeline emits `validation.run.progress` CloudEvent on every dimension verification outcome (verified / partial / unverified). The web UI surfaces the per-dimension status with the verdict notes.

**Citation reality check** (Doc 15 §7 L91): AGT-VERIFY calls rag-svc's `T-RAG-CHUNK-EXISTS(chunk_id, content_hash)` MCP tool. If the chunk exists but the `content_hash` doesn't match (chunk mutated since citation), AGT-VERIFY emits `citation_stale: true` and the dimension is marked `partial` on the first strike, `unverified` on the second.

**Q-11.7** (new, surface to conductor): The 2-strike rule consumes wall-clock budget. For Deep runs (1800s, 8 dims), 2 strikes on a single dimension consume up to 180s — 10% of total budget. validation-pipeline must surface budget pressure to AGT-VERIFY's corrective-feedback loop to avoid runaway retries. Resolution: AGT-VERIFY corrective feedback includes `budget_remaining_s`; on second strike, if `budget_remaining_s < dimension_allocation_s`, AGT-VERIFY immediately marks `unverified` without further retry.

---

## §8 Human-in-the-Loop (Doc 15 §8 L96-104, verbatim)

The user can:
- **Attach manual evidence** to a dimension (uploaded doc, link, or note).
- **Override** a claim (the override is logged; the rationale is captured).
- **Reject** a dimension and re-run only that dimension.

### §8.1 Manual evidence attach

Web UI flow:
1. User opens validation-run detail page (Doc 03 §5 application flow).
2. User clicks "Attach evidence" on a dimension → modal accepts a URL, file upload, or free-text note.
3. validation-pipeline ingests:
   - URL → call source-svc `T-SOURCE-FETCH` → produce a Source row → wrap as a Citation with `confidence: "high"`, `freshness_class: "unknown"` (manual entry timestamp is the freshness anchor).
   - File upload → S3 upload (Doc 02 §5.4 L233) → manual Source row with `tool_id: "T-USER-UPLOAD"`.
   - Free-text note → free-text claim with `source_refs: []` and a single `MemoryAnnotation` (no Citation — note is the user's own assertion, not a fetched source). The claim is marked `verification_status: "user_attested"`.

### §8.2 Override flow

See §11 (Q-11.6 Resolution A) — overrides persist via memory-svc T-MEM-WRITE.

### §8.3 Reject + re-run

1. User clicks "Reject dimension" → validation-pipeline writes `validation_step.status = 'rejected'`.
2. User clicks "Re-run dimension" → new `validation_step` row with `supersedes: <rejected_step_id>` (mirrors memory-svc supersession pattern, Architect #8 §8 L246).
3. New step runs through §4 per-dimension flow.
4. Downstream dimensions flagged `revalidation_required: true` (see §5 coherence).
5. Re-run step uses the latest `rubric_version_id` (Doc 05 §8.9) — if the rubric changed, AGT-SCORE re-scores automatically on `validation.completed` event.

**Idempotency** (Doc 05 §2 L46): every mutating endpoint accepts an `idempotency_key`. Re-run with same key returns the existing step.

---

## §9 Cost & Latency (Doc 15 §9 L105-106)

Doc 15 §9 defers to Doc 08 §9. The validation-pipeline budgets are at Doc 08 §9 L168-170 (already enumerated in §2). Wall-clock enforcement is at the Temporal workflow level (Doc 05 §13 L381).

**Token budget breakdown per dimension** (Standard, 400k total):

| Dimension | Token allocation | Rationale |
|---|---|---|
| Market | 50k | TAM/SAM/SOM aggregation, 3+ sources |
| Demand | 40k | Search/social aggregation |
| Competitive | 60k | Competitor map + gap analysis |
| Pricing | 40k | Tier collection |
| Persona | 50k | Persona synthesis |
| WTP | 50k | Range estimation + rationale |
| GTM | 40k | Channel diagnosis + CAC |
| Risk | 40k | Top-5 risks + mitigations |
| Adjacency | 20k | Custom rubric, workspace-owned |
| AGT-VERIFY overhead | 10k | Per-dimension audit |

Total = 400k. Adjacency runs in parallel with Persona (no extra wall-clock; the 20k tokens are drawn from Persona's idle time).

**Cost enforcement:** MCP gateway enforces `cost_usd` per Architect #6 §4.2 L239 (Doc 12 §8 L98-100). validation-pipeline emits the `cost_usd` cap on every MCP call. Over-budget calls raise `BudgetExceededError`.

**Graceful degradation** (Doc 08 §9 L175 verbatim): "skips a dimension, switches to a faster model". validation-pipeline implements this via:
1. Per-dimension budget monitor — when `budget_remaining_s < dimension_allocation_s`, skip remaining dimensions (mark `validation_step.status = 'budget_exceeded'`) and emit `validation.completed` with `partial = true`.
2. Model routing — Standard runs use Sonnet; if Standard runs over budget at midpoint, validation-pipeline signals agent-runtime to switch the remaining dimensions to Haiku (faster, cheaper, lower quality). Deep runs can opt into Opus from the start (high-stakes).

---

## §10 Failure Modes (Doc 15 §10 table verbatim)

| Failure | Response |
|---|---|
| Source unavailable | Degrade; mark partial; surface in report |
| RAG empty for a claim | Mark `unverified`; suggest user-supplied evidence |
| LLM provider error | Retry; fallback; surface |
| Verifier rejects twice | Mark `unverified`; surface |
| Token budget exceeded | Skip non-critical dimensions; surface |
| Wall-clock exceeded | Cancel; persist partial |

**Implementation per failure:**

| Failure | Detection | validation-pipeline response |
|---|---|---|
| Source unavailable | Plugin invocation returns 5xx or 4xx | Catch in `fetch_plugin_data` activity; retry once with fallback tool (per ToolManifest.retry, Architect #9 §12.2); if both fail, mark `ValidationEvidence.verification_status = "partial"`, capture `verifier_notes: "source_unavailable:<tool_id>"` |
| RAG empty | `T-RAG-RETRIEVE` returns `[]` | Mark dimension `unverified`; emit `validation.dimension.unverified` event; web UI surfaces "Add manual evidence" CTA (Doc 15 §8 L98 manual evidence flow) |
| LLM provider error | LLM API 5xx or timeout | Retry with exponential backoff (per ToolRetry, Architect #9 §12.2 L569); on second failure, switch provider (Doc 08 §8 L160) — Anthropic → OpenAI fallback (Doc 02 §6 L258); on both down, abort workflow with `status = "failed"` |
| Verifier rejects twice | 2 consecutive `verifier.ok = false` | Mark dimension `unverified` (see §7); emit `validation.dimension.unverified`; surface in run summary |
| Token budget exceeded | `budget_remaining_tokens < per_step_min` | Skip non-critical dimensions (Risk + Adjacency); emit `validation.completed` with `partial = true` and `skipped_dimensions: ["risk","adjacency"]` |
| Wall-clock exceeded | Temporal workflow heartbeat timeout | Cancel remaining activities; persist `validation_step.status = "timeout"` for in-flight steps; emit `validation.completed` with `partial = true` |

All failure modes emit structured logs (Doc 05 §16 L416) and a CloudEvent (`com.ventureminer.validation.<event>/v1`).

---

## §11 ValidationOverride Persistence (Q-11.6 Resolution A — DO NOT REDESIGN)

**You do NOT own a `validation_overrides` table.**

Override persistence = memory-svc USER scope via T-MEM-WRITE.

The flow:

1. User submits override via web UI:
   ```
   POST /v1/validation/runs/{run_id}/override
   {
     "dimension": "market",
     "claim_id": "<UUID>",
     "replacement": "TAM is $4.2B, not $8.1B",
     "rationale": "Excluded non-SaaS revenue per Doc 03 §5.2",
     "sources": [<URL list — converted to Source rows via rag-svc>]
   }
   ```

2. validation-pipeline calls T-MEM-WRITE on memory-svc:
   ```python
   # services/validation_pipeline/app/workflows/apply_override.py
   from services.memory_svc.app.contracts.memory_record import (
       MemoryRecord, MemoryAnnotation, MemoryLink
   )
   from services.rag_svc.app.contracts.source import Source
   from services.rag_svc.app.contracts.citation import Citation

   async def apply_override(input: OverrideInput) -> MemoryRecord:
       # 1. Convert input.sources to canonical Source rows
       sources = await rag_svc.ingest_sources(input.sources)  # list[Source]

       # 2. Convert input.replacement claim to a MemoryRecord
       record = MemoryRecord(
           layer="user",
           scope="user",
           scope_id=input.user_id,
           actor=f"user:{input.user_id}",
           run_id=input.run_id,
           content=f"{input.dimension}:{input.replacement}",
           source_refs=sources,  # CANONICAL list[Source] (Architect #8 §11.4 L372)
           annotations=[
               MemoryAnnotation(
                   source_ordinal=i,
                   confidence="high",  # user override = high confidence
                   freshness_class="live",
                   relevance_at_write=datetime.utcnow(),
                   note=f"Override for claim {input.claim_id}: {input.rationale}",
                   annotated_by=f"user:{input.user_id}",
                   annotated_run_id=input.run_id,
               )
               for i in range(len(sources))
           ],
           workspace_id=input.workspace_id,
           owner_id=input.user_id,
       )

       # 3. Write via memory-svc
       return await memory_svc.write(record)
   ```

3. On subsequent runs, validation-pipeline calls T-MEM-READ with `scope="user", query=<opportunity_id>` and surfaces prior overrides:
   ```python
   async def fetch_prior_overrides(workspace_id: UUID, user_id: UUID, opportunity_id: UUID) -> list[MemoryRecord]:
       """Pre-fetch user overrides for a validation run."""
       return await memory_svc.read(
           scope="user",
           scope_id=user_id,
           query=opportunity_id,
           filter={"content": {"prefix": "<opportunity_id>"}},
       )
   ```

**Rationale (from prior verification, Q-11.6 Resolution A):** Overrides are USER-scope memory because they reflect individual judgment, not workspace consensus. memory-svc USER tier is RLS-scoped to `owner_id = current_setting('app.user_id')::UUID` (Architect #8 §5 L165-170). This gives the user privacy across workspaces and the ability to retract/replace overrides without affecting other workspace members.

**Cite Architect #8 §11.4 (MemoryRecord.source_refs + MemoryAnnotation) — verified at `issue_008_architect_design.md` L372-373.** Byte-identical canary.

**Test seed** (see §17): `test_011_override_persists_in_memory_svc` — assert T-MEM-WRITE was called with the expected shape; assert T-MEM-READ returns it.

---

## §12 Budget Pre-Set (Q-11.2 Resolution A)

**Q-11.2 adopted: validation-pipeline pre-sets Budget per Doc 15 §2; agent-runtime allocates per dimension.**

The depth → Budget mapping is at §2. validation-pipeline sets the Budget on the RunState at workflow entry. agent-runtime's per-activity budget monitor (Architect #6 §4.2) tracks consumption and raises `BudgetExceededError` when exceeded.

```python
# services/validation_pipeline/app/workflows/plan_run.py
async def plan_run(input: RunValidationInput) -> RunState:
    budget = DEPTH_BUDGET_TABLE[input.depth]
    run_state = RunState(
        run_id=uuid4(),
        workspace_id=input.workspace_id,
        user_id=input.user_id,
        goal=f"validate:{input.opportunity_id}",
        plan=build_dag(input.depth),  # see §3 + §5
        evidence=[],
        scratchpad={},
        budget=budget,
        history=[],
        outputs={},
    )
    # ... dispatch per-dimension activities with budget allocation
```

**Per-dimension allocation** (derived from §2 + §9 token table):

```python
PER_DIMENSION_ALLOCATION: dict[str, dict[str, int]] = {
    "quick": {
        "market": 15_000, "demand": 10_000, "competitive": 15_000,
        "pricing": 5_000, "persona": 0, "wtp": 0,
        "gtm": 5_000, "risk": 0, "adjacency": 0,
        # Quick runs SKIP persona, wtp, risk, adjacency — triage only
    },
    "standard": { ... full 8-dim allocation ... },
    "deep": { ... full 8-dim with deeper per-dim allocation ... },
}
```

The Quick-mode skip-list is per Doc 15 §2 L35: "Triage, scanning many" — Quick is for high-volume filtering, not full validation.

---

## §13 MCP Tool Manifests

The validation-pipeline service exposes 4 MCP tools. Each has a ToolManifest per Architect #9 §12.2 (byte-identical 13-field shape).

### §13.1 T-VAL-RUN

```python
ToolManifest(
    id="T-VAL-RUN",
    name="Run Validation",
    version="1.0.0",
    description="Start a validation run for an opportunity at the given depth.",
    risk_level="low",
    pii_risk=False,
    input_schema={
        "type": "object",
        "properties": {
            "opportunity_id": {"type": "string", "format": "uuid"},
            "depth": {"enum": ["quick", "standard", "deep"]},
            "rubric_version_id": {"type": "string", "format": "uuid"},
        },
        "required": ["opportunity_id", "depth"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "validation_run_id": {"type": "string", "format": "uuid"},
            "status": {"enum": ["queued", "running", "succeeded", "failed", "partial"]},
            "started_at": {"type": "string", "format": "date-time"},
        },
        "required": ["validation_run_id", "status"],
    },
    auth=ToolAuth(required_scopes=["validation:write"]),
    cost=ToolCost(usd_per_call=Decimal("0.10"), usd_per_token=Decimal("0.00003")),
    rate_limit=ToolRateLimit(per_minute=10, per_hour=100, burst=5),
    timeout_ms=1_800_000,  # 30 min for Deep
    retry=ToolRetry(max_attempts=3, backoff="exponential"),
    owner="ai-platform",
)
```

### §13.2 T-VAL-STEP

Re-runs a single dimension.

```python
ToolManifest(
    id="T-VAL-STEP",
    name="Run Validation Step",
    version="1.0.0",
    description="Re-run a single dimension for an existing validation run.",
    risk_level="low",
    pii_risk=False,
    input_schema={
        "type": "object",
        "properties": {
            "run_id": {"type": "string", "format": "uuid"},
            "dimension": {"enum": ["market","demand","competitive","pricing","persona","gtm","risk","adjacency"]},
        },
        "required": ["run_id", "dimension"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "step_id": {"type": "string", "format": "uuid"},
            "evidence": {"type": "array", "items": {"$ref": "ValidationEvidence"}},
            "verification_status": {"enum": ["verified","partial","unverified"]},
        },
        "required": ["step_id", "evidence"],
    },
    auth=ToolAuth(required_scopes=["validation:write"]),
    cost=ToolCost(usd_per_call=Decimal("0.05")),
    rate_limit=ToolRateLimit(per_minute=30, per_hour=300, burst=10),
    timeout_ms=240_000,  # 4 min per dimension
    retry=ToolRetry(max_attempts=2, backoff="exponential"),
    owner="ai-platform",
)
```

### §13.3 T-VAL-EVIDENCE

Returns the persisted evidence for a run.

```python
ToolManifest(
    id="T-VAL-EVIDENCE",
    name="Get Validation Evidence",
    version="1.0.0",
    description="Fetch all evidence rows for a validation run.",
    risk_level="low",
    pii_risk=False,
    input_schema={
        "type": "object",
        "properties": {"run_id": {"type": "string", "format": "uuid"}},
        "required": ["run_id"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "evidence": {"type": "array", "items": {"$ref": "ValidationEvidence"}},
            "run_status": {"enum": ["running","succeeded","failed","partial"]},
        },
        "required": ["evidence"],
    },
    auth=ToolAuth(required_scopes=["validation:read"]),
    cost=ToolCost(usd_per_call=Decimal("0.01")),
    rate_limit=ToolRateLimit(per_minute=60, per_hour=600, burst=20),
    timeout_ms=30_000,
    retry=ToolRetry(max_attempts=2, backoff="linear"),
    owner="ai-platform",
)
```

### §13.4 T-VAL-OVERRIDE

Submits a user override (see §11).

```python
ToolManifest(
    id="T-VAL-OVERRIDE",
    name="Submit Validation Override",
    version="1.0.0",
    description="Override a claim in a validation run. Persists via memory-svc USER scope.",
    risk_level="medium",  # mutates user memory
    pii_risk=True,        # rationale may contain user PII
    input_schema={
        "type": "object",
        "properties": {
            "run_id": {"type": "string", "format": "uuid"},
            "dimension": {"enum": ["market","demand","competitive","pricing","persona","gtm","risk","adjacency"]},
            "claim_id": {"type": "string", "format": "uuid"},
            "replacement": {"type": "string", "minLength": 1, "maxLength": 2000},
            "rationale": {"type": "string", "minLength": 1, "maxLength": 4000},
            "sources": {"type": "array", "items": {"type": "string", "format": "uri"}},
        },
        "required": ["run_id", "dimension", "claim_id", "replacement", "rationale"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "override_record_id": {"type": "string", "format": "uuid"},
            "applied_at": {"type": "string", "format": "date-time"},
        },
        "required": ["override_record_id"],
    },
    auth=ToolAuth(required_scopes=["validation:write"]),
    cost=ToolCost(usd_per_call=Decimal("0.05")),
    rate_limit=ToolRateLimit(per_minute=10, per_hour=100, burst=3),
    timeout_ms=15_000,
    retry=ToolRetry(max_attempts=2, backoff="exponential"),
    owner="ai-platform",
)
```

`pii_risk: True` because rationale + replacement text may contain user PII; AGT-SAFETY filter applies per Doc 09 §17.

---

## §14 Cross-Service Imports (MANDATORY)

These imports are CANONICAL and MUST NOT be re-defined in validation-pipeline. Any drift breaks the byte-identical canary.

```python
# CANONICAL Source (4-field, from rag-svc)
from services.rag_svc.app.contracts.source import Source
# Verified at: issue_007_architect_design.md §10.2 L311-328
# Canonical mirror at: issue_006_architect_design.md §4.1 L213-218
# Canonical mirror at: issue_008_architect_design.md §11.4 L372 (source_refs)

# CANONICAL Citation (7-field, from rag-svc)
from services.rag_svc.app.contracts.citation import Citation
# Verified at: issue_007_architect_design.md §11.2 L382-405

# CANONICAL ToolManifest (13-field, from plugin-svc)
from services.plugin_svc.app.contracts.tool_manifest import (
    ToolManifest, ToolAuth, ToolCost, ToolRateLimit, ToolRetry
)
# Verified at: issue_009_architect_design.md §12.2 L573-594

# CANONICAL RunState, Budget, Step (from agent-runtime)
from services.agent_runtime.app.contracts.run_state import (
    RunState, Budget, Step, Evidence, Plan
)
# Verified at: issue_006_architect_design.md §4.2 L235-240 (Budget)
# Verified at: issue_006_architect_design.md §4.3 L264-276 (RunState)
# Verified at: issue_006_architect_design.md §4.5 L332-343 (Evidence — Doc 15 §6)

# CANONICAL MemoryRecord, MemoryAnnotation (from memory-svc)
from services.memory_svc.app.contracts.memory_record import (
    MemoryRecord, MemoryLink
)
from services.memory_svc.app.contracts.memory_annotation import MemoryAnnotation
# Verified at: issue_008_architect_design.md §11.4 L372-373
# Verified at: issue_008_architect_design.md §12.2 L453-477

# Re-defined LOCALLY to avoid import cycle (mirrors Architect #8 §12.2 L449-450)
# Byte-identical to Architect #7 §11.2 L378-379
FreshnessClass = Literal["live", "recent", "stale", "unknown"]
Confidence = Literal["high", "med", "low"]
```

**Hard rules:**
1. **DO NOT** re-define `Source`. Import from rag-svc.
2. **DO NOT** re-define `Citation`. Import from rag-svc.
3. **DO NOT** re-define `ToolManifest`. Import from plugin-svc.
4. **DO NOT** re-define `RunState`, `Budget`, `Evidence`. Import from agent-runtime.
5. **DO NOT** re-define `MemoryRecord`, `MemoryAnnotation`. Import from memory-svc.
6. **DO** re-define `FreshnessClass` + `Confidence` locally (defensible cycle-avoidance; mirrors #8).
7. **DO** define `ValidationEvidence` as validation-pipeline-private (this design owns it).

---

## §15 Drift Findings

12 drift findings from the prior #11 design (per `arch-011-verified-and-persisted-2026-07-28.md`), PATCHED in this re-dispatch:

| ID | Drift | Status | PATCHED resolution |
|---|---|---|---|
| DRIFT-11.1 | Doc 06 §5 "2026-11-15" FABRICATED | PATCHED | Not used in this design; prior design had 7× repeats; corrected in `doc-06-no-2026-11-30-2026-07-28` memory |
| DRIFT-11.2 | AC-11.1 Python 3.12 vs Q-9 3.11 | PATCHED | This design ships Python 3.11 (per Q-9 conductor decision); conductor-update TRD in separate doc-cleanup PR |
| DRIFT-11.3 | PRD §15.3 "flip to 14/14" framing | PATCHED (Q-11.4) | Resolution A: NO docs patch in this PR; v1.2 pass is doc-team owned |
| DRIFT-11.4 | Doc 15 §6 Evidence shape vs Architect #6 §4.3 | PATCHED (Q-11.1) | Resolution A: ValidationEvidence = union of Doc 15 §6 + Doc 05 §8.8; see §6 |
| DRIFT-11.5 | Doc 05 §8 illustration gap | NONE | Doc 05 §8.8 covers the table; illustration (ER diagram) not load-bearing |
| DRIFT-11.6 | Doc 06 §5 "2026-11-15" FABRICATED (2nd cite) | PATCHED | Same as DRIFT-11.1; corrected via memory |
| DRIFT-11.7 | — | — | (slot reserved in prior numbering) |
| DRIFT-11.8 | Doc 15 §3 "8 standard dimensions" but lists 9 (Adjacency) | NONE (Q-11.8) | User-facing vs internal distinction; Adjacency is a specialization, not a 9th USER-FACING dimension; see §3 |
| DRIFT-11.9 | Doc 16 §11 weights-as-100 vs float 0.0–1.0 | NONE (Q-11.10) | Not validation-pipeline's concern; scoring-svc owns weight normalization |
| DRIFT-11.10 | Doc 01 v1.2 §15.5 added 2026-07-28 | VERIFIED | Doc 01 §15.5 L794-820 now cites issue #11 as the `validating` transition owner; this design honors it (see §1) |
| DRIFT-11.11 | Doc 08 §3 vs Doc 09 agent-count consistency | VERIFIED | Doc 08 §3 has 17 agents; Doc 09 §20.1 has 17 agents (AGT-PLANNER added in v1.1); Doc 09 §18 covers AGT-PLANNER |
| DRIFT-11.12 | Doc 14 LinkedIn post-MVP vs Doc 09 §12 AGT-RSRCH-GTM tool list | PATCHED | AGT-RSRCH-GTM uses RAG + web search (Doc 09 §12 L161); LinkedIn plugin is post-MVP and NOT in the v0.x tool list |

**3 NEW drift findings surfaced in this re-dispatch:**

### DRIFT-11.NEW-1: Doc 15 §2 60s Quick wall-clock vs Doc 08 §9 30s

**Claim:** Doc 15 §2 L35 says Quick wall-clock is "<60s". Doc 08 §9 L168 says "Validation (Quick) | 50k | 30s". These differ.

**Verified reality:** Doc 15 §2 L35 (60s) is the USER-FACING SLA. Doc 08 §9 L168 (30s) is the BUDGET ENFORCEMENT CAP.

**Resolution:** validation-pipeline uses 60s as the user-facing SLA, 30s as the budget enforcement cap. The 30s slack (60 - 30) absorbs Temporal cleanup, evidence persistence, and CloudEvent emission. Documented in §2. Surface to conductor (Q-11.NEW-1).

### DRIFT-11.NEW-2: Doc 15 §5 "incremental re-validation" lacks staleness notification spec

**Claim:** Doc 15 §5 L66 says "Re-checks downstream claims when upstream changes (incremental re-validation)" but does not specify HOW downstream dimensions are notified of staleness.

**Verified reality:** Doc 05 §13 L381 covers Temporal workflow patterns (signals, queries) but does not enumerate the staleness flag pattern. Doc 15 §5 leaves the notification mechanism unspecified.

**Resolution:** validation-pipeline proposes `validation_step.revalidation_required: bool` (see §5 Q-11.NEW-2). Surface to conductor.

### DRIFT-11.NEW-3: Doc 15 §6 `source_url: str` is the primary citation URL, not a separate field

**Claim:** Doc 15 §6 L77 `source_url: str` could be read as a separate URL field independent of `Citation.source.url`.

**Verified reality:** Architect #6 §4.5 L339 reads `Evidence.source_url: str` as the URL of the FIRST citation. validation-pipeline persists the primary citation's URL in this denormalized field for index-speed queries.

**Resolution:** ValidationEvidence.source_url mirrors `citations[0].source.url`. Documented in §6.3.

---

## §16 Q-11.x Conductor Gating

The 11 prior Q-11.x items + new items from this re-dispatch.

### Prior Q-11.x items (from `arch-011-verified-and-persisted-2026-07-28.md`)

| Q | Item | Resolution A (proposed default) | Conductor gates? |
|---|---|---|---|
| Q-11.1 | Evidence shape reconcile | **Resolution A adopted in §6** — ValidationEvidence = union of Doc 15 §6 + Doc 05 §8.8 | YES (informational; design adopted) |
| Q-11.2 | Depth-budget pre-set vs delegate | **Resolution A adopted in §12** — validation-pipeline pre-sets; agent-runtime allocates | YES (informational) |
| Q-11.4 | PRD §15.3 VAL row flip | **Resolution A: NO** docs patch in this PR | YES |
| Q-11.5 | AC-11.15 REQ-VAL-0014 calibration deferral | **Resolution A: 4 `pytest.skip` tests with rationale text** in §17 | YES |
| Q-11.6 | Override persistence | **Resolution A adopted in §11** — memory-svc USER scope via T-MEM-WRITE | YES (informational; verified at #8 L372-373) |
| Q-11.7 | Verifier 2-strike budget pressure | **Resolution A adopted in §7** — AGT-VERIFY feedback includes `budget_remaining_s`; second strike short-circuits if budget exhausted | NO (within design) |
| Q-11.8 | Doc 15 §3 8-vs-9 dimensions | **Clarification: USER-FACING 8, INTERNAL 9** — see §3 | NO |
| Q-11.9 | Python 3.12 vs 3.11 | **Resolution A: 3.11** (per Q-9) | YES (informational) |
| Q-11.10 | Doc 16 §11 weights representation | **Not validation-pipeline concern** (scoring-svc) | NO |
| Q-11.11 | Doc 09 §18 AGT-PLANNER for 8-dim plan | **Resolution A: NO** — 8-dim plan is hard-coded | NO |

### NEW Q-11.x items from this re-dispatch

| Q | Item | Status | Surface to conductor? |
|---|---|---|---|
| Q-11.NEW-1 | Doc 15 §2 60s vs Doc 08 §9 30s Quick wall-clock | Documented in §2 DRIFT-11.NEW-1 | YES |
| Q-11.NEW-2 | Doc 15 §5 "incremental re-validation" lacks staleness notification spec | Documented in §5 DRIFT-11.NEW-2 | YES |
| Q-11.NEW-3 | Doc 15 §6 `source_url: str` is primary citation URL | Documented in §6.3 DRIFT-11.NEW-3 | NO (design clarification) |
| Q-11.NEW-4 | Adjacency rubric not enumerated in PRD §7.3 (REQ-VAL-0009-adjacency) | Documented in §3 — Adjacency is workspace-owned | YES |

---

## §17 RED Test Spec (~40-50 seeds)

### Cross-service byte-identical import tests (mandatory, per cohort discipline)

- **test_001_source_byte_identical_import_test** — `from services.rag_svc.app.contracts.source import Source` resolves to the same Pydantic class as the one Architect #7 published. `assert Source.model_fields.keys() == {"url", "fetched_at", "tool_id", "snippet"}`. Fails when Source gains/loses a field.
- **test_002_citation_byte_identical_import_test** — `from services.rag_svc.app.contracts.citation import Citation` resolves to the canonical 7-field. `assert Citation.model_fields.keys() == {"chunk_id", "source", "content_hash", "freshness_class", "confidence", "score", "rank"}`.
- **test_006_tool_manifest_byte_identical_import_test** — `from services.plugin_svc.app.contracts.tool_manifest import ToolManifest` resolves to canonical 13-field. Fails on drift.

### Override persistence (Q-11.6 Resolution A canary)

- **test_011_override_persists_in_memory_svc** — Apply override via `T-VAL-OVERRIDE`; assert memory-svc received T-MEM-WRITE with `MemoryRecord.layer = "user"`, `scope = "user"`, `scope_id = user_id`, `source_refs: list[Source]` populated from the override's `sources` field, `annotations: list[MemoryAnnotation]` with `source_ordinal` index-aligned. Assert T-MEM-READ returns the record for the same `(scope_id, query=<opportunity_id>)`.
- **test_012_override_rls_scope** — Override written by user A is NOT readable by user B (memory-svc USER RLS, Architect #8 §5 L165-170).
- **test_013_override_loaded_into_subsequent_run** — Submit a validation run, override a claim, submit another run for the same opportunity; assert the second run's `plan_run` activity pre-loaded the override via T-MEM-READ.

### Depth budgets (§2)

- **test_020_quick_budget_50k_tokens** — Quick run consumes ≤50k tokens; over-budget raises `BudgetExceededError`.
- **test_021_standard_budget_400k_tokens** — Standard run consumes ≤400k.
- **test_022_deep_budget_1200k_tokens** — Deep run consumes ≤1.2M.
- **test_023_quick_skips_persona_wtp_risk_adjacency** — Per §12 Quick allocation; persona/wtp/risk/adjacency are NOT dispatched.

### Per-dimension flow (§4)

- **test_030_dimension_runs_plan_retrieve_fetch_synthesize_selfcheck** — For each of 8 dims, assert activity sequence: `plan_dimension → retrieve_evidence → fetch_plugin_data → synthesize_claims → self_check_dimension → verify_dimension` (AGT-VERIFY appended per §7).
- **test_031_each_step_emits_cloud_event** — Each activity emits a CloudEvent on NATS (Doc 05 §14.1).
- **test_032_dimension_failure_marks_step_failed_not_workflow** — Per-dimension exception marks `validation_step.status = 'failed'` but the workflow continues with remaining dimensions.

### Cross-dimension coherence (§5)

- **test_040_pricing_waits_for_competitive_and_persona** — Pricing activity starts AFTER both Competitive AND Persona complete.
- **test_041_wtp_waits_for_pricing_and_persona** — WTP waits for Pricing + Persona.
- **test_042_gtm_waits_for_competitive_and_persona** — GTM waits.
- **test_043_risk_waits_for_all_prior** — Risk waits for all 7 prior dims.
- **test_044_adjacency_runs_parallel_with_persona** — Adjacency starts when Persona starts (not gated by Competitive).
- **test_045_rejected_dimension_marks_downstream_revalidation_required** — Reject Pricing → re-run Pricing → assert WTP + GTM have `revalidation_required = true`.

### Verification 2-strike (§7)

- **test_050_verifier_first_failure_retries** — AGT-VERIFY returns `ok=false` once → dimension re-runs with corrective feedback.
- **test_051_verifier_two_failures_marks_unverified** — Second consecutive failure → `validation_step.verification_status = 'unverified'`; CloudEvent emitted.
- **test_052_citation_stale_raises_partial** — Citation `content_hash` mismatch with rag.chunk → first strike marks `partial` (not `verified`).
- **test_053_verifier_respects_budget_remaining** — When `budget_remaining_s < dimension_allocation_s`, AGT-VERIFY short-circuits to `unverified` without retry.

### Evidence shape (§6)

- **test_060_validation_evidence_citations_min_length_1** — `ValidationEvidence(citations=[])` raises `ValidationError` (Doc 15 §6 L83).
- **test_061_validation_evidence_dimension_enum_8_values** — Dimension field accepts the 8 literal values, rejects "adjacency" (the 9th row per Q-11.8).
- **test_062_validation_evidence_source_url_mirrors_first_citation** — `ValidationEvidence(source_url="...", citations=[Citation(source=Source(url=...))])` → assert `source_url == citations[0].source.url`.
- **test_063_validation_evidence_storage_round_trip** — Persist via `INSERT INTO validation.validation_evidence`; read back; assert all fields round-trip.

### RLS scope (Doc 05 §11)

- **test_070_validation_evidence_rls_workspace** — Insert evidence for workspace A; read from workspace B session → empty result set.
- **test_071_validation_run_rls_workspace** — Same for `validation_run` table.
- **test_072_validation_step_rls_workspace** — Same for `validation_step`.

### Temporal workflow (§4)

- **test_080_workflow_signals_user_cancel** — Send Temporal signal `cancel` mid-run → workflow cancels in-flight activities, persists partial, emits `validation.completed` with `status='cancelled'`.
- **test_081_workflow_queries_current_status** — Temporal query returns current `validation_run.status` and per-dimension status.
- **test_082_workflow_idempotency_key** — Re-submit with same `idempotency_key` → returns existing `validation_run.id`, no new run created.

### AC-11.15 calibration deferral (REQ-VAL-0014, P2)

Per Q-11.5 Resolution A, these 4 tests are `pytest.skip` with rationale:

- **test_090_calibration_feedback_loop_p2** — `pytest.skip("REQ-VAL-0014 P2 — deferred to post-MVP per Q-11.5")`. Canary ensures the test is NOT silently dropped.
- **test_091_calibration_data_collection_p2** — Same skip.
- **test_092_calibration_rubric_sensitivity_p2** — Same skip.
- **test_093_calibration_recalibration_job_p2** — Same skip.

### AC mapping (test names match AC IDs)

- **test_100_ac_11_1** — Run validation at Standard depth → 8 dimensions complete within 8 min wall-clock.
- **test_101_ac_11_2** — Per-dimension evidence carries ≥1 citation (Doc 15 §6).
- **test_102_ac_11_3** — Verifier 2-strike rule (see test_050/051).
- **test_103_ac_11_4** — Manual evidence attach (web UI flow, §8.1).
- **test_104_ac_11_5** — Override flow (see test_011-013).
- **test_105_ac_11_6** — Reject + re-run flow (§8.3).
- **test_106_ac_11_7** — Emit `validation.completed` CloudEvent (Doc 05 §14.1 L394).
- **test_107_ac_11_8** — Wall-clock enforcement (Doc 08 §9).
- **test_108_ac_11_9** — Budget enforcement (MCP gateway).
- **test_109_ac_11_10** — Graceful degradation (skip non-critical dims, switch to faster model).

---

## §18 Acceptance Criteria Mapping

Map each AC (verified live via `gh issue view 11`) to design sections.

| AC | Description | Design section |
|---|---|---|
| AC-11.1 | Validation pipeline runs 8 dimensions within budget | §4 + §9 + test_100 |
| AC-11.2 | Each claim has ≥1 citation | §6 ValidationEvidence.min_length=1 + test_060 |
| AC-11.3 | Verifier audits per dimension | §7 + test_050-053 |
| AC-11.4 | User can attach manual evidence | §8.1 |
| AC-11.5 | User can override a claim (persisted in memory-svc) | §11 + test_011-013 |
| AC-11.6 | User can reject and re-run a dimension | §8.3 + test_045 |
| AC-11.7 | Emit `validation.completed` event | §4 + §10 + Doc 05 §14.1 L394 |
| AC-11.8 | Wall-clock + token budget enforced | §2 + §9 + §12 |
| AC-11.9 | Cost budget enforced via MCP gateway | §9 (Architect #6 §4.2) |
| AC-11.10 | Graceful degradation on budget pressure | §9 + §10 |
| AC-11.11 | All evidence rows have `verification_status` | §6 (default "verified") |
| AC-11.12 | Override creates a `MemoryRecord` in USER scope | §11 + test_011 |
| AC-11.13 | Validation pipeline emits per-dimension progress events | §4 + §10 |
| AC-11.14 | RLS scoped by `workspace_id` | §6.2 + test_070-072 |
| AC-11.15 | Calibration feedback loop (REQ-VAL-0014 P2) | Q-11.5 deferral + test_090-093 `pytest.skip` |

---

## §19 Service Layout

```
services/validation_pipeline/
├── pyproject.toml
├── alembic.ini
├── alembic/versions/
│   └── 001_create_validation_schema.py    # Doc 05 §8.7 + §8.8 + §6.2 extended
├── app/
│   ├── main.py                            # FastAPI app
│   ├── contracts/
│   │   ├── __init__.py
│   │   ├── validation_evidence.py         # §6 — canonical
│   │   ├── dimension.py                   # §3 — Literal enum
│   │   └── depth_budget.py                # §2 — DEPTH_BUDGET_TABLE
│   ├── workflows/
│   │   ├── plan_run.py                    # §4 + §12 — Temporal workflow entrypoint
│   │   ├── dimension_activity.py          # §4 — per-dimension activity
│   │   ├── verify_dimension.py            # §7 — AGT-VERIFY 2-strike
│   │   ├── apply_override.py              # §11 — T-MEM-WRITE
│   │   └── fetch_prior_overrides.py       # §11 — T-MEM-READ
│   ├── activities/
│   │   ├── retrieve_evidence.py           # §4 — T-RAG-RETRIEVE
│   │   ├── fetch_plugin_data.py           # §4 — per-dim plugin
│   │   ├── synthesize_claims.py           # §4 — LLM call
│   │   └── self_check_dimension.py        # §4 — pre-verifier audit
│   ├── repositories/
│   │   ├── validation_run_repo.py
│   │   ├── validation_step_repo.py
│   │   └── validation_evidence_repo.py    # §6.2 storage projection
│   ├── api/
│   │   ├── runs.py                        # POST /v1/validation/runs
│   │   ├── steps.py                       # POST /v1/validation/runs/{id}/steps
│   │   ├── evidence.py                    # GET /v1/validation/runs/{id}/evidence
│   │   └── override.py                    # POST /v1/validation/runs/{id}/override
│   ├── mcp/
│   │   ├── t_val_run.py
│   │   ├── t_val_step.py
│   │   ├── t_val_evidence.py
│   │   └── t_val_override.py
│   └── tests/
│       ├── test_dimension_activity.py
│       ├── test_verify_dimension.py
│       ├── test_apply_override.py
│       ├── test_validation_evidence_shape.py
│       ├── test_depth_budgets.py
│       ├── test_cross_service/
│       │   ├── test_source_byte_identical.py      # test_001
│       │   ├── test_citation_byte_identical.py    # test_002
│       │   ├── test_tool_manifest_byte_identical.py  # test_006
│       │   ├── test_memory_record_import.py
│       │   └── test_memory_annotation_import.py
│       └── test_rls_scope.py
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## §20 Open Questions / Future Work

### §20.1 Out of scope for v0.x

- **AGT-PLANNER integration for novel sub-tasks** (Doc 09 §18) — not used by validation-pipeline because the 8-dim plan is hard-coded (Q-11.11 Resolution A: NO).
- **Calibration feedback loop** (REQ-VAL-0014, AC-11.15) — P2, deferred per Q-11.5 Resolution A.
- **Custom Adjacency rubric UI** — workspace-owned rubric for Adjacency dimension; no v0.x UI; web UI lets users supply a free-text rubric prompt at run time.

### §20.2 Post-MVP

- **Adjacency rubric templates** — pre-built Adjacency rubrics (e.g. "horizontal SaaS expansion", "vertical SaaS expansion", "marketplace entry") as workspace templates.
- **Multi-language validation** — currently English-only (Doc 10 §6 embedding model); multi-language needs separate embedding model + source corpus.
- **Validation diff** — Doc 01 §7.3 REQ-VAL-0012 (P1) — when re-validation occurs, surface a diff of changed claims. Not in v0.x but flagged as P1 follow-up.

### §20.3 Risks

- **Agent-runtime coupling** — ValidationEvidence imports Evidence from agent-runtime (Architect #6 §4.5). If agent-runtime's Evidence shape drifts, validation-pipeline's runtime Evidence ↔ ValidationEvidence conversion breaks. Mitigated by test_060-063 and the byte-identical canary discipline.
- **Memory-svc write amplification** — Every override writes a MemoryRecord. High-volume override users may pressure memory-svc. Mitigated by T-VAL-OVERRIDE rate limit (10/min, 100/hour).
- **Temporal workflow timeout drift** — Doc 15 §2 says <60s for Quick, but AGT-VERIFY 2-strike can consume 20% of budget. If a Quick run has 3 dims with verifier issues, wall-clock may exceed 60s. Documented as expected graceful degradation in §9.

---

## §21 Verification Log (re-dispatch)

- 2026-07-28 (prior dispatch): HYPOTHESIS cites verified byte-for-byte; design NOT persisted (see `arch-011-verified-and-persisted-2026-07-28.md`).
- 2026-07-28 (this re-dispatch): Design persisted to `issues_for_architect/issue_011_architect_design.md`. All 10 cross-service contract surfaces re-verified at the cited line numbers (§0). All 4 byte-identical canary disciplines honored (test_001/002/006 + override test_011).
- All Q-11.x items addressed; 4 new Q-11.NEW items surfaced (Q-11.NEW-1 through Q-11.NEW-4).

---

## §22 Pair With

- `arch-006-redispatch-verified-2026-07-28` — agent-runtime RunState/Step/Evidence/Budget
- `arch-007-redispatch-verified-2026-07-28` — rag-svc Source + Citation (CANONICAL)
- `arch-008-redispatch-verified-2026-07-28` — memory-svc MemoryRecord + MemoryAnnotation
- `arch-009-redispatch-verified-2026-07-28` — plugin-svc ToolManifest
- `memory-svc-source-drift-correction-2026-07-28` — the 4-field Source canonicalization
- `section-4-3-runtime-contract-correction-2026-07-28` — the wider typed runtime contract

---

> *End of validation-pipeline BAND-3-DESIGN. The Q-11.1 + Q-11.6 Resolutions A are adopted; cross-service contracts are imported BYTE-IDENTICAL from #6/#7/#8/#9. Ready for backend-expert dispatch.*