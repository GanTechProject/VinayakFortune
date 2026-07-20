---
title: CI/CD
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 24 — CI/CD

> The continuous integration and delivery pipeline. How a commit becomes a running service, on every push, with the right gates.

## Table of Contents

1. Purpose & Scope
2. Principles
3. Pipeline overview
4. Pull request pipeline
5. Main branch pipeline
6. Release pipeline
7. Hotfix pipeline
8. Build & test stages
9. Quality gates
10. Secrets in CI
11. Pipeline observability
12. Pipeline cost
13. Appendix

## 1. Purpose & Scope

This document is the contract for the CI/CD pipeline. It governs how code is built, tested, scanned, and deployed from the moment a commit is pushed.

## 2. Principles

1. **Fast feedback.** PR pipeline < 10 min.
2. **Green main is sacred.** Main is always deployable.
3. **Boring by default.** Use the platform (GitHub Actions + Argo CD) and avoid custom logic.
4. **Gates are explicit.** No hidden approval; no skipped steps.
5. **Reproducible.** Same input → same output, byte-for-byte where possible.

## 3. Pipeline overview

```
PR opened  → PR pipeline (lint, unit, integration, contract, SAST, build)
PR merged  → main pipeline (deploy to staging)
Tag pushed → release pipeline (deploy to canary, soak, deploy to prod)
Hotfix     → hotfix pipeline (expedited to prod)
```

## 4. Pull request pipeline

Stages:

1. **Lint & format** — fail on any error.
2. **Type check** — TypeScript / mypy.
3. **Unit tests** — must pass; coverage reported.
4. **Integration tests** — must pass.
5. **Contract tests** — must pass.
6. **SAST** — Snyk; critical fails the build.
7. **Dependency scan** — Snyk + Dependabot; critical fails.
8. **Build** — produces an OCI image with content-addressable tag.
9. **SBOM** — generated and signed.
10. **Reviewer assignments** — CODEOWNERS.
11. **Comment** — coverage, SBOM, plan, image digest posted on PR.

## 5. Main branch pipeline

1. Build and tag with `git-<sha>`.
2. Push image to ECR.
3. Apply Terraform to staging.
4. Deploy to staging.
5. Run E2E smoke.
6. Update OpenAPI spec artifact.

## 6. Release pipeline

Weekly cadence:

1. Tag `vX.Y.Z` on main.
2. Build release image.
3. Deploy to canary (10% of traffic).
4. Soak for 24h; SLO monitoring.
5. If green → full deploy to production.
6. If red → hold; investigate; promote or revert.
7. Publish release notes (auto-generated from PRs + manual edits).

## 7. Hotfix pipeline

For SEV-1 / SEV-2 fixes:

1. Branch from main.
2. Same gates as PR, but a `hotfix` label skips the merge queue.
3. Manual approval by the on-call lead + a second engineer.
4. Direct deploy to production after staging smoke.

## 8. Build & test stages

- **Hermetic builds** — pinned tool versions; no network during build (except for fetching declared dependencies).
- **Caching** — dependencies cached per service.
- **Parallelization** — tests run in parallel where possible.
- **Retries** — flaky tests retried up to 2 times; persistent flakes quarantined.

## 9. Quality gates

| Gate | Required to pass |
|---|---|
| Lint / format | PR merge, release tag |
| Type check | PR merge, release tag |
| Unit tests | PR merge, release tag |
| Integration tests | PR merge, release tag |
| Contract tests | PR merge, release tag |
| SAST | PR merge, release tag |
| Dependency scan | PR merge, release tag |
| E2E (smoke) | Release tag |
| Performance smoke | Release tag |
| Security smoke | Release tag |

A gate failure blocks the next stage; a release tag with a failing gate cannot be cut.

## 10. Secrets in CI

- **OIDC** between GitHub Actions and AWS — short-lived credentials.
- No long-lived secrets in CI; secrets pulled at job start from AWS Secrets Manager via OIDC.
- Logs are scrubbed for secret patterns; CI fails if a known secret is found.

## 11. Pipeline observability

- **Datadog CI Visibility** for build & test traces.
- **GitHub checks** for status.
- **Slack** notifications on tag, on hold, on release.
- **Pipeline dashboards** for DORA metrics (lead time, deploy freq, MTTR, change fail rate).

## 12. Pipeline cost

- **Per-service budget** for CI minutes.
- **Self-hosted runners** for heavy tests (E2E, AI eval).
- **Spot instances** for ephemeral runners.

## 13. Appendix

### 13.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 13.2 Cross-references

- DevOps: Document 23.
- Testing: Document 22.
- Security: Document 21.

---

> *End of Document 24 — CI/CD. The pipeline is the spine of the engineering org.*
