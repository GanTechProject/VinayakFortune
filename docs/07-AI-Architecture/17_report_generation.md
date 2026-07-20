---
title: Report Generation
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 17 — Report Generation

> The report is the artifact. It is what the user ships to a co-founder, a board, an LP, or a client. This document defines the report types, the assembly pipeline, the rendering, and the export formats.

## Table of Contents

1. Purpose & Scope
2. Report types
3. Assembly pipeline
4. Section templates
5. Citation handling
6. Charts and tables
7. Branding (white-label)
8. Export formats
9. Acceptance criteria
10. Cost & latency
11. Failure modes
12. Appendix

## 1. Purpose & Scope

This document is the contract for **report generation** — the system that consumes evidence, scores, and templates and produces a polished, exportable, citable report.

## 2. Report types

| Type | Length | Use | Generation target |
|---|---|---|---|
| One-page brief | 1 page | Quick share, triage | < 60s p75 |
| Full report | 10–25 pages | Default validation artifact | < 8 min p75 |
| Comparison report | 5–10 pages | Side-by-side opportunities | < 3 min p75 |
| Board pack | 15–30 pages | Quarterly review | < 15 min p75 |
| Deal memo | 2–3 pages | Investor deal flow | < 90s p75 |

## 3. Assembly pipeline

```
plan → outline → section drafts (parallel) → verifier pass → assembly → chart render → export
```

- **Plan:** chooses sections based on report type, depth, persona.
- **Outline:** generates a section-by-section outline with target length.
- **Section drafts:** AGT-RPT-WRITER generates each section in parallel; each carries its own citations.
- **Verifier pass:** AGT-VERIFY audits each section.
- **Assembly:** report is composed in order; transitions added.
- **Chart render:** charts (market size, score breakdown, comparison matrix) are generated from structured data.
- **Export:** PDF, DOCX, MD, HTML, plus optional PPTX for board pack.

## 4. Section templates

Each report type has a template. The template defines:

- Section order.
- Target length per section.
- Required elements (citations, charts, callouts).
- Style (executive tone vs. analyst tone).

Templates are versioned and editable per workspace (post-MVP).

## 5. Citation handling

- Citations are **inline** (numbered) and **collected** in a footnotes section.
- Each citation links to the underlying chunk and source URL.
- Each section shows a freshness class.
- A "View sources" panel lists every cited source with freshness.

## 6. Charts and tables

Charts are generated from structured data, not from LLM output:

- **Market size bar** (TAM/SAM/SOM).
- **Growth line** (YoY).
- **Demand bars** (search/social volumes).
- **Score radar** (dimension breakdown).
- **Comparison matrix** (side-by-side).
- **Pricing table** (competitors, tiers).

All charts include alt text and a data table for accessibility.

## 7. Branding (white-label)

For Team+ (and required for Enterprise):

- **Logo** (top + bottom of every page).
- **Palette** (primary, accent).
- **Footer** (custom text, e.g. "Confidential — Acme Strategy").
- **Cover** (custom cover with client name).
- **Citation style** (numbered vs. author-date).

Branding is per-workspace; never per-report (to avoid accidental leakage).

## 8. Export formats

| Format | Engine | Use |
|---|---|---|
| PDF | reportlab + weasyprint | Default, prints well |
| DOCX | python-docx | Editable in Word |
| Markdown | native | Lightweight, git-friendly |
| HTML | native | Web sharing |
| PPTX | python-pptx | Board pack (post-MVP) |

All formats share the same source-of-truth structured report.

## 9. Acceptance criteria

- AC-RPT-0001-1: brief generated < 60s p75.
- AC-RPT-0002-1: full report 10–25 pages.
- AC-RPT-0006-1: PDF, DOCX, MD, HTML available.
- AC-RPT-0008-1: white-label applied (Enterprise).
- AC-RPT-0010-1: every claim footnoted.
- AC-RPT-0011-1: freshness shown per section.

## 10. Cost & latency

See Document 08 §9.

## 11. Failure modes

| Failure | Response |
|---|---|
| Section generation fails | Retry; if persistent, mark section "could not be generated" with explanation. |
| Verifier rejects | Re-generate with feedback; up to 2 retries; then surface. |
| Chart data missing | Render with placeholder; mark freshness. |
| Export fails | Provide alternative format; surface error. |
| User edits report | Edits are stored as a "manual override" version; original kept. |

## 12. Appendix

### 12.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 12.2 Cross-references

- Application Flow: Document 03 §7.
- Multi-Agent: Document 08.
- Agent Specs: Document 09.
- RAG: Document 10.
- Scoring Engine: Document 16.

---

> *End of Document 17 — Report Generation. The report is the artifact that makes the AI work shippable.*
