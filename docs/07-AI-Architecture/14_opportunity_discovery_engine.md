---
title: Opportunity Discovery Engine
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 14 — Opportunity Discovery Engine

> How the platform finds candidate opportunities from raw signals. The discovery engine is the **upstream** of the entire pipeline; the quality of everything downstream depends on it.

## Table of Contents

1. Purpose & Scope
2. Discovery flow
3. Sources
4. Query construction
5. Signal capture
6. Clustering & dedupe
7. Novelty scoring
8. Filtering & ranking
9. Continuous discovery
10. Cost & scale
11. Quality evaluation
12. Failure modes
13. Appendix

## 1. Purpose & Scope

This document defines the discovery engine — the system that takes a seed (or watchlist) and produces a list of candidate opportunities. It is the entry point to the AI pipeline.

## 2. Discovery flow

```
seed + window + depth
  → query construction
  → fan-out to sources
  → signal capture
  → dedupe + cluster
  → novelty score
  → rank + filter
  → present to user
```

Detailed in Document 03 §4 and Document 08 §3.

## 3. Sources

| Source | Type | Auth | Cost |
|---|---|---|---|
| Reddit | Public + OAuth | OAuth | Free |
| X (Twitter) | API v2 | OAuth | $$ |
| Hacker News | Public | — | Free |
| GitHub trending | Public API | Optional OAuth | Free |
| Google Trends | Public | — | Free |
| G2 reviews | Public | — | Free |
| Product Hunt | Public | OAuth | Free |
| App Store / Play Store | Public RSS | — | Free |
| LinkedIn (post-MVP) | API | OAuth | $$$ |
| Industry data packs | Curated | — | $$$ |

Each source has a connector (Document 13) and a configurable weight.

## 4. Query construction

The **discovery planner** (AGT-DISC-PLANNER) generates a list of source-specific queries from a seed. For example, given `"AI for solopreneurs"`:

- Reddit: `solopreneur` `indie hacker` `AI tools` (last 30d, top 200)
- X: `solopreneur AI` (last 30d, top 200 by engagement)
- G2: category `ai-assistants`, sort by `trending`
- Google Trends: `solopreneur AI`, `indie AI tools`, …

## 5. Signal capture

Each connector returns a normalized `DiscoveryHit`:

```json
{
  "id": "...",
  "title": "...",
  "url": "...",
  "summary": "...",
  "source": "reddit",
  "source_meta": { "subreddit": "...", "score": 412, "comments": 53 },
  "captured_at": "2026-07-20T12:00:00Z",
  "freshness": "live",
  "embedding": [ ... ]
}
```

Signals are stored in `discovery.discovery_hit` and indexed in the RAG corpus (Document 10).

## 6. Clustering & dedupe

- Embedding-based clustering (Document 09 §5).
- Intra-cluster similarity ≥ 0.85 → merge.
- Inter-cluster similarity ≤ 0.6 → separate.
- Each cluster becomes a `CandidateOpportunity` with a canonical title and a list of source hits.

## 7. Novelty scoring

Each candidate receives a novelty score based on:

- **Frequency in last 90d** (rising vs. flat).
- **Sentiment shift** (positive vs. negative trend).
- **Source diversity** (more sources = more cross-validated).
- **Uniqueness vs. existing opportunities** in the workspace (cosine distance).

Score range: 0–10.

## 8. Filtering & ranking

- **Filter:** must have ≥ 2 distinct sources (or 1 high-trust source for Quick depth).
- **Filter:** must have at least 1 pain point, trend, or feature request (not pure news).
- **Rank:** composite of novelty + source diversity + freshness.

## 9. Continuous discovery

- **Always-on mode** (Team+, post-MVP) runs the planner on a schedule per workspace.
- A **watchlist** defines seeds; planner produces daily runs; user is notified of high-novelty hits.
- **Quiet hours** can be configured.

## 10. Cost & scale

- **v1:** 5k discovery runs/day, 200k hits/day, 50k candidate opportunities/day.
- **v2:** 50k discovery runs/day.

## 11. Quality evaluation

- **Hit precision:** of hits surfaced, what fraction leads to a pinned opportunity?
- **Cluster purity:** of clusters, what fraction are clean (single concept)?
- **Recall vs. baseline:** is the engine finding opportunities that a human researcher finds?
- Eval set: 100 known opportunities + 100 known non-opportunities.

## 12. Failure modes

| Failure | Response |
|---|---|
| Source API down | Skip; mark partial; user notified. |
| Source rate-limited | Backoff; cap; rotate keys. |
| Embedding failure | Use lexical clustering fallback. |
| Low hit yield | Surface notice; suggest query relaxation. |
| High hit yield | Cap and rank; offer to broaden depth. |

## 13. Appendix

### 13.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 13.2 Cross-references

- Application Flow: Document 03 §4.
- Multi-Agent: Document 08.
- Agent Specs: Document 09.
- RAG: Document 10.
- Plugin Architecture: Document 13.

---

> *End of Document 14 — Opportunity Discovery Engine. The quality of everything downstream depends on this engine's discipline.*
