---
title: AI Operations & Evaluation
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 18 — AI Operations & Evaluation

> How we operate the AI plane in production. This document defines the day-2 concerns: monitoring, evaluation, calibration, incident response, and continuous improvement.

## Table of Contents

1. Purpose & Scope
2. AI observability
3. Evaluation framework
4. Calibration
5. Drift detection
6. Incident response
7. Cost management
8. Continuous improvement
9. Safety & policy
10. Appendix

## 1. Purpose & Scope

This document is the operational contract for the AI plane. It defines what we monitor, how we evaluate, how we respond to incidents, and how we improve the system over time.

## 2. AI observability

### 2.1 Spans

Every AI plane action is a span:

- `agent.run` — a complete run.
- `agent.step` — a single node execution.
- `rag.retrieve` — a retrieval call.
- `mcp.call` — a tool call.
- `llm.invoke` — a model call.
- `verifier.check` — a verification pass.

### 2.2 Metrics

- Per agent: call count, error rate, p50/p95/p99 latency, cost.
- Per tool: call count, error rate, p95 latency, cost, schema-violation rate.
- Per LLM: token in/out, cost, finish reason, fallback rate.
- Per run: total cost, total latency, verifier pass rate, retry count.

### 2.3 Logs

- Structured JSON to stdout; PII-redacted.
- LLM prompts and outputs logged at debug (sampled 100% for AI plane).
- Tool inputs/outputs logged at debug (PII-redacted).

## 3. Evaluation framework

### 3.1 Three layers

- **Offline:** golden test sets, run weekly.
- **Shadow:** new model/prompt runs in parallel; compared against current.
- **Online:** A/B tests on user-facing surfaces.

### 3.2 Golden test sets

- 500 labeled opportunities for validation.
- 200 labeled opportunities for scoring.
- 50 sample reports reviewed by experts.
- 100 adversarial prompts (hallucination, policy, PII).

### 3.3 Online metrics

- Report acceptance rate.
- Score re-edit rate.
- Re-run rate.
- Time-to-first-useful-artifact.
- Tool failure rate per user.

## 4. Calibration

- **Monthly:** score calibration against expert set (Document 16 §9).
- **Quarterly:** full rubric review.
- **Continuous:** user feedback loop feeds a calibration dataset (with consent).

## 5. Drift detection

- **Input drift:** changes in source data shape (e.g. X API breaking).
- **Output drift:** verifier pass rate falling, or model output distribution shifting.
- **User drift:** acceptance rate falling over a 7-day window.

Detection:

- Statistical tests (KS test) on embedding distributions.
- Threshold alerts on metrics.
- Anomaly detection on RAG retrieval recall.

Response:

- Roll back to last known-good model.
- Trigger rubric or prompt review.
- Notify the on-call AI lead.

## 6. Incident response

| Severity | Definition | Response |
|---|---|---|
| SEV-1 | AI plane down or producing unsafe output | Page on-call; freeze deploys; revert |
| SEV-2 | Significant quality drop or cost spike | Notify AI lead; investigate within 2h |
| SEV-3 | Single agent degraded | Investigate within 24h |
| SEV-4 | Cosmetic / minor | Backlog |

Runbooks live in Document 28 (Operations).

## 7. Cost management

- **Per-workspace budgets** with soft caps and overage alerts.
- **Per-run budgets** enforced by the orchestrator.
- **Cost attribution** to model, tool, run, and user.
- **Daily dashboards** of cost per active user.
- **Cost anomaly detection** — alerts on > 2σ deviation.

## 8. Continuous improvement

- **Weekly:** review online metrics.
- **Bi-weekly:** review agent outputs from production.
- **Monthly:** rubric and prompt review.
- **Quarterly:** full eval-set refresh and major prompt overhaul.
- **Yearly:** strategy review — new models, new techniques.

## 9. Safety & policy

- **PII detection** at AI plane boundary; redaction in prompts and logs.
- **Policy engine** filters disallowed content.
- **Adversarial testing** monthly.
- **Red-team** quarterly.
- **Audit log** of every policy decision.

## 10. Appendix

### 10.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 10.2 Cross-references

- Multi-Agent: Document 08.
- RAG: Document 10.
- MCP: Document 12.
- Scoring Engine: Document 16.
- Security: Document 21.
- Operations Guide: Document 28.

---

> *End of Document 18 — AI Operations & Evaluation. The AI plane is operated, not deployed and forgotten.*
