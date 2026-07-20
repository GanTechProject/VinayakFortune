---
title: Data Governance
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 29 — Data Governance

> The contract for how data is collected, stored, processed, shared, and deleted across the platform. This is the bridge between the privacy/compliance regime and the engineering reality.

## Table of Contents

1. Purpose & Scope
2. Principles
3. Data inventory
4. Data classification
5. Data collection
6. Data processing
7. Data sharing
8. Data retention
9. Data deletion
10. Cross-border transfers
11. Subject rights
12. Data quality
13. AI data
14. Third-party processors
15. Audits
16. Appendix

## 1. Purpose & Scope

This document is the contract for **data governance** — what data the platform holds, how it is protected, and how it is operated across its lifecycle. It applies to all customer data and all platform telemetry.

## 2. Principles

1. **Purpose limitation.** Data is collected for a defined purpose and not reused beyond it.
2. **Data minimization.** We collect only what we need.
3. **Accuracy.** We keep data accurate and current.
4. **Storage limitation.** We retain data no longer than necessary.
5. **Integrity & confidentiality.** Data is protected end-to-end.
6. **Accountability.** Every data decision has an owner.

## 3. Data inventory

The platform holds:

- **Account data:** email, name, hashed password, OAuth IDs.
- **Workspace data:** workspace, members, roles.
- **Customer content:** opportunities, validations, reports, notes, uploads.
- **Telemetry data:** logs, metrics, traces (PII-redacted).
- **Billing data:** Stripe customer ID, subscription, invoices.
- **Audit data:** auth events, admin actions, AI plane calls (metadata only).

## 4. Data classification

| Class | Examples | Protection |
|---|---|---|
| Public | Marketing copy, public docs | Standard |
| Internal | Internal runbooks, dashboards | Standard |
| Confidential | Customer content, billing | Encrypted at rest with per-tenant DEK |
| Restricted | PII (email, name), credentials | Encrypted + access-controlled + audited |

## 5. Data collection

- **At signup:** email, name.
- **At workspace creation:** workspace name, region.
- **In the product:** user input (titles, summaries, notes); uploaded files; integration data.
- **Telemetry:** structured logs, metrics, traces — PII-redacted at source.

### 5.1 Cookie & tracker policy

- First-party only; no third-party trackers on the app.
- Analytics via Datadog RUM (PII-scrubbed).
- Marketing site uses privacy-friendly analytics.

## 6. Data processing

- **Within the AI plane:** all retrieved content is treated as untrusted; the verifier and safety filter audit every output.
- **Across services:** data is scoped to the workspace (Document 05 §11).
- **Across regions:** data residency is enforced at the storage layer (Document 21 §7).

## 7. Data sharing

- We do not sell customer data.
- We do not share customer data with third parties except:
  - Sub-processors (Document 29 §14) bound by DPA.
  - As required by law (with notice where lawful).
  - With the customer's explicit instruction (e.g. an integration they configured).

## 8. Data retention

| Class | Default retention |
|---|---|
| Account | Until account deletion + 30 days |
| Workspace content | Until workspace deletion + 30 days |
| Soft-deleted content | 30 days |
| Audit log | 1 year hot, 7 years cold |
| Telemetry | 30 days hot, 1 year cold |
| Billing | 7 years (legal) |

Enterprise customers can configure shorter retention per data class (Document 01 §8.7).

## 9. Data deletion

- **User-initiated:** account deletion cascades to user data within 30 days.
- **Workspace-initiated:** workspace deletion cascades to workspace data within 30 days.
- **Hard delete:** purges from backups within 90 days.
- **Right to be forgotten:** honored within 30 days of request; confirmation issued.

## 10. Cross-border transfers

- **Default:** US residency.
- **EU:** for Enterprise customers, data is held in `eu-west-1`.
- **APAC:** for Enterprise customers, data is held in `ap-northeast-1`.
- **Standard Contractual Clauses** in place for any cross-border processing.

## 11. Subject rights

- **Access:** users can export all their data.
- **Rectification:** users can correct their account data.
- **Erasure:** users can request account deletion.
- **Portability:** exports are available in machine-readable formats.
- **Object:** users can opt out of certain processing (e.g. platform memory).

## 12. Data quality

- **Validation** at every ingress point (Pydantic / Zod).
- **Backfill** jobs repair known data issues.
- **Quality metrics** on key datasets (e.g. opportunity titles are non-empty, citations resolve).
- **Quarterly review** of data quality dashboard.

## 13. AI data

- **Training:** we do not train foundation models on customer data.
- **Embedding:** customer content is embedded into a per-workspace index; never shared.
- **LLM calls:** customer content is sent to LLM providers under our enterprise agreement (no training use, no retention beyond safety logging).
- **Memory:** scoped (Document 11).

## 14. Third-party processors

The list is published at `security.ventureminer.ai/sub-processors`. Any new sub-processor is announced 30 days before activation. Examples:

- Auth0 (auth)
- Anthropic (LLM)
- OpenAI (LLM fallback)
- Stripe (billing)
- Postmark (email)
- AWS (infrastructure)
- Datadog (observability)
- Cloudflare (CDN, optional)

Each is bound by a DPA.

## 15. Audits

- **Internal:** quarterly data governance review.
- **External:** SOC 2 Type II audit (annual), ISO 27001 audit (M18), customer audits (Enterprise).
- **Sub-processor audits:** annual review of each critical sub-processor's posture.

## 16. Appendix

### 16.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 16.2 Cross-references

- PRD: Document 01 §8.
- Security: Document 21.
- Operations: Document 28.
- AI Operations: Document 18.

---

> *End of Document 29 — Data Governance. Trust is a function of how data is handled.*
