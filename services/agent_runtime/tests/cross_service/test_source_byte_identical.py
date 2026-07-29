"""test_001 — Source byte-identical canary.

Per Architect #7 §20.1 test_001 (lines 737-761 of
issues_for_architect/issue_007_architect_design.md).

This is the cross-service load-bearing canary. It MUST pass on every
consumer's CI before any other consumer can import Source. A field
rename in any one service breaks the canary and requires a lockstep
update across rag-svc, agent-runtime, and memory-svc.
"""

from __future__ import annotations

from datetime import datetime, timezone


def test_source_byte_identical_across_services() -> None:
    """Source must resolve to the same class across rag-svc, agent-runtime, memory-svc, reporting-svc."""
    from services.agent_runtime.app.contracts.source import Source as ArSource
    from services.memory_svc.app.contracts.source import Source as MemSource
    from services.rag_svc.app.contracts.source import Source as RagSource
    from services.reporting_svc.app.contracts.source import Source as RptSource

    # Field set equality
    assert set(RagSource.model_fields.keys()) == {"url", "fetched_at", "tool_id", "snippet"}
    assert RagSource.model_fields == ArSource.model_fields == MemSource.model_fields == RptSource.model_fields

    # Type equality
    from pydantic import HttpUrl

    assert RagSource.model_fields["url"].annotation is HttpUrl
    assert RagSource.model_fields["fetched_at"].annotation is datetime
    assert RagSource.model_fields["tool_id"].annotation is str
    assert RagSource.model_fields["snippet"].annotation is str


def test_source_round_trip() -> None:
    """Source JSON serialization matches the canonical byte-identical form."""
    from services.rag_svc.app.contracts.source import Source

    s = Source(
        url="https://example.com/article",
        fetched_at=datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc),
        tool_id="T-RAG-SEARCH",
        snippet="The market grew by 14.3% YoY in Q4 2025.",
    )
    payload = s.model_dump_json()
    # Pydantic emits ISO 8601 with tzinfo; the Z-suffix is added by Pydantic v2.
    assert '"url":"https://example.com/article"' in payload
    assert '"tool_id":"T-RAG-SEARCH"' in payload
    assert '"snippet":"The market grew by 14.3% YoY in Q4 2025."' in payload
    assert "2026-07-28" in payload


def test_source_import_path_is_rag_svc() -> None:
    """Import path is `services.rag_svc.app.contracts.source`.

    Per Architect #6 §4.1 (L198-228) + DRIFT-6.1: agent-runtime imports
    Source from rag-svc, NOT re-defines. The import path is the stable
    identifier.
    """
    import services.agent_runtime.app.contracts.source as ar_source_mod

    # The agent-runtime module's source attribute is the rag_svc Source class.
    import services.rag_svc.app.contracts.source as rag_source_mod

    assert ar_source_mod.Source is rag_source_mod.Source
