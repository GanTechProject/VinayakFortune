---
title: Operations Guide
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 28 — Operations Guide

> The day-2 playbook. How on-call works, what to do in an incident, how to run a release, and how to keep the platform healthy.

## Table of Contents

1. Purpose & Scope
2. Roles
3. On-call
4. Incident response
5. Runbooks
6. Releases
7. Capacity & scaling
8. Disaster recovery
9. Cost management
10. Vendor management
11. Customer comms during incidents
12. Postmortems
13. Continuous improvement
14. Appendix

## 1. Purpose & Scope

This document is the contract for **operations** — what happens after a feature is built. It governs on-call, incident response, releases, scaling, and the recurring rhythms that keep the platform healthy.

## 2. Roles

| Role | Responsibilities |
|---|---|
| On-call primary | First responder; pages → triage → engage |
| On-call secondary | Backup; engages on primary unavailability |
| Service owner | Owns the service's runbook and SLOs |
| Incident commander | Runs the incident; coordinates response |
| Comms lead | Owns customer comms during the incident |
| Security lead | Owns security incidents and forensics |
| SRE | Owns the platform; deploys, scales, debugs infra |

## 3. On-call

- **Primary + secondary** rotation; weekly.
- **Handoff** Friday 10:00 local; documented.
- **Tooling:** PagerDuty + Slack + Datadog + AWS console.
- **Expectation:** acknowledge within 5 min; engaged within 15 min.
- **Compensation:** paid on-call stipend; documented in the People handbook.

## 4. Incident response

### 4.1 Severity

| Sev | Definition | Response time | Customer comms |
|---|---|---|---|
| SEV-1 | Major outage; data loss; security breach | < 15 min | Status page + email |
| SEV-2 | Significant degradation; partial outage | < 30 min | Status page |
| SEV-3 | Limited impact; workaround exists | < 24h | Backlog |
| SEV-4 | Cosmetic / minor | < 1 week | Backlog |

### 4.2 Process

1. **Detect** — page from monitoring, customer report, or internal user.
2. **Triage** — on-call confirms; declares severity; opens incident channel.
3. **Mitigate** — restore service (rollback, scale, disable feature flag).
4. **Resolve** — find and fix root cause.
5. **Close** — verify; post comms; schedule postmortem.

### 4.3 Communication

- Status page updated within 15 min for SEV-1/2.
- Customer email within 1h for SEV-1.
- In-app banner for active incidents.
- Postmortem published within 7 days.

## 5. Runbooks

Every service has a runbook with:

- Service overview (one paragraph).
- Health endpoints and what they mean.
- Common failure modes and responses.
- Escalation contacts.
- Links to dashboards.
- Recent incidents and their resolutions.

Runbooks are in `docs/runbooks/<service>.md` and reviewed quarterly.

## 6. Releases

See Document 24 §6. The release flow is:

1. Tag `vX.Y.Z`.
2. Auto-deploy to canary.
3. Soak 24h; SLO monitoring.
4. Auto-promote or hold.
5. Release notes auto-generated; manually edited.
6. Customer comms drafted (in-app banner, email, status page if relevant).

## 7. Capacity & scaling

- **Stateless services** scale on CPU + RPS.
- **Stateful services** scale via replicas; vertical scale for primary DB.
- **AI plane** scales on queue depth; preemptible workers for backfill.
- **Forecasting** monthly; pre-provisioning for known spikes.

## 8. Disaster recovery

- See TRD §12 and Document 21 §12.
- **RPO 1h, RTO 4h.**
- **Drill** quarterly; result reviewed; misses are SEV-2.

## 9. Cost management

- **Per-service cost** dashboarded daily.
- **Per-workspace cost** dashboarded daily.
- **Budgets** with 80% and 100% alerts.
- **Reserved capacity** reviewed quarterly.
- **Anomaly** alerts on > 2σ deviation.

## 10. Vendor management

- **Critical vendors** (Auth0, Anthropic, OpenAI, Stripe, AWS) reviewed quarterly.
- **Contract renewal** calendar owned by finance.
- **Status feeds** integrated into our status page where possible.
- **Vendor incidents** are tracked and reviewed.

## 11. Customer comms during incidents

- **Status page** is the source of truth.
- **In-app banner** within 30 min of SEV-1.
- **Email** within 1h of SEV-1.
- **Postmortem** published within 7 days.
- **Template** library maintained by the comms lead.

## 12. Postmortems

- **Required for** SEV-1 and SEV-2; encouraged for SEV-3.
- **Format:** blameless; timeline; contributing factors; customer impact; what we learned; action items.
- **Action items** are tickets with owners and dates.
- **Reviewed** by leadership monthly.
- **Trend** tracked; systemic issues are escalated.

## 13. Continuous improvement

- **Weekly ops review** — incidents, alerts, on-call feedback.
- **Monthly SLO review** — SLO compliance and trends.
- **Quarterly DR drill.**
- **Annual** — major tabletop; full security review.

## 14. Appendix

### 14.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 14.2 Cross-references

- DevOps: Document 23.
- Monitoring: Document 25.
- Security: Document 21.
- AI Operations: Document 18.

---

> *End of Document 28 — Operations Guide. Operations is the discipline that makes the system trustworthy.*
