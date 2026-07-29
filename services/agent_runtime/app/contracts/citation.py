"""Citation — cross-service byte-identical canary re-export.

Per Architect #6 §4.6 (L335) and Architect #7 §11.1: Citation is
CANONICAL in rag-svc. agent-runtime imports, NOT re-defines.

The cross-service canary (Architect #7 §20.1 test_002) verifies model
field equality across rag-svc, agent-runtime, memory-svc, reporting-svc.
"""

from __future__ import annotations

from services.rag_svc.app.contracts.citation import Citation

__all__ = ["Citation"]
