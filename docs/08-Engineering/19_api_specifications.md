---
title: API Specifications
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# Document 19 — API Specifications

> The contract for every public REST endpoint. The OpenAPI 3.1 spec is the source of truth; this document is the human-readable companion.

## Table of Contents

1. Purpose & Scope
2. API principles
3. Versioning
4. Authentication
5. Rate limits
6. Pagination
7. Idempotency
8. Errors
9. Webhooks
10. Resource models
11. Endpoint catalog
12. Deprecation policy
13. Appendix

## 1. Purpose & Scope

This document is the API contract. It defines how external clients (and internal services that act as clients) interact with the platform. The OpenAPI spec lives in `docs/api/openapi.yaml`; this document explains its structure and the rules it must follow.

## 2. API principles

- **RESTful** with pragmatic departures (e.g. RPC-style action endpoints for long-running tasks).
- **JSON** request and response bodies.
- **UTF-8** encoding.
- **ISO-8601** timestamps.
- **camelCase** JSON keys; **snake_case** query and path parameters.
- **Versioned URL prefix** (`/v1/`).
- **Predictable resource shapes** — the same shape returned by GET, POST, PATCH where possible.
- **Cursor pagination** for lists (stable under inserts).

## 3. Versioning

- URL-prefix versioning (`/v1/`).
- A breaking change → `/v2/`.
- Breaking changes include: removing a field, renaming a field, changing a field type, changing a status enum value, removing an endpoint, changing an auth flow.
- The v1 API is supported for 12 months after v2 GA.

## 4. Authentication

- **OAuth 2.1** with PKCE for browser flows.
- **API tokens** for server-to-server.
- All endpoints require a valid bearer token except `/healthz`, `/readyz`, `/docs`, `/redoc`, and the marketing site.

### 4.1 Token scopes

Tokens carry scopes. Examples:

- `opportunity:read`
- `opportunity:write`
- `validation:read`
- `validation:write`
- `report:read`
- `report:write`
- `rubric:read`
- `rubric:write`
- `workspace:read`
- `workspace:write`
- `member:read`
- `member:write`
- `webhook:read`
- `webhook:write`

A token is rejected with `403` if a required scope is missing.

## 5. Rate limits

| Tier | Per minute | Per hour | Per day |
|---|---|---|---|
| Free | 60 | 1,000 | 5,000 |
| Solo | 300 | 10,000 | 50,000 |
| Team | 1,500 | 50,000 | 250,000 |
| Enterprise | Custom | Custom | Custom |

- `429` returned with `Retry-After`.
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## 6. Pagination

- `?cursor=...&limit=...`
- Response: `{ "items": [...], "next_cursor": "..." | null }`.
- `limit` capped at 100 (default 25).
- Stable order: created_at DESC, id ASC.

## 7. Idempotency

- Mutating endpoints accept an `Idempotency-Key` header.
- The server stores the result for 24h.
- Retries with the same key return the original result (or a `409` if the request body differs).

## 8. Errors

All errors follow the same envelope:

```json
{
  "error": {
    "code": "string",
    "message": "human-readable",
    "details": { },
    "trace_id": "..."
  }
}
```

| HTTP | Code class | Example |
|---|---|---|
| 400 | `validation_error` | Missing required field |
| 401 | `unauthenticated` | Token missing or expired |
| 403 | `forbidden` | Missing scope |
| 404 | `not_found` | Resource not found |
| 409 | `conflict` | Idempotency key reused with different body |
| 422 | `unprocessable` | Business rule violation |
| 429 | `rate_limited` | Slow down |
| 500 | `internal_error` | Try again; trace_id is the support token |
| 503 | `service_unavailable` | Retry with backoff |

## 9. Webhooks

- Outbound webhooks are signed (`X-Signature: sha256=...`).
- Events use CloudEvents 1.0 envelope.
- Retries with exponential backoff; max 5; dead-letter after.
- `X-Webhook-Id` for dedup.

### 9.1 Event types (excerpt)

- `opportunity.created`
- `opportunity.updated`
- `opportunity.archived`
- `validation.requested`
- `validation.completed`
- `validation.failed`
- `score.computed`
- `report.generated`
- `report.exported`
- `subscription.changed`

## 10. Resource models

The complete JSON schemas are in the OpenAPI spec. Selected highlights:

### 10.1 Opportunity

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "title": "string",
  "summary": "string",
  "status": "watching|validating|active|archived",
  "score": { "total": 7.4, "confidence": "high" },
  "tags": ["string"],
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

### 10.2 Validation run

```json
{
  "id": "uuid",
  "opportunity_id": "uuid",
  "depth": "quick|standard|deep",
  "status": "queued|running|succeeded|partial|failed",
  "started_at": "ISO-8601",
  "completed_at": "ISO-8601 | null"
}
```

## 11. Endpoint catalog (selected)

| Method | Path | Description |
|---|---|---|
| POST | `/v1/opportunities` | Create an opportunity |
| GET | `/v1/opportunities` | List opportunities |
| GET | `/v1/opportunities/{id}` | Retrieve an opportunity |
| PATCH | `/v1/opportunities/{id}` | Update an opportunity |
| DELETE | `/v1/opportunities/{id}` | Archive (soft delete) |
| POST | `/v1/opportunities/{id}/validate` | Start a validation run |
| GET | `/v1/validations/{id}` | Retrieve a validation run |
| GET | `/v1/validations/{id}/evidence` | List evidence |
| GET | `/v1/opportunities/{id}/score` | Retrieve latest score |
| GET | `/v1/opportunities/{id}/scores` | Score history |
| POST | `/v1/opportunities/{id}/reports` | Generate a report |
| GET | `/v1/reports/{id}` | Retrieve a report |
| GET | `/v1/reports/{id}.{format}` | Export (pdf, docx, md, html) |
| GET | `/v1/rubrics` | List rubrics |
| POST | `/v1/rubrics` | Create a rubric |
| PATCH | `/v1/rubrics/{id}/versions` | New version |
| POST | `/v1/discovery/runs` | Start a discovery run |
| GET | `/v1/discovery/runs/{id}` | Retrieve a run |
| GET | `/v1/workspaces` | List workspaces |
| POST | `/v1/workspaces` | Create |
| GET | `/v1/workspaces/{id}/members` | List members |
| POST | `/v1/workspaces/{id}/members` | Invite |
| POST | `/v1/webhooks` | Register a webhook |
| GET | `/v1/webhooks` | List |

## 12. Deprecation policy

- An endpoint can be marked **Deprecated** without removal.
- The response includes a `Deprecation` and `Sunset` header.
- Documentation shows a banner.
- 12-month notice before removal.
- A **stable, deprecation-aware client** is shipped in our SDK.

## 13. Appendix

### 13.1 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 13.2 Cross-references

- TRD: Document 02.
- Backend: Document 05.
- Security: Document 21.

---

> *End of Document 19 — API Specifications. The OpenAPI spec is the source of truth; this document is the narrative.*
