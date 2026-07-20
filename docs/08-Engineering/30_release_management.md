---
title: Release Management
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 30 — Release Management

> How a release is cut, communicated, and supported. The contract for what a release means to engineering, product, sales, support, and customers.

## Table of Contents

1. Purpose & Scope
2. Release cadence
3. Release contents
4. Pre-release checklist
5. Release cut
6. Canary & promotion
7. Release notes
8. Customer comms
9. Rollback
10. Hotfixes
11. Support
12. Post-release
13. Appendix

## 1. Purpose & Scope

This document is the contract for **release management**. It defines what a release is, how it ships, and how the rest of the company supports it.

## 2. Release cadence

- **Weekly release tag** for engineering.
- **Monthly product release** that bundles weekly tags into a customer-facing release.
- **Ad-hoc** for security hotfixes.

## 3. Release contents

Each release is a **coherent unit** of work:

- A versioned set of PRs.
- A migration plan (if any).
- A flag rollout plan.
- A rollback plan.
- A monitoring plan.
- A customer-comm plan.

## 4. Pre-release checklist

- [ ] Scope is locked.
- [ ] All acceptance criteria met.
- [ ] NFRs green on staging.
- [ ] Security review (if in scope).
- [ ] Documentation updated.
- [ ] Migration tested in staging.
- [ ] Rollback tested in staging.
- [ ] Release notes drafted.
- [ ] Customer comms drafted.
- [ ] On-call informed.

## 5. Release cut

1. Tag `vX.Y.Z` on main.
2. Build & deploy to canary.
3. Soak 24h.
4. SLO review; auto-promote or hold.

## 6. Canary & promotion

- **10% of traffic** for 24h.
- **Monitoring:** SLO burn rate, error rate, latency, AI verifier pass rate.
- **Decision:** auto-promote if green; hold for human review if not.
- **Promotion:** full rollout within 1h of decision.

## 7. Release notes

- **Auto-generated** from PR titles + labels.
- **Manually edited** for clarity, customer framing, and screenshots.
- **Published** to `changelog.ventureminer.ai` and as an in-app banner.
- **Tagged** with the product area (Discovery, Validation, Reporting, etc.).

## 8. Customer comms

- **Weekly tags:** internal only.
- **Monthly release:**
  - In-app banner on the new version.
  - Email to active users if the change is significant.
  - Blog post for major changes.
- **Hotfixes:** status page + email for SEV-1/2.

## 9. Rollback

- **Automatic** on health-check fail.
- **Manual** via `argocd app rollback` or feature flag flip.
- **Backout plan** documented per release.
- **Post-rollback review** for any non-trivial rollback.

## 10. Hotfixes

- **For** SEV-1 and SEV-2 only.
- **Branch from main; expedited gates; direct to prod.**
- **Hotfix review** by on-call + second engineer.
- **Hotfix notes** added to the next release.

## 11. Support

- **Tier 1:** in-product help center + chatbot.
- **Tier 2:** support engineers; business hours; < 8h response (paid), < 48h (Free).
- **Tier 3:** engineering; on-call.
- **CSM:** Enterprise customers; named CSM; monthly QBR.

## 12. Post-release

- **T+1 day:** SLO compliance review.
- **T+7 days:** feature adoption check.
- **T+30 days:** KPI impact (where measurable).
- **T+release+1:** retrospective on release process (if any failures).

## 13. Appendix

### 13.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 13.2 Cross-references

- DevOps: Document 23.
- CI/CD: Document 24.
- Operations: Document 28.
- Roadmap: Document 06.

---

> *End of Document 30 — Release Management. A release is a promise; release management is how we keep it.*
