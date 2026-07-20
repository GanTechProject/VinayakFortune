---
title: Pricing & Packaging
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 31 — Pricing & Packaging

> The deep dive on the commercial model. The PRD covers the high-level pricing tiers; this document is the source of truth for packaging decisions, add-ons, discounts, and lifecycle pricing.

## Table of Contents

1. Purpose & Scope
2. Pricing principles
3. Plan matrix
4. Plan selection guide
5. Add-ons & bundles
6. Discounts & overrides
7. Lifecycle pricing
8. Region-specific pricing
9. Competitive positioning
10. Price testing roadmap
11. Sales & CS motions per tier
12. Risks & mitigations
13. Appendix

## 1. Purpose & Scope

This document is the contract for **pricing and packaging**. It governs:

- The four plan tiers.
- Add-ons, bundles, and usage overages.
- Discount policy (sales overrides, promotions, partner pricing).
- Lifecycle pricing (upgrades, downgrades, grandfathering).
- Region-specific pricing (NA, EU, APAC).
- The pricing page and quote-to-cash flow.

## 2. Pricing principles

1. **Simple.** Four plans, each with at most three add-ons.
2. **Aligned with value.** Price scales with active usage, not just seats.
3. **Predictable.** No surprise overages — soft caps, alerts, opt-in.
4. **Fair.** Annual discount is meaningful, not gimmicky.
5. **Defensible.** Pricing is published; no hidden fees.

## 3. Plan matrix

| Tier | Monthly | Annual (-16%) | Seats | Reports/mo | Custom rubric | SSO | SLA | Support |
|---|---|---|---|---|---|---|---|---|
| Free | $0 | $0 | 1 | 5 | No | No | None | Community |
| Solo | $39 | $390 | 1 | 50 | No | No | Standard | Email (48h) |
| Team | $199 + $39/seat | $1,990 + $390/seat × n | 5 included | 300 | Yes | Add-on | Standard | In-app chat (8h) |
| Enterprise | Custom | Custom | Unlimited | Custom | Yes | Yes (SAML/OIDC) + SCIM | 99.9% | Dedicated CSM, 1h |

### 3.1 What's in every plan

| Capability | Free | Solo | Team | Enterprise |
|---|---|---|---|---|
| Discovery | 5 runs/mo | 50 runs/mo | 300 runs/mo | Unlimited |
| Validation (Standard) | 5/mo | 50/mo | 300/mo | Custom |
| One-page brief | ✔ | ✔ | ✔ | ✔ |
| Full report | ✔ | ✔ | ✔ | ✔ |
| Comparison report | ✘ | ✔ | ✔ | ✔ |
| Custom rubric | ✘ | ✘ | ✔ | ✔ |
| White-label reports | ✘ | ✘ | Add-on | ✔ |
| Public API | ✘ | 1k req/day | 10k req/day | Custom |
| Webhooks | ✘ | ✘ | ✔ | ✔ |
| Slack integration | ✔ | ✔ | ✔ | ✔ |
| Notion integration | ✘ | ✘ | ✔ | ✔ |
| Audit log | ✘ | ✘ | 30 days | Unlimited |
| SLA | None | 99.5% | 99.5% | 99.9% |
| DPA | Standard | Standard | Standard | Negotiated |
| Data residency | US | US | US | US/EU/APAC |

## 4. Plan selection guide

### 4.1 Free — "evaluate"

For: a curious user; a hobbyist; a one-time project.

### 4.2 Solo — "ship"

For: an indie founder running one venture; a consultant on a single engagement; an investor screening deals solo.

### 4.3 Team — "scale"

For: a venture studio; a corp-dev team; a fund's research team; a consultancy with multiple clients.

### 4.4 Enterprise — "systematize"

For: Fortune 1000 corp-dev; a fund with $500M+ AUM; a global consultancy.

## 5. Add-ons & bundles

### 5.1 Add-ons (Team+)

- **SSO add-on:** $1,000/mo (10–50 seats), $2,500/mo (50+ seats).
- **Extra reports pack:** 100 reports for $99 (Solo), 500 for $399 (Team).
- **Heavy-research pack:** for Standard → Deep depth unlimited for one quarter, $499.
- **White-label add-on:** $499/mo (Team) — included in Enterprise.

### 5.2 Bundles

- **Founder Bundle** (Solo + Heavy-research pack): $59/mo for first 6 months.
- **Studio Bundle** (Team + SSO + 2 extra seats): $499/mo for first 12 months.
- **Pilot Bundle** (Enterprise, 3-month pilot): 50% off Year 1 if converted within 30 days.

## 6. Discounts & overrides

### 6.1 Annual discount

- **Default:** 16% off monthly.
- **Mechanic:** 12 months upfront, pro-rated on mid-term change.

### 6.2 Sales-led overrides

- **Volume:** > $50k ACV → 5–10% extra; > $100k ACV → 10–15% extra.
- **Multi-year:** 2-year commits get +5%; 3-year commits get +10%.
- **Non-profit / academic:** 30% off all tiers.
- **Startup program:** Free Solo for 12 months for funded seed-stage startups (Y Combinator, Techstars, etc.).
- **Partner program:** 20% revenue share to qualified resellers.

### 6.3 Promotions

- **Quarterly promotion budget:** 5% of new ARR.
- **Promo codes:** tracked; expire after 90 days; never stack.
- **Black-Friday-style promotions:** only for upgrades; never on new Free users.

## 7. Lifecycle pricing

### 7.1 Upgrade

- Pro-rated for current period.
- New plan effective immediately.
- Quota reset to new plan limits.

### 7.2 Downgrade

- Effective at end of current period.
- Over-quota usage is preserved; user is read-only on overage until period ends.
- Quota reduces at renewal.

### 7.3 Cancellation

- Self-serve; no friction.
- Workspace becomes read-only at period end; data retained for 30 days.
- Re-activation within 30 days preserves data.

### 7.4 Grandfathering

- Existing customers keep their plan's pricing for 12 months after a price increase.
- Plan-feature changes are communicated 90 days in advance; opt-in for breaking changes.

## 8. Region-specific pricing

| Region | Adjustment | Reason |
|---|---|---|
| US | Base | — |
| EU | Base + VAT | Legal requirement |
| UK | Base + VAT | Legal requirement |
| India | -30% | PPP adjustment |
| Brazil | -20% | PPP adjustment |
| APAC (other) | -15% | PPP adjustment |

- **Purchasing power parity (PPP)** adjustments are reviewed annually.
- **Local-currency billing** is available in EU, UK, India, Brazil.

## 9. Competitive positioning

| Competitor | Their price | Our price | Why we're different |
|---|---|---|---|
| Crayon (CI) | $30k+/yr | $25k+ (Enterprise) | We do opportunity discovery, not just monitoring |
| Perplexity Pro | $20/mo | $39/mo | We're domain-tuned, not generic |
| CB Insights | $50k+/yr | $25k+ (Enterprise) | We're self-serve to enterprise; faster |
| SparkToro | $80/mo | $39/mo | We validate, not just signal |

## 10. Price testing roadmap

- **Q4 2026:** Solo at $39 (no test).
- **Q1 2027:** A/B Solo at $29 vs $39 — measure activation, retention, LTV.
- **Q2 2027:** A/B Team at $199 vs $249 — measure seat expansion.
- **Q3 2027:** Annual vs monthly for Solo — measure annual conversion.
- **Q4 2027:** PPP adjustments in India.

Each test requires:
- Hypothesis.
- Success metric (LTV, not just conversion).
- Holdout.
- Review at end.

## 11. Sales & CS motions per tier

| Tier | Motion | Owner |
|---|---|---|
| Free | Self-serve + community | Marketing + Product |
| Solo | Self-serve + in-app upsell | Product |
| Team | Product-led; light sales assist on > 10 seats | Sales (AE) |
| Enterprise | Sales-led; pilot → close | Sales (AE + SE) + CS |

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| LLM cost spike erodes margin | CoGS targets; tiered cost ceilings; multi-provider |
| Discount erosion | Centralized discount authority; quarterly review |
| PPP gaming | Identity verification; annual review |
| Cannibalization of Solo with Team | Distinct value; no overlap of core use cases |
| Enterprise discount wars | Value-based selling; pre-built ROI calculator |

## 13. Appendix

### 13.1 Glossary

| Term | Definition |
|---|---|
| ACV | Annual contract value |
| ARR | Annual recurring revenue |
| PPP | Purchasing power parity |
| LTV | Lifetime value |
| CoGS | Cost of goods sold |

### 13.2 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 13.3 Cross-references

- PRD: Document 01 §12 (Business Model).
- Billing service: Document 05.
- Sales Playbook: Document 32.
- Operations Guide: Document 28.

---

> *End of Document 31 — Pricing & Packaging. Discount authority is the VP of Sales + VP of Product (jointly).*
