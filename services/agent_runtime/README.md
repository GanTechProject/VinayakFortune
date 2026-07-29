# agent-runtime

> AI-plane orchestrator — the keystone of the cross-service contract for
> the AI plane (issue #6, Architect #6 BAND-3-DESIGN).

This service is the **LangGraph runtime** that hosts the multi-agent
graph (Doc 08 §3), the per-specialist sub-graphs (Doc 08 §4.1), the
MCP gateway (Doc 12 §3), the verifier pass, the safety filter, and the
model-routing layer (Doc 07 §7.2 + AD-004).

## Cross-service byte-identical canary

agent-runtime **imports** (NOT re-defines) the following canonical
contracts from their owning services:

- `Source` — `from services.rag_svc.app.contracts.source import Source`
- `Citation` — `from services.rag_svc.app.contracts.citation import Citation`
- `ToolManifest` — `from services.plugin_svc.app.contracts.tool_manifest import ToolManifest`

The cross-service canary tests in `tests/cross_service/` enforce that
the field set is byte-identical across all consumers. Any field rename
MUST land in lockstep across the consumers.

## §4.3 Runtime contract (keystone)

Per Architect #6 §4.3 (Doc 08 §5 L113-124, verbatim):

- `Budget` — 4-field per Doc 08 §9 (tokens, wall_clock_s, tool_calls, cost_usd)
- `RunState` — 10-field per Doc 08 §5 L113-124
- `Step` — 11-field operational minimum (Q-6.1)
- `Evidence` — per Doc 15 §6 L70-81 (Q-6.2: source_url is `str`)
- `Plan` — per-run-type union (Q-6.3): `DiscoveryPlan | ValidationPlan | ReportPlan`

## Layout

```
services/agent-runtime/
  app/
    main.py              # FastAPI bootstrap
    contracts/           # §4.3 typed surfaces
    mcp/                 # gateway + policy
    agents/              # 17 per-agent stubs per Doc 09 §20.1
    workflows/           # orchestrator + specialists + verifier
    db/                  # agent schema (TRD Doc 02 §5.2 L219)
    api/                 # REST endpoints
  tests/
    unit/
    integration/
    cross_service/       # byte-identical canary tests
  pyproject.toml
  Dockerfile
  README.md
```

## Quick start

```bash
# Unit + integration + canary tests
pip install -e ".[dev]"
pytest tests/

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## See also

- Architect #6 BAND-3-DESIGN: `issues_for_architect/issue_006_architect_design.md`
- Conductor decisions (Q-6.x): `~/.claude/projects/.../memory/conductor-decisions-2026-07-29.md`
- Cross-service canary discipline: `~/.claude/projects/.../memory/arch-006-redispatch-verified-2026-07-28.md`
