---
title: Agent Specifications
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 09 — Agent Specifications

> Per-agent contracts. Each agent has a system prompt, a tool set, a state schema, success criteria, and a test plan. This document enumerates them.

## Table of Contents

1. Purpose & Scope
2. Specification template
3. Orchestrator (AGT-ORCH)
4. Discovery planner (AGT-DISC-PLANNER)
5. Discovery clusterer (AGT-DISC-CLUSTER)
6. Research — market (AGT-RSRCH-MARKET)
7. Research — demand (AGT-RSRCH-DEMAND)
8. Research — competitive (AGT-RSRCH-COMP)
9. Research — pricing (AGT-RSRCH-PRICING)
10. Research — persona (AGT-RSRCH-PERSONA)
11. Research — WTP (AGT-RSRCH-WTP)
12. Research — GTM (AGT-RSRCH-GTM)
13. Research — risk (AGT-RSRCH-RISK)
14. Scoring (AGT-SCORE)
15. Report writer (AGT-RPT-WRITER)
16. Verifier (AGT-VERIFY)
17. Safety filter (AGT-SAFETY)
18. Critic (AGT-CRITIC)
19. Appendix

## 1. Purpose & Scope

This document is the **per-agent contract**. Each agent must have:

- A unique ID and name.
- A purpose (one sentence).
- A system prompt (kept current in code; summarized here).
- A typed input/output schema.
- A tool set.
- Failure modes.
- Success criteria and test plan.

## 2. Specification template

```yaml
agent:
  id: AGT-<NAME>
  name: <name>
  purpose: <one sentence>
inputs:
  - <typed input>
outputs:
  - <typed output>
tools:
  - <tool id>
dependencies:
  - rag-svc | memory-svc | plugin-svc | ...
failure_modes:
  - <failure>
success_criteria:
  - <criterion>
test_plan:
  - <test>
```

The full per-agent YAMLs live in `agent-runtime/agents/<id>/contract.yaml`. This document is the index.

## 3. Orchestrator (AGT-ORCH)

- **Purpose:** Plan a run, dispatch specialists, manage state and budget.
- **Inputs:** `RunRequest{goal, depth, workspace_id, user_id}`.
- **Outputs:** final `RunState` with `evidence`, `scores`, `report` populated.
- **Tools:** none directly; dispatches specialists via in-process or NATS calls.
- **Dependencies:** RAG (read), memory (read/write), all specialists.
- **Failure modes:** budget exceeded, planner failure, unresolvable conflict.
- **Success criteria:** a complete run with all dimensions scored and cited.
- **Test plan:** mini-graph replays, end-to-end replays, adversarial planners.

## 4. Discovery planner (AGT-DISC-PLANNER)

- **Purpose:** Given a seed and a window, design a discovery run (sources, queries, depth).
- **Inputs:** seed, window, depth, source list.
- **Outputs:** `DiscoveryPlan{sources, queries, expected_yield}`.
- **Tools:** source metadata; planner-only tools (no external calls).
- **Success criteria:** plan that, when executed, produces ≥ expected yield with cited hits.
- **Test plan:** replay on 30 fixed seeds; expected yield threshold.

## 5. Discovery clusterer (AGT-DISC-CLUSTER)

- **Purpose:** Group raw hits into candidate opportunities (deduplicate, cluster).
- **Inputs:** `list[DiscoveryHit]`.
- **Outputs:** `list[CandidateOpportunity{title, summary, source_ids}]`.
- **Tools:** none external; uses embedding-based clustering.
- **Success criteria:** intra-cluster similarity > 0.85; inter-cluster similarity < 0.6.
- **Test plan:** synthetic clusters; cluster purity checks.

## 6. Research — market (AGT-RSRCH-MARKET)

- **Purpose:** Estimate TAM/SAM/SOM and growth for an opportunity.
- **Inputs:** `Opportunity`, source list, RAG.
- **Outputs:** `MarketEstimate{tam_usd, sam_usd, som_usd, growth_yoy_pct, sources, confidence}`.
- **Tools:** market data plugins (Statista-like, free data); RAG.
- **Success criteria:** estimate has ≥ 3 sources; ranges given; confidence assigned.
- **Test plan:** known markets replay; expert-set tolerance band.

## 7. Research — demand (AGT-RSRCH-DEMAND)

- **Purpose:** Aggregate demand signals (search volume, social volume, intent).
- **Inputs:** `Opportunity`, source list, RAG.
- **Outputs:** `DemandSignals{search_volume, social_volume, intent_signals, sources}`.
- **Tools:** Google Trends plugin, social APIs, RAG.
- **Success criteria:** at least 2 independent demand sources; signal strength graded.
- **Test plan:** replay on known keywords.

## 8. Research — competitive (AGT-RSRCH-COMP)

- **Purpose:** Build a competitive map (competitors, positioning, gaps).
- **Inputs:** `Opportunity`, source list, RAG.
- **Outputs:** `CompetitorMap{competitors:[{name, positioning, features, pricing_band}], gaps:[...]}`.
- **Tools:** web search, RAG, app store data, G2.
- **Success criteria:** ≥ 3 named competitors; each cited; ≥ 1 gap identified.
- **Test plan:** replay on known competitive markets.

## 9. Research — pricing (AGT-RSRCH-PRICING)

- **Purpose:** Collect competitor pricing tiers and ranges.
- **Inputs:** `Opportunity`, `CompetitorMap`.
- **Outputs:** `PricingBenchmark{tiers:[{competitor, plan, price, currency, as_of}]}`.
- **Tools:** web search, RAG.
- **Success criteria:** ≥ 50% of competitors have a price; freshness < 90d.
- **Test plan:** replay on known products.

## 10. Research — persona (AGT-RSRCH-PERSONA)

- **Purpose:** Synthesize 1–3 buyer personas from evidence.
- **Inputs:** `Opportunity`, `CompetitorMap`, RAG.
- **Outputs:** `Personas:[{name, demographics, pains, jobs, sources}]`.
- **Tools:** RAG, web search.
- **Success criteria:** each persona has ≥ 3 sourced pains/jobs.
- **Test plan:** replay on known audiences.

## 11. Research — WTP (AGT-RSRCH-WTP)

- **Purpose:** Estimate willingness to pay.
- **Inputs:** `Opportunity`, `PricingBenchmark`, `Personas`, RAG.
- **Outputs:** `WTP{low, mid, high, currency, rationale, sources}`.
- **Tools:** RAG, web search.
- **Success criteria:** range is plausible vs. competitor pricing; rationale cited.
- **Test plan:** replay on known markets.

## 12. Research — GTM (AGT-RSRCH-GTM)

- **Purpose:** Diagnose top 3 GTM channels used by competitors + estimated CAC.
- **Inputs:** `Opportunity`, `CompetitorMap`, RAG.
- **Outputs:** `GTM{channels:[{name, evidence, cac_band}]}`.
- **Tools:** web search, RAG.
- **Success criteria:** each channel has ≥ 1 cited source; CAC band present.
- **Test plan:** replay on known categories.

## 13. Research — risk (AGT-RSRCH-RISK)

- **Purpose:** Identify top risks and mitigations.
- **Inputs:** `Opportunity`, all prior research.
- **Outputs:** `RiskRegister{risks:[{name, likelihood, impact, mitigation, sources}]}`.
- **Tools:** RAG.
- **Success criteria:** ≥ 5 risks; each with mitigation; no generic boilerplate.
- **Test plan:** replay; reviewer scores specificity.

## 14. Scoring (AGT-SCORE)

- **Purpose:** Compute scores from evidence and rubric.
- **Inputs:** `evidence`, `rubric_version`.
- **Outputs:** `Score{total, breakdown, rationale, confidence}`.
- **Tools:** none (pure compute + LLM judge).
- **Success criteria:** score total is within ±0.5 of expert on a calibration set.
- **Test plan:** monthly calibration; rubric sensitivity.

## 15. Report writer (AGT-RPT-WRITER)

- **Purpose:** Assemble a long-form report from evidence + scores.
- **Inputs:** `evidence`, `scores`, `rubric`, persona context, report template.
- **Outputs:** `Report{sections:[{title, body, citations}]}`.
- **Tools:** RAG, chart render.
- **Success criteria:** every claim cited; report fits 10–25 pages; 95% acceptance.
- **Test plan:** golden set; report grading rubric; operator acceptance.

## 16. Verifier (AGT-VERIFY)

- **Purpose:** Audit another agent's output for citation, consistency, policy.
- **Inputs:** candidate output + source corpus.
- **Outputs:** `Verdict{ok, issues:[{severity, message, evidence}]}`.
- **Tools:** RAG, policy service.
- **Success criteria:** recall ≥ 0.9 on planted issues.
- **Test plan:** planted-issue test set; weekly recalibration.

## 17. Safety filter (AGT-SAFETY)

- **Purpose:** Redact PII; enforce content policy.
- **Inputs:** text, call context.
- **Outputs:** redacted text + flags.
- **Tools:** PII detector, policy lookup.
- **Success criteria:** ≥ 99% PII recall on test set; zero policy violations.
- **Test plan:** planted-PII test set; red-team review.

## 18. Critic (AGT-CRITIC)

- **Purpose:** Review a draft report and propose specific revisions.
- **Inputs:** draft report, evidence, persona.
- **Outputs:** `Revisions:[{section, change, rationale}]`.
- **Tools:** RAG, report diff.
- **Success criteria:** revisions accepted ≥ 70%.
- **Test plan:** paired report comparison.

## 19. Appendix

### 19.1 Agent ID index

| ID | Name |
|---|---|
| AGT-ORCH | Orchestrator |
| AGT-DISC-PLANNER | Discovery planner |
| AGT-DISC-CLUSTER | Discovery clusterer |
| AGT-RSRCH-MARKET | Research — market |
| AGT-RSRCH-DEMAND | Research — demand |
| AGT-RSRCH-COMP | Research — competitive |
| AGT-RSRCH-PRICING | Research — pricing |
| AGT-RSRCH-PERSONA | Research — persona |
| AGT-RSRCH-WTP | Research — WTP |
| AGT-RSRCH-GTM | Research — GTM |
| AGT-RSRCH-RISK | Research — risk |
| AGT-SCORE | Scoring |
| AGT-RPT-WRITER | Report writer |
| AGT-VERIFY | Verifier |
| AGT-SAFETY | Safety filter |
| AGT-CRITIC | Critic |

### 19.2 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 19.3 Cross-references

- Multi-Agent: Document 08.
- System Architecture: Document 07.
- Scoring Engine: Document 16.
- Report Generation: Document 17.

---

> *End of Document 09 — Agent Specifications. Per-agent YAML contracts are stored in `agent-runtime/agents/<id>/contract.yaml` and treated as code.*
