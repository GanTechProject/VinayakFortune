"""Unit tests for Evidence (Architect #6 §4.5).

Per Architect #6 §13 test_011, test_012:
- test_011: evidence_carries_source_url_string_mirroring_source_url_value
- test_012: evidence_snippet_may_differ_from_source_snippet
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from services.agent_runtime.app.contracts.evidence import Evidence
from services.rag_svc.app.contracts.citation import Citation
from services.rag_svc.app.contracts.source import Source


def _new_source() -> Source:
    return Source(
        url="https://example.com/article",
        fetched_at=datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc),
        tool_id="T-RAG-SEARCH",
        snippet="RETRIEVED excerpt from the chunk body.",
    )


def _new_citation(source: Source) -> Citation:
    return Citation(
        chunk_id=UUID("00000000-0000-0000-0000-000000000001"),
        source=source,
        content_hash="a" * 64,
        freshness_class="live",
        confidence="high",
        score=0.9,
        rank=1,
    )


def test_evidence_carries_source_url_string_mirroring_source_url_value() -> None:
    """Per Q-6.2: Evidence.source_url is str per Doc 15 §6 L76."""
    s = _new_source()
    cit = _new_citation(s)
    e = Evidence(
        claim="claim",
        citations=[cit],
        freshness="live",
        confidence="high",
        snippet="snippet",
        source_url=str(s.url),
        captured_at=s.fetched_at,
        agent_id="AGT-RSRCH-MARKET",
        step_id=uuid4(),
    )
    assert isinstance(e.source_url, str)
    assert e.source_url == "https://example.com/article"


def test_evidence_snippet_may_differ_from_source_snippet() -> None:
    """Per DRIFT-6.6: Evidence.snippet (asserted) MAY differ from Source.snippet (retrieved)."""
    s = _new_source()
    cit = _new_citation(s)
    e = Evidence(
        claim="claim",
        citations=[cit],
        freshness="live",
        confidence="high",
        snippet="AGENT-ASSERTED excerpt",
        source_url=str(s.url),
        captured_at=s.fetched_at,
        agent_id="AGT-RSRCH-MARKET",
        step_id=uuid4(),
    )
    assert e.snippet == "AGENT-ASSERTED excerpt"
    assert e.snippet != s.snippet


def test_evidence_from_source_factory() -> None:
    """Evidence.from_source casts Source.url to str (Q-6.2 assembly point)."""
    s = _new_source()
    cit = _new_citation(s)
    e = Evidence.from_source(
        claim="market grew 14.3% in Q4 2025",
        source=s,
        citation=cit,
        agent_id="AGT-RSRCH-MARKET",
        step_id=uuid4(),
    )
    assert e.source_url == "https://example.com/article"
    assert e.freshness == "live"
    assert e.confidence == "high"
    assert e.captured_at == s.fetched_at
    assert e.snippet == s.snippet  # defaults to source snippet
