---
title: Implementation Roadmap
version: v1.1
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Implementation Roadmap

> **Document 06 — VentureMiner AI**
> The canonical delivery plan. Aligns the team around quarters, milestones, and release criteria. Inputs come from Documents 01–05; outputs become the engineering backlog and the GTM calendar.

## Table of Contents

1. Purpose & Scope
2. Roadmap Principles
3. Phases
4. Quarter-by-Quarter Plan
5. Milestones
6. Release Criteria (per release)
7. Team Plan
8. Dependencies
9. Risk-Adjusted Plan
10. Open Decisions
11. Appendix

## 1. Purpose & Scope

This document is the **single calendar** for the project. It defines:

- The phasing of work (Foundations → MVP → GA → Scale).
- The quarter-by-quarter deliverables.
- The release gate per release.
- The team composition and growth plan.
- The dependencies between workstreams.

It is intentionally less granular than the engineering backlog (which lives in the tracker). It is the layer above.

## 2. Roadmap Principles

1. **Vertical slices.** Every quarter ships a usable product increment, not a layer of a future product.
2. **Customer evidence early.** The first external users come at end of Q1 2027; everything before that exists to make that moment successful.
3. **Quality gates are non-negotiable.** No release ships without meeting Section 6.
4. **Roadmap is living.** Quarterly re-plan; new evidence rewrites the next two quarters, not the past.

## 3. Phases

| Phase | Window | Theme | Outcome |
|---|---|---|---|
| 0 — Foundations | Q3 2026 | Documentation, hiring, infra baseline | Locked PRD/TRD; team of 8; greenfield infra |
| 1 — Alpha | Q4 2026 | Discovery + validation internals | Internal dogfood of 4 personas |
| 2 — Beta | Q1 2027 | Full MVP behind a feature flag | 50 design partners, weekly releases |
| 3 — Public launch | Q2–Q3 2027 | Public MVP | Free + Solo + Team publicly available |
| 4 — Enterprise | Q4 2027 | SSO, SCIM, white-label | Enterprise plan GA; SOC 2 Type I |
| 5 — Scale | 2028 | i18n, multi-region, API v2 | 5,000 paid users; SOC 2 Type II; ISO 27001 |

## 4. Quarter-by-Quarter Plan

### Q3 2026 — Foundations

- Lock Documents 00–06 (this suite).
- Lock supplementary documents 31–37 (Pricing, Sales, Support, Marketing, Compliance, Sample Report, Onboarding) — required for Q1 2027 Beta and SOC 2 readiness downstream.
- Hire to 8 FTE (see Section 7).
- Set up monorepo, CI/CD, dev environments.
- Stand up staging environment.
- Stand up Auth0, Postgres, Redis, S3, NATS, Temporal, OpenSearch.
- Stand up LLM provider accounts (Anthropic + OpenAI).
- Internal demo: design review of the AI plane architecture (Documents 07–18).

**Exit criteria:** 8-person team operating; all baseline infra up; PRD/TRD/UIUX/Backend/Roadmap approved; supplementary documents 31–37 approved.

### Q4 2026 — Alpha

- Implement the **AI plane** end-to-end: discovery, validation, scoring, reporting.
- Implement the **AI plane services** end-to-end: `agent-runtime` (LangGraph orchestrator), `rag-svc`, `memory-svc`, `plugin-svc`, `source-svc`, `search-svc` (per Document 02 §4.1 service catalog).
- Implement **auth, workspace, opportunity, score, report** services.
- Build web shell (dashboard, opportunity list/detail, score, report viewer).
- Implement **MVP rubric** (default only).
- 1 design partner under NDA starts dogfooding the alpha.

**Exit criteria:** Internal users can run discovery → validation → score → brief in one sitting.

### Q1 2027 — Beta

- Implement **custom rubric editor** (Team-only).
- Implement **comparison report**.
- Implement **Slack integration** + email notifications.
- Implement **CSV import/export**.
- Implement **REST API** (alpha).
- Implement **Stripe billing** for Free, Solo, Team.
- Recruit 50 design partners across personas.
- Onboarding + product tour.
- Performance + security baseline.
- SOC 2 Type I readiness (policies, evidence collection).

**Exit criteria:** 50 active design partners; ≥ 70% activation; ≥ 80% weekly retention.

### Q2 2027 — Hardening

- SOC 2 Type I audit (Type II observation period starts).
- Performance tuning against NFRs.
- Pricing validation (A/B on Solo and Team).
- Content (help center, academy, sample reports).
- Public marketing site and docs site.
- Public launch readiness review (security, legal, support).

**Exit criteria:** All release criteria in Section 6 met for public launch.

### Q3 2027 — Public launch (MVP)

- Public release: Free, Solo, Team.
- ProductHunt, HN, indie founder communities.
- Sales pipeline of 10 enterprise prospects.
- First 100 paying customers.

**Exit criteria:** $20k MRR; 200 paid users; 92% weekly retention.

### Q4 2027 — Enterprise

- Enterprise plan GA: SSO, SCIM, white-label, custom DPA, 99.9% SLA.
- First 5 enterprise customers.
- SOC 2 Type I issued.
- Start ISO 27001 readiness.
- API v1 GA.

**Exit criteria:** $80k MRR; 600 paid users; 5 enterprise customers.

### Q1 2028 — Scale (i18n + continuous)

- Continuous discovery ("always-on" mode).
- Webhooks + Notion integration.
- i18n: Spanish, German, Japanese.
- Self-host pilot (closed beta) for one Fortune 500.

**Exit criteria:** $200k MRR; 1,500 paid users; 12 enterprise customers.

### Q2 2028 — Scale (resilience + integrations)

- SOC 2 Type II issued.
- Linear / Jira integration.
- Public API v2.
- Multi-region (EU residency for Enterprise).
- MCP gateway for external clients.

**Exit criteria:** $400k MRR; 3,000 paid users; 18 enterprise customers.

### Q3 2028 — Scale (platform)

- ISO 27001 issued.
- Public release of MCP gateway.
- Rubric library (community-shared rubrics).
- Self-host GA for select segments.

**Exit criteria:** $700k MRR; 4,500 paid users; 23 enterprise customers.

### Q4 2028 — Year-2 close

- $1M MRR run-rate.
- 5,000 paid users.
- Series A → B transition (target $4M ARR).
- Strategic partnerships (analytics, data providers).

**Exit criteria:** $1M MRR; Series B terms in market.

## 5. Milestones

| Milestone | Date | Owner |
|---|---|---|
| Documentation suite v1.0 | 2026-07-20 | Doc Lead |
| Infra baseline up | 2026-09-30 | Platform Lead |
| Alpha: end-to-end internal | 2026-12-20 | Eng Lead |
| Beta: 50 design partners | 2027-03-31 | Product Lead |
| SOC 2 Type I readiness | 2027-06-30 | Security Lead |
| Public launch | 2027-07-15 | CEO |
| First 5 enterprise customers | 2027-12-15 | Sales Lead |
| SOC 2 Type I issued | 2027-12-15 | Security Lead |
| SOC 2 Type II issued | 2028-06-15 | Security Lead |
| $1M MRR run-rate | 2028-12-15 | CEO + Sales |
| ISO 27001 issued | 2028-09-15 | Security Lead |

## 6. Release Criteria (per release)

A release ships only if all of the following are true.

### 6.1 Functional

- [ ] All acceptance criteria for the release scope are met.
- [ ] End-to-end smoke tests pass on staging with production data shapes.
- [ ] No P0/P1 bugs open for > 5 business days.

### 6.2 Non-functional

- [ ] NFRs (TRD §8) green for 7 consecutive days.
- [ ] Load test passed at 1.5x projected peak.
- [ ] Error budget intact for the previous release.

### 6.3 Security & compliance

- [ ] No open P0/P1 security issues.
- [ ] Dependency scan clean (no unmitigated critical CVEs).
- [ ] SAST/DAST clean for the changed surface.
- [ ] Threat model updated if architecture changed.

### 6.4 Operational

- [ ] Runbook updated.
- [ ] Dashboards and alerts updated.
- [ ] Rollback plan documented and tested in staging.
- [ ] On-call rotation staffed.

### 6.5 Documentation & comms

- [ ] Release notes drafted.
- [ ] Customer comms drafted (email + in-app banner).
- [ ] Public docs updated.
- [ ] Sales enablement updated if Enterprise-impacting.

## 7. Team Plan

### 7.1 End-of-year targets

| Year | FTE | Composition |
|---|---|---|
| 2026 | 8 | 4 eng, 1 AI/ML, 1 design, 1 product, 1 GTM |
| 2027 | 20 | + 6 eng, 1 sales, 1 customer success, 1 marketing, 1 ops, 1 security |
| 2028 | 38 | + 8 eng, 2 sales, 2 CS, 2 marketing, 1 ops, 1 security, 1 finance, 1 people |

### 7.2 Roles at scale

- **Engineering:** backend, frontend, AI/ML, platform/SRE.
- **Product:** PM, design, doc lead.
- **GTM:** sales (SDR + AE), customer success, marketing, content.
- **Operations:** finance, legal, security, people.

## 8. Dependencies

- **External:**
  - Auth0 availability.
  - LLM provider availability and pricing.
  - Source API stability (X, Reddit, GitHub, AppStores, etc.).
  - Stripe + tax compliance.
  - SOC 2 auditor scheduling.
- **Internal:**
  - Architecture docs (07–30) signed off before corresponding engineering work begins.
  - Rubric engine (Document 13) must be stable before custom rubric UI ships.

## 9. Risk-Adjusted Plan

| Risk | Plan B |
|---|---|
| Auth0 delays GA | Drop to self-hosted OIDC stub in v1; migrate later |
| LLM provider price hike | Self-host Llama-class model for routine synthesis |
| Source API locked | License alternative providers; degrade gracefully |
| Enterprise sales cycle | Push Team tier as wedge; productize admin features |
| SOC 2 audit slip | Defer Enterprise GA by 1 quarter; do not delay public launch |
| Hiring slip | Use agency + fractional exec for design / security |

## 10. Open Decisions

- DOC-OD-01: Where to host the LLM plane (AWS vs. dedicated GPU) — decision by 2026-09-30.
- DOC-OD-02: Self-host vs. Auth0 for identity long-term — decision by 2027-03-31.
- DOC-OD-03: pgvector → Qdrant migration trigger — decision at 5M embeddings or Year 1.
- DOC-OD-04: API v2 protocol (REST stays, gRPC optional) — decision by 2028-Q1.

## 11. Appendix

### 11.1 Roadmap visual

```
2026 Q3 ─ Foundations ──── docs, infra, hire
2026 Q4 ─ Alpha ────────── AI plane, MVP services
2027 Q1 ─ Beta ─────────── 50 partners, billing
2027 Q2 ─ Hardening ────── SOC 2 readiness, content
2027 Q3 ─ Public launch ── Free + Solo + Team
2027 Q4 ─ Enterprise ───── SSO, SCIM, white-label
2028 Q1 ─ Scale (i18n) ─── es, de, ja; continuous
2028 Q2 ─ Scale (resil.) ─ SOC 2 II, EU residency
2028 Q3 ─ Scale (platf.) ─ MCP, rubrics, self-host
2028 Q4 ─ Year-2 close ── $1M MRR, Series B
```

### 11.2 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |
| v1.1 | 2026-07-20 | Doc Team | Q3 2026 exit criteria expanded to include supplementary docs 31–37 (closes H-3 from drift report); Q4 2026 plan names the AI plane services explicitly (`agent-runtime`, `rag-svc`, `memory-svc`, `plugin-svc`, `source-svc`, `search-svc` per Document 02 §4.1) |

### 11.3 Cross-references

- PRD: Document 01.
- TRD: Document 02.
- AI Architecture: Documents 07–18.
- Engineering: Documents 19–30.

---

> *End of Document 06 — Implementation Roadmap. The roadmap is reviewed every quarter; substantive changes require a new revision.*
