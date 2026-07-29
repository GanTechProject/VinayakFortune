"""Root conftest for agent-runtime tests.

Injects the monorepo root onto sys.path so that the cross-service
imports (`from services.rag_svc.app.contracts.source import Source`)
resolve. Without this, pytest cannot find the `services` namespace
package.

DO NOT REMOVE — the cross-service byte-identical canary depends on this.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The monorepo root (the directory containing `services/`) is two levels
# up from this conftest.py file.
_MONOREPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_MONOREPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_MONOREPO_ROOT))
