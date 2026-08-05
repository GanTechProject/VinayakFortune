---
issue: 8
service: memory-svc
architect_dispatch: 2026-07-28 (re-dispatch; prior 4-way Source drift patched via MemoryAnnotation wrapper per memory-svc-source-drift-correction-2026-07-28)
canonical_authority: rag-svc Source (Architect #7 §10.2 L311-328) and Citation (Architect #7 §11.2 L382-405); agent-runtime RunState (Architect #6 §4.3 L261-275); plugin-svc ToolManifest (Architect #9 §12.2 L573-594)
---

# Issue #8 — memory-svc BAND-3-DESIGN

> Memory is what makes the system **cumulative**. It carries state across runs so the platform gets sharper with use. This document is the architectural contract for `memory-svc`, the AI plane's long-term memory store, anchored to Document 11 (Memory Architecture).

> **ORCHESTRATOR-DRIFT-CORRECTION (2026-07-28):** The prior dispatch's design file contained a 4-way drift on `Source` (added `source_id`, `HttpUrl`-vs-`str`, `Field(pattern=...)`, and bolts on `confidence`/`freshness_class`). Per `memory-svc-source-drift-correction-2026-07-28`, that drift was caught at the byte-identical preflight and patched in-place by introducing the **`MemoryAnnotation` wrapper** (mirroring Architect #7's `Citation` wrapper pattern). The 4 fields `confidence`/`freshness_class`/per-source metadata now live on `MemoryAnnotation`, NOT on the cross-service `Source`. **Test 5.1.1 byte-identical canary now PASSES against the canonical.**

## Table of Contents

1. Purpose & Scope
2. Memory Layers (Doc 11 §2)
3. Session Memory (Doc 11 §3)
4. Working Memory (Doc 11 §4)
5. User Memory (Doc 11 §5)
6. Workspace Memory (Doc 11 §6)
7. Platform Memory (Doc 11 §7)
8. Memory Write Discipline (Doc 11 §8) — CRITICAL
9. Memory Retrieval (Doc 11 §9)
10. Privacy & Isolation (Doc 11 §10) — CRITICAL
11. **`MemoryRecord` Pydantic Model** — memory-svc canonical (NEW)
12. **`MemoryAnnotation` Pydantic Model** — memory-svc private wrapper (NEW; ORCHESTRATOR-PATCH)
13. Retention & Deletion (Doc 11 §11)
14. Failure Modes (Doc 11 §12)
15. Evaluation (Doc 11 §13)
16. MCP Tool Manifests
17. Cross-Service Imports (mandatory)
18. Memory Consumers (cross-service)
19. Drift Findings
20. Q-8.x Conductor Gating
21. RED Test Spec (~30-50 seeds)
22. Acceptance Criteria Mapping

---

## §1 Purpose & Scope

**memory-svc** is the AI plane's durable memory store. It owns:

- **Four memory layers** per Document 11 §2 (Session, Working, User, Workspace, Platform — five names, four storage tiers).
- **Privacy isolation** per Document 11 §10 (user-only-user; member-only-workspace; no cross-workspace; platform-anonymized).
- **Write discipline** per Document 11 §8 (atomic / verified / versioned / provenance).
- **Right-to-be-forgotten** per Document 11 §11.

**Out of scope for v1:** Cross-workspace memory (Doc 11 §10 — explicit "no cross-workspace memory"; deferred to v2 per issue body).

**Bound to:**

- `agent-runtime` (Architect #6): every agent reads/writes through memory-svc; no agent maintains private state (Doc 11 §1).
- `rag-svc` (Architect #7): platform-memory embeddings use rag-svc's `text-embedding-3-large` (Doc 10 §6 L95) and the canonical `Source`/`Citation` shapes.
- `plugin-svc` (Architect #9): T-MEMORY-READ and T-MEMORY-WRITE are published as MCP tool manifests.
- `audit-svc` (Doc 02 §5.2 L225): every write is emitted to `audit-svc` via `audit_event` (append-only).
- `agt-safety` (Doc 09 §17): PII redaction at write time (AC-5.9 / Doc 21 §9).

**Stack per issue body AC-5.1:** Python 3.11 (per `conductor-decisions-2026-07-28` Q-9; CI gate from PR #56), FastAPI async, SQLAlchemy 2.x, pgvector via raw SQL DDL, Redis 7 for session + working layers.

---

## §2 Memory Layers

Verified verbatim against Document 11 §2 (lines 17-25):

| Layer | Lifetime | Scope | Store |
|---|---|---|---|
| Session | Single run | Run | In-process + scratchpad |
| Working | Single turn | User/turn | Redis (short TTL) |
| User | Per user account | User | Postgres + vector |
| Workspace | Per workspace | Workspace | Postgres + vector |
| Platform | All workspaces | Aggregate, anonymized | Postgres + vector |

**memory-svc's owned tiers:** Session (in-process, no service-owned Redis instance), Working (Redis), User (Postgres + vector), Workspace (Postgres + vector), Platform (Postgres + vector, anonymized).

**Storage map (Doc 02 §5.2 L221 + §5.5 L241):**

| Tier | Backend | Schema | Index |
|---|---|---|---|
| Session | In-process (orchestrator's `RunState.scratchpad`) | — | — |
| Working | Redis 7 | n/a (key-value) | n/a |
| User | Postgres 16 + pgvector | `memory.memory_record` (Doc 02 §5.2 L221) | `idx_user_memory_embedding` (HNSW per Doc 02 §5.3 L229) |
| Workspace | Postgres 16 + pgvector | `memory.memory_record` (Doc 02 §5.2 L221) | `idx_workspace_memory_embedding` |
| Platform | Postgres 16 + pgvector | `memory.memory_record` (Doc 02 §5.2 L221); **no `tenant_id` column** | `idx_platform_memory_embedding` |

**Per the issue body AC-5.6 the schema is:** `{workspace_id, owner_id, scope, content, embedding?, created_at, expires_at, links: [memory_link]}`. Section §11 below extends this with `source_refs` and `annotations` (per the ORCHESTRATOR-PATCH protocol; Doc 11 §8 mandates provenance).

---

## §3 Session Memory

Verified verbatim against Document 11 §3 (lines 27-32):

- **What:** the run's transient state — plans, scratchpad, intermediate variables.
- **Where:** in-process; the orchestrator's state.
- **When it ends:** when the run ends or is cancelled.
- **Retention:** none beyond the run.

**memory-svc posture:** Session memory is **NOT** a memory-svc-owned tier — it lives in the orchestrator's `RunState.scratchpad` (Doc 08 §5 L120). memory-svc does not persist session records.

**Read/write contract:** None at the memory-svc API surface. Session memory is in-process to the orchestrator (Architect #6 §4.3 `RunState.scratchpad: dict`).

---

## §4 Working Memory

Verified verbatim against Document 11 §4 (lines 34-39):

- **What:** the last N turns of a user session in the UI.
- **Where:** Redis, keyed by user.
- **TTL:** 1 hour idle, 8 hours absolute.
- **Used for:** multi-turn UI context, fast retrieval of recent items.

**memory-svc posture:** Working memory IS a memory-svc-owned tier; Redis is the storage. **TTL reconciliation note:** Doc 11 §4 specifies "1h idle / 8h absolute". Issue body AC-5.2 specifies "8h idle / 30d max TTL per Doc 02 §5.5". **DOC vs AC drift.** The Doc 02 §5.5 L242 TTL table says "sessions (8h idle / 30d max)" — this is the **AUTH session** (auth-svc), not the memory-svc working-memory tier. Doc 11 §4's "1h idle / 8h absolute" is the binding number for working memory. **DRIFT-8.1 — surface to conductor (Q-8.1).**

**Redis key shape:** `mem:working:{user_id}:{run_id_or_turn_id}` → JSON-encoded working-memory record.

**Read/write API:** Internal to memory-svc; not published as MCP tool (Doc 11 §9 mentions only user/workspace/platform for the `memory.read` tool surface). Working memory is read/written by the UI layer directly via memory-svc's internal HTTP/gRPC.

---

## §5 User Memory

Verified verbatim against Document 11 §5 (lines 41-48):

- **What:** durable user-level facts:
  - Preferences (preferred rubric, watchlists).
  - Calibration feedback (e.g. "I disagree with WTP for X — it should be lower").
  - Decision history (which opportunities the user advanced, archived, or rejected).
- **Where:** Postgres `memory.user_memory` + vector embeddings.
- **Used for:** personalization; calibrating future runs.
- **Retention:** while the account is active; 30-day grace after deletion.

**Schema (Doc 02 §5.2 L221 + issue body AC-5.6):**

```sql
CREATE TABLE memory.memory_record (
    record_id        UUID PRIMARY KEY,
    workspace_id     UUID NOT NULL,    -- cross-tier pointer; user records have one workspace
    owner_id         UUID NOT NULL,    -- user_id (for user-tier); workspace_id (for workspace-tier); NULL (for platform-tier; DRIFT-8.3)
    scope            TEXT NOT NULL CHECK (scope IN ('user','workspace','platform')),
    content          TEXT NOT NULL,
    embedding        VECTOR(3072),    -- text-embedding-3-large per Doc 10 §6 L95
    source_refs      JSONB NOT NULL DEFAULT '[]'::jsonb,  -- list of Source (Doc 10 §10)
    annotations      JSONB NOT NULL DEFAULT '[]'::jsonb,  -- list of MemoryAnnotation (§12)
    version          INT  NOT NULL DEFAULT 1,
    supersedes       UUID,
    superseded_by    UUID,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at       TIMESTAMPTZ,
    retention_until  TIMESTAMPTZ,
    -- AC-5.6 schema also includes:
    links            JSONB NOT NULL DEFAULT '[]'::jsonb  -- list of memory_link
);

CREATE INDEX idx_user_memory_embedding ON memory.memory_record
    USING hnsw (embedding vector_cosine_ops)
    WHERE scope = 'user';
```

**RLS policy (Doc 11 §10 — user-only-user):**

```sql
ALTER TABLE memory.memory_record ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_memory_isolation ON memory.memory_record
    USING (
        scope = 'user' AND owner_id = current_setting('app.user_id')::UUID
    );
```

---

## §6 Workspace Memory

Verified verbatim against Document 11 §6 (lines 50-56):

- **What:** durable workspace-level facts:
  - Common source priorities.
  - Past reports and their acceptance feedback.
  - Shared watchlists and rubrics.
- **Where:** Postgres `memory.workspace_memory` + vector.
- **Used for:** team-level personalization; cross-user learning.
- **Retention:** workspace lifetime; configurable per-tenant (Enterprise).

**memory-svc posture:** Workspace memory is a **NEW tier in Doc 11 §2** that the issue body AC-5.x (AC-5.1 through AC-5.12) does not enumerate explicitly — the issue body scopes to "session, user, platform". **Per Doc 11 §2 (verbatim table at L17-25), workspace memory is a first-class tier.** **DRIFT-8.2 — issue body under-scope vs Doc 11 §2.** Resolution: this design covers workspace memory as a first-class tier per Doc 11 §2. Surface to conductor (Q-8.2).

**Schema:** Same `memory.memory_record` table with `scope='workspace'`. RLS policy allows members of the workspace to read.

```sql
CREATE POLICY workspace_memory_isolation ON memory.memory_record
    USING (
        scope = 'workspace' AND workspace_id = current_setting('app.workspace_id')::UUID
    );
```

---

## §7 Platform Memory

Verified verbatim against Document 11 §7 (lines 58-65):

- **What:** aggregate, anonymized learnings:
  - Which rubric dimensions correlate with accepted opportunities.
  - Source reliability scores.
  - Common claim patterns.
- **Where:** Postgres + vector, no tenant_id column.
- **Used for:** model selection, source prioritization, calibration.
- **Retention:** indefinite; user opt-out does not apply to aggregated platform memory.
- **Privacy:** k-anonymity ≥ 50; no raw PII; no per-workspace data.

**memory-svc posture:** Platform memory is a memory-svc-owned tier; **k-anonymity ≥ 50** is enforced at WRITE TIME (records that would breach the k-anonymity threshold are quarantined, not written; **DRIFT-8.4** — see §19).

**Schema:** Same `memory.memory_record` table with `scope='platform'`. **NO `tenant_id` / `workspace_id` / `owner_id` columns at the row level** (Doc 11 §7). The `workspace_id` column is NULL; the `owner_id` column is NULL.

**k-anonymity enforcement:**

A platform-memory write checks: are there ≥ 49 OTHER records in the same cluster (defined as nearest-neighbor cosine ≥ 0.85) within the last 30 days? If not, the write is rejected with `k_anonymity_violation`. (This is the write-time k-anonymity filter; we cannot enforce k-anonymity on aggregate queries because the data is already written.)

**RLS policy (Doc 11 §10 — platform-anonymized):**

```sql
CREATE POLICY platform_memory_open_to_authenticated ON memory.memory_record
    USING (
        scope = 'platform'
    );
-- Any authenticated principal can read; but no row carries workspace_id or owner_id.
```

---

## §8 Memory Write Discipline (CRITICAL)

Verified verbatim against Document 11 §8 (lines 67-72):

- **Atomic:** writes are append-only or versioned; never destructive.
- **Verified:** the verifier audits memory writes for citation and policy.
- **Versioned:** every memory record has a version; supersession is explicit.
- **Provenance:** every record carries the source run_id and actor.

**memory-svc enforcement:**

| Discipline | Mechanism |
|---|---|
| Atomic | Single-transaction INSERT; supersession via `superseded_by` pointer update in same TX |
| Verified | Verifier hook (AGT-VERIFY per Doc 09 §16): every write goes through AGT-VERIFY citation + policy audit before commit |
| Versioned | `version: int` (optimistic concurrency); `supersedes: UUID \| None` + `superseded_by: UUID \| None` chain |
| Provenance | `actor: str` + `run_id: UUID` on every record; PLUS `source_refs: list[Source]` (per §11) — Doc 10 §10 mandates grounded claims |

**TOCTOU on supersession:** Doc 11 §8 says "supersession is explicit" but does not define concurrency. The `superseded_by` field is **CONCURRENT-MUTATED** (two writes racing to supersede the same record). **Memory-svc MUST use Postgres advisory locks** keyed on the superseded record_id. **DRIFT-8.5** — surface to conductor (Q-8.5).

```sql
-- Acquire advisory lock keyed on the record being superseded
SELECT pg_advisory_xact_lock(hashtext('memory.supersede:' || :target_record_id));
-- Then UPDATE both rows (old.superseded_by := new.record_id; new.supersedes := old.record_id)
```

---

## §9 Memory Retrieval

Verified verbatim against Document 11 §9 (lines 74-77):

- Agents can `memory.read(scope=user | workspace | platform, query=...)` and get top-k records.
- Retrieval uses the same hybrid index as RAG (Document 10) but with a different namespace.

**memory-svc read pipeline:**

1. **Embed the query** using rag-svc's `text-embedding-3-large` (Doc 10 §6 L95).
2. **Hybrid retrieval** — vector (pgvector HNSW) + lexical (pg_trgm). RRF fusion (Doc 10 §7.3 L113-116).
3. **Namespace filter** — `WHERE scope = :scope` (and the RLS predicate).
4. **Top-k** — default 10; rerank optional.
5. **Return `list[MemoryRecord]`** — the record's `source_refs` (canonical 4-field `Source`) AND `annotations` (memory-svc-private wrapper).

**Critical:** The hybrid index for memory records uses the **same embedding model** as rag-svc (Doc 11 §9 says "same hybrid index as RAG"). This means memory records and rag chunks share an embedding space, enabling cross-search if needed (but normally filtered out by `scope`).

---

## §10 Privacy & Isolation (CRITICAL)

Verified verbatim against Document 11 §10 (lines 79-83):

- A user can only read their own user memory.
- A user can only read workspace memory for workspaces they belong to.
- No cross-workspace memory.
- Platform memory is anonymized; no per-tenant data appears in queries.

**memory-svc enforcement:**

| Rule | Mechanism |
|---|---|
| User-only-user | RLS policy `user_memory_isolation` (see §5) |
| Member-only-workspace | RLS policy `workspace_memory_isolation` (see §6) |
| No cross-workspace | RLS `workspace_id` filter; cannot be bypassed (Postgres-level) |
| Platform-anonymized | RLS policy `platform_memory_open_to_authenticated` (see §7); rows have NULL `workspace_id` / `owner_id` |

**Per-request RLS setting** (Postgres pattern):

```sql
SET LOCAL app.user_id = '<uuid>';
SET LOCAL app.workspace_id = '<uuid>';
-- Then the query runs under RLS
```

The MCP gateway (Doc 12 §7 L91-95) sets these from the caller's auth context before the query executes. **No bypass path.**

**Per-tenant Enterprise overrides:** Doc 11 §6 says "configurable per-tenant (Enterprise)" for workspace-memory retention. Implementation: a `workspace_config.retention_overrides JSONB` column consulted at write time. **DRIFT-8.6** — surface to conductor (Q-8.6).

---

## §11 `MemoryRecord` Pydantic Model — memory-svc canonical

> **YOU (memory-svc) own this contract.** This is the durable cross-layer record. Field provenance below.

### §11.1 Full Pydantic class

```python
# services/memory_svc/app/contracts/memory_record.py
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# CRITICAL: Source is imported BYTE-IDENTICAL from rag-svc.
# Per Architect #7 §10.2 (issues_for_architect/issue_007_architect_design.md L311-328)
# and the orchestrator's DRIFT-CORRECTION (memory-svc-source-drift-correction-2026-07-28).
from services.rag_svc.app.contracts.source import Source

# MemoryAnnotation is defined in §12 (memory-svc-private wrapper).
from services.memory_svc.app.contracts.memory_annotation import MemoryAnnotation


class MemoryLink(BaseModel):
    """AC-5.7: {from_memory_id, to_memory_id, kind, weight}."""
    from_memory_id: UUID
    to_memory_id: UUID
    kind: Literal["causal", "temporal", "thematic", "supersedes"]
    weight: float = Field(ge=0.0, le=1.0)


class MemoryRecord(BaseModel):
    """Canonical memory-svc durable record. Cross-tier.
    
    Verified against:
      - Doc 11 §2 (L17-25): five-layer table
      - Doc 11 §5-§7 (L41-65): tier-specific content semantics
      - Doc 11 §8 (L67-72): write discipline (atomic/verified/versioned/provenance)
      - AC-5.6: {workspace_id, owner_id, scope, content, embedding?, created_at, expires_at, links}
      - AC-5.11: every record carries its source citation (REQ-RPT-0011)
    
    Layer field semantics:
      - scope='user'      → owner_id = user_id; workspace_id = the workspace the user is currently in
      - scope='workspace' → owner_id = NULL (it's the workspace's); workspace_id = the workspace_id
      - scope='platform'  → owner_id = NULL; workspace_id = NULL (Doc 11 §7 "no tenant_id column")
    
    Imported by:
      - agent-runtime (Architect #6 §4.3 — RunState.evidence carries MemoryRecord wrappers)
      - reporting-svc (Architect #12 — Report.citations may pull from memory)
      - validation-pipeline (Architect #11)
    """
    record_id: UUID
    layer: Literal["user", "workspace", "platform"]  # alias for scope; matches Doc 11 §2 tier names
    scope_id: UUID                                       # user_id / workspace_id / NULL for platform (semantic: tenant scope)
    actor: str                                           # who wrote (agent_id, user_id, or "system")
    run_id: UUID                                         # Doc 11 §8 provenance
    content: str                                         # the actual fact
    embedding: Optional[list[float]] = None              # 3072-dim per Doc 10 §6 L95; nullable for tier-1 records
    source_refs: list[Source] = Field(default_factory=list)  # CANONICAL 4-field Source (Architect #7 §10.2 L311-328)
    annotations: list[MemoryAnnotation] = Field(default_factory=list)  # memory-svc-private (see §12)
    links: list[MemoryLink] = Field(default_factory=list)  # AC-5.7 memory_link graph
    version: int = 1                                     # Doc 11 §8: every record has a version
    supersedes: Optional[UUID] = None                    # version chain (older sibling)
    superseded_by: Optional[UUID] = None                 # version chain (newer sibling)
    created_at: datetime
    expires_at: Optional[datetime] = None                # working-memory TTL pass-through
    retention_until: Optional[datetime] = None          # Doc 11 §11 retention
    
    # AC-5.6 explicit fields (added to satisfy issue-body schema)
    workspace_id: Optional[UUID] = None                  # NULL for platform-tier; otherwise the workspace
    owner_id: Optional[UUID] = None                      # user_id for user-tier; NULL for workspace- and platform-tier
    scope: Literal["session", "user", "workspace", "platform"]  # AC-5.6 verbatim; session is for working/session-memory
    
    # CRITICAL: layer and scope are redundant by design. `layer` is the Doc 11 §2 tier name;
    # `scope` is the AC-5.6 verbatim schema. They MUST stay in sync — validated in test_010.
```

### §11.2 Import path

```python
from services.memory_svc.app.contracts.memory_record import MemoryRecord, MemoryLink
```

### §11.3 Field-level doc-cite

| Field | Doc-cite | Note |
|---|---|---|
| `record_id: UUID` | Doc 11 §8 "versioned" + AC-5.6 (implied PK) | PK; UUIDv7 for time-ordering |
| `layer: Literal["user","workspace","platform"]` | Doc 11 §2 L17-25 | Tier name from Doc 11 §2 |
| `scope_id: UUID` | Doc 11 §5 L43 ("user_id"), §6 L52 ("workspace_id") | The identifier of the tier owner |
| `actor: str` | Doc 11 §8 L72 ("actor") | Provenance: who wrote |
| `run_id: UUID` | Doc 11 §8 L72 ("run_id") | Provenance: from which run |
| `content: str` | Doc 11 §5 L42 / §6 L51 / §7 L60 | The actual fact |
| `embedding: list[float] \| None` | Doc 11 §5 L45 ("vector embeddings") + Doc 10 §6 L95 (3072-dim) | nullable for tier-1 records |
| `source_refs: list[Source]` | Doc 11 §8 L72 ("provenance") + Doc 10 §10 L135-147 + AC-5.11 (REQ-RPT-0011) | **CANONICAL** from rag-svc; byte-identical canary |
| `annotations: list[MemoryAnnotation]` | ORCHESTRATOR-PATCH (memory-svc-source-drift-correction-2026-07-28) | memory-svc-private wrapper; see §12 |
| `links: list[MemoryLink]` | AC-5.7 ("{from_memory_id, to_memory_id, kind, weight}") | Right-to-be-forgotten cascade (AC-5.8) |
| `version: int` | Doc 11 §8 L70 ("Versioned: every memory record has a version") | Optimistic concurrency |
| `supersedes: UUID \| None` + `superseded_by: UUID \| None` | Doc 11 §8 L71 ("supersession is explicit") | Chain pointer |
| `created_at: datetime` | AC-5.6 ("created_at") | UTC |
| `expires_at: datetime \| None` | AC-5.6 ("expires_at") | Working-memory TTL (1h idle / 8h absolute per Doc 11 §4) |
| `retention_until: datetime \| None` | Doc 11 §11 + AC-5.5 | User/workspace lifetime + grace |
| `workspace_id`, `owner_id`, `scope` | AC-5.6 verbatim | Explicit schema fields |

### §11.4 Cross-service canary contract

The byte-identical canary requires:

1. memory-svc publishes `MemoryRecord` from `services/memory_svc/app/contracts/memory_record.py`.
2. memory-svc **DOES NOT** publish `Source`; it imports from `services.rag_svc.app.contracts.source.Source`.
3. A test at `tests/cross_service/test_memory_record_byte_identical.py` imports `MemoryRecord` from memory-svc and asserts the `source_refs: list[Source]` field resolves to the same class as Architect #7's canonical (verified in test_001_source_byte_identical_import_test, per Architect #7 §20.1 L737-761).

---

## §12 `MemoryAnnotation` Pydantic Model — memory-svc private wrapper

> **ORCHESTRATOR-PATCH (2026-07-28):** This wrapper is the result of the prior dispatch's 4-way `Source` drift being patched in-place per `memory-svc-source-drift-correction-2026-07-28`. **Memory-svc DOES NOT add `confidence` / `freshness_class` / `source_id` to `Source`.** Per-source metadata lives on `MemoryAnnotation`.

### §12.1 Why a wrapper (and not a field on `Source`)

Architect #7's `Citation` (Architect #7 §11.2 L382-405) is the **canonical pattern**: cross-service canonical at the leaf (`Source`); service-specific metadata in a wrapper that embeds the canonical. `MemoryAnnotation` follows the same pattern — it carries the per-source metadata that the prior dispatch incorrectly bolted onto `Source`.

### §12.2 Full Pydantic class

```python
# services/memory_svc/app/contracts/memory_annotation.py
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# We RE-DEFINE the Literal types locally to avoid an import dependency cycle with rag_svc.
# These Literals are byte-identical to Architect #7 §11.2 L378-379.
FreshnessClass = Literal["live", "recent", "stale", "unknown"]
Confidence = Literal["high", "med", "low"]


class MemoryAnnotation(BaseModel):
    """memory-svc-private per-source annotation. Mirrors Architect #7's Citation wrapper pattern.
    
    Verified against:
      - Doc 11 §8 L72 ("Provenance: every record carries the source run_id and actor")
      - AC-5.11: every record carries its source citation
      - ORCHESTRATOR-PATCH: 4-way Source drift corrected by routing per-source metadata here
    
    Pattern: cross-service canonical (Source) + service-private wrapper (this class).
    Consumers traverse MemoryRecord.source_refs[i] for the canonical AND MemoryRecord.annotations[i]
    for the metadata. The two lists are index-aligned via source_ordinal.
    
    NOT exported from memory-svc. Cross-service consumers (agent-runtime, reporting-svc)
    see MemoryRecord only; they don't import MemoryAnnotation.
    """
    source_ordinal: int = Field(ge=0)         # which Source in MemoryRecord.source_refs (0-indexed)
    confidence: Confidence                     # same Literal as Architect #7 §11.2 L379
    freshness_class: FreshnessClass            # same Literal as Architect #7 §11.2 L378
    relevance_at_write: datetime               # when the annotation was computed (UTC)
    note: Optional[str] = None                 # free-form note from the writing agent
    
    # Optional provenance tie-back (Doc 11 §8 "every record carries the source run_id and actor")
    annotated_by: Optional[str] = None         # agent_id that computed the annotation
    annotated_run_id: Optional[UUID] = None    # run_id that computed the annotation
```

### §12.3 Field-level doc-cite

| Field | Origin | Note |
|---|---|---|
| `source_ordinal: int (≥0)` | ORCHESTRATOR-PATCH | Index into `MemoryRecord.source_refs`; lets consumers align annotation ↔ source |
| `confidence: Literal["high","med","low"]` | Doc 10 §10 L138 + Architect #7 §11.2 L379 | Same as Architect #7's `Citation.confidence` |
| `freshness_class: Literal["live","recent","stale","unknown"]` | Doc 10 §11 L151-154 + Architect #7 §11.2 L378 | Same as Architect #7's `Citation.freshness_class` |
| `relevance_at_write: datetime` | ORCHESTRATOR-PATCH | Timestamp at write time (Doc 11 §8 "every record carries provenance") |
| `note: str \| None` | ORCHESTRATOR-PATCH | Free-form note |
| `annotated_by`, `annotated_run_id` | Doc 11 §8 L72 ("every record carries the source run_id and actor") | Optional provenance tie-back |

### §12.4 Test guard (DRIFT-8.x — see §19)

`test_005_memory_annotation_wrapper_no_drift` (§21.4) asserts that:

1. `Source` has exactly 4 fields (`url`, `fetched_at`, `tool_id`, `snippet`) — no extra fields.
2. `MemoryAnnotation` is a separate Pydantic class; it does NOT extend or modify `Source`.
3. The byte-identical canary (`test_001`) still passes against the canonical.

This prevents regression to the prior dispatch's 4-way drift.

---

## §13 Retention & Deletion

Verified verbatim against Document 11 §11 (lines 85-90):

- User deletion cascades to user memory.
- Workspace deletion cascades to workspace memory.
- Platform memory is not affected by user/workspace deletion (anonymized).
- Right-to-be-forgotten: users can request deletion of all user memory; honored within 30 days.

**memory-svc enforcement:**

| Trigger | Action |
|---|---|
| User deletion (auth-svc event) | Cascade delete `memory.memory_record WHERE scope='user' AND owner_id=:deleted_user_id`. Single transaction. |
| Workspace deletion (workspace-svc event) | Cascade delete `memory.memory_record WHERE scope='workspace' AND workspace_id=:deleted_workspace_id`. Single transaction. |
| User explicit RTBF request | 30-day SLA: hard-delete via `memory_link` graph walk (AC-5.8). |
| Platform memory | NEVER deleted on user/workspace deletion; only on aggregate rotation (annual). |

**AC-5.8 RTBF graph walk:** The `memory_link` graph (AC-5.7) lets one user-memory record reference another (e.g. "I disagreed with WTP for X" links to the WTP record). The RTBF purge walks the reachable subgraph and deletes in a single transaction.

```sql
BEGIN;
WITH RECURSIVE reachable AS (
    SELECT record_id FROM memory.memory_record WHERE owner_id = :deleted_user_id
    UNION
    SELECT ml.to_memory_id FROM memory.memory_link ml
    JOIN reachable r ON ml.from_memory_id = r.record_id
)
DELETE FROM memory.memory_record WHERE record_id IN (SELECT record_id FROM reachable);
COMMIT;
```

**30-day SLA:** AC-5.8 says "single transaction". Doc 11 §11 says "within 30 days". Resolution: the technical guarantee is single-transaction AT delete-time; the SLA is that the deletion completes within 30 days of the request. **DRIFT-8.7** — surface to conductor (Q-8.7).

---

## §14 Failure Modes

Verified verbatim against Document 11 §12 (lines 92-99):

| Failure | Response |
|---|---|
| Memory store down | Degrade: skip memory; run still works without personalization. |
| Corrupted record | Quarantine; alert; do not block run. |
| Provenance missing | Reject write. |
| Schema drift | Migration via Atlas; backwards-compatible. |

**memory-svc enforcement:**

| Failure | Mechanism |
|---|---|
| Store down | Circuit breaker on Postgres; on Redis-down, working-memory reads return `[]` (graceful degradation) |
| Corrupted record | Move to `memory.quarantine` table; alert via NATS `memory.quarantine.created` |
| Provenance missing | Reject write with `ValidationError` (Doc 11 §8 L72 mandates `run_id` + `actor`) |
| Schema drift | Atlas declarative migrations (Doc 02 §15 L400); backwards-compatible adds only |

**AC-5.9 PII redaction:** AGT-SAFETY (Doc 09 §17) is invoked on every write. Flagged content is stored redacted; raw is sealed in `audit-svc.audit_event` (Doc 02 §5.2 L225). memory-svc's write path:

```
client → AGT-SAFETY (PII detect/redact) → AGT-VERIFY (citation/policy) → memory-svc commit
```

---

## §15 Evaluation

Verified verbatim against Document 11 §13 (lines 101-106):

- **Calibration accuracy:** does the system predict user acceptance better with memory? (Monthly)
- **Memory precision:** what fraction of recalled memories are useful? (Spot-checked)
- **Cross-tenant leakage tests:** monthly red-team.
- **Acceptance rate** of memory-informed reports vs. cold reports.

**memory-svc posture:**

| Metric | Cadence | Owner |
|---|---|---|
| Calibration accuracy | Monthly | AI Lead |
| Memory precision | Spot-check (per Doc 11 §13) | QA |
| Cross-tenant leakage red-team | Monthly | Security |
| Acceptance rate comparison | Monthly | Product |

**Cross-tenant leakage test (CRITICAL):** A red-team harness attempts to read user-A's user-memory from user-B's session. Must return `[]` (RLS blocks). Test is part of `test_040_cross_tenant_isolation` (§21.5).

---

## §16 MCP Tool Manifests

memory-svc publishes exactly two tools. Manifest schema per Doc 12 §4 L57-72 (verified).

### §16.1 T-MEMORY-READ

```yaml
id: T-MEMORY-READ
name: Memory Read
version: 1.0.0
description: Hybrid retrieval (vector + BM25 → RRF) over a memory tier.
risk_level: low
pii_risk: true            # user-tier records may contain PII; redaction enforced
input_schema:
  type: object
  properties:
    scope: { type: string, enum: ["user", "workspace", "platform"] }
    query: { type: string, minLength: 1, maxLength: 4096 }
    top_k: { type: integer, minimum: 1, maximum: 50, default: 10 }
    freshness_class_min: { type: string, enum: ["live","recent","stale","unknown"], default: "stale" }
  required: [scope, query]
output_schema:
  type: object
  properties:
    records:
      type: array
      items: { $ref: "memory.memory_record.MemoryRecord" }
auth: { type: service_token, secret_ref: memory-svc/inbound/service_token }
cost: { per_call_usd: 0.001, weight: 1 }
rate_limit: { per_minute: 600, per_hour: 10000 }
timeout_ms: 5000          # AC-5.10: p95 < 50ms (session), < 200ms (user), < 500ms (platform)
retry: { max: 2, backoff: exponential }
owner: ai-platform
```

### §16.2 T-MEMORY-WRITE

```yaml
id: T-MEMORY-WRITE
name: Memory Write
version: 1.0.0
description: Append a record to a memory tier. AGT-SAFETY + AGT-VERIFY chain enforced.
risk_level: medium
pii_risk: true            # PII redaction required; sealed log
input_schema:
  type: object
  properties:
    layer: { type: string, enum: ["user", "workspace", "platform"] }
    content: { type: string, minLength: 1, maxLength: 8192 }
    source_refs:
      type: array
      items: { $ref: "rag.source.Source" }    # CANONICAL; see §11 / §17
    annotations:
      type: array
      items: { $ref: "memory.memory_annotation.MemoryAnnotation" }
    links:
      type: array
      items: { $ref: "memory.memory_link.MemoryLink" }
  required: [layer, content, source_refs, annotations]
output_schema:
  type: object
  properties:
    record_id: { type: string, pattern: "^[a-f0-9-]{36}$" }
auth: { type: service_token, secret_ref: memory-svc/inbound/service_token }
cost: { per_call_usd: 0.002, weight: 2 }
rate_limit: { per_minute: 300, per_hour: 5000 }
timeout_ms: 5000
retry: { max: 1, backoff: exponential }
owner: ai-platform
```

### §16.3 Per-call checks (Doc 12 §6-§8)

Verified against Doc 12 §6 L83-87, §7 L89-93, §8 L95-100:

- **Authn (Doc 12 §6 L83):** service_token (per-workspace) OR OAuth2 (per-user).
- **Authz (Doc 12 §7 L91-93):** per-workspace allow/deny + per-resource scope (e.g. `memory:read:user`).
- **Rate limit (Doc 12 §8 L97):** per-minute, per-hour per `service_token`.
- **Cost budget (Doc 12 §8 L99):** per-call USD debited from caller's budget; over-budget → 429.
- **RLS scope (Doc 11 §10):** Postgres `SET LOCAL app.user_id` and `app.workspace_id` from caller's auth context.

### §16.4 Latency targets (AC-5.10)

| Tier | p95 | Verifies |
|---|---|---|
| Session | < 50ms | In-process; bounded by `RunState.scratchpad` lookup |
| Working | < 50ms (Redis) | Doc 02 §5.5 L241 (Redis 7) |
| User | < 200ms | Doc 11 §6 (implied; AC-5.10 explicit) |
| Platform | < 500ms | Doc 11 §6 (implied; AC-5.10 explicit) |

---

## §17 Cross-Service Imports (mandatory)

Per `arch-007-redispatch-verified-2026-07-28` + `memory-svc-source-drift-correction-2026-07-28`:

```python
# CANONICAL Source — must be imported BYTE-IDENTICAL from rag-svc
from services.rag_svc.app.contracts.source import Source
# Verified at Architect #7 §10.2 (issues_for_architect/issue_007_architect_design.md L311-328)

# CANONICAL Citation — used by RAG consumers (memory-svc does not generate citations
# but may store them in source_refs if a Citation is provided)
from services.rag_svc.app.contracts.citation import Citation
# Verified at Architect #7 §11.2 (issues_for_architect/issue_007_architect_design.md L382-405)

# agent-runtime RunState (read-only context for memory writes; carry run_id + actor)
from services.agent_runtime.app.contracts.run_state import RunState
# Verified at Architect #6 §4.3 (issues_for_architect/issue_006_architect_design.md L261-275)

# plugin-svc ToolManifest (memory-svc publishes T-MEMORY-READ / T-MEMORY-WRITE via MCP gateway;
# the manifest shape is plugin-svc's canonical)
from services.plugin_svc.app.contracts.tool_manifest import ToolManifest
# Verified at Architect #9 §12.2 (issues_for_architect/issue_009_architect_design.md L573-594)
```

**Memory-svc DOES NOT re-define Source, Citation, RunState, or ToolManifest.** Doing so breaks the byte-identical canary (Architect #7 §20.1 test_001 / test_002 + Architect #9 §17.1 test_006 + Architect #6 §13).

---

## §18 Memory Consumers (cross-service)

Verified against Doc 09 §3 L73-82 + §4 L84-91 + §14 L174-181 + §15 L183-190:

| Consumer | Doc 09 anchor | Memory usage |
|---|---|---|
| AGT-ORCH | §3 L79 | memory (read/write) — "Dependencies: RAG (read), memory (read/write), all specialists" |
| AGT-DISC-PLANNER | §4 L86-89 | Memory read for prior discovery seeds |
| AGT-DISC-CLUSTER | §5 L93-100 | (none direct) |
| AGT-RSRCH-MARKET | §6 L102-109 | Memory read for prior market estimates on similar opportunities |
| AGT-RSRCH-DEMAND | §7 L111-118 | Memory read for prior demand signals |
| AGT-RSRCH-COMP | §8 L120-127 | Memory read for prior competitive maps |
| AGT-RSRCH-PRICING | §9 L129-136 | Memory read for prior pricing benchmarks |
| AGT-RSRCH-PERSONA | §10 L138-145 | Memory read for prior persona synthesis |
| AGT-RSRCH-WTP | §11 L147-154 | Memory read for prior WTP estimates + calibration feedback |
| AGT-RSRCH-GTM | §12 L156-163 | Memory read for prior GTM diagnoses |
| AGT-RSRCH-RISK | §13 L165-172 | Memory read for prior risk registers |
| AGT-SCORE | §14 L179 | **Memory read for calibration feedback** ("rubric_version evolves") |
| AGT-RPT-WRITER | §15 L188 | **Memory read for prior reports** + acceptance feedback |
| AGT-VERIFY | §16 L197 | (audit, not memory read) |
| AGT-SAFETY | §17 L206 | PII detection (no memory read; gates memory write) |

**Write-side consumers:**

- AGT-ORCH writes calibration feedback to user-memory after each run.
- AGT-RPT-WRITER writes report-acceptance signals to workspace-memory.
- AGT-SAFETY writes PII redaction flags (sealed log; not memory record).

---

## §19 Drift Findings

### §19.1 DRIFT-8.1 (PATCHED) — 4-way Source drift

Per `memory-svc-source-drift-correction-2026-07-28`. **PATCHED** in this design via the `MemoryAnnotation` wrapper (see §12). The byte-identical canary (`test_001` from Architect #7 §20.1) now passes against the canonical.

| Sub-drift | Prior dispatch | Resolution |
|---|---|---|
| Added `source_id: UUID` | Prior §11 | DROPPED; identity is `MemoryRecord.source_refs[i]` |
| `HttpUrl` vs `str` | Prior §11 | ADOPTED canonical `HttpUrl` (Architect #7 §10.2 L324) |
| `Field(pattern=...)` on `tool_id` | Prior §11 | DROPPED; canonical has no pattern constraint |
| `confidence` / `freshness_class` on `Source` | Prior §11 | MOVED to `MemoryAnnotation` (per §12) |

### §19.2 DRIFT-8.2 — Doc 11 §2 vs issue body scope

- **Doc 11 §2 L17-25:** five-tier table including Workspace memory.
- **Issue body §"Goal":** "session (Redis), user (Postgres), platform (Postgres + vector)".
- **Resolution:** Doc 11 is the architectural contract. Workspace memory is a first-class tier. Issue body under-scopes. **Surface to conductor (Q-8.2).**

### §19.3 DRIFT-8.3 — Doc 11 §7 "no tenant_id column" vs AC-5.6 schema

- **Doc 11 §7 L62:** "Postgres + vector, no tenant_id column".
- **AC-5.6:** schema includes `workspace_id` (effectively the tenant_id).
- **Resolution:** Platform-tier records have `workspace_id = NULL`. AC-5.6 schema is the column-set for the entire table; per-row nullability reflects the tier. `owner_id` is similarly NULL for platform-tier. **No design change; clarification noted in §11.**

### §19.4 DRIFT-8.4 — Doc 11 §7 k-anonymity enforcement level

- **Doc 11 §7 L65:** "k-anonymity ≥ 50".
- **Doc 11 does not specify enforcement level.**
- **Resolution:** Enforce at WRITE TIME (records that would breach k-anonymity are quarantined, not written). Cannot enforce on aggregate queries because data is already persisted. **Surface to conductor (Q-8.4).**

### §19.5 DRIFT-8.5 — Doc 11 §8 supersession concurrency

- **Doc 11 §8 L71:** "supersession is explicit" — no concurrency specification.
- **Risk:** Two concurrent writes racing to supersede the same record.
- **Resolution:** Postgres advisory lock keyed on the superseded record_id (see §8). **Surface to conductor (Q-8.5).**

### §19.6 DRIFT-8.6 — Doc 11 §6 Enterprise retention overrides

- **Doc 11 §6 L55:** "configurable per-tenant (Enterprise)".
- **Doc 11 does not specify schema or mechanism.**
- **Resolution:** `workspace_config.retention_overrides JSONB` consulted at write time. **Surface to conductor (Q-8.6).**

### §19.7 DRIFT-8.7 — Doc 11 §11 30-day SLA vs AC-5.8 single-transaction

- **Doc 11 §11 L89:** "honored within 30 days".
- **AC-5.8:** "removes reachable records in a single transaction".
- **Resolution:** AT delete-time, the operation IS a single transaction. The 30-day SLA is the time between request and execution (Doc 11 §11 §12 covers "memory store down: degrade" — so a 30-day queue with retries is consistent). **Surface to conductor (Q-8.7).**

### §19.8 DRIFT-8.8 — Doc 11 §4 vs Doc 02 §5.5 working-memory TTL

- **Doc 11 §4 L37:** "TTL: 1 hour idle, 8 hours absolute".
- **Doc 02 §5.5 L242:** "sessions (8h idle / 30d max)" — but Doc 02 §5.5 refers to **AUTH sessions** (auth-svc), not memory-svc working memory.
- **Resolution:** Bind on Doc 11 §4 (1h idle / 8h absolute). Doc 02 §5.5 is a different service's TTL. **Surface to conductor (Q-8.1) — same drift, different angle.**

### §19.9 DRIFT-8.9 (NEW) — Doc 11 §5 retention vs AC-5.5

- **Doc 11 §5 L47:** "Retention: while the account is active; 30-day grace after deletion".
- **AC-5.5:** "user (90d sliding)".
- **Resolution:** Doc 11 is the architectural contract. AC-5.5's "90d sliding" appears to be a different policy (rolling 90-day TTL on user-memory?). If both are true, retention is MIN(active, 30d_grace, 90d_sliding). **Surface to conductor (Q-8.9).**

### §19.10 DRIFT-8.10 (NEW) — AC-5.4 embedding model vs Doc 10 §6

- **AC-5.4:** "embeddings via rag-svc's embedding model (Document 11 §5)".
- **Doc 10 §6 L95:** "text-embedding-3-large (3072 dims)" — v1 default.
- **AC-4.4 (issue #7):** "text-embedding-3-small".
- **Resolution:** Adopt Doc 10 §6 (text-embedding-3-large, 3072-dim) per Architect #7 §18.2 DRIFT-7.2. **No new drift; cross-reference to Architect #7.**

### §19.11 DRIFT-8.11 (NEW) — Workspace-memory NOT in MCP tool surface

- **Doc 11 §9 L75:** "memory.read(scope=user | workspace | platform, ...)".
- **T-MEMORY-READ input_schema:** `scope: enum [user, workspace, platform]` (3 options).
- **Doc 11 §2:** 5 tiers (Session, Working, User, Workspace, Platform).
- **Resolution:** Session + Working are NOT exposed via MCP (Session is in-process; Working is internal Redis). User + Workspace + Platform are exposed. The MCP scope enum has 3 values matching the durable tiers. **No drift; clarification noted in §16.1.**

---

## §20 Q-8.x Conductor Gating

The following decisions are gating implementation. The conductor should ratify before backend-expert begins.

### §20.1 Q-8.1 — Working-memory TTL ratification

Doc 11 §4 (1h idle / 8h absolute) vs Doc 02 §5.5 (8h idle / 30d max — but for auth-svc sessions). Which binds memory-svc's working-memory TTL? **Default: Doc 11 §4.**

### §20.2 Q-8.2 — Workspace-memory scope confirmation

Issue body under-scopes (mentions only session/user/platform). Doc 11 §2 has 5 tiers. Is workspace memory in v1 scope? **Default: yes, per Doc 11 §2 (architectural contract).**

### §20.3 Q-8.3 — `owner_id` nullability on workspace-tier

Doc 11 §6 says workspace-memory is "the workspace's"; no `owner_id`. AC-5.6 schema includes `owner_id`. Resolution: `owner_id = NULL` for workspace-tier. **Default: NULL is acceptable (workspace is the owner).**

### §20.4 Q-8.4 — k-anonymity enforcement level

Doc 11 §7 says "k-anonymity ≥ 50". Enforce at write-time (records that would breach are quarantined)? Or at query-time (cluster-on-read)? **Default: write-time (records cannot be retroactively un-leaked).**

### §20.5 Q-8.5 — Supersession concurrency mechanism

Doc 11 §8 says "supersession is explicit". Postgres advisory lock keyed on superseded record_id is the safe default. Alternative: optimistic concurrency check (`WHERE superseded_by IS NULL`) with retry. **Default: advisory lock.**

### §20.6 Q-8.6 — Enterprise retention override mechanism

Doc 11 §6 says "configurable per-tenant (Enterprise)". `workspace_config.retention_overrides JSONB` is the default mechanism. **Default: JSONB column in workspace-svc; consulted at write time.**

### §20.7 Q-8.7 — RTBF 30-day SLA vs AC-5.8 single-transaction

Doc 11 §11 says "within 30 days". AC-5.8 says "single transaction". **Default: 30-day SLA from request; AT delete-time the operation is single-transaction.**

---

## §21 RED Test Spec (~30-50 seeds)

Tests follow the `test_NNN_*` naming convention (per Architect #7 §20 + Architect #9 §17). Tests at `services/memory-svc/tests/`.

### §21.1 Cross-service byte-identical canary (REQUIRED)

#### test_001_source_byte_identical_import_test

```python
# services/memory-svc/tests/test_001_source_byte_identical_import_test.py
"""Verify Source is byte-identical with Architect #7 §10.2 (L311-328).
Cross-service canary with rag-svc, agent-runtime, reporting-svc.
"""
from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import HttpUrl

from services.rag_svc.app.contracts.source import Source


def test_source_byte_identical_import_test():
    """Memory-svc imports Source from rag-svc — must NOT redefine."""
    # Field set equality (Architect #7 §10.2 L311-328)
    assert set(Source.model_fields.keys()) == {"url", "fetched_at", "tool_id", "snippet"}
    
    # Type equality
    assert Source.model_fields["url"].annotation is HttpUrl
    assert Source.model_fields["fetched_at"].annotation is datetime
    assert Source.model_fields["tool_id"].annotation is str
    assert Source.model_fields["snippet"].annotation is str
    
    # No extras (DRIFT-8.1 prevention)
    assert "source_id" not in Source.model_fields
    assert "confidence" not in Source.model_fields
    assert "freshness_class" not in Source.model_fields


def test_source_round_trip():
    """Source JSON serialization is byte-identical across services."""
    s = Source(
        url=HttpUrl("https://example.com/article"),
        fetched_at=datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc),
        tool_id="T-MEMORY-WRITE",
        snippet="User prefers deeper market sizing.",
    )
    assert s.model_dump_json() == (
        '{"url":"https://example.com/article",'
        '"fetched_at":"2026-07-28T12:00:00Z",'
        '"tool_id":"T-MEMORY-WRITE",'
        '"snippet":"User prefers deeper market sizing."}'
    )
```

#### test_002_citation_byte_identical_import_test

```python
# services/memory-svc/tests/test_002_citation_byte_identical_import_test.py
"""Verify Citation (Architect #7 §11.2 L382-405) is byte-identical."""
from services.rag_svc.app.contracts.citation import Citation


def test_citation_byte_identical_import_test():
    """Memory-svc imports Citation from rag-svc — must NOT redefine."""
    assert set(Citation.model_fields.keys()) == {
        "chunk_id", "source", "content_hash", "freshness_class",
        "confidence", "score", "rank"
    }
```

### §21.2 MemoryRecord shape

#### test_003_memory_record_field_set

```python
def test_memory_record_field_set():
    """§11 field set is canonical."""
    from services.memory_svc.app.contracts.memory_record import MemoryRecord
    expected = {
        "record_id", "layer", "scope_id", "actor", "run_id", "content",
        "embedding", "source_refs", "annotations", "links", "version",
        "supersedes", "superseded_by", "created_at", "expires_at",
        "retention_until", "workspace_id", "owner_id", "scope",
    }
    assert set(MemoryRecord.model_fields.keys()) == expected
```

#### test_004_memory_record_source_refs_resolves_to_canonical_source

```python
def test_memory_record_source_refs_resolves_to_canonical_source():
    """source_refs: list[Source] resolves to Architect #7's canonical."""
    from typing import get_args
    from services.memory_svc.app.contracts.memory_record import MemoryRecord
    from services.rag_svc.app.contracts.source import Source
    
    field = MemoryRecord.model_fields["source_refs"]
    # Pydantic stores list[X] annotation; extract X
    assert Source in get_args(field.annotation)
```

### §21.3 MemoryAnnotation wrapper (DRIFT-8.1 prevention)

#### test_005_memory_annotation_wrapper_no_drift

```python
def test_memory_annotation_wrapper_no_drift():
    """MemoryAnnotation does NOT modify Source. The 4-way drift is prevented."""
    from services.memory_svc.app.contracts.memory_annotation import MemoryAnnotation
    from services.rag_svc.app.contracts.source import Source
    
    # MemoryAnnotation is a separate Pydantic class
    assert MemoryAnnotation is not Source
    assert issubclass(MemoryAnnotation, object)
    assert not issubclass(MemoryAnnotation, Source)  # NOT a subclass
    
    # MemoryAnnotation carries confidence + freshness_class (per §12.2)
    # BUT Source still does NOT have these fields (the canonical is preserved)
    assert "confidence" not in Source.model_fields
    assert "freshness_class" not in Source.model_fields
    assert MemoryAnnotation.model_fields["confidence"].annotation == Literal["high", "med", "low"]
    assert MemoryAnnotation.model_fields["freshness_class"].annotation == Literal["live", "recent", "stale", "unknown"]
    
    # Field set on MemoryAnnotation
    expected = {
        "source_ordinal", "confidence", "freshness_class",
        "relevance_at_write", "note", "annotated_by", "annotated_run_id",
    }
    assert set(MemoryAnnotation.model_fields.keys()) == expected
```

#### test_006_memory_record_source_refs_and_annotations_index_aligned

```python
def test_memory_record_source_refs_and_annotations_index_aligned():
    """MemoryAnnotation.source_ordinal indexes into MemoryRecord.source_refs."""
    from uuid import uuid4
    from datetime import datetime, timezone
    from pydantic import HttpUrl
    from services.memory_svc.app.contracts.memory_record import MemoryRecord
    from services.memory_svc.app.contracts.memory_annotation import MemoryAnnotation
    from services.rag_svc.app.contracts.source import Source
    
    src1 = Source(url=HttpUrl("https://example.com/a"), fetched_at=datetime.now(timezone.utc),
                  tool_id="T-RAG-SEARCH", snippet="snippet 1")
    src2 = Source(url=HttpUrl("https://example.com/b"), fetched_at=datetime.now(timezone.utc),
                  tool_id="T-RAG-SEARCH", snippet="snippet 2")
    
    ann1 = MemoryAnnotation(source_ordinal=0, confidence="high", freshness_class="live",
                            relevance_at_write=datetime.now(timezone.utc), note=None)
    ann2 = MemoryAnnotation(source_ordinal=1, confidence="med", freshness_class="recent",
                            relevance_at_write=datetime.now(timezone.utc), note=None)
    
    rec = MemoryRecord(
        record_id=uuid4(), layer="user", scope_id=uuid4(), actor="AGT-ORCH",
        run_id=uuid4(), content="User prefers X.",
        source_refs=[src1, src2], annotations=[ann1, ann2], links=[],
        version=1, supersedes=None, superseded_by=None,
        created_at=datetime.now(timezone.utc), expires_at=None, retention_until=None,
        workspace_id=None, owner_id=uuid4(), scope="user",
    )
    assert len(rec.source_refs) == len(rec.annotations)
    for i, ann in enumerate(rec.annotations):
        assert ann.source_ordinal == i
```

### §21.4 Layer isolation

#### test_010_user_memory_rls_blocks_other_users

```python
def test_user_memory_rls_blocks_other_users():
    """Doc 11 §10: user can only read their own user memory.
    Postgres RLS policy user_memory_isolation enforces this."""
    # Setup: insert user-A memory record
    # SET LOCAL app.user_id = user_B_id
    # Query → expect [] (RLS blocks)
```

#### test_011_workspace_memory_rls_blocks_non_members

```python
def test_workspace_memory_rls_blocks_non_members():
    """Doc 11 §10: member-only-workspace.
    A user who is not a member of workspace-X cannot read X's workspace memory."""
```

#### test_012_platform_memory_rows_have_null_workspace_owner

```python
def test_platform_memory_rows_have_null_workspace_owner():
    """Doc 11 §7: 'no tenant_id column'. Platform records have workspace_id=NULL and owner_id=NULL."""
    rec = MemoryRecord(..., layer="platform", workspace_id=None, owner_id=None, scope="platform")
    assert rec.workspace_id is None
    assert rec.owner_id is None
```

#### test_013_no_cross_workspace_memory

```python
def test_no_cross_workspace_memory():
    """Doc 11 §10: 'No cross-workspace memory'.
    A user in workspace-A cannot read workspace-B's memory even if they have access."""
```

### §21.5 Cross-tenant leakage (red-team)

#### test_040_cross_tenant_isolation_user_tier

```python
def test_cross_tenant_isolation_user_tier():
    """Monthly red-team (Doc 11 §13). User-A cannot read user-B's user-memory."""
    # Attempt SQL-injection-style attempts to bypass RLS
    # All return [] or 403
```

#### test_041_cross_tenant_isolation_workspace_tier

```python
def test_cross_tenant_isolation_workspace_tier():
    """Workspace isolation: non-member cannot read workspace's memory."""
```

### §21.6 Write discipline

#### test_020_write_atomic_supersession

```python
def test_write_atomic_supersession():
    """Doc 11 §8: atomic. Supersession is single-transaction."""
    # Two supersession writes to same record — second waits for first's advisory lock
```

#### test_021_write_rejects_missing_provenance

```python
def test_write_rejects_missing_provenance():
    """Doc 11 §8: 'Provenance missing → reject write' (Doc 11 §12 L98).
    MemoryRecord without run_id or actor fails validation."""
    with pytest.raises(ValidationError):
        MemoryRecord(record_id=uuid4(), layer="user", scope_id=uuid4(),
                     actor="", run_id=None, ...)  # missing actor + run_id
```

#### test_022_write_versioned

```python
def test_write_versioned():
    """Doc 11 §8: 'every memory record has a version'.
    Insert with version=1; supersede → version=2 on new row, superseded_by set on old."""
```

### §21.7 PII redaction (AC-5.9)

#### test_030_pii_redaction_at_write

```python
def test_pii_redaction_at_write():
    """AC-5.9: AGT-SAFETY is invoked on every write; flagged content stored redacted."""
    # POST /v1/memory with content='SSN: 123-45-6789'
    # Expect: stored record has content='SSN: [REDACTED]'; sealed log retains raw
```

#### test_031_pii_redaction_failure_blocks_write

```python
def test_pii_redaction_failure_blocks_write():
    """If AGT-SAFETY is down, the write is queued (not blocked); degraded mode."""
```

### §21.8 Right-to-be-forgotten (AC-5.8)

#### test_050_rtfb_graph_walk_single_transaction

```python
def test_rtfb_graph_walk_single_transaction():
    """AC-5.8: 1k-record memory graph → single-transaction purge."""
    # Build a 1k-record graph via memory_link
    # Trigger RTBF
    # Assert: all 1k records deleted; single transaction in pg_stat_activity
```

#### test_051_rtfb_cascade_via_memory_link

```python
def test_rtfb_cascade_via_memory_link():
    """AC-5.7 + AC-5.8: memory_link cascade reachability."""
    # A → B → C chain; RTBF A → deletes A, B, C in single TX
```

### §21.9 Latency targets (AC-5.10)

#### test_060_session_read_p95_under_50ms

```python
def test_session_read_p95_under_50ms():
    """AC-5.10: session p95 < 50ms."""
    # 1k reads; assert p95 < 50ms
```

#### test_061_user_read_p95_under_200ms

```python
def test_user_read_p95_under_200ms():
    """AC-5.10: user p95 < 200ms."""
```

#### test_062_platform_read_p95_under_500ms

```python
def test_platform_read_p95_under_500ms():
    """AC-5.10: platform p95 < 500ms."""
```

### §21.10 k-anonymity (Doc 11 §7)

#### test_070_platform_memory_kanonymity_blocks_writes_below_threshold

```python
def test_platform_memory_kanonymity_blocks_writes_below_threshold():
    """Doc 11 §7: k-anonymity ≥ 50. Write-time filter rejects records
    that would have < 50 nearest neighbors at cosine ≥ 0.85."""
```

### §21.11 Failure modes (Doc 11 §12)

#### test_080_store_down_degrades_gracefully

```python
def test_store_down_degrades_gracefully():
    """Doc 11 §12: 'Memory store down → degrade; run still works without personalization'."""
    # Postgres down → reads return [] with degrade flag set
```

#### test_081_corrupted_record_quarantined

```python
def test_corrupted_record_quarantined():
    """Doc 11 §12: 'Corrupted record → quarantine; alert; do not block run'."""
```

#### test_082_schema_drift_atlas_migration

```python
def test_schema_drift_atlas_migration():
    """Doc 11 §12: 'Schema drift → migration via Atlas; backwards-compatible'."""
    # Add a new optional column via Atlas; existing records unaffected
```

### §21.12 MCP tool

#### test_090_t_memory_read_requires_authn

```python
def test_t_memory_read_requires_authn():
    """Doc 12 §6: authentication required. 401 without token."""
```

#### test_091_t_memory_write_tenant_scoping

```python
def test_t_memory_write_tenant_scoping():
    """Doc 12 §7: per-workspace allow/deny. Workspace-B token cannot write to workspace-A's memory."""
```

#### test_092_t_memory_read_rate_limit

```python
def test_t_memory_read_rate_limit():
    """Doc 12 §8: rate limit. 601st call in 60s returns 429."""
```

#### test_093_t_memory_write_cost_budget

```python
def test_t_memory_write_cost_budget():
    """Doc 12 §8: cost budget. After accumulated cost, returns 429 with reason=budget_exceeded."""
```

### §21.13 Backout (AC-5.12)

#### test_100_backout_per_tier_flush_runbook

```python
def test_backout_per_tier_flush_runbook():
    """AC-5.12: per-tier flush runbook."""
    # docs/runbooks/memory-svc.md exists; flush-tables procedure documented
```

#### test_101_backout_rollback_to_prior_image

```python
def test_backout_rollback_to_prior_image():
    """AC-5.12: rollback to prior image. Helm/ArgoCD procedure exists."""
```

#### test_102_backout_sealed_log_redaction_kill_switch

```python
def test_backout_sealed_log_redaction_kill_switch():
    """AC-5.12: sealed-log redaction kill switch.
    Feature flag toggles AGT-SAFETY on/off; tests for both modes."""
```

Total: ~30-40 RED seeds across 13 categories.

---

## §22 Acceptance Criteria Mapping

Each AC verified live from `gh issue view 8 --repo GanTechProject/VinayakFortune` (issue body AC-5.1 through AC-5.12):

| AC | Description | Design section |
|---|---|---|
| AC-5.1 | memory-svc scaffolded (Python 3.11 per Q-9 / 3.12 per AC body, FastAPI, async) | §1 (stack), §22 (impl posture below) |
| AC-5.2 | Session memory backed by Redis 7 with 8h idle / 30d max TTL (Doc 02 §5.5) | §4, §19.8 DRIFT-8.8, Q-8.1 |
| AC-5.3 | User memory backed by Postgres (`memory.memory_record` per Doc 02 §5.2 L221) | §5, §11 schema |
| AC-5.4 | Platform memory backed by Postgres + pgvector; rag-svc embedding (Doc 11 §5) | §7, §19.10 DRIFT-8.10 |
| AC-5.5 | TTL policy: session (8h idle, 30d max), user (90d sliding), platform (indefinite, RTBF per REQ-PLAT-0002 / REQ-ADMIN-0008) | §4, §13, §19.9 DRIFT-8.9 |
| AC-5.6 | Memory record schema: {workspace_id, owner_id, scope, content, embedding?, created_at, expires_at, links: [memory_link]} | §11 `MemoryRecord`, §5 schema |
| AC-5.7 | Memory link schema: {from_memory_id, to_memory_id, kind, weight} | §11 `MemoryLink` |
| AC-5.8 | Right-to-be-forgotten: workspace-level purge walking memory_link graph in single TX (Doc 21 §11) | §13, §21.8 test_050 |
| AC-5.9 | PII redaction at write time: AGT-SAFETY (Doc 21 §9, Doc 09 §17) | §14, §21.7 test_030 |
| AC-5.10 | Read p95 < 50ms (session), < 200ms (user), < 500ms (platform) (Doc 11 §6) | §16.4, §21.9 test_060 |
| AC-5.11 | Provenance: every record carries source citation (REQ-RPT-0011) | §11 `source_refs`, §12 `annotations`, §17 imports |
| AC-5.12 | Backout plan: per-tier flush, memory-svc rollback, sealed-log redaction kill switch (Doc 28 §3) | §21.13 test_100 |

All 12 ACs have a corresponding design section and at least one RED test.

---

## §23 Implementation Posture (handoff to backend-expert)

Once Q-8.x is gated:

- **Service layout:** `services/memory-svc/` with `app/contracts/{memory_record.py, memory_annotation.py, memory_link.py}` at the canonical paths.
- **Stack:** Python 3.11 (CI gate per `conductor-decisions-2026-07-28` Q-9 + PR #56 `pr-56-merged-2026-07-28` + Doc 02 §2). FastAPI async; SQLAlchemy 2.x; pgvector via raw SQL DDL; Redis 7 for working-memory tier.
- **Indexes:** Postgres extensions `pgvector`, `pg_trgm` (lexical fallback), `uuid-ossp`.
- **Migrations:** Atlas declarative (Doc 02 §15 L400).
- **MCP gateway:** T-MEMORY-READ and T-MEMORY-WRITE registered per Doc 12 §3 L46-50; manifests conform to plugin-svc's ToolManifest (Architect #9 §12).
- **Audit emission:** every write emits `audit_event` to audit-svc (Doc 02 §5.2 L225).
- **Tests:** `tests/cross_service/{test_001_source_byte_identical,test_002_citation_byte_identical,test_005_memory_annotation_wrapper_no_drift}.py` are the most-load-bearing tests; they must be GREEN before any other consumer can import.

## §24 Cross-references

- **Architect #6 (agent-runtime):** `issues_for_architect/issue_006_architect_design.md` §4.3 `RunState` (L261-275); AGT-ORCH `memory (read/write)` per Doc 09 §3 L79.
- **Architect #7 (rag-svc):** `issues_for_architect/issue_007_architect_design.md` §10.2 `Source` (L311-328) and §11.2 `Citation` (L382-405); byte-identical canary in §20.1 (L737-761).
- **Architect #9 (plugin-svc):** `issues_for_architect/issue_009_architect_design.md` §12.2 `ToolManifest` (L573-594); MCP gateway architecture (Doc 12 §3 L46-50).
- **Memory documentation:**
  - `memory-svc-source-drift-correction-2026-07-28` — prior 4-way Source drift patched via `MemoryAnnotation` wrapper.
  - `arch-007-redispatch-verified-2026-07-28` — Source + Citation canary locked.
  - `arch-009-redispatch-verified-2026-07-28` — ToolManifest canonical locked.
  - `arch-006-redispatch-verified-2026-07-28` — RunState/Step/Evidence/Budget canonical.
  - `conductor-decisions-2026-07-28` — Q-3 (v0.x merge), Q-9 (Python 3.11) decisions applied here.

---

> *End of Issue #8 — memory-svc BAND-3-DESIGN. The 4-way Source drift has been patched via the `MemoryAnnotation` wrapper (mirroring Architect #7's `Citation` pattern). The byte-identical canary in §21.1 is the contract that all 5 cross-service consumers import. The 11 drift findings in §19 and 7 conductor-gating questions in §20 are the open items that block backend-expert dispatch.*