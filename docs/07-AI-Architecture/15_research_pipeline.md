---
title: Research Pipeline
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 15 — Research Pipeline

> The research pipeline is the **per-dimension** work that turns a candidate into a validated opportunity. This document specifies the depth levels, the per-dimension work, and the verification step.

## Table of Contents

1. Purpose & Scope
2. Depth levels
3. Dimensions
4. Per-dimension flow
5. Cross-dimension coherence
6. Evidence model
7. Verification
8. Human-in-the-loop
9. Cost & latency
10. Failure modes
11. Appendix

## 1. Purpose & Scope

This document is the contract for the **validation pipeline** — the system that takes a candidate opportunity and produces a structured, cited set of evidence across the eight standard dimensions.

## 2. Depth levels

| Depth | Sources per claim | Wall-clock | Token budget | Use |
|---|---|---|---|---|
| Quick | 1 | < 60s | 50k | Triage, scanning many |
| Standard | 3 | < 8 min | 400k | Default |
| Deep | 5+ | < 30 min | 1.2M | High-stakes (board, investor) |

## 3. Dimensions

The eight standard dimensions:

1. **Market** — size, growth, segmentation (AGT-RSRCH-MARKET).
2. **Demand** — search/social/intent signals (AGT-RSRCH-DEMAND).
3. **Competitive** — map, gaps (AGT-RSRCH-COMP).
4. **Pricing** — competitor pricing, WTP band (AGT-RSRCH-PRICING, AGT-RSRCH-WTP).
5. **Persona** — buyer personas (AGT-RSRCH-PERSONA).
6. **GTM** — channels and CAC (AGT-RSRCH-GTM).
7. **Risk** — risk register (AGT-RSRCH-RISK).
8. **Adjacency** — relation to user's existing business (custom rubric, AGT-RSRCH-COMP).

## 4. Per-dimension flow

```
plan → retrieve (RAG) → fetch (plugins) → synthesize → self-check
```

Detailed per agent in Document 09.

## 5. Cross-dimension coherence

Some claims span dimensions (e.g. WTP depends on persona and pricing). The pipeline:

- Identifies cross-dimension dependencies at plan time.
- Sequences the dependent dimensions so the upstream is finished first.
- Re-checks downstream claims when upstream changes (incremental re-validation).

## 6. Evidence model

```python
class Evidence(BaseModel):
    claim: str
    citations: list[Citation]
    freshness: Freshness
    confidence: Confidence
    snippet: str
    source_url: str
    captured_at: datetime
    agent_id: str
    step_id: UUID
```

Every claim is bound to ≥ 1 citation. The verifier audits this discipline.

## 7. Verification

Every dimension's output is verified (AGT-VERIFY):

- Each claim has a citation.
- Each citation is real (the chunk exists and the snippet matches).
- The claim is consistent with the source.
- No policy violations.

If verification fails, the orchestrator retries with corrective feedback. Two consecutive failures mark the dimension `unverified` and surface to the user.

## 8. Human-in-the-loop

The user can:

- **Attach manual evidence** to a dimension (uploaded doc, link, or note).
- **Override** a claim (the override is logged; the rationale is captured).
- **Reject** a dimension and re-run only that dimension.

## 9. Cost & latency

See Document 08 §9.

## 10. Failure modes

| Failure | Response |
|---|---|
| Source unavailable | Degrade; mark partial; surface in report. |
| RAG empty for a claim | Mark `unverified`; suggest user-supplied evidence. |
| LLM provider error | Retry; fallback; surface. |
| Verifier rejects twice | Mark `unverified`; surface. |
| Token budget exceeded | Skip non-critical dimensions; surface. |
| Wall-clock exceeded | Cancel; persist partial. |

## 11. Appendix

### 11.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 11.2 Cross-references

- Application Flow: Document 03 §5.
- Multi-Agent: Document 08.
- Agent Specs: Document 09.
- RAG: Document 10.
- Scoring Engine: Document 16.

---

> *End of Document 15 — Research Pipeline. The verification step is the trust backbone of the entire system.*
