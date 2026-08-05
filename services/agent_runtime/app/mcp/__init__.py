"""MCP gateway — per-agent singleton (Doc 12 §3 L42).

Per Architect #6 §8. Doc 12 §3 L42 (verbatim):
    agent → MCP client (in-process) → MCP gateway (singleton per agent) → tool server

The orchestrator CANNOT directly call any tool (Doc 07 §7.3 L176). All
tool calls flow through the MCP gateway; this is the single chokepoint
for policy enforcement (Doc 12 §2 L36).
"""
