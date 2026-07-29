"""Canonical Source row — the cross-service byte-identical canary.

Owned by rag-svc (issue #7). Imported verbatim by:
  - agent-runtime (Architect #6 §4.1 L198-228)
  - memory-svc   (Architect #8 §11 Source.MemoryAnnotation wrapper)
  - reporting-svc (Architect #12 §11.3 Source citations)

Drifts in this 4-field shape break the byte-identical canary test
(Architect #7 §20.1 test_001). Any field rename requires updating
rag-svc, agent-runtime, AND memory-svc in the same PR.

Verified against Doc 10 §10 L135-147 + Architect #6 §4.1 L213-218.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, HttpUrl


class Source(BaseModel):
    """Canonical Source row — the cross-service byte-identical canary."""

    url: HttpUrl  # canonical URL (after redirects; final URL)
    fetched_at: datetime  # UTC; the moment the source connector retrieved it
    tool_id: str  # MCP tool manifest ID, e.g. "T-MARKET-DATA-FETCHER"
    snippet: str  # the literal text excerpt used to ground the claim


__all__ = ["Source"]
