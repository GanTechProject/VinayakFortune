---
title: DevOps & Infrastructure
version: v1.1
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 23 — DevOps & Infrastructure

> How the platform is built, deployed, and operated day-to-day. IaC, environments, release flow, and operational tooling.

## Table of Contents

1. Purpose & Scope
2. Principles
3. Infrastructure as Code
4. Environments
5. Source control & branching
6. Build & artifact
7. Release flow
8. Deployment
9. Feature flags
10. Database operations
11. Cost engineering
12. Operational tooling
13. Disaster recovery
14. Appendix

## 1. Purpose & Scope

This document is the contract for DevOps and infrastructure. It governs how code becomes a running service, how environments are managed, and how the platform is operated.

## 2. Principles

1. **Everything as code.** Infrastructure, configuration, runbooks.
2. **Boring is good.** We pick mature, well-supported tools.
3. **Reversible.** Every change has a defined rollback.
4. **Observable by default.** Every service emits traces, logs, metrics from day one.
5. **Cost-aware.** Engineers see the cost of what they ship.

## 3. Infrastructure as Code

- **Tool:** Terraform.
- **State:** S3 + DynamoDB lock; per environment.
- **Modules:** a `vma-` prefixed library; services consume via modules.
- **PR-based:** every change is a PR; CI plans, plan-comment in PR.
- **Drift detection:** nightly `terraform plan` against production; alerts on drift.

## 4. Environments

| Env | Purpose | Provisioned by | Data |
|---|---|---|---|
| dev | local | docker-compose | synthetic |
| ci | ephemeral per PR | GitHub Actions + Terraform | synthetic |
| staging | pre-prod | Terraform | anonymized prod clone |
| canary | production-like | Terraform | live mirror (read-only) |
| production | live | Terraform | customer |

Each environment is in its own AWS account; cross-account access is least-privilege.

## 5. Source control & branching

- **Monorepo** at `github.com/<org>/ventureminer`.
- **Branching:** trunk-based with short-lived feature branches.
- **Branch naming:** `<type>/<ticket>-<short-desc>` (e.g. `feat/VM-142-opportunity-bulk-actions`).
- **Commits:** Conventional Commits.
- **PRs:** small (< 400 lines), 2+ reviewers for sensitive areas, CODEOWNERS enforced.

### 5.1 Repository policy (canonical reference)

The canonical, version-controlled record of the `main` branch protection policy lives at `docs/00-Governance/branch_protection.json`. Operators and CI jobs that need to verify or re-apply the rule read that file, not the GitHub API directly. The current rule is:

- 0 approving reviews required (the author can self-merge).
- `enforce_admins: true` — admins are subject to the same rule.
- No force-pushes, no deletions.
- Conversation resolution required before merge.
- Status checks: strict, with the project's CI suite providing the required contexts.

> **Why 0 approvals on a single-human repo:** GitHub blocks self-approval of one's own PR for classic branch protection. The repository owner cannot satisfy a `required_approving_review_count: 1` rule by approving their own PR — the rule is structurally unsatisfiable when the author is the only writer. With 0 approvals, the author can merge their own PR through the UI/API. The PR-required gate (no direct pushes) and the CI-required gate (status checks must pass) provide the actual review-quality guarantees. The historical Option 3 cycle (DELETE rule → merge → PUT back) was the pre-Path-1 workaround for the unsatisfiable 1-approval gate; with 0 approvals, the cycle is no longer required for routine merges (the conductor hits the merge button directly). See `docs/00-Governance/branch_protection.json` for the policy comment block, and the `single-human-repo-self-approval-block` memory for the full rationale.

## 6. Build & artifact

- **Build:** GitHub Actions; matrix per service.
- **Artifact:** OCI images; pushed to ECR with content-addressable tags.
- **SBOM:** generated per build; signed (Sigstore).
- **Vulnerability scan:** Snyk per build; failure on critical.

## 7. Release flow

```
PR → CI (lint, unit, integration, contract) → main → staging deploy → smoke → tag → canary deploy → soak → prod deploy
```

- **PR:** required checks pass; CODEOWNERS satisfied.
- **Main:** every merge auto-deploys to staging.
- **Tag:** weekly release tag; auto-deploys to canary.
- **Soak:** canary holds for 24h with SLO monitoring.
- **Prod:** auto-promote if SLOs hold; otherwise hold for human review.

## 8. Deployment

- **Strategy:** rolling for stateless; blue/green for AI plane and DB.
- **Rollback:** automatic on health check fail; manual via `argocd app rollback`.
- **Migrations:** expand-contract; coordinated with service deploy.
- **Backout:** every release has a documented backout plan.

## 9. Feature flags

- **Tool:** LaunchDarkly (managed).
- **Default:** off.
- **Naming:** `<service>.<feature>`.
- **Lifetimes:** flags older than 90 days are removed or graduated.
- **Audit:** every flag change is logged.

## 10. Database operations

- **Migrations:** Atlas; PR-based; CI on ephemeral DB.
- **Backups:** daily full + continuous WAL; PITR to 35 days.
- **Restore drills:** quarterly.
- **Schema change** discipline (Document 05 §10).
- **Long-running migrations:** scheduled window, expand-contract, monitored.

## 11. Cost engineering

- **Per-service cost dashboards.**
- **Tagging:** every resource tagged with `service`, `env`, `owner`.
- **Budgets:** per service; alerts at 80%, 100%.
- **Right-sizing:** monthly review.
- **Anomaly detection:** cost spike alert.

## 12. Operational tooling

- **Observability:** Datadog (logs, metrics, traces, RUM, synthetics).
- **Incident:** PagerDuty.
- **On-call:** PagerDuty schedule; weekly rotation.
- **Status page:** public; auto-updated from health checks.
- **Runbooks:** in `docs/runbooks/`, owned by service teams.
- **ChatOps:** Slack-integrated deploys, rollbacks, feature-flag toggles.

## 13. Disaster recovery

- **RPO:** 1h.
- **RTO:** 4h.
- **DR region:** `us-west-2` (warm standby).
- **Drill:** quarterly; measured; postmortem on misses.
- See TRD §12 and Document 21 §12.

## 14. Appendix

### 14.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |
| v1.1 | 2026-07-20 | Doc Team | §5.1 "Repository policy" subsection added, pointing operators to `docs/00-Governance/branch_protection.json` as the canonical record of the `main` branch protection rule. Closes M-3 from the drift report (branch policy was previously invisible to readers of this DevOps doc). |

### 14.2 Cross-references

- TRD: Document 02.
- Backend: Document 05.
- Security: Document 21.
- Operations: Document 28.

---

> *End of Document 23 — DevOps & Infrastructure. Boring infrastructure is good infrastructure.*
