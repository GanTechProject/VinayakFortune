---
title: MCP Tool Catalog
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 20 — MCP Tool Catalog

> The catalog of every tool exposed via the MCP gateway. The manifest of each tool is the source of truth; this document is the human index.

## Table of Contents

1. Purpose & Scope
2. Tool ID conventions
3. Bundled tools
4. Source tools
5. RAG tools
6. Memory tools
7. Internal tools
8. Public tools (v2)
9. Deprecation
10. Appendix

## 1. Purpose & Scope

This document is the index of every tool the platform exposes. It exists so that an engineer (or a future agent) can find the right tool quickly and know its risk profile.

## 2. Tool ID conventions

- `T-<DOMAIN>-<NAME>` for internal tools.
- `T-EXT-<PROVIDER>` for external services.
- `T-PUB-<NAME>` for public-facing tools (v2).

Risk levels: **low / medium / high** — see Document 12 §4.

## 3. Bundled tools (shipped with the platform)

| ID | Name | Description | Risk |
|---|---|---|---|
| T-RAG-SEARCH | RAG Search | Hybrid retrieval from corpus | low |
| T-RAG-INDEX | RAG Index | Upsert chunk into index | medium |
| T-MEM-READ | Memory Read | Read user/workspace memory | low |
| T-MEM-WRITE | Memory Write | Append a memory record | medium |
| T-WEB-SEARCH | Web Search | Search the public web | low |
| T-WEB-FETCH | Web Fetch | Fetch a URL with caching | low |
| T-CHART-RENDER | Chart Render | Render chart from data | low |
| T-EXPORT-PDF | Export PDF | Render a PDF from structured data | low |
| T-EXPORT-DOCX | Export DOCX | Render a DOCX | low |
| T-NUMERIC-EVAL | Numeric Eval | Safe evaluator for math | low |

## 4. Source tools (external data sources)

| ID | Name | Description | Risk |
|---|---|---|---|
| T-REDDIT-SEARCH | Reddit Search | Search public subreddits | low |
| T-X-SEARCH | X Search | Search X (Twitter) | medium |
| T-HN-SEARCH | HN Search | Search Hacker News | low |
| T-GH-TRENDING | GitHub Trending | Trending repos | low |
| T-GH-SEARCH | GitHub Search | Search public code/issues | low |
| T-GTRENDS | Google Trends | Trends over time | low |
| T-APPSTORE | App Store | iOS app search | low |
| T-PLAYSTORE | Play Store | Android app search | low |
| T-G2 | G2 Reviews | G2 reviews for a product | medium |
| T-PH | Product Hunt | Product Hunt data | medium |

## 5. RAG tools

- `T-RAG-SEARCH` — primary retrieval.
- `T-RAG-INDEX` — for ingestion jobs.

## 6. Memory tools

- `T-MEM-READ` — agent reads memory.
- `T-MEM-WRITE` — agent writes memory; subject to verifier + safety filter.

## 7. Internal tools

- `T-INTERNAL-OPPORTUNITY-READ` — read opportunity.
- `T-INTERNAL-OPPORTUNITY-WRITE` — write opportunity (RBAC-checked).
- `T-INTERNAL-VALIDATION-READ` / `-WRITE`.
- `T-INTERNAL-REPORT-READ` / `-WRITE`.
- `T-INTERNAL-AUDIT-LOG` — emit an audit event.

## 8. Public tools (v2)

- A curated subset of the above, exposed to third-party MCP-aware clients.
- Per-client rate limits; per-client API tokens.

## 9. Deprecation

- A tool can be marked deprecated in its manifest.
- The gateway continues to serve it but emits a deprecation header.
- 12-month notice before retirement.

## 10. Appendix

### 10.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 10.2 Cross-references

- MCP Architecture: Document 12.
- Plugin Architecture: Document 13.

---

> *End of Document 20 — MCP Tool Catalog. The manifest is the contract; this document is the index.*
