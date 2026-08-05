"""test_002 — Citation byte-identical canary.

Per Architect #7 §20.1 test_002 (lines 763-779 of
issues_for_architect/issue_007_architect_design.md).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID


def test_citation_byte_identical_across_services() -> None:
    """Citation must resolve to the same class across rag-svc, agent-runtime, memory-svc, reporting-svc."""
    from services.agent_runtime.app.contracts.citation import Citation as ArCitation
    from services.memory_svc.app.contracts.citation import Citation as MemCitation
    from services.rag_svc.app.contracts.citation import Citation as RagCitation
    from services.reporting_svc.app.contracts.citation import Citation as RptCitation

    assert set(RagCitation.model_fields.keys()) == {
        "chunk_id", "source", "content_hash", "freshness_class",
        "confidence", "score", "rank",
    }
    assert (
        RagCitation.model_fields
        == ArCitation.model_fields
        == MemCitation.model_fields
        == RptCitation.model_fields
    )


def test_citation_content_hash_pattern() -> None:
    """content_hash must be a 64-character lowercase hex string (sha256)."""
    import pytest
    from pydantic import ValidationError

    from services.rag_svc.app.contracts.citation import Citation
    from services.rag_svc.app.contracts.source import Source

    src = Source(
        url="https://example.com/article",
        fetched_at=datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc),
        tool_id="T-RAG-SEARCH",
        snippet="snippet",
    )
    # Valid: 64 hex chars
    Citation(
        chunk_id=UUID("00000000-0000-0000-0000-000000000001"),
        source=src,
        content_hash="a" * 64,
        freshness_class="live",
        confidence="high",
        score=0.9,
        rank=1,
    )
    # Invalid: not hex
    with pytest.raises(ValidationError):
        Citation(
            chunk_id=UUID("00000000-0000-0000-0000-000000000002"),
            source=src,
            content_hash="not-hex",
            freshness_class="live",
            confidence="high",
            score=0.9,
            rank=1,
        )


def test_citation_import_path_is_rag_svc() -> None:
    """agent-runtime's Citation is the canonical rag-svc Citation."""
    import services.agent_runtime.app.contracts.citation as ar_cit_mod
    import services.rag_svc.app.contracts.citation as rag_cit_mod

    assert ar_cit_mod.Citation is rag_cit_mod.Citation
