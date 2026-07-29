"""Canonical Citation row — the cross-service byte-identical canary.

Realizes Doc 10 §10 L133-147. Every claim by every agent must carry
one of these. The wire-level per-claim citation (Doc 10 §10 L143-145)
is a subset of this model.

Owned by rag-svc (issue #7). Imported verbatim by:
  - agent-runtime (Architect #6 §4.6 L335)
  - memory-svc   (Architect #8 §11)
  - validation-pipeline (Architect #11)
  - reporting-svc (Architect #12 §11.3)

Verified against Doc 10 §10 L135-147 + Doc 10 §6 L98 metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from services.rag_svc.app.contracts.source import Source


FreshnessClass = Literal["live", "recent", "stale", "unknown"]
Confidence = Literal["high", "med", "low"]


class Citation(BaseModel):
    """Canonical Citation row — the cross-service byte-identical canary."""

    chunk_id: UUID  # immutable chunk identifier; PK on rag.chunk
    source: Source  # the canonical Source row (Architect #7 §10)
    content_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",  # sha256 hex digest
    )  # Doc 10 §6 L98 metadata; Doc 10 §10 L144 implicit
    freshness_class: FreshnessClass  # Doc 10 §11 L151-154
    confidence: Confidence  # Doc 10 §10 L138 L143
    score: float = Field(ge=0.0, le=1.0)  # post-rerank similarity score
    rank: int = Field(ge=1)  # 1-indexed position in the returned list


__all__ = ["Citation", "FreshnessClass", "Confidence"]
