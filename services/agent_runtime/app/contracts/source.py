"""Source — cross-service byte-identical canary re-export.

Per Architect #6 §4.1 (L198-228) and DRIFT-6.1: Source is CANONICAL in
rag-svc. agent-runtime imports, NOT re-defines.

CRITICAL: do NOT redefine Source here. A field rename here breaks the
byte-identical canary (Architect #7 §20.1 test_001) across rag-svc,
agent-runtime, memory-svc, reporting-svc. Renames must land in lockstep.
"""

from __future__ import annotations

from services.rag_svc.app.contracts.source import Source

__all__ = ["Source"]
