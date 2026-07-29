"""agent schema — TRD Doc 02 §5.2 L219.

3 tables:
- agent_run        (one row per run)
- agent_step       (one row per Step appended to RunState.history)
- agent_tool_call  (one row per MCP call)

PER DOC 02 §5.2 L219 (verified live). Schema owner is agent-runtime.
"""

from __future__ import annotations

# DDL for the agent schema. Postgres-flavoured (no pgvector here).
# The actual DDL applied via Alembic migrations in `migrations/`.

DDL_AGENT_RUN = """
CREATE TABLE IF NOT EXISTS agent.agent_run (
    run_id        UUID PRIMARY KEY,
    workspace_id  UUID NOT NULL,
    user_id       UUID NOT NULL,
    goal          TEXT NOT NULL,
    plan_type     TEXT NOT NULL,
    budget_tokens     BIGINT NOT NULL,
    budget_wall_clock_s INTEGER NOT NULL,
    budget_tool_calls  INTEGER NOT NULL,
    budget_cost_usd    NUMERIC(12, 4) NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'budget_exhausted', 'cancelled')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at   TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS agent_run_workspace_idx ON agent.agent_run(workspace_id);
CREATE INDEX IF NOT EXISTS agent_run_user_idx ON agent.agent_run(user_id);
CREATE INDEX IF NOT EXISTS agent_run_status_idx ON agent.agent_run(status);
"""

DDL_AGENT_STEP = """
CREATE TABLE IF NOT EXISTS agent.agent_step (
    step_id    UUID PRIMARY KEY,
    run_id     UUID NOT NULL REFERENCES agent.agent_run(run_id) ON DELETE CASCADE,
    agent_id   TEXT NOT NULL,
    node_name  TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    inputs     JSONB NOT NULL DEFAULT '{}'::jsonb,
    outputs    JSONB NOT NULL DEFAULT '{}'::jsonb,
    cost_json  JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_json JSONB
);
CREATE INDEX IF NOT EXISTS agent_step_run_idx ON agent.agent_step(run_id);
CREATE INDEX IF NOT EXISTS agent_step_agent_idx ON agent.agent_step(agent_id);
"""

DDL_AGENT_TOOL_CALL = """
CREATE TABLE IF NOT EXISTS agent.agent_tool_call (
    invocation_id UUID PRIMARY KEY,
    run_id        UUID NOT NULL REFERENCES agent.agent_run(run_id) ON DELETE CASCADE,
    step_id       UUID REFERENCES agent.agent_step(step_id) ON DELETE SET NULL,
    tool_id       TEXT NOT NULL,
    workspace_id  UUID NOT NULL,
    user_id       UUID NOT NULL,
    requested_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    latency_ms    INTEGER,
    cost_usd      NUMERIC(12, 6),
    exit_code     INTEGER,
    input_hash    TEXT,
    output_hash   TEXT,
    error_json    JSONB
);
CREATE INDEX IF NOT EXISTS agent_tool_call_run_idx ON agent.agent_tool_call(run_id);
CREATE INDEX IF NOT EXISTS agent_tool_call_tool_idx ON agent.agent_tool_call(tool_id);
"""

ALL_DDL: tuple[str, ...] = (
    DDL_AGENT_RUN,
    DDL_AGENT_STEP,
    DDL_AGENT_TOOL_CALL,
)


__all__ = ["ALL_DDL", "DDL_AGENT_RUN", "DDL_AGENT_STEP", "DDL_AGENT_TOOL_CALL"]
