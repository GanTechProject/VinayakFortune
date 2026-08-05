"""ToolManifest — cross-service canary re-export (MCP gateway validation).

Per Architect #9 §12 + Architect #6 §13: ToolManifest is CANONICAL in
plugin-svc. agent-runtime imports, NOT re-defines. The MCP gateway in
agent-runtime validates per-call input against the manifest.

The cross-service canary (Architect #9 §17.1 test_006) verifies field
set equality across plugin-svc and any consumer that re-exports.
"""

from __future__ import annotations

from services.plugin_svc.app.contracts.tool_manifest import (
    ToolAuth,
    ToolCost,
    ToolManifest,
    ToolRateLimit,
    ToolRetry,
)

__all__ = [
    "ToolAuth",
    "ToolCost",
    "ToolManifest",
    "ToolRateLimit",
    "ToolRetry",
]
