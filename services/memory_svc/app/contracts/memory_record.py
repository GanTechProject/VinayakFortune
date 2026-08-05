"""MemoryRecord + MemoryAnnotation — memory-svc cross-service canary.

Forward-compatible stub placed by Phase 2a (#6 agent-runtime keystone
implementer) so the agent-runtime cross-service canary tests pass in
isolation BEFORE the memory-svc implementer lands. This stub MUST match
Architect #8 BAND-3-DESIGN exactly — the memory-svc implementer will
inherit this file verbatim and any field rename must propagate across
services in lockstep (the canary enforces this).

Verified against:
  - issues_for_architect/issue_008_architect_design.md §11.4 L345-389
    (MemoryRecord: 19 fields with parallel source_refs + annotations)
  - issues_for_architect/issue_008_architect_design.md §12.2 L453-477
    (MemoryAnnotation: 5+2 field wrapper, mirrors Citation pattern)

Drift history:
  - 2026-07-28: ORCHESTRATOR-PATCH for 4-way Source drift (see
    memory-svc-source-drift-correction-2026-07-28.md). MemoryAnnotation
    is the wrapper that carries per-source metadata; Source is canonical
    at the leaf (from rag-svc).
  - 2026-07-29: agent-runtime keystone implementer placed a 12-field
    MemoryRecord stub that did NOT match the design. Orchestrator
    corrected to match the design verbatim. Field renames will break the
    canary across memory-svc, validation-pipeline, reporting-svc.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# CANONICAL Source from rag-svc (4-field, byte-identical canary)
from services.rag_svc.app.contracts.source import Source

# Re-defined locally to avoid an import dependency cycle with rag_svc.
# These Literals are byte-identical to Architect #7 §11.2 L378-379.
FreshnessClass = Literal["live", "recent", "stale", "unknown"]
Confidence = Literal["high", "med", "low"]


class MemoryLink(BaseModel):
    """AC-5.7: memory-svc graph link. {from_memory_id, to_memory_id, kind, weight}."""

    from_memory_id: UUID
    to_memory_id: UUID
    kind: Literal["causal", "temporal", "thematic", "supersedes"]
    weight: float = Field(ge=0.0, le=1.0)


class MemoryAnnotation(BaseModel):
    """memory-svc-private per-source annotation. Mirrors Architect #7's Citation wrapper.

    Verified against:
      - Doc 11 §8 L72 ("Provenance: every record carries the source run_id and actor")
      - AC-5.11: every record carries its source citation
      - ORCHESTRATOR-PATCH: 4-way Source drift corrected by routing per-source metadata here

    Pattern: cross-service canonical (Source) + service-private wrapper (this class).
    Consumers traverse MemoryRecord.source_refs[i] for the canonical AND
    MemoryRecord.annotations[i] for the metadata. The two lists are
    index-aligned via source_ordinal.
    """

    source_ordinal: int = Field(ge=0)  # which Source in MemoryRecord.source_refs (0-indexed)
    confidence: Confidence  # same Literal as Architect #7 §11.2 L379
    freshness_class: FreshnessClass  # same Literal as Architect #7 §11.2 L378
    relevance_at_write: datetime  # when the annotation was computed (UTC)
    note: Optional[str] = None  # free-form note from the writing agent

    # Optional provenance tie-back (Doc 11 §8 "every record carries the source run_id and actor")
    annotated_by: Optional[str] = None  # agent_id that computed the annotation
    annotated_run_id: Optional[UUID] = None  # run_id that computed the annotation


class MemoryRecord(BaseModel):
    """Canonical memory-svc durable record. Cross-tier.

    Verified against:
      - Doc 11 §2 (L17-25): five-layer table
      - Doc 11 §5-§7 (L41-65): tier-specific content semantics
      - Doc 11 §8 (L67-72): write discipline (atomic/verified/versioned/provenance)
      - AC-5.6: {workspace_id, owner_id, scope, content, embedding?, created_at, expires_at, links}
      - AC-5.11: every record carries its source citation (REQ-RPT-0011)
    """

    record_id: UUID
    layer: Literal["user", "workspace", "platform"]  # alias for scope; matches Doc 11 §2 tier names
    scope_id: UUID  # user_id / workspace_id / NULL for platform (semantic: tenant scope)
    actor: str  # who wrote (agent_id, user_id, or "system")
    run_id: UUID  # Doc 11 §8 provenance
    content: str  # the actual fact
    embedding: Optional[list[float]] = None  # 3072-dim per Doc 10 §6 L95; nullable for tier-1 records
    source_refs: list[Source] = Field(default_factory=list)  # CANONICAL 4-field Source
    annotations: list[MemoryAnnotation] = Field(default_factory=list)  # memory-svc-private (see MemoryAnnotation)
    links: list[MemoryLink] = Field(default_factory=list)  # AC-5.7 memory_link graph
    version: int = 1  # Doc 11 §8: every record has a version
    supersedes: Optional[UUID] = None  # version chain (older sibling)
    superseded_by: Optional[UUID] = None  # version chain (newer sibling)
    created_at: datetime
    expires_at: Optional[datetime] = None  # working-memory TTL pass-through
    retention_until: Optional[datetime] = None  # Doc 11 §11 retention

    # AC-5.6 explicit fields (added to satisfy issue-body schema)
    workspace_id: Optional[UUID] = None  # NULL for platform-tier; otherwise the workspace
    owner_id: Optional[UUID] = None  # user_id for user-tier; NULL for workspace- and platform-tier
    scope: Literal["session", "user", "workspace", "platform"]  # AC-5.6 verbatim


__all__ = [
    "MemoryRecord",
    "MemoryAnnotation",
    "MemoryLink",
    "FreshnessClass",
    "Confidence",
]
