---
title: Memory Architecture
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 11 — Memory Architecture

> Memory is what makes the system **cumulative**. It carries state across runs so the platform gets sharper with use. This document defines the four memory layers, their contracts, and their governance.

## Table of Contents

1. Purpose & Scope
2. Memory layers
3. Session memory
4. Working memory
5. User memory
6. Workspace memory
7. Platform memory
8. Memory write discipline
9. Memory retrieval
10. Privacy & isolation
11. Retention & deletion
12. Failure modes
13. Evaluation
14. Appendix

## 1. Purpose & Scope

This document defines what the system remembers, for how long, and under what rules. It is the contract for cumulative learning without leaking across tenants.

## 2. Memory layers

| Layer | Lifetime | Scope | Store |
|---|---|---|---|
| Session | Single run | Run | In-process + scratchpad |
| Working | Single turn | User/turn | Redis (short TTL) |
| User | Per user account | User | Postgres + vector |
| Workspace | Per workspace | Workspace | Postgres + vector |
| Platform | All workspaces | Aggregate, anonymized | Postgres + vector |

## 3. Session memory

- **What:** the run's transient state — plans, scratchpad, intermediate variables.
- **Where:** in-process; the orchestrator's state.
- **When it ends:** when the run ends or is cancelled.
- **Retention:** none beyond the run.

## 4. Working memory

- **What:** the last N turns of a user session in the UI.
- **Where:** Redis, keyed by user.
- **TTL:** 1 hour idle, 8 hours absolute.
- **Used for:** multi-turn UI context, fast retrieval of recent items.

## 5. User memory

- **What:** durable user-level facts:
  - Preferences (preferred rubric, watchlists).
  - Calibration feedback (e.g. "I disagree with WTP for X — it should be lower").
  - Decision history (which opportunities the user advanced, archived, or rejected).
- **Where:** Postgres `memory.user_memory` + vector embeddings.
- **Used for:** personalization; calibrating future runs.
- **Retention:** while the account is active; 30-day grace after deletion.

## 6. Workspace memory

- **What:** durable workspace-level facts:
  - Common source priorities.
  - Past reports and their acceptance feedback.
  - Shared watchlists and rubrics.
- **Where:** Postgres `memory.workspace_memory` + vector.
- **Used for:** team-level personalization; cross-user learning.
- **Retention:** workspace lifetime; configurable per-tenant (Enterprise).

## 7. Platform memory

- **What:** aggregate, anonymized learnings:
  - Which rubric dimensions correlate with accepted opportunities.
  - Source reliability scores.
  - Common claim patterns.
- **Where:** Postgres + vector, no tenant_id column.
- **Used for:** model selection, source prioritization, calibration.
- **Retention:** indefinite; user opt-out does not apply to aggregated platform memory.
- **Privacy:** k-anonymity ≥ 50; no raw PII; no per-workspace data.

## 8. Memory write discipline

- **Atomic:** writes are append-only or versioned; never destructive.
- **Verified:** the verifier audits memory writes for citation and policy.
- **Versioned:** every memory record has a version; supersession is explicit.
- **Provenance:** every record carries the source run_id and actor.

## 9. Memory retrieval

- Agents can `memory.read(scope=user | workspace | platform, query=...)` and get top-k records.
- Retrieval uses the same hybrid index as RAG (Document 10) but with a different namespace.

## 10. Privacy & isolation

- A user can only read their own user memory.
- A user can only read workspace memory for workspaces they belong to.
- No cross-workspace memory.
- Platform memory is anonymized; no per-tenant data appears in queries.

## 11. Retention & deletion

- User deletion cascades to user memory.
- Workspace deletion cascades to workspace memory.
- Platform memory is not affected by user/workspace deletion (anonymized).
- Right-to-be-forgotten: users can request deletion of all user memory; honored within 30 days.

## 12. Failure modes

| Failure | Response |
|---|---|
| Memory store down | Degrade: skip memory; run still works without personalization. |
| Corrupted record | Quarantine; alert; do not block run. |
| Provenance missing | Reject write. |
| Schema drift | Migration via Atlas; backwards-compatible. |

## 13. Evaluation

- **Calibration accuracy:** does the system predict user acceptance better with memory? (Monthly)
- **Memory precision:** what fraction of recalled memories are useful? (Spot-checked)
- **Cross-tenant leakage tests:** monthly red-team.
- **Acceptance rate** of memory-informed reports vs. cold reports.

## 14. Appendix

### 14.1 Glossary

| Term | Definition |
|---|---|
| Session memory | Transient state of a single run |
| Working memory | Recent turn context (Redis) |
| User memory | Per-user durable facts |
| Workspace memory | Per-workspace durable facts |
| Platform memory | Anonymized aggregate learnings |

### 14.2 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 14.3 Cross-references

- Multi-Agent: Document 08.
- RAG: Document 10.

---

> *End of Document 11 — Memory Architecture. The four-layer model is the contract for cumulative learning without cross-tenant leakage.*
