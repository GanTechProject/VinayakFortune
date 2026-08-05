"""Evidence — per Doc 15 §6 L70-81 (the only inline evidence shape).

Per Architect #6 §4.5 (verbatim):
    claim: str
    citations: list[Citation]
    freshness: Freshness
    confidence: Confidence
    snippet: str
    source_url: str
    captured_at: datetime
    agent_id: str
    step_id: UUID

Q-6.2 (conductor-ratified): Evidence.source_url is `str` (Doc 15 literal),
NOT HttpUrl. The cast from Source.url (HttpUrl) to str happens at the
Evidence assembly point.

DRIFT-6.6: Evidence.snippet (the asserted verbatim excerpt) MAY differ
from Source.snippet (the retrieved chunk excerpt). The verifier (Doc 15
§7 L91) checks the match.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from services.rag_svc.app.contracts.citation import Citation
from services.rag_svc.app.contracts.source import Source

Freshness = Literal["live", "recent", "stale", "unknown"]
Confidence = Literal["high", "med", "low"]


class Evidence(BaseModel):
    """Per-claim evidence row (Doc 15 §6 L70-81)."""

    claim: str
    citations: list[Citation] = Field(default_factory=list)
    freshness: Freshness
    confidence: Confidence
    snippet: str  # asserted verbatim excerpt (may differ from Source.snippet)
    source_url: str  # str per Doc 15 §6 L76 (Q-6.2 ratified)
    captured_at: datetime
    agent_id: str
    step_id: UUID

    @classmethod
    def from_source(
        cls,
        *,
        claim: str,
        source: Source,
        citation: Citation,
        agent_id: str,
        step_id: UUID,
        snippet: str | None = None,
        confidence: Confidence = "high",
        freshness: Freshness | None = None,
    ) -> Evidence:
        """Build an Evidence row from a Source + Citation.

        The source_url is cast to str per Q-6.2 (Doc 15 §6 L76).
        The freshness is inherited from the citation if not provided.
        """
        return cls(
            claim=claim,
            citations=[citation],
            freshness=freshness or citation.freshness_class,
            confidence=confidence,
            snippet=snippet if snippet is not None else source.snippet,
            source_url=str(source.url),
            captured_at=source.fetched_at,
            agent_id=agent_id,
            step_id=step_id,
        )


__all__ = ["Confidence", "Evidence", "Freshness"]
