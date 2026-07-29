"""Source re-export — memory-svc cross-service canary.

Per Architect #6 §4.1 (DRIFT-6.1) and Architect #8 §11: memory-svc re-exports
the canonical Source from rag-svc. NOT a re-definition. A field rename here
breaks the byte-identical canary (Architect #7 §20.1 test_001).
"""

from __future__ import annotations

from services.rag_svc.app.contracts.source import Source

__all__ = ["Source"]
