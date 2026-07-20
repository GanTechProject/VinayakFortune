---
title: Onboarding & Activation Playbook
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 37 — Onboarding & Activation Playbook

> How we get a new user to their first useful artifact in 10 minutes or less — and how we keep them coming back. The contract for the activation funnel.

## Table of Contents

1. Purpose & Scope
2. Activation principles
3. North Star & counter-metrics
4. User journey (per persona)
5. Onboarding flow
6. Activation checkpoints
7. First 7 days
8. First 30 days
9. Re-engagement
10. Cohort analyses
11. Experimentation roadmap
12. Appendix

## 1. Purpose & Scope

This document is the contract for **onboarding and activation**. It governs:

- The user journey from signup to "aha moment".
- The in-product onboarding flow.
- The activation metrics and counter-metrics.
- The re-engagement motions.
- The experimentation roadmap.

It does not cover sales (Document 32) or support (Document 33) — though both are downstream consumers of activation data.

## 2. Activation principles

1. **Time to value is the only metric that matters.** Ship the user to their first useful artifact in < 10 minutes.
2. **Show, don't tell.** Use their data, their seed, their outcome.
3. **Reduce decisions.** Defaults that work > choice paralysis.
4. **Earn the next step.** Each step earns the right to ask for the next.
5. **No dead ends.** Every state has a clear next action.

## 3. North Star & counter-metrics

### 3.1 North Star

**Validated opportunities acted on per week per active user.**

- Captures the behavior we want: not just generating, but acting.
- Increases with breadth (more opportunities) and depth (more action).

### 3.2 Counter-metrics (to prevent gaming)

| Counter-metric | Why it matters | Threshold |
|---|---|---|
| Reports-per-user (cap) | Prevent farming | ≤ 30/week/paid user |
| Report rejection rate | Quality | ≤ 5% |
| Subscription churn (per cohort) | Stickiness | < 3% monthly |
| Time-to-first-edit | Quality proxy | < 5 min p75 |

## 4. User journey (per persona)

### 4.1 Indie founder

```
Signup → Onboarding tour → Sample brief → "Try your own" CTA →
Run discovery (their seed) → Pin a hit → Validate (Quick) →
See score → Generate brief → Export → AHA
```

**Time to AHA:** 8 min (target).

### 4.2 Corporate innovator

```
Signup → Choose "Corporate" track → Onboarding tour (corp-specific) →
Upload competitor list → Run adjacency exploration →
Pin 3 candidates → Compare → Generate board report →
Share with team → AHA
```

**Time to AHA:** 10 min (target).

### 4.3 Investor

```
Signup → Choose "Investor" track → Onboarding tour →
Add a watchlist (sector, keywords) → Run discovery →
Pin a candidate → Generate deal memo → AHA
```

**Time to AHA:** 7 min (target).

### 4.4 Consultant

```
Signup → Choose "Consultant" track → Onboarding tour →
Create a client workspace (template) → Run a white-label report →
Preview → AHA
```

**Time to AHA:** 9 min (target).

## 5. Onboarding flow

### 5.1 Components

- **Welcome modal** (after signup) — "What brings you here?" (persona selector).
- **Product tour** (skippable, resumable) — 5 screens, 90s total.
- **Sample artifact** (one-click) — generates a sample brief in their industry.
- **Activation checklist** (persistent) — 5 actions to reach AHA.
- **Empty states** — each empty state shows a "Try this" CTA.
- **Tooltips** — contextual, dismissable.

### 5.2 The 5-step activation checklist

1. **Complete profile** (workspace name, persona).
2. **Run first discovery** (1-click with their seed).
3. **Pin one opportunity** (1-click).
4. **Run first validation** (Quick depth, 1-click).
5. **Generate first report** (1-click).

**Each step** is logged; the checklist UI shows progress and the next step.

### 5.3 Sample data

- **Sample seed library** — 50 industry-specific seeds.
- **Sample opportunities** — 5 pre-generated, fully cited.
- **Sample reports** — 3 anonymized templates.

## 6. Activation checkpoints

| Checkpoint | Definition | KPI |
|---|---|---|
| **C0 — Signup** | Account created | Volume |
| **C1 — Activated** | First artifact generated | 70% of signups in 7d |
| **C2 — Engaged** | 3+ artifacts in 14d | 50% of activated |
| **C3 — Habit** | 1+ artifact per week for 4 weeks | 40% of engaged |
| **C4 — Power** | 10+ artifacts per week for 4 weeks | 10% of habit |

## 7. First 7 days

### 7.1 Email cadence

| Day | Subject | Content |
|---|---|---|
| 0 | "Welcome — your first brief in 60s" | CTA to sample |
| 1 | "Did you try your own seed?" | CTA to first discovery |
| 3 | "3 things you can do in 3 minutes" | Activation checklist nudge |
| 5 | "How [Persona] use VentureMiner" | Case study |
| 7 | "Your weekly summary" | Recap + next steps |

### 7.2 In-product nudges

- **Day 0:** sample artifact CTA.
- **Day 1 (if no discovery):** "Run your first discovery in 90s."
- **Day 3 (if < 3 artifacts):** checklist nudge.
- **Day 7 (if habit forming):** "Subscribe to weekly digest."

## 8. First 30 days

### 8.1 Habit loop

- **Trigger:** weekly digest email + in-app notification.
- **Action:** open app → view trends → validate top opportunity.
- **Reward:** new score / new evidence / new trend.

### 8.2 Activation events that prompt upgrade

- **3rd workspace attempted** on Solo → upgrade CTA to Team.
- **Custom rubric requested** on Solo → upgrade CTA to Team.
- **Audit log viewed** on Team → upgrade CTA to Enterprise.
- **SSO attempted** on Team → upgrade CTA to Enterprise.

## 9. Re-engagement

### 9.1 Inactive users (no login in 14d)

- **Day 14:** "Here's what changed" email — top 3 new trends in their watched categories.
- **Day 21:** "Your pinned opportunities have new evidence" — value-reminder email.
- **Day 30:** "We saved your workspace — come back?" — one-click login.
- **Day 60:** Suppress; do not email.

### 9.2 Lapsed paid users

- **Day 7 post-cancel:** "What changed?" survey (1 question).
- **Day 30 post-cancel:** "Your data is here" — soft win-back.
- **Day 60 post-cancel:** Suppress; add to win-back list (90+ days).

## 10. Cohort analyses

### 10.1 Standard cohorts

- **By persona** — how does activation differ by self-reported persona?
- **By acquisition channel** — paid vs organic vs referral.
- **By first seed** — do certain seed types predict retention?
- **By sign-up week** — cohort retention curves.

### 10.2 Standard dashboards

- **Funnel:** C0 → C1 → C2 → C3 → C4 (per cohort).
- **Time to AHA** (p50, p75, p90).
- **Activation by step** — where do users drop off the checklist?
- **Re-engagement rate** — % of inactive users who return.

## 11. Experimentation roadmap

### 11.1 Q4 2026 (alpha)

- Test: persona selector in welcome modal vs. no selector.
- Test: product tour skippable vs. forced.
- Test: 5-step checklist vs. 3-step.

### 11.2 Q1 2027 (beta)

- Test: sample brief as default vs. sample discovery.
- Test: email cadence density (3 vs. 5 emails in week 1).
- Test: AHA definition (first brief vs. first pin).

### 11.3 Q2 2027 (pre-launch)

- Test: paywall timing (immediate vs. after 5 reports).
- Test: pricing display (per-seat vs. per-workspace).
- Test: re-engagement subject lines.

## 12. Appendix

### 12.1 Glossary

| Term | Definition |
|---|---|
| AHA | The moment a user understands the product's value |
| Activation | The first session where the user reaches AHA |
| Habit | Repeat usage ≥ 1 session/week for 4 weeks |
| Cohort | Users grouped by a shared attribute (e.g. signup week) |
| Win-back | A re-engagement campaign targeted at lapsed users |

### 12.2 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 12.3 Cross-references

- PRD: Document 01 §6.2.
- Application Flow: Document 03 §3.
- UI/UX: Document 04 §12.
- Marketing Site: Document 34.
- Support: Document 33.

---

> *End of Document 37 — Onboarding & Activation Playbook. Time to value is the only metric that matters in the first week.*
