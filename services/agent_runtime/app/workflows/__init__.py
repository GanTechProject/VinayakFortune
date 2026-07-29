"""LangGraph workflows — top-level orchestrator + per-specialist sub-graphs.

Per Architect #6 §5 (Doc 08 §4 L76-92 mermaid, verbatim):

    Plan → Safety → Plan dimensions → {For each dim → Specialist → Verify}
    → Score → Verify2 → Report → Verify3 → Done

Per-specialist sub-graph (Doc 08 §4.1 L99, verbatim):
    plan → retrieve (RAG) → fetch (plugin) → synthesize → self-check
"""
