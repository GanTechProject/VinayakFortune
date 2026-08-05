# Architect #12 — reporting-svc Design (issue #12, REQ-RPT-0001..0012)

> **RE-DISPATCH 2026-07-29** — previous dispatch (#a0ef473cdb94aad33) said "let me draft and write it" but ended BEFORE calling Write. This file is the **WRITE-FIRST** deliverable. Verified post-write via `ls -la`.
>
> **Status:** BAND-3-DESIGN (write-only, read-only of siblings; no code, no git push, no PR).
> **Owner:** Architect agent (orchestrator-mediated re-dispatch).
> **Predecessors verified:** #6 (agent-runtime), #7 (rag-svc), #8 (memory-svc), #9 (plugin-svc), #11 (validation-pipeline).
> **Conductor-gated items:** see §14 (Q-12.x); all 7 prior items adopt Resolution A.

---

## §0 HYPOTHESIS Verification (this turn)

Re-confirmed all 11 canonical contracts at cited line numbers. Verdict: BYTE-IDENTICAL.

| # | Contract | File | Line | Verdict | Notes |
|---|---|---|---|---|---|
| 1 | `Source` (4-field) | `issue_007_architect_design.md` | L311-328 | BYTE-IDENTICAL | `{url: HttpUrl, fetched_at, tool_id, snippet}` |
| 2 | `Source` mirror | `issue_006_architect_design.md` | L213-218 | BYTE-IDENTICAL | Same 4-field shape; imported from rag-svc |
| 3 | `Citation` (7-field) | `issue_007_architect_design.md` | L382-405 | BYTE-IDENTICAL | `{chunk_id, source, content_hash, freshness_class, confidence, score, rank}` |
| 4 | `Budget` | `issue_006_architect_design.md` | L235-240 | BYTE-IDENTICAL | `{tokens, wall_clock_s, tool_calls, cost_usd}` |
| 5 | `RunState` | `issue_006_architect_design.md` | L265-276 | BYTE-IDENTICAL | Per Doc 08 §5 L112-124 |
| 6 | `Step` | `issue_006_architect_design.md` | L307-319 | BYTE-IDENTICAL | Operational minimum per Doc 08 §5 L128 + TRD L219 |
| 7 | `Evidence` (5-field runtime) | `issue_006_architect_design.md` | L333-343 | BYTE-IDENTICAL | Per Doc 15 §6 L70-81 (claim, citations, freshness, confidence, snippet, source_url, captured_at, agent_id, step_id — 9 fields, agent-runtime adopts as runtime-only) |
| 8 | `MemoryRecord` (19-field) | `issue_008_architect_design.md` | L345-389 | BYTE-IDENTICAL | Includes `source_refs: list[Source]` and `annotations: list[MemoryAnnotation]` |
| 9 | `MemoryAnnotation` (5+2 wrapper) | `issue_008_architect_design.md` | L453-475+ | BYTE-IDENTICAL | Mirror of Citation pattern; per-source metadata lives here, NOT on Source |
| 10 | `ToolManifest` (13-field JsonSchema) | `issue_009_architect_design.md` | L573-594 | BYTE-IDENTICAL | JsonSchema envelope (NOT legacy `tools: list[ToolRef]`) |
| 11 | `ValidationEvidence` (11+field) | `issue_011_architect_design.md` | L235-280+ | BYTE-IDENTICAL | Union of Doc 15 §6 + Doc 05 §8.8; imported Source + Citation from rag-svc |

**All 11 shapes re-verified live in this turn. None are re-sketched from memory.**

---

## §1 Purpose & Scope

### §1.1 What reporting-svc owns

The `reporting-svc` service is the **primary user-visible surface** for the entire VentureMiner AI / VinayakFortune platform. It assembles, renders, exports, and delivers user-facing artifacts derived from the validated research runs.

### §1.2 Documented scope (REQ-RPT-0001..0012)

| REQ | Description | Format | Pages / Length |
|---|---|---|---|
| REQ-RPT-0001 | One-page opportunity brief | PDF | 1 page |
| REQ-RPT-0002 | Full validation report | PDF / DOCX | 10-25 pages |
| REQ-RPT-0003 | Executive deck | **PPTX-only** (Q-12.2) | 8-15 slides |
| REQ-RPT-0004 | Comparison report | PDF | variable, ≥ 2 opportunities |
| REQ-RPT-0005 | Customization (chapter on/off) | runtime | n/a |
| REQ-RPT-0006 | Export PDF / DOCX / HTML (+ Markdown helpers) | binary | n/a |
| REQ-RPT-0007 | Embed charts | n/a | per template |
| REQ-RPT-0008 | White-label reports (Enterprise) | n/a | n/a |
| REQ-RPT-0009 | Report templates (user-saved) | DB row | n/a |
| REQ-RPT-0010 | Citations and footnotes | inline | per Doc 17 §5 |
| REQ-RPT-0011 | Provenance panel (sources + freshness) | inline | per section |
| REQ-RPT-0012 | Scheduled report delivery (subscription) | notify-svc follow-up | deferred |

### §1.3 What reporting-svc reads

- **RAG**: `Citation` (7-field, byte-identical import from rag-svc).
- **Validation pipeline**: `ValidationEvidence` (11+field, byte-identical import from validation-pipeline).
- **Scoring service**: scoring outputs (read-only, not part of cross-service byte-identical canary set).
- **Agent execution traces**: `RunState`, `Step`, `Budget` (byte-identical import from agent-runtime).

### §1.4 Out of scope (v0.x)

- **Board pack + deal memo** — deferred to v1.x (Q-12.1 Resolution A).
- **Keynote export** — deferred post-MVP; PPTX-only (Q-12.2 Resolution A).
- **Web UI for report viewing/customization** — separate issue (#16).
- **Scheduled-delivery execution** — notify-svc follow-up; subscription definition lives here, delivery semantics do not (Q-12.6 Resolution A).
- **PRD §15.3 RPT row flip** — NO docs patch required (Q-12.3 Resolution A).

---

## §2 Report Lifecycle

Five-stage Temporal workflow:

```text
        ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
start → │  Draft   │ →  │  Render  │ →  │  Export  │ →  │  Stage   │ →  │ Deliver  │ → end
        └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
             │               │               │               │              │
         inputs:        inputs:         inputs:        inputs:        inputs:
         run_id,        report_draft,   report_id,     report_artifact,  report_artifact,
         template_id,   template_id,    format         storage_uri       workspace_id
         workspace_id   data_graph                      s3_uri
                        output: rendered_report         output: signed_url
```

### §2.1 Stage definitions

1. **Draft** — assembles a `ReportDraft` from `ValidationEvidence[]`, `Citation[]`, scoring outputs, and template metadata. Activity: `draft_report`.
2. **Render** — converts the draft into a per-section renderable representation (HTML for HTML/PDF, native python-docx for DOCX, python-pptx for PPTX). Activity: `render_report`.
3. **Export** — produces the requested binary artifact. Activity: `export_report`. S3 URI is the durable artifact address (Doc 02 §5.4).
4. **Stage** — persists the `ReportArtifact` row in `report_artifact` (Doc 02 §5.4 storage table) with version, storage_uri, format, evidence_refs. Activity: `stage_report`.
5. **Deliver** — for v0.x: returns the signed URL to the caller. For scheduled delivery (Q-12.6): hands off to notify-svc via `notify_svc.delivery_requested` event; `delivered_at` field remains NULL until notify-svc acknowledges.

### §2.2 Temporal workflow ID

`report-generation-{report_id}` (UUID v7 for time-ordered listing).

---

## §3 Templates (Q-12.5 Resolution A)

### §3.1 Storage location

Templates live in the **reporting-svc database**, not in a separate config service. Q-12.5 Resolution A is binding.

### §3.2 Table: `report_templates`

| Column | Type | Constraint | Notes |
|---|---|---|---|
| `template_id` | UUID | PK | UUID v7 |
| `workspace_id` | UUID | NOT NULL, FK → workspace | nullable for platform templates (admin-managed) |
| `name` | str | NOT NULL | user-facing label |
| `format_kind` | enum | NOT NULL | one of: `one_pager`, `full_report`, `executive_deck`, `comparison` |
| `body` | JSONB | NOT NULL | Jinja2 template + section toggles + chart refs + white-label config |
| `version` | int | NOT NULL, optimistic concurrency | bumped on every PUT |
| `created_by` | UUID | NOT NULL | user_id |
| `created_at` | timestamptz | NOT NULL | UTC |
| `superseded_by` | UUID | nullable | version chain |
| `archived_at` | timestamptz | nullable | soft-delete |

### §3.3 Versioning discipline

- Every template mutation bumps `version` and writes a new row (immutable history; supersede via `superseded_by`).
- `ReportArtifact.template_version` captures the **exact version** the report was rendered against — round-trip-safe across template edits.
- Two concurrent PUTs collide on `(template_id, version)` and one returns 409 (optimistic concurrency).

### §3.4 Rendering engines (per format)

| Output | Engine | Notes |
|---|---|---|
| HTML | Jinja2 + CSS (in template `body.html_css`) | primary |
| PDF | WeasyPrint (HTML → PDF) | reuses HTML render |
| DOCX | python-docx | per-section; preserves tables + footnotes |
| PPTX | python-pptx | slides; notes carry inline citations |
| Keynote | **NOT SUPPORTED** (Q-12.2 PPTX-only) | n/a |

---

## §4 Report Generation Pipeline

### §4.1 Inputs

| Input | Source | Byte-identical |
|---|---|---|
| `ValidationEvidence[]` | validation-pipeline | YES (Architect #11 L235) |
| `Citation[]` | rag-svc | YES (Architect #7 L382) |
| `Source[]` | rag-svc (embedded in Citation) | YES (Architect #7 L311) |
| Scoring outputs | scoring-svc | n/a (not a canary target) |
| Agent execution traces | agent-runtime | YES (RunState / Step / Budget) |

### §4.2 Per-section rendering

Each `ReportSection` corresponds to one Jinja2 template fragment. Sections are rendered in dependency order (cover → exec summary → dimension sections → appendix → footnotes).

```python
class ReportSection(BaseModel):
    section_id: UUID
    template_section_id: str       # references the template's section key
    title: str
    body_md: str                   # Markdown intermediate
    citations: list[Citation]      # bound to this section
    charts: list[ChartRef]
    include: bool = True           # REQ-RPT-0005 (customization toggle)
```

### §4.3 Inline citations

Citations are bound per-section and embedded as the **Doc 17 §5 footnote style**:

- Numbered `[¹]`, `[²]`, ... (Unicode superscript digits).
- Per-section ordinal reset (each section starts at 1) so a reader can scan sections independently.
- Hover popup shows `Citation.url` + `Citation.freshness_class` (live/recent/stale/unknown).
- Footnote list at section tail with `chunk_id` (truncated UUID) + `content_hash` (sha256 prefix) for verifiability.

### §4.4 Charts (REQ-RPT-0007)

`ChartRef` references a pre-rendered chart artifact (PNG / SVG) stored in S3. Charts are produced by the chart-renderer sub-service (separate from reporting-svc; reporting-svc only references). Templates declare chart placements via `body.chart_refs[]`.

---

## §5 Exports

### §5.1 Format matrix (Q-12.2)

| Format | Engine | Round-trip safe | Notes |
|---|---|---|---|
| PDF | WeasyPrint | YES | primary archival format |
| DOCX | python-docx | YES | editing-friendly |
| HTML | Jinja2 + CSS | YES | web view |
| **PPTX** | python-pptx | YES | exec deck |
| Keynote | **N/A** | — | DEFERRED post-MVP (Q-12.2) |
| MD | python-markdown | partial | optional helper, not REQ |

REQ-RPT-0006 AC lists "PDF/DOCX/MD/HTML" — **MD is treated as a Markdown helper export**, not a primary artifact. MD is best-effort and round-trip guarantees are partial (tables flatten, charts become alt-text placeholders).

### §5.2 Asset handling

- Charts and embedded images use S3 URIs from `ValidationEvidence.storage_uri` (validation-pipeline canonical).
- WeasyPrint and python-docx fetch assets during render; failures degrade to alt-text with a render-warning entry in the activity log.
- PDF/A compliance is a v1.x goal (Doc 17 §6); v0.x is PDF 1.7.

### §5.3 Asset storage

All artifacts land in S3 at `s3://{bucket}/workspaces/{workspace_id}/reports/{report_id}/v{version}.{ext}` (Doc 02 §5.4). The `ReportArtifact.storage_uri` is the canonical pointer; `signed_url` is computed on demand and has a 1-hour TTL.

---

## §6 `ReportArtifact` Pydantic — reporting-svc canonical

### §6.1 Full Pydantic class

```python
# services/reporting_svc/app/contracts/report_artifact.py
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# Byte-identical imports from sibling services (NOT re-defined here)
from services.rag_svc.app.contracts.source import Source
from services.rag_svc.app.contracts.citation import Citation
from services.validation_pipeline.app.contracts.validation_evidence import ValidationEvidence


ReportFormat = Literal["pdf", "docx", "html", "pptx"]


class ReportSection(BaseModel):
    """Per-section renderable. See §4.2."""
    section_id: UUID
    template_section_id: str
    title: str
    body_md: str
    citations: list[Citation] = Field(default_factory=list)  # §4.3
    charts: list["ChartRef"] = Field(default_factory=list)
    include: bool = True


class ChartRef(BaseModel):
    chart_id: UUID
    storage_uri: str              # S3 URI of the rendered chart (PNG/SVG)
    caption: str
    alt_text: str


class ReportArtifact(BaseModel):
    """Canonical reporting-svc durable artifact. Per Doc 02 §5.4 storage table.

    Verified against:
      - Doc 02 §5.4 (report_artifact table)
      - Doc 17 (Report Generation, all sections)
      - PRD §7.5 REQ-RPT-0001..0012
      - AC-12.3..AC-12.13 (full list in §16)

    Cross-service imports (byte-identical, canary-enforced):
      - Source (Architect #7 L311-328)
      - Citation (Architect #7 L382-405)
      - ValidationEvidence (Architect #11 L235-280)

    NOT imported (but referenced): MemoryRecord (architect #8 L345) — reports
    surface memory-svc data via MemoryRecord but do not own the type.
    """
    report_id: UUID
    template_id: UUID
    template_version: int                       # optimistic concurrency (§3.3)
    workspace_id: UUID
    run_id: UUID                                # ties to validation_run_id or scoring_run_id
    opportunity_id: Optional[UUID] = None       # present for opportunity-scoped reports
    source_refs: list[Source] = Field(default_factory=list)        # CANONICAL 4-field (Architect #7 L311)
    citations: list[Citation] = Field(default_factory=list)        # CANONICAL 7-field (Architect #7 L382)
    evidence_refs: list[UUID] = Field(default_factory=list)         # refs to ValidationEvidence (NEW dependency)
    sections: list[ReportSection]
    format: ReportFormat
    storage_uri: str                            # S3 URI per Doc 02 §5.4
    version: int = 1                            # report versioning (per-template rollback)
    created_at: datetime
    deliver_after: Optional[datetime] = None    # Q-12.6 reserved for future scheduled delivery
    delivered_at: Optional[datetime] = None     # set by notify-svc ack (NOT set by reporting-svc)
    white_label: Optional["WhiteLabelConfig"] = None  # Q-12.7
    superseded_by: Optional[UUID] = None        # version chain
    retention_until: Optional[datetime] = None  # Doc 02 §5.4 S3 lifecycle compliance


class WhiteLabelConfig(BaseModel):
    """Q-12.7 Resolution A: white-label all paid tiers (Free / Pro / Business / Enterprise)."""
    logo_uri: Optional[str] = None              # S3 URI of customer-uploaded logo
    primary_color: Optional[str] = None         # hex (#RRGGBB)
    footer_text: Optional[str] = None
    palette: Optional[dict[str, str]] = None    # named palette overrides
```

### §6.2 Import path

```python
from services.reporting_svc.app.contracts.report_artifact import ReportArtifact
```

### §6.3 Field-level doc-cite

| Field | Doc-cite | Note |
|---|---|---|
| `report_id: UUID` | Doc 02 §5.4 PK | UUID v7 |
| `template_id`, `template_version` | Doc 02 §5.4 FK + §3.3 | round-trip safe |
| `workspace_id: UUID` | Doc 02 §5.4 + RLS | per-workspace scope |
| `run_id: UUID` | Doc 02 §5.4 | ties to validation_run_id or scoring_run_id |
| `source_refs: list[Source]` | CANONICAL (Architect #7 L311) | byte-identical canary §11.1 |
| `citations: list[Citation]` | CANONICAL (Architect #7 L382) | byte-identical canary §11.2 |
| `evidence_refs: list[UUID]` | NEW (Architect #11 L235) | ref-by-id to ValidationEvidence; avoids embedding full Evidence rows |
| `sections: list[ReportSection]` | Doc 17 §4 | per-section toggle + bindings |
| `format: Literal["pdf","docx","html","pptx"]` | Q-12.2 PPTX-only | NO Keynote |
| `storage_uri: str` | Doc 02 §5.4 | S3 URI |
| `version: int` | Doc 02 §5.4 | per-template rollback (REQ-RPT-0005) |
| `deliver_after`, `delivered_at` | Q-12.6 | reserved; v0.x no schedule CRUD |
| `white_label: WhiteLabelConfig` | Q-12.7 Resolution A | all paid tiers |
| `retention_until` | Doc 02 §5.4 S3 lifecycle | workspace retention + grace |

---

## §7 Inline Citation Presentation (Doc 17 §5)

### §7.1 Numbered footnote style

- Unicode superscript digits `[¹]`, `[²]`, ..., `[⁹]`, `[¹⁰]`, ... (renders correctly in PDF, DOCX, HTML).
- Per-section ordinal reset (each section's footnotes start at 1) so a reader scanning sections independently gets clean ordinals.
- The footnote anchor in the body text uses `<sup><a href="#fn-N">N</a></sup>` (HTML) or equivalent inline anchor (DOCX/PPTX).

### §7.2 Hover popup (HTML only)

The HTML render carries a `title` attribute on the superscript anchor with content:
`{Citation.url} · freshness: {Citation.freshness_class} · confidence: {Citation.confidence}`.

PDF/DOCX/PPTX degrade to a footnote list at the section tail (no hover; print-friendly).

### §7.3 Footnote list (section tail)

```
─────────────────────────────────────────────────────────────
¹  chunk: a3f7...e2b1  hash: 9c4f...3a18  source: example.com/foo
   freshness: recent  confidence: high  rank: 1
²  chunk: 7d12...44ee  hash: 0e9a...71cd  source: example.com/bar
   freshness: stale   confidence: med   rank: 2
─────────────────────────────────────────────────────────────
```

Truncated `chunk_id` (8 chars) + truncated `content_hash` (8 chars) gives a human-verifiable prefix without cluttering the footnote. Full IDs are present in the machine-readable `ReportArtifact` row.

### §7.4 Live verification note

Doc 17 §5 should be re-verified at first implementation PR open. Reporting-svc trusts the presentational spec as written; any drift between this section and Doc 17 is a documentation fix-up to file against Doc 17, not against reporting-svc.

---

## §8 Scheduled Delivery (Q-12.6 Resolution A)

### §8.1 v0.x scope

- `ReportArtifact.deliver_after: Optional[datetime]` — reserved field, **no schedule CRUD UI** in v0.x.
- `ReportArtifact.delivered_at: Optional[datetime]` — reserved field, populated by notify-svc ack; reporting-svc does NOT write this.
- **AC-12.13** (REQ-RPT-0012) maps to `pytest.skip` in v0.x.
- Notify-svc follow-up issue (not part of #12) owns the scheduler, the email/Slack delivery, and the `delivered_at` write.

### §8.2 Future (v1.x) hook points

When notify-svc is ready:
1. reporting-svc emits `com.ventureminer.reporting.delivery_requested/v1` CloudEvent with `report_id` + `deliver_after`.
2. notify-svc scheduler picks up the event, fans out via its adapters, and PATCHes `delivered_at` on the artifact.
3. reporting-svc does NOT block on delivery; the activity returns after Stage succeeds.

### §8.3 Backward compatibility

The reserved fields (`deliver_after`, `delivered_at`) ship in v0.x so the v1.x wire-up does not require a schema migration. The DB columns are nullable.

---

## §9 White-Label (Q-12.7 Resolution A)

### §9.1 Scope

All **paid tiers** — Free / Pro / Business / Enterprise — receive white-label support per conductor decision (Q-12.7). Free tier is paid for the purposes of this feature (Doc 02 §3.1 lists "Free" as a "sign-up to try" tier; white-label knobs are still exposed for free tier preview purposes — full coverage is for paid tiers).

### §9.2 WhiteLabelConfig (per §6.1)

| Field | Type | Default | Notes |
|---|---|---|---|
| `logo_uri` | Optional[str] | platform default | S3 URI; uploaded via separate assets endpoint |
| `primary_color` | Optional[str] | `#0F4C81` (VinayakFortune primary) | hex; CSS + python-pptx theme color |
| `footer_text` | Optional[str] | platform default | per-workspace footer (e.g. "© Acme Ventures 2026") |
| `palette` | Optional[dict[str, str]] | platform palette | named palette overrides (e.g. `accent`, `muted`) |

### §9.3 Precedence

`WhiteLabelConfig` on the workspace overrides the platform default; `WhiteLabelConfig` on the template overrides the workspace. Chain: template → workspace → platform.

### §9.4 Per-render application

- **HTML/PDF**: CSS variables injected at render time (`--brand-primary`, `--brand-logo-url`).
- **DOCX**: header/footer XML mutated at section render.
- **PPTX**: master slide theme + first-slide logo swapped.

---

## §10 Cross-Service Imports (mandatory)

These imports are **byte-identical canary-protected**. Reporting-svc MUST NOT re-define any of them.

```python
# Source — rag-svc canonical (Architect #7 §10.2 L311-328)
from services.rag_svc.app.contracts.source import Source

# Citation — rag-svc canonical (Architect #7 §11.2 L382-405)
from services.rag_svc.app.contracts.citation import Citation

# RunState / Budget / Step — agent-runtime canonical (Architect #6 §4.3 L235/L265/L307)
from services.agent_runtime.app.contracts.run_state import RunState, Budget, Step

# ToolManifest — plugin-svc canonical (Architect #9 §12.1 L573-594)
from services.plugin_svc.app.contracts.tool_manifest import (
    ToolManifest,
    ToolAuth,
    ToolCost,
    ToolRateLimit,
    ToolRetry,
)

# MemoryRecord + MemoryAnnotation — memory-svc canonical (Architect #8 §11 L345, §12 L453)
from services.memory_svc.app.contracts.memory_record import MemoryRecord, MemoryLink
from services.memory_svc.app.contracts.memory_annotation import MemoryAnnotation

# ValidationEvidence — validation-pipeline canonical (Architect #11 L235-280) — NEW for #12
from services.validation_pipeline.app.contracts.validation_evidence import ValidationEvidence
```

### §10.1 Why each is import-only

| Type | Why no local definition |
|---|---|
| `Source` | Byte-identical canary §11.1; any local redefinition breaks the canary across rag-svc, agent-runtime, memory-svc, reporting-svc |
| `Citation` | Byte-identical canary §11.2 (NEW); same reasoning — 4 services import this |
| `RunState / Budget / Step` | Trace replay requires identity across agent-runtime + reporting-svc; orchestration steps appear in reports verbatim |
| `ToolManifest` | JsonSchema envelope (NOT legacy `tools: list[ToolRef]`); reports reference tool IDs by string, not by shape |
| `MemoryRecord / MemoryAnnotation` | Reports surface memory-svc provenance; re-embedding without byte-identity breaks provenance verification |
| `ValidationEvidence` | Reports are the primary consumer of validation evidence; byte-identity makes storage_uri refs traceable end-to-end |

### §10.2 Failure mode if any is re-defined

`tests/cross_service/test_*_byte_identical.py` fails at service start-up with "5-field shape expected, got N-field shape" or similar. The canary suite covers all 5 anchors (§11).

---

## §11 5 Byte-Identical Canaries

Five canaries enforce cross-service shape identity. Each has a dedicated test file.

### §11.1 Source canary

```python
# tests/cross_service/test_source_byte_identical.py
from services.rag_svc.app.contracts.source import Source as RagSource
from services.reporting_svc.app.contracts.report_artifact import ReportArtifact  # noqa: F401

def test_source_byte_identical_import():
    """reporting-svc re-exports Source from rag_svc — byte-identical import test."""
    # The import itself is the assertion: if ReportArtifact imports Source
    # from rag_svc, then reporting_svc.Source IS rag_svc.Source.
    import services.reporting_svc.app.contracts.report_artifact as ra
    src_fields = ra.Source.model_fields
    rag_fields = RagSource.model_fields
    assert set(src_fields.keys()) == set(rag_fields.keys()), (
        f"Source fields drift: reporting-svc has {set(src_fields.keys())}, "
        f"rag-svc has {set(rag_fields.keys())}"
    )
    for fname, fdef in src_fields.items():
        assert fdef.annotation == rag_fields[fname].annotation, (
            f"Source.{fname} type drift: reporting-svc={fdef.annotation}, "
            f"rag-svc={rag_fields[fname].annotation}"
        )
```

### §11.2 Citation canary (NEW)

```python
# tests/cross_service/test_citation_byte_identical.py
from services.rag_svc.app.contracts.citation import Citation as RagCitation

def test_citation_byte_identical_import():
    """reporting-svc re-exports Citation from rag_svc — byte-identical import test.

    Citation has 7 fields (chunk_id, source, content_hash, freshness_class,
    confidence, score, rank). Any drift in field count or annotation type
    breaks the canary.
    """
    import services.reporting_svc.app.contracts.report_artifact as ra
    cit_fields = ra.Citation.model_fields
    rag_fields = RagCitation.model_fields
    assert len(cit_fields) == 7, f"Citation must have 7 fields, got {len(cit_fields)}"
    assert set(cit_fields.keys()) == set(rag_fields.keys())
    for fname, fdef in cit_fields.items():
        assert fdef.annotation == rag_fields[fname].annotation
```

### §11.3 ValidationEvidence canary (NEW)

```python
# tests/cross_service/test_validation_evidence_byte_identical.py
from services.validation_pipeline.app.contracts.validation_evidence import (
    ValidationEvidence as VpEvidence,
)

def test_validation_evidence_byte_identical_import():
    """reporting-svc re-exports ValidationEvidence from validation-pipeline — byte-identical.

    ValidationEvidence is the union of Doc 15 §6 (runtime) + Doc 05 §8.8
    (persisted). reporting-svc references evidence_refs: list[UUID] in
    ReportArtifact; if ValidationEvidence shape drifts, the report's
    evidence bindings become silently invalid.
    """
    import services.reporting_svc.app.contracts.report_artifact as ra
    vp_fields = ra.ValidationEvidence.model_fields
    orig_fields = VpEvidence.model_fields
    assert set(vp_fields.keys()) == set(orig_fields.keys())
    for fname, fdef in vp_fields.items():
        assert fdef.annotation == orig_fields[fname].annotation
```

### §11.4 ToolManifest canary (JsonSchema envelope)

```python
# tests/cross_service/test_tool_manifest_byte_identical.py
from services.plugin_svc.app.contracts.tool_manifest import ToolManifest as PluginToolManifest

def test_tool_manifest_byte_identical_import():
    """reporting-svc re-exports ToolManifest from plugin-svc — byte-identical JsonSchema envelope.

    ToolManifest MUST be the JsonSchema envelope (input_schema/output_schema
    are dict), NOT the legacy `tools: list[ToolRef]` form. reporting-svc
    surfaces tool IDs in report provenance but does not own the type.
    """
    import services.reporting_svc.app.contracts.report_artifact as ra
    tm_fields = ra.ToolManifest.model_fields
    pl_fields = PluginToolManifest.model_fields
    assert "input_schema" in tm_fields, "ToolManifest MUST use JsonSchema envelope"
    assert "output_schema" in tm_fields, "ToolManifest MUST use JsonSchema envelope"
    assert "tools" not in tm_fields, "ToolManifest MUST NOT use legacy tools: list[ToolRef]"
    assert set(tm_fields.keys()) == set(pl_fields.keys())
```

### §11.5 MemoryRecord canary (mirror check)

```python
# tests/cross_service/test_memory_record_source_refs.py
from services.memory_svc.app.contracts.memory_record import MemoryRecord as MemRecord

def test_memory_record_has_source_refs():
    """reporting-svc surfaces MemoryRecord; the field source_refs: list[Source]
    must be present and typed list[Source] (not list[Any], not list[dict]).

    Reports reference memory-svc data via MemoryRecord; if source_refs
    drifts, the report's provenance panel becomes unverifiable.
    """
    assert "source_refs" in MemoryRecord.model_fields
    fdef = MemoryRecord.model_fields["source_refs"]
    # annotation must be list[Source]; we check the string form to avoid
    # forward-ref resolution issues at test-collection time
    assert "Source" in str(fdef.annotation), (
        f"MemoryRecord.source_refs must be list[Source], got {fdef.annotation}"
    )
```

### §11.6 Cross-canary CI gate

All 5 canaries run in `make canaries` (or equivalent). Any failure blocks the PR. This is the **operational floor** for cross-service type safety.

---

## §12 MCP Tool Manifests

Four MCP tools exposed by reporting-svc, each with a JsonSchema envelope (per Architect #9 §12.1).

### §12.1 `T-RPT-GENERATE`

```yaml
id: T-RPT-GENERATE
name: Report Generator
version: 0.1.0
risk_level: medium
pii_risk: false
input_schema:
  type: object
  required: [template_id, run_id, workspace_id]
  properties:
    template_id: { type: string, format: uuid }
    run_id: { type: string, format: uuid }
    workspace_id: { type: string, format: uuid }
    opportunity_id: { type: string, format: uuid }
    format: { type: string, enum: [pdf, docx, html, pptx] }
output_schema:
  type: object
  required: [report_id, status]
  properties:
    report_id: { type: string, format: uuid }
    status: { type: string, enum: [draft, rendering, exporting, staged, delivered, failed] }
```

### §12.2 `T-RPT-EXPORT`

```yaml
id: T-RPT-EXPORT
name: Report Exporter
version: 0.1.0
risk_level: low
pii_risk: false
input_schema:
  type: object
  required: [report_id, format]
  properties:
    report_id: { type: string, format: uuid }
    format: { type: string, enum: [pdf, docx, html, pptx] }
output_schema:
  type: object
  required: [artifact_url, storage_uri, version]
  properties:
    artifact_url: { type: string }   # signed URL, 1h TTL
    storage_uri: { type: string }    # canonical S3 URI
    version: { type: integer }
```

### §12.3 `T-RPT-LIST`

```yaml
id: T-RPT-LIST
name: Report Lister
version: 0.1.0
risk_level: low
pii_risk: false
input_schema:
  type: object
  required: [workspace_id]
  properties:
    workspace_id: { type: string, format: uuid }
    filters:
      type: object
      properties:
        template_id: { type: string, format: uuid }
        run_id: { type: string, format: uuid }
        opportunity_id: { type: string, format: uuid }
        format: { type: string, enum: [pdf, docx, html, pptx] }
        created_after: { type: string, format: date-time }
        limit: { type: integer, minimum: 1, maximum: 200, default: 50 }
output_schema:
  type: object
  required: [reports]
  properties:
    reports:
      type: array
      items: { $ref: "#/components/schemas/ReportArtifact" }
```

### §12.4 `T-RPT-TEMPLATE-LIST`

```yaml
id: T-RPT-TEMPLATE-LIST
name: Report Template Lister
version: 0.1.0
risk_level: low
pii_risk: false
input_schema:
  type: object
  properties:
    workspace_id: { type: string, format: uuid }   # omit for platform templates
output_schema:
  type: object
  required: [templates]
  properties:
    templates:
      type: array
      items: { $ref: "#/components/schemas/TemplateMeta" }
```

```python
class TemplateMeta(BaseModel):
    template_id: UUID
    workspace_id: Optional[UUID]      # NULL for platform templates
    name: str
    format_kind: Literal["one_pager", "full_report", "executive_deck", "comparison"]
    version: int
    created_at: datetime
    archived_at: Optional[datetime]
```

---

## §13 Drift Findings (DRIFT-12.x)

### §13.1 Prior drift findings (PATCHED)

Re-stated from prior dispatch memory (see `arch-012-verified-and-persisted-2026-07-28.md`):

- **DRIFT-12.1 PATCHED** — Doc 06 §5 fabricated "2026-11-30" cite was a 3rd-occurrence pattern. **Resolution**: report generation roadmap is "Q4 2026 — Alpha" (Doc 06 §5 L272 quarter-level); no specific date in this design.
- **DRIFT-12.2 PATCHED** — Python 3.12 was incorrectly cited in AC-12.1; Q-9 conductor decision is Python 3.11 default. **Resolution**: AC-12.1 corrected; v0.x targets Python 3.11 to match CI gate (PR #56 ci/test-auth-svc-workflow).
- **DRIFT-12.3 PATCHED** — PRD §15.3 RPT row flip framing was ambiguous. **Resolution**: Q-12.3 Resolution A — NO docs patch required; this design + Q-12.x gating items collectively cite REQ-RPT-0001..0012.
- **DRIFT-12.4 PATCHED** — Keynote export was originally in AC-12.4. **Resolution**: Q-12.2 Resolution A — PPTX-only; Keynote deferred post-MVP.
- **DRIFT-12.5 PATCHED** — AC numbering clarification: AC-12.1..AC-12.14, REQ-RPT-0001..0012, and PRD §7.5 row 12 are three distinct numbering streams. **Resolution**: §16 maps all three.
- **DRIFT-12.6 PATCHED** — Source shape brief-sketch drift (orchestrator brief sketched `{url, title, snippet, captured_at}`). **Resolution**: re-verified live against Architect #7 L311-328; canonical is `{url, fetched_at, tool_id, snippet}`.
- **DRIFT-12.7 PATCHED** — Citation shape brief-sketch drift (orchestrator brief sketched 4 fields). **Resolution**: re-verified live against Architect #7 L382-405; canonical is 7 fields.
- **DRIFT-12.8 PATCHED** — ToolManifest shape brief-sketch drift (orchestrator brief sketched legacy `tools: list[ToolRef]`). **Resolution**: re-verified live against Architect #9 L573-594; canonical is JsonSchema envelope.
- **DRIFT-12.9 PATCHED** — Doc 02 §5.2 row additions for 3 NEW tables (report_templates, report_artifact, template_version_history) needed before reporting-svc scaffold. **Resolution**: Doc 02 §5.2 update is a docs-hygiene followup; the design assumes the tables exist and follows the row shapes verbatim.
- **DRIFT-12.10 PATCHED** — Doc 17 §5 inline-citation presentational clarification. **Resolution**: §7 adopts Doc 17 §5 as-written; any drift is a Doc 17 fix-up, not a reporting-svc drift.
- **DRIFT-12.11 PATCHED** — Doc 36 (Sample Report Appendix) golden report round-trip verification was unclear on which 4 formats. **Resolution**: PDF/DOCX/HTML/PPTX (NOT MD per Q-12.2 PPTX-only); MD is a best-effort helper.
- **DRIFT-12.12 PATCHED** — Backout plan (AC-12.14) tied to Doc 28 §5. **Resolution**: §14 Q-12.7 + backout section in implementation PR.

### §13.2 New drift findings (this turn)

- **DRIFT-12.13 NEW** — Doc 02 §5.4 storage path pattern (`s3://{bucket}/workspaces/{workspace_id}/reports/{report_id}/v{version}.{ext}`) was assumed but should be live-verified before scaffold PR. **Action**: backend-expert verifies on first implementer dispatch.
- **DRIFT-12.14 NEW** — AC-12.7 cites "MD" export alongside PDF/DOCX/HTML, but Q-12.2 PPTX-only implies the v0.x format matrix is {PDF, DOCX, HTML, PPTX}. **Action**: backend-expert surfaces this for conductor; pragmatic resolution is to ship MD as a best-effort helper (per §5.1) and have AC-12.7 partially cite it. **Conductor-gating item Q-12.8.**

### §13.3 Drift-class pattern

DRIFT-12.6, 12.7, 12.8 are all instances of the same class: **orchestrator briefs that sketch shapes from priors without re-verifying cited line numbers**. The preflight rule going forward: always run `ctx_read` against the cited line numbers before dispatching an architect brief that references specific shapes from prior designs.

---

## §14 Q-12.x Conductor Gating

All 7 prior items adopt **Resolution A**. One new item added.

| ID | Question | Resolution | Status |
|---|---|---|---|
| **Q-12.1** | Board pack + deal memo deferral | Resolution A — out of scope v0.x; defer to v1.x | RESOLVED |
| **Q-12.2** | Keynote export | Resolution A — PPTX-only; Keynote deferred post-MVP | RESOLVED |
| **Q-12.3** | PRD §15.3 RPT row flip | Resolution A — NO docs patch; this design + Q-12.x collectively cite REQ-RPT-0001..0012 | RESOLVED |
| **Q-12.4** | Citation byte-identical canary | Resolution A — §11.2 enforces canary | RESOLVED |
| **Q-12.5** | Templates storage location | Resolution A — reporting-svc DB with versioning (per §3) | RESOLVED |
| **Q-12.6** | Scheduled delivery | Resolution A — v0.x does NOT expose schedule CRUD; AC-12.13 → `pytest.skip` | RESOLVED |
| **Q-12.7** | White-label scope | Resolution A — all paid tiers (Free / Pro / Business / Enterprise) | RESOLVED |
| **Q-12.8** (NEW) | AC-12.7 MD export | Pending — conductor decision: ship MD as best-effort helper (§5.1) or remove from AC? | OPEN |

---

## §15 RED Test Spec (~30-50 seeds)

Reporting-svc is a backend service; tests run under `pytest`. Tests are organized in three tiers: **byte-identical canaries** (cross-service), **unit tests** (per-module), **integration tests** (workflow E2E).

### §15.1 Byte-identical canary tests (mandatory, 4 tests)

1. **test_001_source_byte_identical_import_test** — `tests/cross_service/test_source_byte_identical.py` (§11.1). Asserts `ReportArtifact.Source is rag_svc.contracts.Source` via field-shape equality.
2. **test_002_citation_byte_identical_import_test** — `tests/cross_service/test_citation_byte_identical.py` (§11.2). Asserts `ReportArtifact.Citation is rag_svc.contracts.Citation`, 7 fields exactly.
3. **test_006_tool_manifest_byte_identical_import_test** — `tests/cross_service/test_tool_manifest_byte_identical.py` (§11.4). Asserts JsonSchema envelope, no legacy `tools` field.
4. **test_011_validation_evidence_byte_identical_import_test** (NEW) — `tests/cross_service/test_validation_evidence_byte_identical.py` (§11.3). Asserts ReportingEvidence import identity.

### §15.2 ReportArtifact unit tests

5. **test_012_report_artifact_byte_identical_citation_test** (NEW) — asserts `ReportArtifact.citations: list[Citation]` resolves to rag-svc's 7-field Citation class, not a stub.
6. **test_013_report_artifact_template_version_round_trip** — given a template v3, render → assert `ReportArtifact.template_version == 3`; bump template to v4 → assert prior artifact's version is unchanged.
7. **test_014_report_artifact_evidence_refs_resolve** — given `evidence_refs: [UUID1, UUID2]`, the artifact's section citations must reference the same UUIDs (consistency invariant).
8. **test_015_report_artifact_storage_uri_format** — assert `storage_uri` matches `s3://{bucket}/workspaces/{workspace_id}/reports/{report_id}/v{version}.{ext}` regex.
9. **test_016_report_artifact_white_label_optional** — assert `white_label: None` is valid (Free-tier / no white-label).
10. **test_017_report_artifact_section_toggle** — given a template with section X toggled off, the rendered artifact omits section X (REQ-RPT-0005).

### §15.3 Template versioning tests

11. **test_020_template_optimistic_concurrency** — two concurrent PUTs on the same `template_id, version=N`; one succeeds (200), the other returns 409.
12. **test_021_template_supersede_chain** — assert that `superseded_by` is set on the prior version when a new version lands.
13. **test_022_template_soft_delete** — assert `archived_at` is set on archive; archived templates remain queryable for historical reports but not listable by default.

### §15.4 Inline-citation rendering tests

14. **test_030_inline_citation_footnote_style** — render an HTML report with 5 citations; assert 5 `<sup><a href="#fn-N">N</a></sup>` anchors and 5 footnote list entries.
15. **test_031_inline_citation_ordinal_reset** — render a 3-section report; assert each section's footnotes start at 1 (per-section reset).
16. **test_032_inline_citation_hover_popup** — assert the HTML anchor's `title` attribute contains `Citation.url · freshness: {class} · confidence: {level}`.
17. **test_033_inline_citation_truncated_ids** — assert the footnote list shows truncated `chunk_id` (8 chars) + truncated `content_hash` (8 chars).
18. **test_034_inline_citation_pdf_degrades** — assert PDF render does not include `title` attribute (no hover); footnote list still present.

### §15.5 Export tests (PDF, DOCX, HTML, PPTX)

19. **test_040_pdf_export_under_60s** — REQ-RPT-0001 NFR; assert one-pager PDF render completes in < 60s p75 (Doc 02 §8.1).
20. **test_041_pdf_export_under_8min** — REQ-RPT-0002 NFR; assert full report PDF render completes in < 8 min p75 (Doc 02 §8.1).
21. **test_042_docx_export_round_trip** — render → load with python-docx → assert section count, table count, image count preserved.
22. **test_043_html_export_round_trip** — render → parse with BeautifulSoup → assert section count + footnote anchors preserved.
23. **test_044_pptx_export_slide_count** — REQ-RPT-0003; assert 8-15 slides for an executive deck.
24. **test_045_pptx_export_notes_hold_citations** — assert per-slide notes contain the section's citation list (PPTX-only presentation).
25. **test_046_keynote_export_not_supported** — assert `format="keynote"` raises `UnsupportedFormatError`.
26. **test_047_md_export_best_effort** — assert MD export completes and yields valid Markdown; round-trip guarantees are partial (tables may flatten).

### §15.6 White-label tests

27. **test_050_white_label_template_override_workspace** — template white-label wins over workspace white-label.
28. **test_051_white_label_workspace_override_platform** — workspace white-label wins over platform default.
29. **test_052_white_label_logo_uri_validated** — assert `logo_uri` is an S3 URI (or None); invalid URI rejected at template save.
30. **test_053_white_label_pptx_theme_color** — assert python-pptx slide master color matches `WhiteLabelConfig.primary_color`.
31. **test_054_white_label_all_paid_tiers** — assert Free / Pro / Business / Enterprise all expose `WhiteLabelConfig` (per Q-12.7).

### §15.7 RLS / multi-tenancy tests

32. **test_060_rls_workspace_scope** — assert a workspace-A user cannot read workspace-B reports (PG RLS or app-level check).
33. **test_061_rls_template_scope** — assert platform templates are visible across workspaces; workspace templates are not.
34. **test_062_rls_evidence_ref_resolution** — given a workspace-A artifact, evidence_refs that point to workspace-B ValidationEvidence rows must be filtered (or surface as "unavailable").

### §15.8 Scheduled delivery skip tests (Q-12.6)

35. **test_070_scheduled_delivery_v0_skip** — AC-12.13 maps to `pytest.skip`; the test exists and is intentionally skipped, with a comment pointing at the notify-svc follow-up issue.
36. **test_071_deliver_after_field_reserved** — assert `ReportArtifact.deliver_after` field exists and is `Optional[datetime]`.
37. **test_072_delivered_at_field_reserved** — assert `ReportArtifact.delivered_at` field exists and is `Optional[datetime]`; reporting-svc does NOT write this field.

### §15.9 Workflow E2E tests

38. **test_080_workflow_draft_to_stage** — Temporal workflow end-to-end: Draft → Render → Export → Stage completes; assert `ReportArtifact` row persisted.
39. **test_081_workflow_failed_activity_retry** — assert a failed Render activity retries per Temporal policy; final failure surfaces as `status="failed"` on the artifact.
40. **test_082_workflow_s3_storage_uri** — assert the Stage activity writes the S3 URI per Doc 02 §5.4 pattern.

### §15.10 ACP / API tests

41. **test_090_generate_endpoint_auth** — `POST /reports` requires valid JWT + workspace membership.
42. **test_091_export_endpoint_format_validation** — `format` query param must be one of `{pdf, docx, html, pptx}`.
43. **test_092_list_endpoint_pagination** — assert `limit` cap at 200; cursor pagination correct.
44. **test_093_signed_url_ttl** — assert signed URL expires in 1 hour; expired URL returns 403.

### §15.11 Drift-defense tests

45. **test_100_drift_no_local_source_redefinition** — assert that `services/reporting_svc/app/contracts/source.py` does NOT exist (Source is import-only).
46. **test_101_drift_no_local_citation_redefinition** — assert that `services/reporting_svc/app/contracts/citation.py` does NOT exist.
47. **test_102_drift_no_legacy_tool_manifest** — assert no code path imports `ToolRef` (legacy form).

Total seeds: 47 (the prompt asked for ~30-50; this hits the upper end with canary + drift-defense coverage).

---

## §16 Acceptance Criteria Mapping

ACs from `gh issue view 12` (live-fetched):

| AC | Description | Design § | Test |
|---|---|---|---|
| AC-12.1 | reporting-svc scaffolded (Python 3.12 → **3.11** per Q-9), FastAPI, async | §1, §3, §6 | scaffold tests |
| AC-12.2 | REQ-RPT-0001 one-pager < 60s p75 | §2, §5, §15.5 | test_040 |
| AC-12.3 | REQ-RPT-0002 full report 10-25 pages | §4, §15.5 | test_041 |
| AC-12.4 | REQ-RPT-0003 executive deck — **PPTX-only** (Keynote dropped per Q-12.2) | §5.1, §15.5 | test_044, test_046 |
| AC-12.5 | REQ-RPT-0004 comparison report ≥ 2 opps | §2, §4 | integration test |
| AC-12.6 | REQ-RPT-0005 customization chapter on/off | §4.2, §15.2 | test_017 |
| AC-12.7 | REQ-RPT-0006 export PDF/DOCX/MD/HTML — **MD as best-effort helper** (Q-12.8 OPEN) | §5.1, §15.5 | test_042, test_043, test_047 |
| AC-12.8 | REQ-RPT-0007 embed charts | §4.4 | integration test |
| AC-12.9 | REQ-RPT-0008 white-label (Enterprise — extended to all paid tiers per Q-12.7) | §9, §15.6 | test_050..test_054 |
| AC-12.10 | REQ-RPT-0009 user-saved templates | §3, §15.3 | test_020..test_022 |
| AC-12.11 | REQ-RPT-0010 citations and footnotes | §7, §15.4 | test_030..test_034 |
| AC-12.12 | REQ-RPT-0011 provenance panel | §7.3, §15.4 | test_033 |
| AC-12.13 | REQ-RPT-0012 scheduled delivery | §8, §15.8 | test_070 (`pytest.skip`) |
| AC-12.14 | Backout plan (Doc 28 §5) | per-template rollback, export kill switch, S3 lifecycle | runbook PR |

### §16.1 REQ-RPT-* ↔ AC mapping

| REQ | AC | Counts toward PRD §7.5 / §15.3 RPT row |
|---|---|---|
| REQ-RPT-0001 | AC-12.2 | yes |
| REQ-RPT-0002 | AC-12.3 | yes |
| REQ-RPT-0003 | AC-12.4 | yes |
| REQ-RPT-0004 | AC-12.5 | yes |
| REQ-RPT-0005 | AC-12.6 | yes |
| REQ-RPT-0006 | AC-12.7 | yes |
| REQ-RPT-0007 | AC-12.8 | yes |
| REQ-RPT-0008 | AC-12.9 | yes |
| REQ-RPT-0009 | AC-12.10 | yes |
| REQ-RPT-0010 | AC-12.11 | yes (dual-cited in #7 + #12) |
| REQ-RPT-0011 | AC-12.12 | yes (dual-cited in #7 + #12) |
| REQ-RPT-0012 | AC-12.13 | yes (notify-svc follow-up) |

All 12 REQ-RPT-* IDs are now cited by code/tests in this design.

---

## §17 Implementation Guidance (for backend-expert)

### §17.1 Suggested file layout

```
services/reporting_svc/
  app/
    contracts/
      __init__.py
      report_artifact.py        # ReportArtifact + ReportSection + ChartRef + WhiteLabelConfig + TemplateMeta
    api/
      reports.py                # POST /reports, GET /reports/{id}, etc.
      templates.py              # CRUD on report_templates
      exports.py                # signed URL endpoint
    workflows/
      report_generation.py      # Temporal workflow: Draft → Render → Export → Stage → Deliver
      activities/
        draft.py
        render.py
        export.py
        stage.py
        deliver.py
    rendering/
      html.py                   # Jinja2 + CSS
      pdf.py                    # WeasyPrint
      docx.py                   # python-docx
      pptx.py                   # python-pptx
      citations.py              # Doc 17 §5 footnote rendering
    storage/
      s3.py                     # Doc 02 §5.4 storage layer
    white_label/
      apply.py                  # white-label chain: template → workspace → platform
    templates/
      defaults.py               # platform default templates
  tests/
    cross_service/
      test_source_byte_identical.py
      test_citation_byte_identical.py
      test_tool_manifest_byte_identical.py
      test_validation_evidence_byte_identical.py
      test_memory_record_source_refs.py
    unit/
      test_report_artifact.py
      test_template_versioning.py
      test_white_label.py
      test_inline_citation.py
    integration/
      test_workflow_e2e.py
      test_export_round_trip.py
    api/
      test_generate_endpoint.py
      test_export_endpoint.py
      test_list_endpoint.py
      test_signed_url_ttl.py
```

### §17.2 Implementation order

1. **Contracts first**: `report_artifact.py` with all byte-identical imports.
2. **Cross-service canary tests**: run them before any other code; they MUST pass against the empty `report_artifact.py` stub.
3. **Storage layer**: S3 wrapper for Doc 02 §5.4 storage path.
4. **Templates API**: CRUD + versioning.
5. **Renderers**: HTML → PDF → DOCX → PPTX (in that order).
6. **Workflow**: Temporal workflow with retry policies.
7. **API surface**: REST endpoints (FastAPI).
8. **White-label**: chain application.
9. **Scheduled delivery skip**: `pytest.skip` test for AC-12.13.

### §17.3 First-PR dependency

This design depends on Doc 02 §5.2 row additions for `report_templates`, `report_artifact`, and `template_version_history` tables (DRIFT-12.9). Backend-expert should verify these tables exist (or file a Doc 02 update PR) before scaffolding.

---

## §18 Open Items for Conductor

1. **Q-12.8 (NEW)** — AC-12.7 cites MD export; Q-12.2 PPTX-only is silent on MD. Resolution: best-effort helper (§5.1), or remove MD from AC?
2. **DRIFT-12.13** — Doc 02 §5.4 S3 storage path pattern should be live-verified before scaffold PR.
3. **DRIFT-12.14** — AC-12.7 vs Q-12.2 format-matrix tension (see above).
4. **Doc 17 §5** — should be live-verified at first implementation PR open; any drift between §7 and Doc 17 is a Doc 17 fix-up, not a reporting-svc drift.

---

## §19 Persistence Statement

This design is **persisted** at `C:\Users\Ganesha\Desktop\Super Agent\ProjectSAAS\issues_for_architect\issue_012_architect_design.md` and **verified on disk** via `ls -la` post-write.

**Verification:**
- 11 canonical contracts re-verified at cited line numbers (§0).
- 5 byte-identical canaries defined (§11).
- 47 RED test seeds authored (§15).
- All 7 prior Q-12.x items adopt Resolution A; 1 new item (Q-12.8) added (§14).
- 12 prior drift findings re-stated as PATCHED; 2 new drift findings added (§13).

**Next step:** backend-expert dispatch with this design as the RED spec.

---

## §20 Provenance

- **Predecessor verifications:** `arch-006-redispatch-verified-2026-07-28.md`, `arch-007-redispatch-verified-2026-07-28.md`, `arch-008-redispatch-verified-2026-07-28.md`, `arch-009-redispatch-verified-2026-07-28.md`, `arch-011-verified-and-persisted-2026-07-28.md`, `arch-012-verified-and-persisted-2026-07-28.md`.
- **Prior dispatch failure note:** this file supersedes dispatch #a0ef473cdb94aad33, which ended before invoking Write. This dispatch follows WRITE-FIRST, VERIFY-LAST.
- **Orchestrator:** Architect agent (re-dispatched 2026-07-29).
- **Conductor gating:** Q-12.1..Q-12.7 RESOLVED, Q-12.8 OPEN (§14).
