---
title: Marketing Site Specification
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 34 — Marketing Site Specification

> The contract for the public marketing site (`ventureminer.ai`). What it says, how it's structured, how it's measured, and how it stays consistent with the product.

## Table of Contents

1. Purpose & Scope
2. Audience & goals
3. Information architecture
4. Page inventory
5. Page specifications
6. Brand & voice (web)
7. SEO strategy
8. Performance budget
9. Conversion strategy
10. Analytics & measurement
11. Localization
12. Accessibility
13. Compliance
14. Stack & hosting
15. Maintenance
16. Appendix

## 1. Purpose & Scope

This document is the contract for the **public marketing site**. It governs:

- Information architecture and page inventory.
- Per-page content and structure.
- Brand and voice on the web.
- SEO, performance, and conversion strategy.
- Localization, accessibility, and compliance.

It does not cover the in-product UI (Document 04) or the help center (which is part of the app).

## 2. Audience & goals

### 2.1 Audiences (per PRD §5)

- **Indie founder** — visiting from organic / paid social; wants proof of value in < 30s.
- **Corporate innovator** — visiting from LinkedIn / referral; wants security and ROI.
- **Investor** — visiting from a partner; wants product depth.
- **Consultant** — visiting from search; wants pricing and a sample.

### 2.2 Goals

- **Primary:** convert visitor to signup.
- **Secondary:** request a demo (Enterprise).
- **Tertiary:** capture for nurture (Free).

### 2.3 KPIs

| KPI | Target |
|---|---|
| Visitor → signup | 4% |
| Visitor → demo request | 1% |
| Bounce rate | < 50% |
| LCP | < 2.0s p75 |
| Organic traffic (Year 1) | 100k MAU |

## 3. Information architecture

```
ventureminer.ai/
├── /                          # Home
├── /product                   # Product overview
│   ├── /product/discovery
│   ├── /product/validation
│   ├── /product/scoring
│   └── /product/reports
├── /solutions                 # Per-persona
│   ├── /solutions/indie-founder
│   ├── /solutions/corporate-innovator
│   ├── /solutions/investor
│   └── /solutions/consultant
├── /pricing
├── /customers                 # Case studies
├── /resources
│   ├── /blog
│   ├── /academy               # Tutorials
│   ├── /sample-reports        # Anonymized reports
│   └── /changelog
├── /about
│   ├── /careers
│   └── /press
├── /security
├── /legal
│   ├── /privacy
│   ├── /terms
│   ├── /dpa
│   └── /sub-processors
├── /contact
└── /signup
```

## 4. Page inventory

| ID | Page | URL | Goal |
|---|---|---|---|
| MS-001 | Home | `/` | Convert to signup/demo |
| MS-002 | Product overview | `/product` | Educate + CTA |
| MS-003 | Discovery | `/product/discovery` | Educate + signup |
| MS-004 | Validation | `/product/validation` | Educate + signup |
| MS-005 | Scoring | `/product/scoring` | Educate + signup |
| MS-006 | Reports | `/product/reports` | Educate + signup |
| MS-010 | Solutions — founder | `/solutions/indie-founder` | Convert to signup |
| MS-011 | Solutions — corp | `/solutions/corporate-innovator` | Convert to demo |
| MS-012 | Solutions — investor | `/solutions/investor` | Convert to signup |
| MS-013 | Solutions — consultant | `/solutions/consultant` | Convert to signup |
| MS-020 | Pricing | `/pricing` | Convert to signup |
| MS-030 | Customers | `/customers` | Build trust + CTA |
| MS-040 | Blog | `/blog` | SEO + trust |
| MS-041 | Academy | `/academy` | Education + retention |
| MS-042 | Sample reports | `/sample-reports` | Trust + signup |
| MS-043 | Changelog | `/changelog` | Retention + trust |
| MS-050 | About | `/about` | Trust |
| MS-051 | Careers | `/careers` | Recruiting |
| MS-052 | Press | `/press` | Trust |
| MS-060 | Security | `/security` | Trust (Enterprise) |
| MS-070 | Privacy | `/legal/privacy` | Compliance |
| MS-071 | Terms | `/legal/terms` | Compliance |
| MS-072 | DPA | `/legal/dpa` | Enterprise sales |
| MS-073 | Sub-processors | `/legal/sub-processors` | Compliance |
| MS-080 | Contact | `/contact` | Lead capture |
| MS-090 | Signup | `/signup` | Conversion |
| MS-091 | Demo request | `/demo` | Enterprise sales |

## 5. Page specifications (selected)

### 5.1 MS-001 — Home

**Goal:** convert in < 30s.

**Structure:**

```
┌─ Hero ──────────────────────────────────────────────────┐
│ Headline (8–10 words)                                    │
│ Subhead (1 sentence, value prop)                         │
│ CTA primary (Start free)  CTA secondary (Watch demo)    │
│ Hero illustration / product animation                    │
└──────────────────────────────────────────────────────────┘

┌─ Social proof ──────────────────────────────────────────┐
│ Logos (8–12 customers)                                   │
│ Quote (3 testimonials)                                  │
└──────────────────────────────────────────────────────────┘

┌─ How it works (3 steps) ────────────────────────────────┐
│ Step 1 → Step 2 → Step 3 (with screenshots)             │
└──────────────────────────────────────────────────────────┘

┌─ Sample report (interactive demo) ──────────────────────┐
│ Embed: an interactive sample brief                      │
└──────────────────────────────────────────────────────────┘

┌─ Per-persona value (4 cards) ───────────────────────────┐
│ Founder · Corp · Investor · Consultant                  │
└──────────────────────────────────────────────────────────┘

┌─ Final CTA ─────────────────────────────────────────────┐
│ Headline + CTA                                          │
└──────────────────────────────────────────────────────────┘
```

### 5.2 MS-020 — Pricing

- Tier comparison table (Document 31 §3).
- FAQ (10 most common).
- ROI calculator (input: team size, current cost).
- CTA: per-tier.

### 5.3 MS-060 — Security

- SOC 2 status + report download.
- Sub-processor list.
- DPA download.
- Architecture diagram.
- Compliance roadmap (ISO 27001, etc.).

## 6. Brand & voice (web)

- **Voice** is per Document 04 §3.
- **Tone on marketing site:** slightly more aspirational; lead with outcomes.
- **Visual style:** clean, evidence-led, restrained (per Document 04 §2).
- **Logos & assets** in the brand kit (`/brand/`).

## 7. SEO strategy

- **Keyword targets** per page (owned by SEO lead).
- **Schema.org** markup: Organization, Product, FAQPage, Article.
- **Internal linking** strategy; topical clusters around "SaaS opportunity research", "market intelligence", "venture validation".
- **Programmatic SEO** for `/sample-reports/<vertical>/<stage>/` (long-tail).
- **Sitemap** auto-generated; submitted to Google + Bing.
- **Core Web Vitals** are a ranking factor; performance budget (Section 8) is enforced.

## 8. Performance budget

| Metric | Target |
|---|---|
| LCP | < 2.0s p75 |
| FID | < 100ms p75 |
| CLS | < 0.1 |
| TTI | < 3.0s |
| Total JS (gzipped, home) | < 100 KB |
| Total CSS (gzipped) | < 20 KB |
| Image sizes | WebP/AVIF, lazy-loaded, responsive |

## 9. Conversion strategy

- **Primary CTA** on every page (signup or demo).
- **Secondary CTA** contextual.
- **Sticky CTA** on long pages.
- **Exit intent** (limited, non-intrusive) on pricing.
- **Retargeting** via LinkedIn and Google.
- **A/B test** framework: home hero, pricing layout, CTA copy.

## 10. Analytics & measurement

- **Tool:** Datadog RUM (web) + Plausible (privacy-friendly analytics).
- **Events:** pageview, CTA click, signup, demo request, scroll depth.
- **Funnels:** visitor → signup, signup → first report, demo request → SQL.
- **Dashboards:** marketing dashboards in Datadog.
- **Attribution:** first-touch + last-touch + linear.

## 11. Localization

- v1: `en-US`.
- v2: `es-ES`, `de-DE`, `ja-JP`.
- Hreflang tags.
- Locale-specific content where needed (case studies, currency).

## 12. Accessibility

- WCAG 2.1 AA minimum.
- All images alt-text.
- Color contrast verified.
- Keyboard navigable.
- Form fields labeled.

## 13. Compliance

- **GDPR** compliant (consent banner; data processing addendum).
- **CCPA** compliant (do-not-sell link).
- **Cookie policy** clear and current.
- **DPA** and **sub-processor list** publicly available.
- **Accessibility statement** linked in footer.

## 14. Stack & hosting

- **Framework:** Next.js 15 (same as the app; shared design system).
- **Hosting:** Vercel (CDN, image optimization, edge).
- **CMS:** Sanity (blog, customers, sample reports).
- **Forms:** HubSpot.
- **Email capture:** HubSpot.
- **A/B testing:** Vercel Edge Config + GrowthBook.

## 15. Maintenance

- **Content updates:** weekly (blog, changelog, sample reports).
- **Code updates:** per release.
- **Performance audits:** monthly.
- **SEO audits:** quarterly.
- **Accessibility audits:** quarterly.

## 16. Appendix

### 16.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 16.2 Cross-references

- UI/UX: Document 04.
- Pricing: Document 31.
- Sales Playbook: Document 32.
- Coding Standards (Web): Document 27.

---

> *End of Document 34 — Marketing Site Specification. The marketing site is the first impression — it must earn the click.*
