"""agent-runtime db — the `agent` schema (TRD Doc 02 §5.2 L219).

3 tables:
- agent_run        (one row per run)
- agent_step       (one row per Step appended to RunState.history)
- agent_tool_call  (one row per MCP call)

agent-runtime OWNS this schema. No other service writes to it.
"""
