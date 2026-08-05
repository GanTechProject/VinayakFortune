"""agent-runtime.contracts — the §4.3 typed runtime contract.

Per Architect #6 §4.3, the keystone cross-service contract:
- Source: IMPORTED from rag-svc (NOT re-defined)
- Budget: 4-field per Doc 08 §9
- RunState: 10-field per Doc 08 §5 L113-124
- Step: 11-field operational minimum
- Evidence: per Doc 15 §6
- Plan: per-run-type union (Q-6.3)
"""
