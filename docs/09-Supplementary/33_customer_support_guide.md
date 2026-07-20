---
title: Customer Support Guide
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 33 — Customer Support Guide

> How we support customers — from first ticket to resolution, with tier-specific SLAs and the playbooks for the issues we see most.

## Table of Contents

1. Purpose & Scope
2. Support principles
3. Channels
4. SLAs by tier
5. Ticket lifecycle
6. Severity model
7. Common issues & playbooks
8. Escalation paths
9. Self-serve resources
10. Support metrics
11. CSM (Customer Success Manager) motions
12. Voice & tone
13. Crisis communications
14. Tooling
15. Appendix

## 1. Purpose & Scope

This document is the contract for **customer support**. It governs:

- The support channels (in-app, email, chat, phone).
- SLAs by tier.
- The ticket lifecycle and severity model.
- The playbooks for the most common issues.
- Escalation paths into engineering.

It does not cover sales (Document 32) or customer success motions (Section 11).

## 2. Support principles

1. **The customer is the source of truth.** Their description of the problem is real, even if our logs disagree.
2. **One owner.** Every ticket has one assigned person.
3. **Communicate first, fix second.** Update before you ship.
4. **Document the workaround.** Even before the fix.
5. **Close the loop.** When the fix ships, the customer hears from us.

## 3. Channels

| Channel | Free | Solo | Team | Enterprise |
|---|---|---|---|---|
| Help center | ✔ | ✔ | ✔ | ✔ |
| Community forum | ✔ | ✔ | ✔ | ✔ |
| Email | — | ✔ (48h) | ✔ (8h) | ✔ (4h) |
| In-app chat | — | — | ✔ (8h) | ✔ (1h) |
| Phone | — | — | — | ✔ (1h) |
| Dedicated CSM | — | — | — | ✔ |
| Slack Connect | — | — | — | ✔ (Enterprise) |

## 4. SLAs by tier

| Tier | First response | Resolution target |
|---|---|---|
| Free | 48h business hours | Best-effort |
| Solo | 48h business hours | 5 business days |
| Team | 8h business hours | 2 business days |
| Enterprise | 1h business hours, 24x7 for SEV-1 | 1 business day (SEV-1: 4h) |

## 5. Ticket lifecycle

```
New → Triaged → In Progress → Waiting on Customer → Resolved → Closed
```

- **New** — customer submitted.
- **Triaged** — severity assigned, owner assigned.
- **In Progress** — actively being worked.
- **Waiting on Customer** — needs more info; auto-reminded after 5 days.
- **Resolved** — fix shipped or workaround provided; auto-closed after 7 days.
- **Closed** — terminal.

## 6. Severity model

| Sev | Definition | Examples | Response |
|---|---|---|---|
| SEV-1 | Service down; data loss; security incident | Login broken; reports failing | Page on-call; < 1h response |
| SEV-2 | Significant degradation; major feature broken | Discovery returns 0 hits; export fails | < 4h response |
| SEV-3 | Limited impact; workaround exists | Specific report type errors; UI bug | < 24h response |
| SEV-4 | Cosmetic / minor | Typo; dark mode glitch | < 1 week |

## 7. Common issues & playbooks

### 7.1 "My report failed mid-run"

1. Check run status in the agent observability dashboard.
2. Capture run_id; check partial findings.
3. If transient → re-run.
4. If persistent → check source health; escalate to AI on-call.

### 7.2 "The score doesn't match my expectation"

1. Show the score breakdown + rationale + citations.
2. If the rubric is custom → explain how the dimension was scored.
3. Offer a manual override (Document 09 §17).
4. If a calibration issue → tag for monthly calibration review.

### 7.3 "I'm being charged for overages I didn't expect"

1. Pull the usage record.
2. Explain how the cap works.
3. Offer a plan upgrade or overage pack.
4. Refund if our metering is wrong.

### 7.4 "I can't log in"

1. Check Auth0 logs.
2. Reset password or magic link.
3. If SSO issue → engage the customer's IdP admin.
4. If MFA issue → walk through recovery.

### 7.5 "The citation is wrong / outdated"

1. Show the chunk and the source URL.
2. If our index is stale → trigger a re-fetch.
3. If the source itself is wrong → file a source-quality ticket.
4. Re-screenshot the report.

### 7.6 "I want to delete my data"

1. Verify identity.
2. Trigger account deletion (Document 29 §9).
3. Confirm within 30 days.
4. Send data export before deletion if requested.

### 7.7 "My source isn't being included"

1. Check the source is enabled in workspace settings.
2. Check source health (rate limit, error rate).
3. If the source is failing → escalate; if it's expected to fail → notify user.

## 8. Escalation paths

| Issue | Escalate to |
|---|---|
| Auth / billing | Auth on-call or billing on-call |
| AI plane (discovery, validation, scoring, report) | AI on-call |
| Backend service | Service on-call |
| Frontend / UI | Web on-call |
| Data export / deletion | Compliance + Data on-call |
| Security incident | Security on-call |
| Customer threatening churn | CSM + Sales Lead |

## 9. Self-serve resources

- **Help center** — articles indexed and searchable; updated weekly.
- **Sample reports** — anonymized board reports and briefs.
- **Video tutorials** — 5–10 minutes each, in the help center.
- **Changelog** — every release with screenshots.
- **Community forum** — peer-to-peer, with light moderation.
- **Office hours** — weekly live Q&A (Team+).

## 10. Support metrics

| Metric | Target |
|---|---|
| First-response SLA attainment | 95% |
| Resolution SLA attainment | 90% |
| CSAT | 4.5/5 |
| NPS (post-resolution) | 60+ |
| Tickets per active customer / month | < 0.5 |
| Self-serve deflection rate | 50% (Tier 1) |
| Escalation rate to engineering | < 8% |
| Median time to resolution (Solo) | 24h |
| Median time to resolution (Team) | 6h |
| Median time to resolution (Enterprise SEV-1) | 1h |

## 11. CSM motions

### 11.1 Cadence (Enterprise)

- **Kickoff** — week 1.
- **Adoption check-in** — week 4.
- **First QBR** — month 3.
- **Quarterly QBRs** — ongoing.
- **Renewal planning** — T-90.

### 11.2 Health score

- **Inputs:** logins, reports, integrations, NPS, ticket count.
- **Score:** green / yellow / red.
- **Action:** green = nurture; yellow = proactive outreach; red = executive escalation.

### 11.3 Expansion signals

- Usage trends up → upgrade conversation.
- New use case surfaced → cross-sell.
- Stakeholder expansion → introduce new buyer.

## 12. Voice & tone

- **Empathetic, not patronizing.**
- **Specific, not generic.**
- **Confident, not arrogant.**
- **Concise, not curt.**

Tone spectrum:

| Context | Tone |
|---|---|
| First contact | Warm, helpful |
| Bug report | Apologetic, action-oriented |
| Feature request | Curious, transparent about roadmap |
| Angry customer | Calm, owning, clear next steps |
| Resolution | Brief, factual, with a "what's next" |

## 13. Crisis communications

- **SEV-1** — within 15 min: status page, in-app banner.
- **Email** to all affected customers within 1h.
- **Postmortem** within 7 days; published publicly.
- **CSM outreach** to all Enterprise customers on the same day.

## 14. Tooling

- **Helpdesk:** Zendesk.
- **Live chat:** Intercom (post-MVP) → custom (v2).
- **Phone:** Dialpad.
- **Knowledge base:** Zendesk Guide.
- **Community:** Discourse.
- **SLAs:** Zendesk + custom monitoring.
- **CSM tool:** Vitally / Catalyst.
- **Surveys:** Delighted (CSAT), Wootric (NPS).

## 15. Appendix

### 15.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 15.2 Cross-references

- Sales Playbook: Document 32.
- Onboarding: Document 37.
- Operations: Document 28.
- Security: Document 21.

---

> *End of Document 33 — Customer Support Guide. A good support interaction is itself a feature.*
