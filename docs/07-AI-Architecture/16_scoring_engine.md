---
title: Scoring Engine
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 16 — Scoring Engine

> The scoring engine turns evidence into a single, defensible number. This document defines the default rubric, the scoring algorithm, the rationale discipline, and the calibration methodology.

## Table of Contents

1. Purpose & Scope
2. Scoring principles
3. Default rubric
4. Custom rubrics
5. Scoring algorithm
6. Sub-scoring
7. Rationale
8. Confidence
9. Calibration
10. Re-scoring & history
11. Failure modes
12. Appendix

## 1. Purpose & Scope

This document is the contract for the scoring engine — the system that consumes evidence and a rubric and produces a defensible score with full traceability.

## 2. Scoring principles

- **Transparent.** The rubric is editable; the formula is exposed.
- **Cited.** Every sub-score has at least one contributing evidence citation.
- **Calibrated.** Scores are tested against expert judgments monthly.
- **Versioned.** A score is always bound to a specific rubric version.
- **Composable.** Sub-scores can be combined in user-defined ways.

## 3. Default rubric

| Dimension | Weight | Description |
|---|---|---|
| Market size | 20% | TAM/SAM/SOM band |
| Growth | 15% | YoY/CAGR |
| Demand | 20% | Search/social/intent |
| Buildability | 15% | Time + cost to MVP |
| Defensibility | 15% | Differentiation, moat |
| AI-fit | 15% | Natural LLM advantage |

## 4. Custom rubrics

- Workspace admins can edit:
  - Add / remove / rename dimensions.
  - Change weights (must sum to 100).
  - Add sub-criteria to a dimension.
  - Override description text.
- Every change is a **new rubric version**.
- Scores from old versions remain visible.

## 5. Scoring algorithm

For each dimension:

1. **Retrieve** relevant evidence (RAG, scoped to opportunity).
2. **LLM judge** produces a sub-score (0–10) + rationale + confidence.
3. **Verifier** audits the sub-score:
   - Rationale references real evidence.
   - Sub-score is consistent with rationale.
   - No policy violation.

Total score = Σ (weight_i × sub_score_i), normalized to 0–10.

## 6. Sub-scoring

A dimension can have sub-criteria. The dimension score is:

```
dim_score = Σ (sub_weight_j × sub_score_j)
```

The total score is unchanged (sum of dim_weights × dim_scores).

## 7. Rationale

Every sub-score ships with:

- 1–3 sentences explaining the score.
- Citations to the evidence that drove the score.
- A confidence grade (low / med / high).

Rationales are user-visible; they are the trust surface.

## 8. Confidence

Confidence is graded by:

- **Evidence count** — more sources → higher confidence.
- **Evidence quality** — primary sources rank higher than secondary.
- **Recency** — recent data boosts confidence.
- **Convergence** — multiple sources agreeing boost confidence.

Confidence is exposed in the UI as a colored band on the score.

## 9. Calibration

- **Calibration set:** 200 scored opportunities reviewed by 3 experts.
- **Monthly:** the engine scores the set; mean absolute error (MAE) is measured.
- **Threshold:** MAE > 1.0 triggers a rubric review.
- **Drift detection:** weekly tracking of user feedback (acceptance, edits); significant drift triggers recalibration.

## 10. Re-scoring & history

- **Re-score** on new evidence is automatic (subscribed to `validation.completed`).
- **History** is preserved; users can view the score timeline.
- **Diff** is shown when the score changes by > 0.5.

## 11. Failure modes

| Failure | Response |
|---|---|
| LLM judge unavailable | Retry; fallback model. |
| Evidence missing for a dimension | Sub-score = null; dimension excluded from total; surface. |
| Rubric invalid (weights ≠ 100) | Reject; admin must fix. |
| Verifier rejects twice | Mark dimension `unverified`; surface. |
| Calibration drift | Trigger rubric review. |

## 12. Appendix

### 12.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 12.2 Cross-references

- Agent Specs: Document 09 §14.
- Research Pipeline: Document 15.
- Report Generation: Document 17.

---

> *End of Document 16 — Scoring Engine. A score without rationale is not a score — it is a guess.*
