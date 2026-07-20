---
title: Product Requirements Document (PRD)
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Product Requirements Document (PRD)

> **Document 01 — VentureMiner AI**
> The canonical product specification. This document defines the *what* and *why* of the AI Venture Intelligence Platform. All other documents (architecture, design, engineering) derive from the requirements captured here.

## Table of Contents

1. Executive Summary
2. Product Vision & Mission
3. Market Opportunity
4. Problem Statement
5. Stakeholders & User Personas
6. Product Goals & Success Criteria
7. Functional Requirements
8. Non-Functional Requirements
9. Feature Catalogue
10. User Stories
11. KPIs & Success Metrics
12. Business Model
13. Risks & Assumptions
14. MVP Scope & Product Roadmap
15. Glossary & Appendix

## 1. Executive Summary

VentureMiner AI is an **AI Venture Intelligence Platform** that turns raw, fragmented market signals into validated, monetizable SaaS opportunities.

Today's entrepreneurs, intrapreneurs, and investors spend 60–80% of their discovery time on **manual research** — RSS feeds, Twitter threads, Product Hunt, LinkedIn, Google Trends, ad libraries, app store charts, job boards, SEC filings. The result is a **low-signal, high-bias pipeline** that misses opportunities or duplicates ideas already validated by better-resourced teams.

VentureMiner AI replaces that pipeline with an autonomous, multi-agent research system that continuously:

1. **Discovers** candidate opportunities from public, semi-public, and licensed sources.
2. **Validates** each opportunity against market size, growth, demand, willingness to pay, and competitive landscape.
3. **Scores** opportunities on a transparent, configurable rubric (market, demand, buildability, defensibility, AI-fit).
4. **Generates** board-ready reports with cited evidence.
5. **Surfaces** opportunities to the user via dashboards, alerts, and an API.

The platform is sold as a multi-tenant SaaS to **four primary personas** (Section 5): independent founders, corporate innovation teams, investors, and product/strategy consultants.

### 1.1 One-line value proposition

> *From signal noise to venture-ready decisions — in hours, not quarters.*

### 1.2 Strategic positioning

VentureMiner AI is positioned as a **decision-support layer** above the existing tool stack. It does not replace CRM, BI, or financial modeling tools — it provides the **upstream intelligence** those tools act on. Differentiation comes from three places:

- **Multi-agent research depth** — not one LLM prompt, but a coordinated team of specialist agents.
- **Evidence discipline** — every claim is cited; every score has a trace.
- **Calibrated scoring** — the rubric is exposed, versioned, and editable.

### 1.3 At a glance

| Metric | Value |
|---|---|
| Document | PRD v1.0 |
| Total requirements | 174 |
| MVP features | 22 |
| Personas | 4 primary, 2 secondary |
| Target launch | Q3 2027 (MVP) |
| Pricing tiers | 4 (Free, Solo, Team, Enterprise) |

## 2. Product Vision & Mission

### 2.1 Vision

A world where **anyone with ambition and a credible idea** can validate, refine, and launch a venture backed by the same caliber of market intelligence historically reserved for top-tier venture firms.

### 2.2 Mission

Build the most rigorous, transparent, and fast AI research platform for venture opportunity discovery and validation.

### 2.3 Guiding principles

1. **Evidence over opinion.** Every claim is sourced. Every score is traceable.
2. **Transparent models.** The rubric is a first-class artifact, not a black box.
3. **Human-in-the-loop.** AI accelerates; humans decide.
4. **Compounding knowledge.** Each run enriches the platform's corpus for the next.
5. **Operator-grade reliability.** If a researcher would trust it, an operator must trust it.

## 3. Market Opportunity

### 3.1 Total Addressable Market (TAM)

The global market for **market intelligence and competitive intelligence software** is approximately **$52B in 2026**, growing at a CAGR of ~13%. The subset relevant to VentureMiner AI — opportunity discovery, market sizing, and competitive monitoring — is **~$8.4B**.

### 3.2 Serviceable Addressable Market (SAM)

Geographically (NA + EU + ANZ) and segmentally (SMB founders, corporate innovation, VCs, consultancies), the SAM is **~$2.1B**.

### 3.3 Serviceable Obtainable Market (SOM)

Realistic 5-year capture assuming the product-market fit trajectory in this PRD: **$45M ARR** ≈ **~$63M in platform spend** at gross-margin-blended pricing.

### 3.4 Why now

- **LLM capability inflection.** Multi-agent orchestration and tool-use are now production-ready (2025–2026).
- **Cost collapse.** Inference cost per 1M tokens has dropped ~12x in 18 months.
- **Source accessibility.** APIs for X, Reddit, GitHub, Stripe, App Stores, SEC EDGAR, job boards, Google Trends, Similarweb, and SEMrush are mature and affordable.
- **Founder saturation.** Globally, ~580M people attempt a business each year; even 0.1% adoption of a $40/mo tool is a $28M ARR business.
- **Enterprise AI budget growth.** Corporate innovation teams have dedicated AI tooling budgets (avg $310k/year) — a wedge into enterprise.

### 3.5 Competitive landscape

| Segment | Players | Position |
|---|---|---|
| Market intelligence suites | Crayon, Klue, Kompyte | Enterprise CI, no opportunity generation |
| Trend monitoring | TrendWatching, Trend Hunter | Editorial, no AI |
| Indie research | SparkToro, Exploding Topics | Niche signals, no validation |
| VC deal flow | CB Insights, PitchBook | Closed-network deal sourcing |
| LLM research assistants | Perplexity Pro, You.com, ChatGPT Deep Research | Generic, not domain-tuned |

**White space:** no current product offers *closed-loop discovery → validation → scoring → report* for SaaS opportunities, with evidence discipline and an editable rubric.

## 4. Problem Statement

### 4.1 Jobs-to-be-done

When a founder, intrapreneur, or investor sits down to identify a new opportunity, they hire a research process to do the following jobs:

- **JOB-1** — *Find* ventures worth pursuing, faster than their peers.
- **JOB-2** — *Confirm* the opportunity is real, growing, and monetizable.
- **JOB-3** — *Compare* it against alternatives and the competitive landscape.
- **JOB-4** — *Decide* whether to commit time, money, or reputation to it.
- **JOB-5** — *Communicate* the decision to partners, LPs, or executives.

### 4.2 Today, this is broken

| Failure mode | Today | Cost |
|---|---|---|
| Manual research | 60–80% of discovery time | Weeks → quarters of latency |
| Bias | Confirmation bias, recency bias, network bias | Missed opportunities, false positives |
| Inconsistency | Different researchers, different rubrics | Non-comparable decisions |
| Opacity | "Why this score?" | Unauditable decisions |
| Brittleness | One spreadsheet crash = lost context | Repeated work |

### 4.3 Why this is the moment to fix it

Until 2024, this problem resisted automation because:

- Source integration was expensive.
- LLMs hallucinated evidence.
- Orchestrating multi-step research was brittle.

By 2026, all three are solvable. VentureMiner AI is built to capitalize on this convergence.

## 5. Stakeholders & User Personas

### 5.1 Primary personas

#### P-1: Indie Founder (e.g. Maya)

- **Demographics:** Solo or two-person team, pre-seed, technical.
- **Time per week on opportunity discovery:** 4–10 hours.
- **Pains:** Idea generation, validation, GTM.
- **Gains sought:** Confidence, speed, differentiation.
- **Buying behavior:** $30–$80/mo self-serve; will pay annually for a deal.
- **Success measure:** "I shipped a v1 in 90 days from first prompt."

#### P-2: Corporate Innovator (e.g. Daniel)

- **Demographics:** Innovation scout, corporate strategy, or new-venture team inside a Fortune 1000.
- **Time per week on opportunity discovery:** 10–20 hours.
- **Pains:** Quarterly reporting, executive-ready artifacts, sourcing outside the core market.
- **Gains sought:** Audit trail, repeatable process, breadth.
- **Buying behavior:** $25k–$120k/year contract; security review required.
- **Success measure:** "I delivered a pipeline of 12 validated adjacencies per quarter."

#### P-3: Early-Stage Investor (e.g. Aria)

- **Demographics:** Solo capitalist or analyst at a $50M–$500M fund.
- **Time per week on opportunity discovery:** 8–15 hours.
- **Pains:** Sourcing off-market, thesis consistency, deal memo throughput.
- **Gains sought:** Defensibility of thesis, memo reuse, faster screening.
- **Buying behavior:** $300–$1,500/seat/mo.
- **Success measure:** "I doubled my sourced-deal volume without adding headcount."

#### P-4: Product / Strategy Consultant (e.g. Lin)

- **Demographics:** Boutique consultancy or independent, 3–30-person firms.
- **Time per week on opportunity discovery:** 20+ hours (per engagement).
- **Pains:** Replicability, client-ready reports, source provenance.
- **Gains sought:** Brand differentiation, deliverable speed.
- **Buying behavior:** $200–$600/seat/mo, multi-seat.
- **Success measure:** "I deliver 3x more research engagements per quarter."

### 5.2 Secondary personas

- **S-1: Growth-stage founder** — validating adjacencies, market expansion.
- **S-2: Operator at a B2B SaaS company** — competitive positioning, market monitoring.

### 5.3 Anti-personas

We explicitly do **not** build for:

- **A-1: Hobbyists without willingness to act** — low willingness to pay, high support load.
- **A-2: Speculative trend-chasers** — chase every signal, never ship.
- **A-3: Pure coders who never speak to customers** — research is a means, not the product.

## 6. Product Goals & Success Criteria

### 6.1 Product goals (12-month horizon)

| # | Goal | Owner |
|---|---|---|
| PG-1 | Reach 5,000 paid users across all tiers | CEO + Growth |
| PG-2 | Reach $3M ARR | CFO + Sales |
| PG-3 | Hit a sustained NPS ≥ 50 | Product + Support |
| PG-4 | Maintain ≥ 92% weekly active rate among paid users | Product |
| PG-5 | Reduce median time-to-first-report from 6h to < 45 min | Engineering |
| PG-6 | Achieve 95%+ report acceptance (operator sign-off without rewrite) | Product |
| PG-7 | Land 25 enterprise customers ($25k+ ACV) | Sales |
| PG-8 | Reach SOC 2 Type II + ISO 27001 | Security + Compliance |
| PG-9 | Time-to-value ≤ 10 minutes from signup to first useful artifact | Product |
| PG-10 | Achieve 80% rubric customization adoption on Team/Enterprise | Product |

### 6.2 North Star Metric

**Validated opportunities acted on per week per active user.** This is the metric that ties the product to behavior we want to drive: not "reports generated" (gameable) but "opportunities a user committed to next action on."

### 6.3 Counter-metrics (to prevent gaming)

- Reports-per-user (cap to prevent farming)
- Report rejection rate (operator edit-after-generation)
- Subscription churn (per cohort)
- Time-to-edit (proxy for low-quality output)

## 7. Functional Requirements

This section enumerates functional requirements at the requirement-ID level defined in Document 00 §7.1. Each requirement has a unique ID, a one-line statement, an owner, an acceptance criterion summary, and a priority (P0 = MVP, P1 = GA, P2 = post-GA).

### 7.1 Authentication & Identity (REQ-AUTH)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-AUTH-0001 | Email/password signup with email verification | P0 | AC-AUTH-0001: User can sign up, verify, and log in. |
| REQ-AUTH-0002 | OAuth (Google, GitHub, Microsoft) | P0 | AC-AUTH-0002: User can link/unlink an OAuth provider. |
| REQ-AUTH-0003 | Magic-link sign-in | P1 | AC-AUTH-0003: User can sign in via one-time link. |
| REQ-AUTH-0004 | MFA via TOTP | P1 | AC-AUTH-0004: User can enroll and challenge with TOTP. |
| REQ-AUTH-0005 | SSO (SAML 2.0 / OIDC) for Enterprise | P0 for Enterprise | AC-AUTH-0005: Admin can configure IdP; users SSO. |
| REQ-AUTH-0006 | SCIM 2.0 provisioning | P0 for Enterprise | AC-AUTH-0006: Sync creates/updates/disables users. |
| REQ-AUTH-0007 | Role-based access control (Owner, Admin, Member, Viewer) | P0 | AC-AUTH-0007: Role gates all write actions. |
| REQ-AUTH-0008 | Workspace + project membership | P0 | AC-AUTH-0008: Users can belong to multiple workspaces. |
| REQ-AUTH-0009 | Audit log of auth events | P0 for Enterprise | AC-AUTH-0009: Log every sign-in, role change, token issue. |
| REQ-AUTH-0010 | Session timeout & refresh token rotation | P0 | AC-AUTH-0010: 30-day refresh, 8-hour idle. |

### 7.2 Discovery (REQ-DISC)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-DISC-0001 | Trend mining across configured sources | P0 | AC-DISC-0001: User sees ≥ 20 weekly trends. |
| REQ-DISC-0002 | Niche topic exploration | P0 | AC-DISC-0002: User enters seed → returns ≥ 10 adjacent topics. |
| REQ-DISC-0003 | Pain-point harvesting from public forums | P0 | AC-DISC-0003: User receives cited pain quotes. |
| REQ-DISC-0004 | Competitor-derivative opportunity generation | P0 | AC-DISC-0004: User uploads competitor list → returns derivative opportunities. |
| REQ-DISC-0005 | Source configuration (per workspace) | P1 | AC-DISC-0005: Admin can enable/disable sources. |
| REQ-DISC-0006 | Continuous background discovery ("always-on") | P1 | AC-DISC-0006: New opportunities surface daily. |
| REQ-DISC-0007 | Deduplication across sources | P0 | AC-DISC-0007: Same opportunity surfaces once. |
| REQ-DISC-0008 | Time-windowed discovery (last 7/30/90 days) | P0 | AC-DISC-0008: User filters discovery window. |
| REQ-DISC-0009 | Source attribution on every opportunity | P0 | AC-DISC-0009: Each opportunity lists its sources. |
| REQ-DISC-0010 | Saved searches | P1 | AC-DISC-0010: User can save and re-run a discovery query. |

### 7.3 Validation (REQ-VAL)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-VAL-0001 | Market size estimation (TAM/SAM/SOM) | P0 | AC-VAL-0001: User sees triangulated estimate with confidence. |
| REQ-VAL-0002 | Growth-rate estimation | P0 | AC-VAL-0002: User sees YoY and CAGR with sources. |
| REQ-VAL-0003 | Demand signal aggregation | P0 | AC-VAL-0003: User sees search volume, social volume, and intent. |
| REQ-VAL-0004 | Competitive landscape mapping | P0 | AC-VAL-0004: User sees competitor table with positioning. |
| REQ-VAL-0005 | Pricing benchmark collection | P0 | AC-VAL-0005: User sees competitor pricing tiers. |
| REQ-VAL-0006 | Customer review synthesis | P0 | AC-VAL-0006: User sees top 5 praised and complained features. |
| REQ-VAL-0007 | Buyer persona synthesis | P0 | AC-VAL-0007: User sees 1–3 buyer personas with citations. |
| REQ-VAL-0008 | Willingness-to-pay signal estimation | P0 | AC-VAL-0008: User sees WTP range with rationale. |
| REQ-VAL-0009 | GTM-channel diagnosis | P0 | AC-VAL-0009: User sees top 3 channels used by competitors. |
| REQ-VAL-0010 | Risk register | P0 | AC-VAL-0010: User sees top 5 risks with mitigations. |
| REQ-VAL-0011 | Validation depth setting (Quick / Standard / Deep) | P0 | AC-VAL-0011: User selects depth, sees time estimate. |
| REQ-VAL-0012 | Validation re-run with new data | P1 | AC-VAL-0012: User can re-validate and diff. |
| REQ-VAL-0013 | Human-expert override (manual evidence add) | P0 | AC-VAL-0013: User can attach manual evidence to a finding. |
| REQ-VAL-0014 | Calibration against prior decisions | P2 | AC-VAL-0014: User feedback improves future estimates. |

### 7.4 Scoring (REQ-SCORE)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-SCORE-0001 | Default rubric v1.0 | P0 | AC-SCORE-0001: Default rubric with 5 dimensions. |
| REQ-SCORE-0002 | Custom rubric editor | P0 for Team | AC-SCORE-0002: User can add, weight, rename dimensions. |
| REQ-SCORE-0003 | Per-dimension sub-criteria | P1 | AC-SCORE-0003: User can break a dimension into sub-criteria. |
| REQ-SCORE-0004 | Rubric versioning | P0 for Team | AC-SCORE-0004: Each rubric change is versioned. |
| REQ-SCORE-0005 | Score rationale trace | P0 | AC-SCORE-0005: Every dimension score shows contributing evidence. |
| REQ-SCORE-0006 | Score normalization across rubrics | P1 | AC-SCORE-0006: Scores comparable across versions. |
| REQ-SCORE-0007 | Score confidence intervals | P1 | AC-SCORE-0007: Each score has low/mid/high estimate. |
| REQ-SCORE-0008 | Portfolio view (multi-opportunity ranking) | P0 | AC-SCORE-0008: User can sort and filter by score. |
| REQ-SCORE-0009 | Risk-adjusted score | P1 | AC-SCORE-0009: Score weighted by risk dimension. |
| REQ-SCORE-0010 | Custom scoring weights per persona/team | P1 | AC-SCORE-0010: User can save weight presets. |

### 7.5 Reporting (REQ-RPT)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-RPT-0001 | One-page opportunity brief | P0 | AC-RPT-0001: Generated within 60 seconds. |
| REQ-RPT-0002 | Full validation report (10–25 pages) | P0 | AC-RPT-0002: Cover, exec summary, sections, sources. |
| REQ-RPT-0003 | Executive deck (slides) | P1 | AC-RPT-0003: Exportable to PPTX/Keynote. |
| REQ-RPT-0004 | Comparison report (≥ 2 opportunities) | P0 | AC-RPT-0004: Side-by-side comparison. |
| REQ-RPT-0005 | Report customization (chapter on/off) | P1 | AC-RPT-0005: User toggles sections. |
| REQ-RPT-0006 | Export to PDF, DOCX, MD, HTML | P0 | AC-RPT-0006: All four formats available. |
| REQ-RPT-0007 | Embed charts in reports | P0 | AC-RPT-0007: Charts auto-rendered from data. |
| REQ-RPT-0008 | White-label reports (Enterprise) | P0 for Enterprise | AC-RPT-0008: Logo, palette, footer configurable. |
| REQ-RPT-0009 | Report templates | P1 | AC-RPT-0009: User can save a report template. |
| REQ-RPT-0010 | Citations and footnotes | P0 | AC-RPT-0010: Every claim is footnoted. |
| REQ-RPT-0011 | Provenance panel (sources, freshness) | P0 | AC-RPT-0011: Each report lists its data freshness. |
| REQ-RPT-0012 | Scheduled report delivery | P1 | AC-RPT-0012: User can subscribe a digest. |

### 7.6 Dashboards & Workspace (REQ-DASH)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-DASH-0001 | Opportunity pipeline board | P0 | AC-DASH-0001: Kanban (Watching, Validating, Active, Archived). |
| REQ-DASH-0002 | Portfolio view | P0 | AC-DASH-0002: Multi-dimensional table. |
| REQ-DASH-0003 | Saved filters | P0 | AC-DASH-0003: User can save filter combos. |
| REQ-DASH-0004 | Alerts & notifications | P0 | AC-DASH-0004: User can configure alert rules. |
| REQ-DASH-0005 | Trends dashboard | P0 | AC-DASH-0005: Surface top trends per workspace. |
| REQ-DASH-0006 | Activity feed | P0 | AC-DASH-0006: Per-workspace activity timeline. |
| REQ-DASH-0007 | Quick search (Cmd-K) | P0 | AC-DASH-0007: Global search across opportunities, reports, sources. |
| REQ-DASH-0008 | Watchlists | P1 | AC-DASH-0008: User can watch keywords or competitors. |
| REQ-DASH-0009 | Multi-workspace switching | P0 | AC-DASH-0009: User can switch in one click. |

### 7.7 Integration & API (REQ-INT)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-INT-0001 | REST API | P0 | AC-INT-0001: OpenAPI 3.1 spec published. |
| REQ-INT-0002 | Webhooks | P1 | AC-INT-0002: Outbound event delivery. |
| REQ-INT-0003 | Zapier integration | P2 | AC-INT-0003: Public Zap. |
| REQ-INT-0004 | Notion integration | P1 | AC-INT-0004: Push opportunities and reports. |
| REQ-INT-0005 | Slack integration | P0 | AC-INT-0005: Receive alerts in Slack. |
| REQ-INT-0006 | Linear / Jira integration | P2 | AC-INT-0006: Convert opportunity into issue. |
| REQ-INT-0007 | CSV import/export | P0 | AC-INT-0007: Round-trip preserves data. |
| REQ-INT-0008 | Google Drive / Dropbox export | P2 | AC-INT-0008: Export reports to folder. |
| REQ-INT-0009 | Public API tokens (scoped) | P0 | AC-INT-0009: User can mint scoped tokens. |
| REQ-INT-0010 | Rate-limited public API | P0 | AC-INT-0010: Tier-based rate limits. |

### 7.8 Billing & Plans (REQ-BIL)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-BIL-0001 | Free tier with quotas | P0 | AC-BIL-0001: 5 reports/month, 1 user. |
| REQ-BIL-0002 | Solo plan ($39/mo) | P0 | AC-BIL-0002: 50 reports/month, 1 user. |
| REQ-BIL-0003 | Team plan ($199/mo + $39/seat) | P0 | AC-BIL-0003: Multi-user, custom rubric, SSO-ready. |
| REQ-BIL-0004 | Enterprise plan (custom) | P0 | AC-BIL-0004: SSO, SCIM, custom legal, SLA. |
| REQ-BIL-0005 | Stripe-backed billing | P0 | AC-BIL-0005: Self-serve checkout. |
| REQ-BIL-0006 | Annual discount (16%) | P0 | AC-BIL-0006: Annual plans show savings. |
| REQ-BIL-0007 | Usage-based overages | P1 | AC-BIL-0007: Soft cap with overage. |
| REQ-BIL-0008 | Plan upgrade/downgrade | P0 | AC-BIL-0008: Pro-rated billing. |
| REQ-BIL-0009 | Tax handling (US sales tax, EU VAT) | P0 | AC-BIL-0009: Tax computed and itemized. |
| REQ-BIL-0010 | Invoice history | P0 | AC-BIL-0010: All invoices downloadable. |

### 7.9 Settings & Admin (REQ-ADMIN)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-ADMIN-0001 | Workspace settings | P0 | AC-ADMIN-0001: Name, logo, default rubric. |
| REQ-ADMIN-0002 | Member management | P0 | AC-ADMIN-0002: Invite, remove, role change. |
| REQ-ADMIN-0003 | Source management | P0 | AC-ADMIN-0003: Enable/disable + credentials. |
| REQ-ADMIN-0004 | Billing & plan management | P0 | AC-ADMIN-0004: Self-serve plan changes. |
| REQ-ADMIN-0005 | Audit log (Enterprise) | P0 for Enterprise | AC-ADMIN-0005: Filterable, exportable. |
| REQ-ADMIN-0006 | API token management | P0 | AC-ADMIN-0006: Mint/revoke scoped tokens. |
| REQ-ADMIN-0007 | Custom report branding | P0 for Enterprise | AC-ADMIN-0007: Logo, palette, footer. |
| REQ-ADMIN-0008 | Data retention configuration | P0 for Enterprise | AC-ADMIN-0008: Per-data-class retention. |
| REQ-ADMIN-0009 | Webhook configuration | P1 | AC-ADMIN-0009: Endpoint + secret. |
| REQ-ADMIN-0010 | Compliance & DPA downloads | P0 for Enterprise | AC-ADMIN-0010: Self-serve DPA, SOC 2 report. |

### 7.10 Onboarding & Help (REQ-OB)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-OB-0001 | Interactive product tour | P0 | AC-OB-0001: First-run tour, skippable. |
| REQ-OB-0002 | Sample opportunities for first run | P0 | AC-OB-0002: One-click "try this". |
| REQ-OB-0003 | Help center (in-app) | P0 | AC-OB-0003: Search + articles. |
| REQ-OB-0004 | Email support (Free, Solo) | P0 | AC-OB-0004: < 48h response. |
| REQ-OB-0005 | In-app chat (Team) | P0 | AC-OB-0005: < 8h business hours. |
| REQ-OB-0006 | Dedicated CSM (Enterprise) | P0 for Enterprise | AC-OB-0006: Named CSM, monthly QBR. |
| REQ-OB-0007 | In-app feedback widget | P0 | AC-OB-0007: One-click feedback. |
| REQ-OB-0008 | Status page | P0 | AC-OB-0008: Public status.history. |
| REQ-OB-0009 | Changelog & release notes | P0 | AC-OB-0009: In-app + RSS. |
| REQ-OB-0010 | Onboarding checklist | P0 | AC-OB-0010: Tracks first 5 actions. |

### 7.11 Platform internals (REQ-PLAT)

| ID | Statement | Priority | AC summary |
|---|---|---|---|
| REQ-PLAT-0001 | Multi-tenant isolation | P0 | AC-PLAT-0001: Row-level isolation per workspace. |
| REQ-PLAT-0002 | Configurable data residency | P0 for Enterprise | AC-PLAT-0002: US, EU, APAC. |
| REQ-PLAT-0003 | Encryption at rest (AES-256) | P0 | AC-PLAT-0003: All persistent storage. |
| REQ-PLAT-0004 | Encryption in transit (TLS 1.3) | P0 | AC-PLAT-0004: All network traffic. |
| REQ-PLAT-0005 | Key management (KMS) | P0 | AC-PLAT-0005: Per-tenant DEKs. |
| REQ-PLAT-0006 | Background job orchestration | P0 | AC-PLAT-0006: Async pipelines survive restarts. |
| REQ-PLAT-0007 | Idempotency keys on write APIs | P0 | AC-PLAT-0007: Duplicate retries are no-ops. |
| REQ-PLAT-0008 | Event sourcing for AI pipeline | P0 | AC-PLAT-0008: Every AI step is replayable. |
| REQ-PLAT-0009 | Rate limiting per workspace | P0 | AC-PLAT-0009: Tier-based limits. |
| REQ-PLAT-0010 | Health endpoints | P0 | AC-PLAT-0010: `/healthz`, `/readyz`. |

## 8. Non-Functional Requirements

### 8.1 Performance

| NFR | Target | Measurement |
|---|---|---|
| NFR-PERF-001 | Time to first dashboard render | < 1.5s p75 |
| NFR-PERF-002 | One-page brief generation | < 60s p75 |
| NFR-PERF-003 | Full report generation (Standard depth) | < 8 min p75 |
| NFR-PERF-004 | Search response | < 300ms p75 |
| NFR-PERF-005 | API p95 latency | < 500ms (sync) / async otherwise |

### 8.2 Availability

- **Production SLO:** 99.9% monthly availability for paid tiers.
- **Free tier SLO:** 99.5%.
- **Planned maintenance windows:** Sundays 02:00–04:00 UTC, with 7-day notice.

### 8.3 Scalability

- Support **10,000 concurrent users** at GA, **50,000 at Year 2**.
- **1M opportunities** per workspace maximum.
- **100M documents** in the platform knowledge base.

### 8.4 Security & compliance

- **SOC 2 Type II** at GA; **ISO 27001** by Month 18.
- **GDPR** + **CCPA** compliant at launch.
- **HIPAA** not in scope for v1.
- All customer data encrypted at rest and in transit.
- Penetration test annually + on major releases.

### 8.5 Accessibility

- **WCAG 2.1 AA** across all user-facing pages.
- Keyboard navigability for every interaction.
- Screen-reader compatibility (NVDA, VoiceOver).
- Color contrast ≥ 4.5:1 for text.

### 8.6 Internationalization

- v1 supports **English (en-US)**.
- v2 adds Spanish, German, Japanese.

### 8.7 Data retention

- User content retained while account is active.
- Soft-delete with 30-day recovery window.
- Hard delete after 90 days, fully purged.
- Configurable per-tenant for Enterprise.

### 8.8 Disaster recovery

- **RPO:** 1 hour.
- **RTO:** 4 hours.
- Multi-region backups (US-EAST primary, US-WEST standby).

## 9. Feature Catalogue

The following 35 features (FEAT-001..FEAT-035) compose the MVP + GA product. Each is mapped to the requirements it satisfies.

| ID | Feature | Requirements | MVP | GA |
|---|---|---|---|---|
| FEAT-001 | Email/OAuth sign-up | REQ-AUTH-0001..0002 | ✔ | |
| FEAT-002 | SSO + SCIM (Enterprise) | REQ-AUTH-0005..0006 | ✔ | |
| FEAT-003 | MFA | REQ-AUTH-0004 | | ✔ |
| FEAT-004 | RBAC | REQ-AUTH-0007 | ✔ | |
| FEAT-005 | Multi-workspace | REQ-AUTH-0008 | ✔ | |
| FEAT-006 | Trend mining | REQ-DISC-0001 | ✔ | |
| FEAT-007 | Niche exploration | REQ-DISC-0002 | ✔ | |
| FEAT-008 | Pain harvesting | REQ-DISC-0003 | ✔ | |
| FEAT-009 | Competitor-derivative | REQ-DISC-0004 | ✔ | |
| FEAT-010 | Continuous discovery | REQ-DISC-0006 | | ✔ |
| FEAT-011 | Saved searches | REQ-DISC-0010 | | ✔ |
| FEAT-012 | Market size | REQ-VAL-0001 | ✔ | |
| FEAT-013 | Growth rate | REQ-VAL-0002 | ✔ | |
| FEAT-014 | Demand signals | REQ-VAL-0003 | ✔ | |
| FEAT-015 | Competitive map | REQ-VAL-0004 | ✔ | |
| FEAT-016 | Pricing benchmarks | REQ-VAL-0005 | ✔ | |
| FEAT-017 | Review synthesis | REQ-VAL-0006 | ✔ | |
| FEAT-018 | Buyer personas | REQ-VAL-0007 | ✔ | |
| FEAT-019 | WTP estimation | REQ-VAL-0008 | ✔ | |
| FEAT-020 | GTM diagnosis | REQ-VAL-0009 | ✔ | |
| FEAT-021 | Risk register | REQ-VAL-0010 | ✔ | |
| FEAT-022 | Validation depth | REQ-VAL-0011 | ✔ | |
| FEAT-023 | Default rubric | REQ-SCORE-0001 | ✔ | |
| FEAT-024 | Custom rubric | REQ-SCORE-0002 | ✔ | |
| FEAT-025 | Rubric versioning | REQ-SCORE-0004 | | ✔ |
| FEAT-026 | Score rationale | REQ-SCORE-0005 | ✔ | |
| FEAT-027 | Portfolio view | REQ-SCORE-0008 | ✔ | |
| FEAT-028 | One-page brief | REQ-RPT-0001 | ✔ | |
| FEAT-029 | Full report | REQ-RPT-0002 | ✔ | |
| FEAT-030 | Comparison report | REQ-RPT-0004 | ✔ | |
| FEAT-031 | White-label | REQ-RPT-0008 | ✔ (Ent) | |
| FEAT-032 | Pipeline board | REQ-DASH-0001 | ✔ | |
| FEAT-033 | Alerts | REQ-DASH-0004 | ✔ | |
| FEAT-034 | Slack integration | REQ-INT-0005 | ✔ | |
| FEAT-035 | Public REST API | REQ-INT-0001 | | ✔ |

**MVP scope:** 22 features (✔ in MVP column). The remaining 13 are post-MVP / GA-only.

## 10. User Stories

A sample of 12 representative user stories. The full backlog lives in the project's tracking tool; these are the spec-defining ones.

### US-FOUNDER-001 — Trend exploration

> As Maya (indie founder), I want to enter a broad interest like "AI for solopreneurs" and see the top 20 trending sub-niches so that I can pick one to dig into.

**Acceptance Criteria:**

- AC-US-FOUNDER-001-1: System returns ≥ 20 sub-niches ranked by composite trend score.
- AC-US-FOUNDER-001-2: Each sub-niche lists 3+ supporting sources.
- AC-US-FOUNDER-001-3: User can pin a sub-niche to start validation.

### US-FOUNDER-002 — Pain point harvesting

> As Maya, I want to see the top complaints and unmet needs in my chosen niche from public forums so that I can ground my product idea in real demand.

**Acceptance Criteria:**

- AC-US-FOUNDER-002-1: System aggregates from ≥ 3 configured sources (Reddit, HN, X, G2).
- AC-US-FOUNDER-002-2: Each pain point has ≥ 1 direct quote and a permalink.
- AC-US-FOUNDER-002-3: User can save pains to a "Discovery notes" panel.

### US-FOUNDER-003 — One-page brief

> As Maya, I want a one-page brief on a sub-niche I selected so I can share it with a potential co-founder in 60 seconds.

**Acceptance Criteria:**

- AC-US-FOUNDER-003-1: Brief includes: opportunity, target user, market size band, top 3 competitors, score, top 3 risks, citations.
- AC-US-FOUNDER-003-2: Generation completes in < 60s p75.
- AC-US-FOUNDER-003-3: User can export to PDF or share a read-only link.

### US-FOUNDER-004 — GTM diagnosis

> As Maya, I want to know which channels competitors use to acquire users so I can pick a launch channel.

**Acceptance Criteria:**

- AC-US-FOUNDER-004-1: GTM panel lists top 3 channels with evidence.
- AC-US-FOUNDER-004-2: Each channel has an estimated CAC band.

### US-CORP-001 — Adjacency exploration

> As Daniel (corporate innovator), I want to explore adjacencies to our core business so we can identify new product lines.

**Acceptance Criteria:**

- AC-US-CORP-001-1: User can enter a base business descriptor; system returns ≥ 10 adjacencies.
- AC-US-CORP-001-2: Each adjacency is mapped to existing capabilities and customer segments.

### US-CORP-002 — Quarterly report

> As Daniel, I want to deliver a quarterly board report summarizing 10 validated opportunities so leadership can decide on resourcing.

**Acceptance Criteria:**

- AC-US-CORP-002-1: Report is a multi-section PDF with cover, exec summary, ranked opportunities, top 3 recommendations.
- AC-US-CORP-002-2: White-label branding is applied.
- AC-US-CORP-002-3: Report generation completes in < 30 minutes for 10 opportunities.

### US-INVESTOR-001 — Deal memo

> As Aria (investor), I want a deal-memo-style brief on a startup that surfaced in my feed so I can decide whether to take a meeting.

**Acceptance Criteria:**

- AC-US-INVESTOR-001-1: Memo includes: thesis fit, market context, comparable rounds, founder-style questions.
- AC-US-INVESTOR-001-2: User can attach the memo to a CRM record via API.

### US-INVESTOR-002 — Thesis portfolio

> As Aria, I want to see my entire pipeline scored against my thesis so I can balance the portfolio.

**Acceptance Criteria:**

- AC-US-INVESTOR-002-1: System scores each opportunity against saved thesis criteria.
- AC-US-INVESTOR-002-2: User can see concentration / coverage heatmap.

### US-CONSULT-001 — Client report

> As Lin (consultant), I want a branded client report so I can deliver it under my firm's identity.

**Acceptance Criteria:**

- AC-US-CONSULT-001-1: User can apply their firm's brand to the report.
- AC-US-CONSULT-001-2: Footer and citation style are configurable.

### US-CONSULT-002 — Multi-engagement workspace

> As Lin, I want one workspace per client so that work does not leak between engagements.

**Acceptance Criteria:**

- AC-US-CONSULT-002-1: User can create up to 5 workspaces (Free), 25 (Team), unlimited (Enterprise).
- AC-US-CONSULT-002-2: Members can be added to a specific workspace only.

### US-PLAT-001 — API access

> As any user, I want a token-based API so I can integrate the platform with my workflow.

**Acceptance Criteria:**

- AC-US-PLAT-001-1: User can mint a token scoped to specific resources.
- AC-US-PLAT-001-2: Token can be revoked.

### US-PLAT-002 — Audit log

> As a security officer, I want to see who did what so I can answer audit questions.

**Acceptance Criteria:**

- AC-US-PLAT-002-1: Audit log captures sign-ins, role changes, exports, deletes.
- AC-US-PLAT-002-2: Audit log is exportable to CSV.

## 11. KPIs & Success Metrics

| KPI | Target | Window | Source |
|---|---|---|---|
| MRR | $250k → $3M | 12 months | Stripe |
| Paid users | 5,000 | 12 months | App |
| Activation rate | 70% (signup → first report) | 30 days | App |
| Weekly active rate (paid) | 92% | Continuous | App |
| Report acceptance rate | 95% | Continuous | App |
| Time-to-first-report | 45 min median | Continuous | App |
| NPS | 50+ | Quarterly | Survey |
| Logo churn (monthly) | < 3% | Continuous | Stripe |
| Net revenue retention | 115%+ | Annual | Stripe |
| Source coverage | 95% of priority sources live | Quarterly | App |

## 12. Business Model

### 12.1 Pricing tiers

| Tier | Price | Users | Reports/mo | Custom rubric | SSO | SLA |
|---|---|---|---|---|---|---|
| Free | $0 | 1 | 5 | No | No | None |
| Solo | $39/mo | 1 | 50 | No | No | Standard |
| Team | $199 + $39/seat | 5 included | 300 | Yes | Add-on | Standard |
| Enterprise | Custom | Unlimited | Custom | Yes | Yes | 99.9% |

### 12.2 Revenue model

- **Subscription** is 88% of revenue.
- **Usage overages** are 7% (driven by Team+ power users).
- **Enterprise services** (custom integrations, training) are 5%.

### 12.3 Cost structure

- **Inference (LLM + tools)** is the largest variable cost; targeted at < 30% of revenue.
- **Engineering & product** dominate fixed cost.
- **Sales & marketing** target CAC payback < 14 months.

### 12.4 Funding posture

- Seed-to-Series-A transition targeted at $4M ARR.
- Series B at $12M ARR for enterprise GTM build-out.

## 13. Risks & Assumptions

### 13.1 Top risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RISK-001 | LLM hallucination in evidence | High | High | Multi-agent verification + citation requirements + operator sign-off |
| RISK-002 | Source API cost escalation | Medium | High | Multi-source fallback + cache + cost dashboards |
| RISK-003 | Enterprise sales cycle > 6 months | Medium | Medium | Land-and-expand with Team tier as wedge |
| RISK-004 | Regulatory change (AI Act, etc.) | Medium | Medium | Continuous compliance review + data-residency |
| RISK-005 | Big tech competitor enters | High | High | Speed-to-feature + multi-agent depth + community |
| RISK-006 | IP / copyright on training data | Medium | High | Source provenance + license audit + indemnity |
| RISK-007 | Founding team concentration | Medium | High | Hire aggressively + documentation culture |
| RISK-008 | Runway burn | Low | High | Conservative seed + revenue focus |

### 13.2 Key assumptions

- ASP-001: Inference cost continues to fall ≥ 20% YoY.
- ASP-002: Founders will pay $39+/mo for a tool that materially reduces research time.
- ASP-003: Enterprise security reviews can be passed within 60 days of contracting.
- ASP-004: A 4-person founding team can ship MVP in 9 months.

## 14. MVP Scope & Product Roadmap

### 14.1 MVP definition (Q3 2027 launch)

- 22 features (Section 9).
- 4 personas supported at basic depth.
- Web app + REST API.
- English only.
- US/EU data residency.
- Stripe billing, 4 tiers.

### 14.2 Roadmap

| Quarter | Milestone |
|---|---|
| Q3 2026 | PRD locked, architecture baseline, team complete (8 FTE) |
| Q4 2026 | Alpha: discovery + basic validation; internal dogfood |
| Q1 2027 | Beta: full MVP features behind a flag; 50 design partners |
| Q2 2027 | Hardening: security review, pricing validation, content |
| Q3 2027 | Public launch (Free + Solo + Team); ProductHunt, HN |
| Q4 2027 | Enterprise plan launches; SOC 2 Type I |
| Q1 2028 | i18n (es, de, ja); continuous discovery; webhook v1 |
| Q2 2028 | SOC 2 Type II; Notion + Linear; cohort analytics |
| Q3 2028 | API v2; multi-tenant rubric library; 25 enterprise customers |
| Q4 2028 | ISO 27001; 5,000 paid users; $3M ARR target |

### 14.3 Release criteria (per release)

- All acceptance criteria for the release scope pass.
- Performance NFRs (Section 8.1) green for 7 consecutive days.
- No open P0/P1 security issues.
- Documentation updated and indexed.
- Customer comms drafted (changelog, email, in-app banner).

## 15. Glossary & Appendix

### 15.1 Glossary

| Term | Definition |
|---|---|
| Validation | Confirming an opportunity is real, growing, and monetizable. |
| Discovery | Generating candidate opportunities from raw signals. |
| Scoring | Computing a numeric rating from a configurable rubric. |
| Rubric | The set of dimensions, weights, and criteria used to score. |
| Adjacency | A business area near (but not identical to) an existing one. |
| WTP | Willingness to pay. |
| GTM | Go-to-market. |
| TAM / SAM / SOM | Total / Serviceable / Serviceable-Obtainable market. |
| North Star | The single user-behavior metric that defines product success. |

### 15.2 Appendix A — Document index

| ID | Document | Path |
|---|---|---|
| 00 | Documentation Governance | `docs/00-Governance/00_documentation_governance.md` |
| 01 | PRD (this document) | `docs/01-PRD/01_product_requirements_document.md` |
| 02 | TRD | `docs/02-TRD/02_technical_requirements_document.md` |
| 03 | Application Flow | `docs/03-ApplicationFlow/03_application_flow.md` |
| 04 | UI/UX Spec | `docs/04-UIUX/04_uiux_design_specification.md` |
| 05 | Backend & DB | `docs/05-Backend/05_backend_database_architecture.md` |
| 06 | Roadmap | `docs/06-Roadmap/06_implementation_roadmap.md` |
| 07..18 | AI Architecture | `docs/07-AI-Architecture/` |
| 19..30 | Engineering | `docs/08-Engineering/` |

### 15.3 Appendix B — Requirement → Document map

| Domain | Count | Primary document |
|---|---|---|
| AUTH | 10 | PRD (here), TRD, Security |
| DISC | 10 | PRD, AI Architecture, Multi-Agent, Plugin |
| VAL | 14 | PRD, Research Pipeline, Scoring |
| SCORE | 10 | PRD, Scoring Engine |
| RPT | 12 | PRD, Report Generation |
| DASH | 9 | PRD, UI/UX, Application Flow |
| INT | 10 | PRD, API Specs |
| BIL | 10 | PRD, Backend |
| ADMIN | 10 | PRD, Backend, Security |
| OB | 10 | PRD, UI/UX |
| PLAT | 10 | PRD, Backend, DevOps |

### 15.4 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.1 | 2026-07-20 | Doc Team | Initial outline |
| v0.5 | 2026-07-20 | Doc Team | All 15 chapters drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

---

> *End of Document 01 — PRD. This document is the upstream source of truth for every requirement ID, persona, and KPI used elsewhere in the suite.*
