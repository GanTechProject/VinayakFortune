---
title: Monitoring & Observability
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 25 — Monitoring & Observability

> How we see the platform. Logs, metrics, traces, RUM, synthetics, dashboards, alerts, and SLOs.

## Table of Contents

1. Purpose & Scope
2. Principles
3. Logs
4. Metrics
5. Traces
6. Real User Monitoring
7. Synthetics
8. Dashboards
9. Alerts
10. SLOs
11. AI plane observability
12. Cost observability
13. On-call
14. Appendix

## 1. Purpose & Scope

This document is the contract for observability. It defines what we collect, how we collect it, how we surface it, and how we act on it.

## 2. Principles

1. **Three pillars by default.** Every service emits logs, metrics, and traces.
2. **Structured.** JSON logs; standardized metric names; OTLP traces.
3. **PII-safe.** PII is redacted at the source.
4. **SLO-driven.** Alerts are SLO burn-rate based.
5. **Cheap at the edges.** Sampling where it doesn't hurt diagnosis.

## 3. Logs

- **Format:** JSON to stdout; shipped via Vector to Datadog.
- **Required fields:** `timestamp`, `level`, `service`, `env`, `trace_id`, `span_id`, `workspace_id` (where available), `message`, `attrs`.
- **PII:** redacted by the AGT-SAFETY filter; a redaction counter is emitted.
- **Sampling:** 100% error; 10% info in production.
- **Retention:** 30 days hot, 1 year cold.

## 4. Metrics

- **Standard:** Prometheus client.
- **Naming:** `<service>.<subject>.<metric>` (e.g. `opportunity.created.count`).
- **Required service-level metrics:**
  - `requests_total` (counter)
  - `request_duration_seconds` (histogram)
  - `errors_total` (counter, by code)
  - `in_flight` (gauge)
- **AI plane adds:**
  - `llm.tokens.total` (counter, by direction)
  - `llm.cost_usd.total` (counter)
  - `mcp.calls.total` (counter, by tool, by status)
  - `verifier.pass_rate` (gauge)

## 5. Traces

- **Tool:** OpenTelemetry → Datadog APM.
- **Sampling:** 100% for AI plane; 10% for HTTP at production; 100% in staging.
- **Required attributes:** `workspace_id`, `user_id` (hashed), `run_id`, `agent_id` (AI plane), `tool_id` (AI plane).
- **Service map:** built from spans; reviewed monthly.

## 6. Real User Monitoring

- **Tool:** Datadog RUM.
- **Coverage:** all web pages.
- **PII:** scrubbed; we do not capture form values.
- **Sampling:** 100% (cheap).

## 7. Synthetics

- **API smoke:** every 5 min; 10 critical endpoints.
- **Browser smoke:** every 30 min; key user journey.
- **Multi-region:** 3 PoPs.
- **Failures** page on-call.

## 8. Dashboards

Standard dashboards (one per service + cross-cutting):

- **Service health:** request rate, error rate, latency, saturation.
- **SLO:** current budget, burn rate, error budget remaining.
- **AI plane:** per-agent latency, per-tool cost, verifier pass rate.
- **Cost:** per-service, per-workspace.

A new service must have a dashboard before it ships.

## 9. Alerts

- **SLO burn rate** — page on burn ≥ 2x in 1h; ticket on burn ≥ 1x in 24h.
- **Error spike** — page on error rate > 5x baseline for 5 min.
- **Saturation** — page on resource > 85% for 15 min.
- **Synthetics** — page on any smoke fail.
- **Cost** — page on per-workspace cost > 1.5x of trailing 7-day average.

Every alert has a runbook link and an owner team.

## 10. SLOs

| Service | SLI | SLO |
|---|---|---|
| Public API | success rate | 99.9% (30d) |
| Dashboard | TTI < 1.5s p75 | 99.5% |
| Report generation | < 10 min p95 | 99% |
| Discovery | < 30s p95 for fresh hit | 99% |
| Validation (Standard) | < 8 min p75 | 95% |
| AI verifier | pass rate | 90% |

SLOs are reviewed quarterly.

## 11. AI plane observability

See Document 18 §2.

## 12. Cost observability

- Per-workspace cost dashboards.
- Per-service cost dashboards.
- Cost anomaly detection (2σ over trailing 14 days).
- Reserved Instance / Savings Plan coverage tracked.

## 13. On-call

- **Rotation:** weekly; primary + secondary.
- **Tooling:** PagerDuty + Slack + Datadog on-call.
- **Handoff:** Friday 10:00 local; documented.
- **Postmortem:** within 7 days of any SEV-1 / SEV-2.

## 14. Appendix

### 14.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 14.2 Cross-references

- TRD: Document 02 §11.
- DevOps: Document 23.
- AI Operations: Document 18.
- Operations Guide: Document 28.

---

> *End of Document 25 — Monitoring & Observability. If you can't see it, you can't fix it.*
