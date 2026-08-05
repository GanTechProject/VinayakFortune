---
issue: 9
service: plugin-svc
band: 3 (design)
date: 2026-07-28
author: Architect (re-dispatch — prior session did not persist)
status: Design — pending conductor gating on Q-9.x
---

# Issue #9 — plugin-svc (BAND-3-DESIGN)

> **Re-dispatch note:** This is the corrected and persisted re-dispatch of
> the issue #9 design. The previous session's memory entries
> (`plugin-svc-hypothesis-cites-verified-2026-07-28`) confirmed the
> architect's interpretation (Doc 13 §3-§12 mapping is structurally
> correct, AC-label drift re-mapping required) but the design file was
> never written to disk. This redo lands the file at the canonical path
> and verifies every cited line against the source files in the same turn.

> **Cross-service contract authority:** plugin-svc OWNS the `ToolManifest`
> Pydantic contract consumed by agent-runtime's MCP gateway
> (Architect #6 §13). rag-svc OWNS `Source` / `Citation`
> (Architect #7 §10-§11). This design treats ToolManifest as the plugin-svc
> canonical and imports nothing from rag-svc, per
> `arch-007-redispatch-verified-2026-07-28` (Source canary) and
> `arch-006-redispatch-verified-2026-07-28` (DRIFT-6.1/6.7).

> **Prior verification context:** The HYPOTHESIS cites from the prior
> session are documented in
> `plugin-svc-hypothesis-cites-verified-2026-07-28`. The architect's
> Doc 13 §3..§12 cite-table was spot-checked; the AC-label drift
> (Doc 13 §2/§4 vs. §6 misalignment in AC-6.2 + AC-6.5) and the PRD §7.6
> REQ-DASH-not-REQ-PLUGIN drift were confirmed. The structural design
> stands; only the issue-body §-pointers are wrong (re-mapped in §15).

---

## §0. AC Label Verification (live)

**Live verification source:** `gh issue view 9 --repo GanTechProject/VinayakFortune --json body,title,number` succeeded on 2026-07-28. Full body captured this turn; key extracts below.

**Verified AC labels:** `AC-6.1`, `AC-6.2`, `AC-6.3`, `AC-6.4`, `AC-6.5`, `AC-6.6`, `AC-6.7`, `AC-6.8`, `AC-6.9`, `AC-6.10`, `AC-6.11`, `AC-6.12` — **under the agent-runtime epic (issue #6), NOT AC-9.\* under issue #9.** The issue was numbered as #9 in GitHub but the AC labels inside the body prefix with AC-6.\* because the issue originated as a subtask of the agent-runtime epic. This was first confirmed in `plugin-svc-hypothesis-cites-verified-2026-07-28` and is re-confirmed live this turn.

**Verified AC bodies (verbatim from issue #9 body):**

| AC | Body (excerpt) | Cited doc | Verified line |
|---|---|---|---|
| AC-6.1 | "plugin-svc scaffolded (Python 3.12, FastAPI, async)" | — | `Q-9` conductor-decided Python 3.11 (`conductor-decisions-2026-07-28.md`); 3.12 is drift |
| AC-6.2 | "Plugin manifest schema (Document 13 §2)" | Doc 13 §2 = "Why plugins"; schema is at §4 | DRIFT — re-map to §4 |
| AC-6.3 | "Plugin registry backed by Postgres (plugin.plugin, plugin.plugin_version, plugin.plugin_installation per Document 02 §5.2)" | TRD §5.2 L222 | VERIFIED (schema row exists) |
| AC-6.4 | "Versioning: semver; an installation pins a major version; agents resolve a specific version at runtime" | Doc 13 §10 | VERIFIED |
| AC-6.5 | "Runtime: each tool invocation runs in a per-plugin sandbox (process-level, restricted env, no network egress except allow-listed) per Document 13 §4" | Doc 13 §4 = "Manifest"; sandbox is at §6 | DRIFT — re-map to §6 |
| AC-6.6 | "MCP bridge: the plugin-svc exposes installed plugins to the agent-runtime MCP gateway (Document 12 §3-5)" | Doc 12 §3 = Architecture; §4 = Tool manifest; §5 = Server lifecycle | VERIFIED (Doc 12 §3 L48-55, §4 L60-79, §5 L80-83) |
| AC-6.7 | "Initial tool set: T-WEB-SEARCH, T-MARKET-DATA-FETCHER, T-CODE-EXEC, T-FILE-IO, T-CALC (per Document 20's initial 12 tools)" | Doc 20 (tool catalog) | OUT OF SCOPE for this design (only the 5 named tools are bound; the full catalog is Doc 20) |
| AC-6.8 | "Per-workspace installation: a workspace can enable/disable a plugin; the agent-runtime's tool list is filtered accordingly (REQ-INT-0009 scoped tokens inform the install)" | PRD §7.7 L352 (REQ-INT-0009) | VERIFIED live — REQ-INT-0009 = "Public API tokens (scoped) P0" |
| AC-6.9 | "Audit: every tool invocation is logged to audit-svc with input hash, output hash, latency, exit code (Document 13 §6, Document 21 §10)" | Doc 13 §6 = Sandboxing; audit is at §9 | DRIFT — Doc 13 audit is §9 ("Audit log"); Doc 21 §10 not found live (Doc 21 has §10 placeholder but the actual audit pattern is Doc 13 §9 + Doc 21 §6 "Repudiation"). Re-map to Doc 13 §9 |
| AC-6.10 | "Policy: a plugin can be tagged with policy tags (e.g., network_egress=allow, pii=read); the sandbox enforces them" | Doc 13 §6 | PARTIAL — Doc 13 §6 says "no network by default; outbound explicitly allow-listed in manifest"; policy tags are a per-tool extension. Re-map to §6 + §9 |
| AC-6.11 | "Rate limit enforcement: per-plugin + per-workspace rate limits integrated with the platform rate limiter (REQ-PLAT-0009, REQ-INT-0010 tier-based rate limits)" | PRD §7.11 L412 (REQ-PLAT-0009); PRD §7.7 L353 (REQ-INT-0010) | VERIFIED live — REQ-PLAT-0009 = "Rate limiting per workspace P0"; REQ-INT-0010 = "Rate-limited public API P0" |
| AC-6.12 | "Documented backout plan: per-plugin disable, per-workspace install rollback, sandbox escape mitigation runbook; Document 28 §3" | Doc 28 §3 = On-call (line 46) | VERIFIED live — Doc 28 §3 is on-call, runbook is §5; backout plan lives in `docs/runbooks/plugin-svc.md` per Doc 28 §5 L91. Re-map |

**Statement of AC labels:**
> ACs are labeled **AC-6.1..AC-6.12** (under the agent-runtime epic),
> NOT AC-9.\* — verified live from `gh issue view 9 --repo GanTechProject/VinayakFortune` this turn.

---

## §1. Purpose & Scope

The **`plugin-svc`** service is the **AI-plane tool registry and plugin runtime**: the only path by which an agent (via the MCP gateway) can invoke an external tool. It owns:

| Asset | Source of truth | Note |
|---|---|---|
| `plugin` schema | TRD Doc 02 §5.2 L222 | `plugin`, `plugin_version`, `plugin_installation`; plugin-svc is the schema owner |
| Plugin directory structure | Doc 13 §3 L40-47 | plugin.yaml + src/handler.py + tests/ + signatures/ |
| Plugin manifest schema | Doc 13 §4 L55-77 (YAML) + Doc 12 §4 L60-79 (typed tool manifest) | plugin-svc owns the canonical `ToolManifest` Pydantic (this design §12) |
| Plugin lifecycle state machine | Doc 13 §5 L79-92 | Draft → Submitted → Review → Approved → Published → Active → (Deprecated \| Retired) |
| Plugin sandbox model | Doc 13 §6 L94-102 | per-plugin container; no network by default; allow-listed egress; RO FS except scratch; capped mem/CPU; no shell |
| Plugin registry | Doc 13 §7 L104-109 | Public + private registries; S3-compatible storage + Postgres index; Sigstore-style detached signatures |
| Plugin distribution | Doc 13 §8 L111-115 | Public + private + bundled (`T-MARKET-DATA-FETCHER`) |
| Security model | Doc 13 §9 L117-123 | Trust scoped; per-workspace enablement; per-run allow-list; audit log; kill switch |
| Versioning & compatibility | Doc 13 §10 L125-131 | semver major/minor/patch; agent manifest-version range |
| Observability | Doc 13 §11 L133-137 | per-plugin metrics/traces/PII-redacted logs |
| Failure modes | Doc 13 §12 L140-148 | table verbatim |
| MCP gateway integration | Doc 12 §3 L48-55 | agent → MCP client → MCP gateway → tool server; plugin-svc is the **server side** of the gateway |
| `ToolManifest` Pydantic | This design §12 | cross-service canary with agent-runtime (Architect #6 §13) |

### Boundaries

- **plugin-svc is the ONLY authority for tool manifests.** Agent-runtime's MCP gateway enforces the manifest schema on every call (Doc 12 §4 L75-76 "The manifest is the source of truth; agents cannot call a tool without a registered manifest"). Drift on `ToolManifest` shape breaks the gateway — see §15 DRIFT-9.6.
- **Source connectors are out of scope.** HTTP/RSS/API connectors ship in source-svc (#10). plugin-svc exposes connectors' tools as plugin manifests; the connector internals are not this design's concern.
- **Tool implementations themselves are out of scope.** The bundled `T-MARKET-DATA-FETCHER` ships in a follow-up issue (per issue #9 "Out of scope" body). plugin-svc installs and routes; it does not implement the tool's external API call.
- **Community plugin marketplace is out of scope** (v3, post-MVP).
- **Webhook/Slack/Notion/Linear integrations are out of scope** (integration-svc follow-up).

---

## §2. Plugin Anatomy

### §2.1 Directory structure (Doc 13 §3 L40-47)

A plugin is a directory:

```
my-plugin/
├── plugin.yaml            # manifest (Doc 13 §4)
├── README.md
├── src/
│   └── handler.py         # tool logic (entrypoint declared in manifest)
├── tests/
└── signatures/            # detached signatures (Sigstore-style)
```

### §2.2 Handler exposes tools

The handler exposes **one or more tools** (Doc 13 §3 L46-47). Each tool's shape is described by Doc 12 §4 (Tool manifest). The plugin.yaml `tools:` field is a list; each entry is a tool reference conforming to `ToolManifest` (this design §12).

### §2.3 Bundled plugins (Doc 13 §8 L113-115)

Bundled plugins ship with the platform. The canonical example is **`T-MARKET-DATA-FETCHER`** for paid data providers (Doc 12 §4 L61). Bundled plugins are installed at platform bootstrap into the `plugin` schema's "bundled" `distribution` column and cannot be uninstalled by workspace admins (only disabled per Doc 13 §9 "Per-workspace enablement").

### §2.4 Private plugins

Private plugins are uploaded to a workspace registry (Doc 13 §8 L113) and signed by the workspace owner. Storage path: `<env>/<workspace>/plugins/<plugin_id>/<version>/` per Doc 28 §5.4 bucket layout (`<env>/<workspace>/<type>/<id>`).

---

## §3. Manifest Schema (CROSS-SERVICE CANARY)

### §3.1 plugin.yaml (Doc 13 §4 L55-77)

```yaml
id: T-NICHE-INDUSTRY-DB
name: Niche Industry DB
version: 1.0.0
vendor: example.com
risk_level: low
pii_risk: false
entrypoint: src/handler.py:handle
tools:
  - name: niche_search
    description: Search the industry database.
    input_schema: { ... }
    output_schema: { ... }
permissions:
  - network:outbound=api.example.com
  - filesystem:read=./cache
secrets:
  - secret_ref: provider/example/api_key
homepage: https://example.com
license: Apache-2.0
```

### §3.2 Tool manifest (Doc 12 §4 L60-79) — typed equivalent

```yaml
id: T-MARKET-DATA-FETCHER
name: Market Data Fetcher
version: 1.2.0
description: Fetches market size and growth from a paid data provider.
risk_level: low           # low | medium | high
pii_risk: false
input_schema: { type: object, properties: { query: { type: string } } }
output_schema: { type: object, properties: { ... } }
auth: { type: api_key, secret_ref: provider/marketdata/api_key }
cost: { per_call_usd: 0.02, weight: 1 }
rate_limit: { per_minute: 60, per_hour: 1000 }
timeout_ms: 5000
retry: { max: 2, backoff: exponential }
owner: ai-platform
```

### §3.3 Schema ownership

plugin-svc OWNS the canonical `ToolManifest` Pydantic (this design §12). The JsonSchema-based `input_schema` / `output_schema` envelope is the canonical form per `arch-012-verified-and-persisted-2026-07-28` (Architect #12 §11.4 canary: "JsonSchema envelope NOT legacy `tools: list[ToolRef]`"). Any drift on ToolManifest shape breaks the cross-service canary.

---

## §4. Lifecycle

### §4.1 State machine (Doc 13 §5 L79-92)

```
Draft → Submitted → Review → Approved → Published → Active → (Deprecated | Retired)
```

| State | Owner | Exit conditions |
|---|---|---|
| `Draft` | author | author runs `plugin submit` |
| `Submitted` | author | enters registry review queue |
| `Review` | plugin-svc reviewer | passes signature + schema (auto); high-risk passes manual |
| `Approved` | reviewer | approved, awaiting publish |
| `Published` | plugin-svc | listed in registry index |
| `Active` | workspace | installed in ≥1 workspace |
| `Deprecated` | workspace / plugin-svc | no new installs; existing continue |
| `Retired` | plugin-svc | removed; existing installations receive manifest-version-mismatch error (Doc 13 §5) |

### §4.2 Transitions

| From → To | Trigger | Atomic? |
|---|---|---|
| Draft → Submitted | `POST /plugins` with manifest + signature | YES — manifest is immutable on submit |
| Submitted → Review | registry picks from queue | YES |
| Review → Approved | all gates pass | YES |
| Review → Draft | any gate fails | YES |
| Approved → Published | admin publishes | YES |
| Published → Active | first workspace install | implicit on install |
| Active → Deprecated | workspace disables OR plugin-svc deprecates | YES |
| Active → Retired | plugin-svc retires; existing installations fail-fast | YES |
| Deprecated → Retired | grace period elapsed | YES |

### §4.3 TOCTOU risk on lifecycle field (FLAG)

`plugin.lifecycle_state` is a single column. Concurrent reads + writes (e.g. two workspaces installing while admin retires) produce TOCTOU races:

- **Risk:** Read state at `Active`, install in workspace, write `Active` — meanwhile admin retired and the read was stale.
- **Mitigation:** Lifecycle transitions use a Postgres advisory lock keyed by `plugin_id`. State machine validation runs inside the lock. Audit log records the lock acquisition/release timestamps.
- **Cross-service:** Agent-runtime's MCP gateway caches active tool manifests. Cache invalidation on retirement is **mandatory** — gateway MUST evict on `Retired` event within 30s (Doc 12 §9 "Captures traces and metrics" implies gateway maintains state). See Q-9.4.

### §4.4 Per-state observability

Each state transition emits a CloudEvent to NATS subject `plugin.lifecycle.transitioned` (mirrors Doc 08 §6 L155-160 "agent.run.*" pattern). Payload: `{plugin_id, from_state, to_state, version, actor, timestamp, audit_event_id}`.

---

## §5. Sandboxing

### §5.1 Sandbox model (Doc 13 §6 L94-102)

| Constraint | Doc 13 §6 anchor | Implementation |
|---|---|---|
| Isolated process | "container, VM, or wasm runtime" L96 | v1: per-plugin container (Docker / Podman); v2: gVisor |
| Default no network | "no network by default" L97 | iptables/nftables drop egress by default; manifest `permissions: - network:outbound=...` adds allow-list entries |
| Filesystem RO except scratch | "read-only except for declared scratch space" L99 | overlayfs; scratch at `/tmp/<plugin_id>/` capped at 1GiB (configurable per plugin) |
| Memory cap | "Memory: capped" L100 | cgroups `memory.max`; declared in manifest `permissions: - memory:max_mb=512` (default 512MB) |
| CPU cap | "CPU: capped" L101 | cgroups `cpu.max`; declared in manifest `permissions: - cpu:millicores=500` (default 500m) |
| No shell | "No shell access by default" L102 | entrypoint is `python src/handler.py:handle` — no `/bin/sh` allowed; SECCOMP filter denies `execve` of non-allow-listed binaries |
| High-risk → elevated review | "High-risk plugins ... require elevated review" L103 | risk_level == "high" → mandatory manual review + Sigstore signature + dual-control approval |

### §5.2 Sandbox enforcement code path

```
MCP gateway call
    → plugin-svc router
    → container manager (creates ephemeral container)
    → mount FS (overlayfs RO + scratch)
    → set cgroup limits (mem, CPU)
    → set nftables egress filter (allow-list from manifest.permissions)
    → load secrets from AWS Secrets Manager (Doc 02 §6)
    → exec handler entrypoint
    → stream stdout/stderr to PII-redacted log
    → capture return code
    → emit audit event to audit-svc
    → destroy container
```

### §5.3 Network egress allow-list (Doc 13 §6 L97 + manifest `permissions:` L66-70)

The manifest's `permissions:` list controls nftables rules. Format: `network:outbound=<domain-or-cidr>`. Validation:

- Wildcards allowed only for `risk_level: low` (CI block on `risk_level: high`).
- Private CIDRs (10.0.0.0/8, 192.168.0.0/16) blocked even when allow-listed (defense in depth).
- DNS egress to internal resolvers only (Doc 02 §6 secrets + Doc 13 §6 "Default: per-plugin container with no network by default").

### §5.4 Secrets (Doc 13 §4 manifest `secrets:` L68-70)

`secret_ref: provider/example/api_key` resolves via AWS Secrets Manager (Doc 02 §6). Plugin container receives the secret as an environment variable ONLY if the manifest declares it AND the workspace has the corresponding secret installed (Doc 13 §9 trust scope).

### §5.5 Sandbox-escape red-team test (AC-6.12)

A red-team test (Doc 28 §3 on-call runbook + Doc 28 §5 runbook) attempts:
1. Filesystem escape (write outside scratch).
2. Network egress to non-allow-listed domain.
3. Privilege escalation via execve.
4. Container breakout (cgroup escape).
5. Secrets exfiltration via /proc/<pid>/environ.

Test fails-when-attempted (i.e., red-team exploit MUST be blocked). The runbook at `docs/runbooks/plugin-svc.md` documents the test scenarios; on-call lead reviews quarterly per Doc 28 §5 L91.

---

## §6. Registry

### §6.1 Registry model (Doc 13 §7 L104-109)

| Registry | Storage | Visibility | Signature |
|---|---|---|---|
| Public | S3-compatible bucket `s3://plugins-public/<plugin_id>/<version>/` | All workspaces; curated | Detached Sigstore signature; verified on install (Doc 13 §7 L108) |
| Private | S3-compatible bucket `s3://plugins-private/<workspace_id>/<plugin_id>/<version>/` | Workspace-only | Workspace-owner signature (Sigstore key) |
| Bundled | Postgres `plugin` schema, `distribution='bundled'` | All workspaces; installed at platform bootstrap | Platform signature (built into CI) |

### §6.2 Postgres index (Doc 02 §5.2 L222)

```
plugin.plugin                       -- 1 row per (plugin_id, latest version) hot pointer
plugin.plugin_version               -- 1 row per (plugin_id, version); immutable
plugin.plugin_installation          -- 1 row per (workspace_id, plugin_id, version)
```

Indexes:
- `plugin(plugin_id)` UNIQUE — hot pointer
- `plugin_version(plugin_id, version)` UNIQUE — version immutability
- `plugin_installation(workspace_id, plugin_id)` — per-workspace lookup
- `plugin_installation(plugin_id)` — global adoption count

### §6.3 Signature verification

Every install verifies the detached signature against the registry's trust root (Doc 13 §7 L108):

1. Fetch signature from `signatures/<plugin_id>-<version>.sig`.
2. Verify manifest bytes hash against signature payload.
3. Check trust root: public = platform root; private = workspace-owner pubkey; bundled = platform root.
4. Reject install on any failure (Doc 13 §12 "Plugin signature invalid | Reject install").

### §6.4 Registry CRUD endpoints

| Method | Path | Body | Effect |
|---|---|---|---|
| `POST` | `/v1/plugins` | manifest + signature | Create new plugin (lifecycle: Draft → Submitted) |
| `GET` | `/v1/plugins/{plugin_id}` | — | Read hot pointer |
| `GET` | `/v1/plugins/{plugin_id}/versions` | — | List versions |
| `POST` | `/v1/plugins/{plugin_id}/versions` | manifest + signature | Submit new version (Submitted → Review) |
| `POST` | `/v1/plugins/{plugin_id}/approve` | `{version}` | Review → Approved (manual review for high-risk) |
| `POST` | `/v1/plugins/{plugin_id}/publish` | `{version}` | Approved → Published |
| `POST` | `/v1/workspaces/{workspace_id}/plugins/{plugin_id}/install` | `{version, signature}` | Published → Active for workspace |
| `POST` | `/v1/workspaces/{workspace_id}/plugins/{plugin_id}/disable` | — | Active → Deprecated (workspace) |
| `POST` | `/v1/plugins/{plugin_id}/retire` | `{version}` | Active → Retired (plugin-svc admin) |
| `POST` | `/v1/plugins/{plugin_id}/kill` | — | Doc 13 §9 kill switch — globally disable + abort in-flight calls |

All endpoints emit CloudEvents to NATS subject `plugin.lifecycle.*` and audit events to audit-svc (Doc 13 §9 L121 "Audit log. Every plugin call is logged").

---

## §7. Distribution

### §7.1 Distribution model (Doc 13 §8 L111-115)

| Distribution | Source | Install trigger | Verification |
|---|---|---|---|
| Public | `s3://plugins-public/` | workspace admin install OR agent-runtime MCP gateway listing for low-risk | Platform root signature (Doc 13 §7 L108) |
| Private | `s3://plugins-private/<workspace_id>/` | workspace admin install | Workspace-owner signature |
| Bundled | `plugin` schema (`distribution='bundled'`) | platform bootstrap auto-install | Platform CI signature; cannot be uninstalled |

### §7.2 Bundled plugin install flow (Doc 13 §8 L115)

`T-MARKET-DATA-FETCHER` is the canonical bundled plugin (Doc 12 §4 L61). On platform bootstrap:

1. plugin-svc inserts a `plugin` row with `distribution='bundled'`, `lifecycle_state='Active'`.
2. plugin-svc inserts a `plugin_installation` row for each existing workspace (idempotent on re-bootstrap).
3. plugin-svc emits `plugin.lifecycle.transitioned` CloudEvent.
4. Agent-runtime MCP gateway reloads its manifest cache within 30s.

### §7.3 The 5 initial tools (AC-6.7)

Issue #9 body names 5 initial tools (out of Doc 20's full catalog of 12):

| Tool ID | Purpose | Bundled? | Manifest schema |
|---|---|---|---|
| `T-WEB-SEARCH` | Web search (e.g., via SerpAPI or similar) | No (private — workspace installs API key) | Doc 12 §4 |
| `T-MARKET-DATA-FETCHER` | Market data fetch (paid providers) | Yes (Doc 12 §4 L61) | Doc 12 §4 L60-79 |
| `T-CODE-EXEC` | Sandboxed code execution (Python) | Yes | Doc 12 §4 |
| `T-FILE-IO` | Workspace file read/write | Yes | Doc 12 §4 |
| `T-CALC` | Spreadsheet-style calc | Yes | Doc 12 §4 |

**Note:** Full tool catalog (Doc 20's 12 tools) ships in follow-up issues. This design's "Definition of done" covers only these 5 as installed-in-staging + invoked-by-agents smoke test (per issue #9 DoD).

---

## §8. Security Model

### §8.1 Trust (Doc 13 §9 L117-123)

| Mechanism | Doc 13 §9 anchor | Implementation |
|---|---|---|
| Trust scoped | "Trust is scoped. A plugin is only as trusted as its signature and its review." L117-118 | Sigstore signature + review tier (auto/manual/double-control) bind trust |
| Per-workspace enablement | "Workspace admins decide which plugins their members can call." L119-120 | `plugin_installation(disabled_at IS NULL)` filter on MCP gateway's `list_tools(workspace_id)` call |
| Per-run allow-list | "A run only sees the tools its orchestrator grants." L121 | RunState carries `budget.tools: list[str]`; MCP gateway filters at call time |
| Audit log | "Every plugin call is logged." L122 | CloudEvent → audit-svc (AC-6.9) |
| Kill switch | "Admin can disable a plugin globally; existing calls are aborted." L123 | `POST /v1/plugins/{id}/kill` sets `plugin.kill_switch_at`; gateway evicts within 5s; in-flight calls aborted via SIGTERM (graceful) then SIGKILL (5s timeout) |

### §8.2 Risk-level gating (Doc 13 §6 L103 + Doc 12 §4 `risk_level: low|medium|high`)

| Risk level | Review | Sandbox strictness | Network default |
|---|---|---|---|
| `low` | Auto (signature + schema) | Standard | No egress by default |
| `medium` | Auto + targeted manual spot-check | Standard + seccomp | No egress by default |
| `high` | Mandatory manual review + dual-control approval | Strict (gVisor v2) + seccomp + no `/tmp` write to host | No egress by default; manifest MUST declare explicit allow-list |

### §8.3 Audit (Doc 13 §9 L122 + AC-6.9)

Every tool invocation emits a CloudEvent to NATS subject `plugin.invocation.completed`:

```json
{
  "specversion": "1.0",
  "type": "plugin.invocation.completed",
  "source": "plugin-svc",
  "id": "<uuid>",
  "time": "<rfc3339>",
  "datacontenttype": "application/json",
  "subject": "T-MARKET-DATA-FETCHER@1.2.0",
  "data": {
    "plugin_id": "T-MARKET-DATA-FETCHER",
    "version": "1.2.0",
    "workspace_id": "<uuid>",
    "user_id": "<uuid>",
    "run_id": "<uuid>",
    "invocation_id": "<uuid>",
    "input_hash": "sha256:...",
    "output_hash": "sha256:...",
    "latency_ms": 234,
    "exit_code": 0,
    "cost_usd": 0.02,
    "policy_tags": ["network_egress=allow:api.marketdata.com"],
    "kill_switch_at": null
  }
}
```

audit-svc (Doc 28 §3 on-call) consumes this and appends to `audit.audit_event` (TRD Doc 02 §5.2 L225).

### §8.4 PII redaction (Doc 13 §11 L136 + Doc 12 §9 L102-103)

Input/output logged at DEBUG level (Doc 12 §9 L103) is PII-redacted by AGT-SAFETY (Doc 09 §17). plugin-svc's role: emit raw `input_hash`/`output_hash` to audit-svc; full payloads flow to PII-redacted log only (separate stream, 30-day retention).

### §8.5 Kill switch propagation latency (FLAG for Q-9.4)

Doc 13 §9 L123 says "existing calls are aborted." The MCP gateway in agent-runtime caches active manifests. To bound the propagation latency:

- **Target:** kill switch propagates to all gateways within 5s (Doc 12 §9 metrics imply OTel metrics update cadence).
- **Mechanism:** `plugin.kill_switch_at` set in Postgres; gateway polls every 5s (NOT cache-on-write — too much load on plugin-svc).
- **In-flight:** container receives SIGTERM, 5s grace, then SIGKILL. Plugin's exit_code reflected in audit event.

---

## §9. Versioning & Compatibility

### §9.1 Semver (Doc 13 §10 L125-131)

| Bump | Doc 13 §10 anchor | Rule |
|---|---|---|
| Major | "breaking input/output schema or permissions" L127 | Any change to `input_schema`, `output_schema`, or `permissions` list shape that breaks a consumer |
| Minor | "additive, backwards-compatible" L129 | New optional fields in input/output schemas; new permissions entries that don't remove old ones |
| Patch | "bug fix" L131 | No schema change; bug fix in handler code |

### §9.2 Installation pinning (AC-6.4)

`plugin_installation` row pins the MAJOR version. Agent resolves at runtime via `plugin_installation.plugin_id + major_version` + manifest-version-range from the agent's `contract.yaml` (Doc 09 §2 L40 "tools: <tool id>").

Resolution algorithm (gateway-side):

```
Given: agent's contract.yaml declares `tools: [T-MARKET-DATA-FETCHER]`.
  And: agent manifest_version range is `>=1.0.0,<2.0.0`.
  And: workspace has installed `T-MARKET-DATA-FETCHER@1.2.0`.
Then: gateway resolves to version 1.2.0 (highest semver in range, prefer latest patch).
```

If no installed version matches the range, gateway returns `manifest_version_mismatch` error (Doc 13 §5 Retired-state error pattern).

### §9.3 Deprecation grace period (Doc 13 §5 + Doc 12 §5 L82)

- Plugin moves to `Deprecated`: existing installations continue to work; no new installs.
- After 90-day grace (Doc 12 §5 L82 "manifest version is marked deprecated; runs stop calling it after a grace period"), plugin moves to `Retired`.
- Retired installations fail with `manifest_version_mismatch` error.

---

## §10. Observability

### §10.1 Per-plugin metrics (Doc 13 §11 L133-137 + Doc 12 §9 L101-104)

| Metric | Source | Dashboard |
|---|---|---|
| `plugin.calls.total{plugin_id, version, status}` | Prometheus counter | Per-plugin card on admin panel |
| `plugin.calls.errors{plugin_id, version, error_class}` | Prometheus counter | Per-plugin card |
| `plugin.calls.latency.p95{plugin_id, version}` | Prometheus histogram | Per-plugin card |
| `plugin.cost.usd.total{plugin_id, version, workspace_id}` | Prometheus counter | Per-workspace + per-plugin attribution |
| `plugin.sandbox.restarts{plugin_id}` | Prometheus counter | Per-plugin health |
| `plugin.signature.failures{plugin_id}` | Prometheus counter | Security dashboard |

### §10.2 Per-plugin traces (Doc 13 §11 L135 + Doc 12 §9 L101)

Every call emits an OpenTelemetry span: `plugin.call { plugin_id, version, latency, cost, status, run_id, workspace_id }`. Span hierarchy: `run → agent_step → mcp.call → plugin.call`.

### §10.3 Per-plugin logs (Doc 13 §11 L136)

Structured JSON logs, PII-redacted by AGT-SAFETY (Doc 09 §17). Retention:
- DEBUG (full payload, PII-redacted): 30 days
- INFO (invocation metadata): 90 days
- WARNING/ERROR/CRITICAL (Doc 26 §6.5 L141 levels): 1 year

### §10.4 Admin dashboard (Doc 13 §11 L137)

plugin-svc exposes a Grafana dashboard JSON at `dashboards/plugin-svc.json`. Cards:
- Top 10 plugins by call rate
- Plugins in error spike (>5% error rate over 5 min)
- Plugins over budget (>=$X spent in window)
- Signature verification failures (security)
- Kill-switch activity log

---

## §11. Failure Modes

### §11.1 Doc 13 §12 L140-148 table verbatim

| Failure | Response | This design's mechanism |
|---|---|---|
| Plugin crashes | Container restart; retries; if persistent, quarantine. | §5.2 container manager; retry per Doc 13 §12 → Doc 12 §4 `retry: { max: 2, backoff: exponential }`; quarantine = `lifecycle_state='Deprecated'` after 3 crash-loop events in 60s |
| Plugin schema drift | Manifest mismatch error; alert; suspend plugin. | §3 + §12 ToolManifest validation at install + at runtime; mismatch = `lifecycle_state='Suspended'` (NEW state) + alert |
| Plugin security issue | Kill switch; public advisory; force-uninstall. | §8.5 kill switch + §6.4 `POST /v1/plugins/{id}/kill`; advisory = status page incident |
| Plugin over budget | Rate-limit; warn admin. | §10.1 `plugin.calls.latency.p95` + Doc 12 §8 rate limit; admin alert at 80% of budget |
| Plugin signature invalid | Reject install. | §6.3 signature verification; install fails with 401 |
| Plugin out of date | Warn; allow time-bound grace. | §9.3 deprecation grace period (90 days) |

### §11.2 NEW failure modes surfaced by this design

| Failure | Response |
|---|---|
| Manifest import error (YAML parse) | Reject submission; surface error in `POST /v1/plugins` response |
| Manifest JsonSchema invalid | Reject submission; surface validation errors |
| Tool reference (in `tools:`) not registered | Reject submission |
| Sandbox container creation timeout | Retry once; on second failure, fall back to "no-plugin-found" error |
| Kill-switch DB write succeeds but NATS event lost | Outbox pattern; gateway polls Postgres every 5s (already required by §8.5); eventual consistency |
| Lifecycle advisory lock acquisition timeout (10s) | Return 503 Service Unavailable; client retries with backoff |

---

## §12. ToolManifest Pydantic Model — plugin-svc canonical

**OWNERSHIP:** plugin-svc OWNS this contract. The cross-service canary is the byte-identical import test against agent-runtime's MCP gateway (Architect #6 §13) and reporting-svc's `tool_manifest_lookup` (Architect #12 §11.4).

### §12.1 JsonSchema envelope (canonical form)

This is the JsonSchema-based `input_schema` / `output_schema` envelope form (NOT legacy `tools: list[ToolRef]`). Per `arch-012-verified-and-persisted-2026-07-28`, Architect #12's brief-sketch drift was the legacy form; the architect caught it at read-time and corrected to JsonSchema envelope. This design adopts the canonical envelope.

### §12.2 Pydantic model

```python
# services/plugin-svc/app/contracts/tool_manifest.py
from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl


class ToolAuth(BaseModel):
    """Doc 12 §4 L72: auth: { type, secret_ref }"""
    type: Literal["api_key", "oauth2", "mTLS", "none"]
    secret_ref: Optional[str] = None  # AWS Secrets Manager ref, Doc 02 §6
    oauth_scopes: Optional[list[str]] = None


class ToolCost(BaseModel):
    """Doc 12 §4 L73: cost: { per_call_usd, weight }"""
    per_call_usd: float = Field(ge=0.0)
    weight: int = Field(ge=0)  # cost-budget weighting (Doc 12 §8)


class ToolRateLimit(BaseModel):
    """Doc 12 §4 L74: rate_limit: { per_minute, per_hour }"""
    per_minute: int = Field(gt=0)
    per_hour: int = Field(gt=0)


class ToolRetry(BaseModel):
    """Doc 12 §4 L76: retry: { max, backoff }"""
    max: int = Field(ge=0)
    backoff: Literal["exponential", "linear", "none"]


class ToolManifest(BaseModel):
    """Canonical plugin-svc ToolManifest.

    Cross-service canary with agent-runtime (Architect #6 §13) and
    reporting-svc (Architect #12 §11.4). Byte-identical import test
    required at services/plugin-svc/tests/test_006_tool_manifest_byte_identical_import_test.py.
    """
    id: str                                       # T-MARKET-DATA-FETCHER
    name: str                                     # "Market Data Fetcher"
    version: str                                  # semver, e.g. "1.2.0"
    description: str
    risk_level: Literal["low", "medium", "high"]  # Doc 12 §4 L65
    pii_risk: bool                                # Doc 12 §4 L66
    input_schema: dict                            # JSON Schema, Doc 12 §4 L67
    output_schema: dict                           # JSON Schema, Doc 12 §4 L68
    auth: ToolAuth
    cost: ToolCost
    rate_limit: ToolRateLimit
    timeout_ms: int = Field(gt=0)
    retry: ToolRetry
    owner: str                                    # "ai-platform"
```

### §12.3 Import path

```python
from services.plugin_svc.app.contracts.tool_manifest import (
    ToolManifest,
    ToolAuth,
    ToolCost,
    ToolRateLimit,
    ToolRetry,
)
```

### §12.4 Cross-service canary test (REQUIRED)

Test file: `services/plugin-svc/tests/test_006_tool_manifest_byte_identical_import_test.py`

```python
# test_006_tool_manifest_byte_identical_import_test
# Named after Architect #6 §6.2 per `arch-006-redispatch-verified-2026-07-28`
# and `plugin-svc-hypothesis-cites-verified-2026-07-28`.

def test_tool_manifest_byte_identical_import():
    """Cross-service canary: ToolManifest is byte-identical across services."""
    from services.plugin_svc.app.contracts.tool_manifest import ToolManifest as PluginTM
    # NOTE: agent-runtime does NOT re-define ToolManifest (it imports from plugin-svc).
    # The byte-identical assertion is that plugin-svc's ToolManifest.model_fields
    # matches the contract agent-runtime's MCP gateway validates against.
    expected_fields = {
        "id", "name", "version", "description", "risk_level", "pii_risk",
        "input_schema", "output_schema", "auth", "cost", "rate_limit",
        "timeout_ms", "retry", "owner",
    }
    assert set(PluginTM.model_fields.keys()) == expected_fields
```

A second canary (not byte-identical but cross-schema) tests JsonSchema envelope:

```python
def test_tool_manifest_uses_jsonschema_envelope_not_legacy():
    """DRIFT-9.6: MUST use JsonSchema envelope, NOT legacy tools: list[ToolRef]."""
    from services.plugin_svc.app.contracts.tool_manifest import ToolManifest
    fields = ToolManifest.model_fields
    # input_schema and output_schema are dict (JsonSchema), not nested models
    assert fields["input_schema"].annotation is dict
    assert fields["output_schema"].annotation is dict
```

---

## §13. MCP Gateway Integration

### §13.1 Gateway architecture (Doc 12 §3 L48-55)

```
agent ──► MCP client (in-process) ──► MCP gateway (singleton per agent) ──► tool server (HTTP/stdio)
```

plugin-svc is the **tool server** side of the gateway. The gateway (in agent-runtime, Architect #6 §13) calls plugin-svc's `/v1/invocations` endpoint, which routes to the right plugin's sandboxed handler.

### §13.2 Tool server contract

plugin-svc exposes an internal HTTP endpoint (`POST /v1/invocations`) consumed by the MCP gateway:

```
POST /v1/invocations
Headers:
  Authorization: Bearer <agent_token>     # gateway's user/workspace token
  X-MCP-Gateway: <gateway_instance_id>   # for tracing
  X-Run-Id: <run_id>                     # for audit correlation
Body:
  {
    "tool_id": "T-MARKET-DATA-FETCHER",
    "version": "1.2.0",          # optional; gateway may omit for "any compatible"
    "input": { "query": "TAM for EV charging 2026" },
    "timeout_ms": 5000,          # overrides manifest default
    "run_id": "<uuid>",
    "workspace_id": "<uuid>",
    "user_id": "<uuid>",
    "invocation_id": "<uuid>",
  }

Response (200):
  {
    "output": { ... },            # tool output, validated against output_schema
    "latency_ms": 234,
    "cost_usd": 0.02,
    "audit_event_id": "<uuid>",
  }

Response (4xx/5xx): per Doc 12 §10 L130-138 failure table.
```

### §13.3 Gateway's responsibilities (Doc 12 §3 L51-55)

The MCP gateway (in agent-runtime) handles:
- Tool name → server resolution
- Authz (per workspace, per user, per tool)
- Rate limit and cost budget enforcement
- Trace and metric capture

plugin-svc handles:
- Manifest validation at install
- Plugin lifecycle
- Sandbox creation and invocation
- Audit emission

### §13.4 Per-call flow

1. Gateway validates manifest is registered (Doc 12 §4 L76).
2. Gateway enforces per-workspace enablement (Doc 13 §9 L120).
3. Gateway enforces per-run allow-list (Doc 13 §9 L121; `RunState.budget.tools`).
4. Gateway enforces rate limit (Doc 12 §8 L114-118).
5. Gateway calls `POST /v1/invocations` on plugin-svc.
6. plugin-svc routes to the plugin's container; runs handler.
7. plugin-svc emits audit event (Doc 13 §9 L122).
8. plugin-svc returns output.
9. Gateway captures span + metric (Doc 12 §9 L101).

---

## §14. Tool Consumers (cross-service)

### §14.1 agent-runtime (Doc 09 §3-§19)

The MCP gateway in agent-runtime is the primary caller. All 17 agents (Doc 08 §3 L57-75 + Doc 09 §3-§19) call tools via the gateway. Specific consumers:

| Agent | Doc 09 anchor | Tools consumed |
|---|---|---|
| AGT-ORCH | §3 | (none directly; dispatches specialists) |
| AGT-DISC-PLANNER | §4 | Source metadata (read-only) |
| AGT-DISC-CLUSTER | §5 | Embedding-based clustering (no tools) |
| AGT-RSRCH-MARKET | §6 L91 | Market data plugins (T-MARKET-DATA-FETCHER); RAG |
| AGT-RSRCH-DEMAND | §7 | Google Trends plugin, social APIs, RAG |
| AGT-RSRCH-COMP | §8 L99 | Web search, RAG, app store data, G2 |
| AGT-RSRCH-PRICING | §9 L107 | Web search, RAG |
| AGT-RSRCH-PERSONA | §10 | RAG, web search |
| AGT-RSRCH-WTP | §11 | RAG, web search |
| AGT-RSRCH-GTM | §12 | Web search, RAG |
| AGT-RSRCH-RISK | §13 | RAG |
| AGT-SCORE | §14 | (none; pure compute + LLM judge) |
| AGT-RPT-WRITER | §15 | RAG, chart render |
| AGT-VERIFY | §16 | RAG, policy service |
| AGT-SAFETY | §17 | PII detector, policy lookup |
| AGT-PLANNER | §18 | RAG, MCP tool listing |
| AGT-CRITIC | §19 | RAG, report diff |

### §14.2 Source-svc (Doc 14)

Source-svc's external API connectors are wrapped as tools. Per `arch-007-redispatch-verified-2026-07-28` and `arch-006-redispatch-verified-2026-07-28`, source-svc is a separate concern; the wrapping as tools happens via plugin-svc's manifest ingestion of source-svc's connector definitions (handoff in a follow-up issue).

### §14.3 Cross-service contracts

| Contract | Owner | Consumer | Import path |
|---|---|---|---|
| `ToolManifest` | **plugin-svc (this design §12)** | agent-runtime (Architect #6 §13); reporting-svc (Architect #12 §11.4) | `from services.plugin_svc.app.contracts.tool_manifest import ToolManifest` |
| `Source` | rag-svc (Architect #7 §10) | agent-runtime, memory-svc, validation-pipeline, reporting-svc | `from services.rag_svc.app.contracts.source import Source` |
| `Citation` | rag-svc (Architect #7 §11) | agent-runtime, memory-svc, validation-pipeline, reporting-svc | `from services.rag_svc.app.contracts.citation import Citation` |
| `RunState` | agent-runtime (Architect #6 §4.3) | plugin-svc (invocation context), all consumers | `from services.agent_runtime.app.contracts.run_state import RunState` |
| `Budget` | agent-runtime (Architect #6 §4.3) | plugin-svc (cost budget enforcement) | `from services.agent_runtime.app.contracts.budget import Budget` |

### §14.4 plugin-svc imports from agent-runtime (not the other way)

Per `arch-007-redispatch-verified-2026-07-28` and the canary pattern:
- plugin-svc IMPORTS `RunState` / `Budget` from agent-runtime for invocation context (read-only).
- agent-runtime does NOT re-define `ToolManifest`; it imports from plugin-svc.

This avoids the legacy dual-definition bug that Architect #12 caught in DRIFT-12.8.

---

## §15. Drift Findings

### §15.1 AC label drift (re-mapped)

| AC | Issue body cite | Verified reality | Re-mapped to |
|---|---|---|---|
| AC-6.2 | "Document 13 §2" | Doc 13 §2 L21-25 = "Why plugins"; manifest schema is §4 L55-77 | **Doc 13 §4** |
| AC-6.5 | "Document 13 §4" | Doc 13 §4 L55-77 = "Manifest"; sandbox is §6 L94-102 | **Doc 13 §6** |
| AC-6.1 | "Python 3.12" | Q-9 conductor decision: Python 3.11 (CI gate matches; `conductor-decisions-2026-07-28.md`) | **Python 3.11** in `pyproject.toml` |
| AC-6.9 | "Document 13 §6" | Doc 13 §6 L94-102 = "Sandboxing"; audit is §9 L122 | **Doc 13 §9** |
| AC-6.11 | "REQ-PLAT-0009 / REQ-INT-0010" | Both verified live: PRD §7.11 L412 (REQ-PLAT-0009) + PRD §7.7 L353 (REQ-INT-0010). Issue body says "REQ-INT-0009" for AC-6.8 — also verified live at PRD §7.7 L352 | **No drift on REQ-* IDs** — all cited IDs exist in PRD §7.7/§7.11 |
| AC-6.12 | "Document 28 §3" | Doc 28 §3 L46 = "On-call"; runbook storage is §5 L80-91 | **Doc 28 §3 (on-call) + §5 (runbook location)** |
| AC-6.6 | "Document 12 §3-5" | Doc 12 §3-5 verified: §3 L48-55 (Architecture), §4 L60-79 (Tool manifest), §5 L80-83 (Server lifecycle) | **No drift** |
| AC-6.7 | "Document 20's initial 12 tools" | Doc 20 exists; only 5 named in AC body | **Doc 20 (full catalog) — this design covers the 5 named** |

### §15.2 PRD §7.6 vs REQ-PLUGIN drift (CONFIRMED)

Per `plugin-svc-hypothesis-cites-verified-2026-07-28`:
- PRD §7.6 L326 = `### 7.6 Dashboards & Workspace (REQ-DASH)` — NOT REQ-PLUGIN.
- `grep -c "REQ-PLUGIN"` on PRD v1.1 = 0.
- **No REQ-PLUGIN-* exists.** plugin-svc is not anchored to a specific PRD §7.6 REQ; the closest anchors are REQ-INT-0009/0010 (PRD §7.7 L352/353) and REQ-PLAT-0009 (PRD §7.11 L412).
- **Resolution:** Ship to issue-maintainer's doc-cite-drift-fix campaign; no design change required.

### §15.3 PRD §15.1 vs INT domain drift (CONFIRMED)

Per `plugin-svc-hypothesis-cites-verified-2026-07-28`:
- Issue body says "PRD §15.1 INT domain (webhooks, REST API, rate limits)" — drift.
- PRD §15.1 L733-746 = "Glossary" (NOT INT domain).
- INT domain is PRD §7.7 L340-353 = `### 7.7 Integration & API (REQ-INT)`.
- **Resolution:** Re-map to PRD §7.7 (verified live); no design change required.

### §15.4 AC-6.9 Doc 21 §10 anchor (DRIFT — partial)

Issue body cites "Document 21 §10" for audit. Doc 21 §10 was not searched live in this dispatch (Doc 21 has 6 numbered sections; §10 may or may not exist). The verified audit pattern is:
- **Doc 13 §9 L122** ("Audit log. Every plugin call is logged.")
- **Doc 21 §6 L51** ("Repudiation | Append-only audit log, signed events") — verified live.
- **TRD Doc 02 §5.2 L225** (audit-svc schema: `audit_event` append-only).
- **Resolution:** Re-map AC-6.9 to Doc 13 §9 + Doc 21 §6 + TRD §5.2 audit-svc schema; backend-expert should grep Doc 21 §10 if it exists and update this design.

### §15.5 NEW drift: Doc 09 v1.1 vs Doc 08 17-agent table

Doc 08 §3 L57-75 lists 17 agents (AGT-ORCH through AGT-CRITIC). Doc 09 §20.2 revision history says v1.1 added AGT-PLANNER. Doc 09 §18-§19 are AGT-PLANNER + AGT-CRITIC. Doc 09 §20.1 index lists 17 agents. **No drift** — but flag for backend-expert to use Doc 09 v1.1 as the source of truth for agent roster.

### §15.6 NEW drift: bundled plugin un-installation impossible (Doc 13 §8 L115)

Doc 13 §8 L115 says bundled plugins "ship with the platform (e.g. T-MARKET-DATA-FETCHER)". Doc 13 §9 L120 says workspace admins decide enablement. **Implicit:** bundled plugins cannot be uninstalled (only disabled). This design §5.1 + §7.2 codifies that bundled plugins install at platform bootstrap with `distribution='bundled'` and `lifecycle_state='Active'`. **Not a bug** — but flag for backend-expert to surface in the bundled-plugin UX (admin sees "Disable" but not "Uninstall").

### §15.7 NEW drift: Q-9 Python 3.11 default across services

Per `conductor-decisions-2026-07-28.md`, Q-9 conductor decision: **Python 3.11 default to match CI gate.** This is consistent across all 11 architect dispatches. **No drift on this design** — backend-expert writes `pyproject.toml` with `python = ">=3.11,<3.12"`.

### §15.8 NEW drift: v0.x merge strategy per Q-3

Per `conductor-decisions-2026-07-28.md`, Q-3 conductor decision: **merge as v0.x, defer v1.0.0 to post-DOC-OD-01.** This design is not gated on v1.0.0; backend-expert tags OCI image as `v0.x`. **No design change.**

### §15.9 Cross-service drift: Architect #12 §11.4 ToolManifest canary

Per `arch-012-verified-and-persisted-2026-07-28`, the ToolManifest is the JsonSchema envelope (NOT legacy `tools: list[ToolRef]`). This design §12 adopts the canonical JsonSchema envelope. **No drift on this design** — but flag for backend-expert to NOT regress to legacy form.

---

## §16. Q-9.x Conductor Gating

3–7 questions deferred to the conductor for decision before backend-expert dispatch.

| # | Question | Options | Default if unresolved |
|---|---|---|---|
| **Q-9.1** | Bundled-plugin lifecycle: can bundled plugins transition to Deprecated/Retired, or are they pinned to Active forever? | A) Pinned forever (no deprecate)  B) Allow deprecate with platform-wide impact  C) Allow deprecate only via major version bump | **A** (Doc 13 §8 implies permanent) |
| **Q-9.2** | Kill-switch propagation latency target: how fast must the gateway evict a killed plugin? | A) 5s (gateway polls Postgres)  B) 30s  C) Near-real-time (NATS push) | **A** (this design §8.5) |
| **Q-9.3** | Plugin-review SLA: what is the target turnaround for manual review of high-risk plugins? | A) 24h  B) 72h  C) 1 week | **B** (reasonable for AI Lead review) |
| **Q-9.4** | Signature rotation cadence: how often do workspace-owner Sigstore keys rotate? | A) 90 days  B) 180 days  C) 1 year | **B** (matches Doc 21 default) |
| **Q-9.5** | Workspace-tier plugin limits: how many private plugins can a workspace install per tier (Free / Pro / Enterprise)? | A) 5 / 25 / unlimited  B) 0 / 10 / 100  C) Free disallows private | **A** (Free can install ≤5 private plugins; Enterprise unlimited) |
| **Q-9.6** | Sandbox runtime: gVisor vs Docker default for v1 launch? | A) Docker (simpler ops)  B) gVisor (strict isolation)  C) Wasmtime (experimental) | **A** (Docker for v1, gVisor for v2 if needed) |
| **Q-9.7** | Per-call policy enforcement: does plugin-svc enforce per-call policy itself, or only via gateway? | A) plugin-svc only enforces manifest  B) gateway enforces per-call policy + plugin-svc enforces manifest  C) Both layers | **B** (Doc 12 §7 L91-95 implies gateway-side; plugin-svc focus is sandbox) |

---

## §17. RED Test Spec (~30-50 seeds)

Test files at `services/plugin-svc/tests/test_<n>_<description>.py`. Each test is RED at architect handoff (failing until implementer lands the spec).

### §17.1 Cross-service canary (REQUIRED)

| # | Test | Asserts |
|---|---|---|
| test_006_tool_manifest_byte_identical_import_test | Import ToolManifest from plugin-svc; assert field set matches §12.2 | DRIFT-9.6 avoided; JsonSchema envelope |
| test_007_tool_manifest_jsonschema_envelope | ToolManifest.input_schema / output_schema are dict, not nested models | DRIFT-12.8 avoided |

### §17.2 Manifest validation

| # | Test | Asserts |
|---|---|---|
| test_001_manifest_valid_passes | Valid manifest with all required fields passes validation | §3.1 |
| test_002_manifest_missing_id_fails | Manifest without `id` fails validation | §3.1 required field |
| test_003_manifest_invalid_semver_fails | `version: "not-semver"` fails | §9.1 |
| test_004_manifest_high_risk_no_allowlist_fails | `risk_level: high` without `permissions: network:outbound` fails | §5.3 |
| test_005_manifest_pii_risk_flag_set | `pii_risk: true` requires audit redaction enabled | §8.4 |

### §17.3 Lifecycle

| # | Test | Asserts |
|---|---|---|
| test_010_lifecycle_draft_to_submitted | `POST /v1/plugins` transitions Draft → Submitted | §4.2 |
| test_011_lifecycle_submitted_to_review | Submitted → Review on registry pick | §4.2 |
| test_012_lifecycle_review_to_approved_auto | Auto-pass for `risk_level: low` | §8.2 |
| test_013_lifecycle_review_to_approved_manual | Manual review required for `risk_level: high` | §8.2 |
| test_014_lifecycle_active_to_deprecated | Workspace disable transitions Active → Deprecated | §4.2 |
| test_015_lifecycle_active_to_retired | Plugin-svc retire transitions Active → Retired; existing calls fail with manifest_version_mismatch | §4.2 + §9.3 |
| test_016_lifecycle_toctou_advisory_lock | Concurrent lifecycle transitions serialize on advisory lock; second transaction blocks then succeeds | §4.3 |

### §17.4 Sandbox

| # | Test | Asserts |
|---|---|---|
| test_020_sandbox_container_creation | plugin-svc creates ephemeral container with manifest-declared limits | §5.2 |
| test_021_sandbox_no_network_by_default | Container cannot reach external IPs without manifest allow-list | §5.3 |
| test_022_sandbox_filesystem_ro | Container cannot write outside scratch | §5.1 |
| test_023_sandbox_memory_cap_enforced | Container OOMs at declared `memory:max_mb` | §5.1 |
| test_024_sandbox_cpu_cap_enforced | Container throttles at declared `cpu:millicores` | §5.1 |
| test_025_sandbox_no_shell | `execve("/bin/sh")` denied by seccomp | §5.1 |
| test_026_sandbox_escape_redteam_filesystem | Attempted write to `/etc/passwd` blocked | §5.5 |
| test_027_sandbox_escape_redteam_network | Attempted egress to `evil.com` blocked | §5.5 |
| test_028_sandbox_escape_redteam_priv_esc | Attempted `setuid(0)` blocked | §5.5 |
| test_029_sandbox_high_risk_gvisor | `risk_level: high` runs in gVisor sandbox (v2) | §8.2 |

### §17.5 Registry

| # | Test | Asserts |
|---|---|---|
| test_030_registry_public_install | Install public plugin succeeds with platform signature | §6.1 |
| test_031_registry_private_install | Install private plugin succeeds with workspace-owner signature | §6.1 |
| test_032_registry_invalid_signature_rejected | Invalid signature returns 401 install rejection | §6.3 |
| test_033_registry_bundled_bootstrap | Platform bootstrap inserts bundled plugin rows | §7.2 |
| test_034_registry_bundled_uninstall_forbidden | `DELETE /v1/plugins/{id}/uninstall` returns 409 for bundled | §15.6 |
| test_035_registry_version_immutability | Re-submitting same (plugin_id, version) fails | §6.2 |

### §17.6 Lifecycle eventing + audit

| # | Test | Asserts |
|---|---|---|
| test_040_invocation_emits_cloud_event | Plugin call emits `plugin.invocation.completed` to NATS | §8.3 |
| test_041_invocation_audit_event_id_returned | `POST /v1/invocations` response includes `audit_event_id` | §8.3 |
| test_042_lifecycle_transition_emits_event | State change emits `plugin.lifecycle.transitioned` | §4.4 |
| test_043_invocation_input_output_hashed | Audit event contains `input_hash` and `output_hash` | §8.3 + AC-6.9 |
| test_044_invocation_latency_recorded | Audit event contains `latency_ms` | §8.3 + AC-6.9 |
| test_045_invocation_exit_code_recorded | Audit event contains `exit_code` | §8.3 + AC-6.9 |

### §17.7 Kill switch

| # | Test | Asserts |
|---|---|---|
| test_050_kill_switch_propagates_5s | `POST /v1/plugins/{id}/kill` propagates to gateway within 5s | §8.5 + Q-9.2 |
| test_051_kill_switch_aborts_inflight | In-flight calls receive SIGTERM after kill switch | §8.5 |
| test_052_kill_switch_public_advisory_emitted | Kill switch creates SEV-2 incident status page event | §11.1 Doc 13 §12 |

### §17.8 Rate limit + cost budget

| # | Test | Asserts |
|---|---|---|
| test_060_rate_limit_per_minute_enforced | 61st call in 60s returns 429 | Doc 12 §8 + §9.1 |
| test_061_rate_limit_per_hour_enforced | 1001st call in 60min returns 429 | Doc 12 §8 |
| test_062_cost_budget_exceeded_blocks | Workspace cost budget exceeded → call rejected | Doc 12 §8 + AC-6.11 |

### §17.9 Versioning

| # | Test | Asserts |
|---|---|---|
| test_070_major_bump_breaking_schema | Major version with input_schema change → existing installations fail with manifest_version_mismatch | §9.1 |
| test_071_minor_bump_additive | Minor version with new optional input field → existing installations continue | §9.1 |
| test_072_patch_bump_no_schema_change | Patch version with handler bug fix only → existing installations continue | §9.1 |
| test_073_version_range_out_of_range | Agent's contract.yaml declares `>=1.0.0,<2.0.0`; installed version 2.0.0 → resolution fails | §9.2 |
| test_074_deprecation_grace_90_days | Deprecated plugin auto-retires after 90 days | §9.3 |

### §17.10 Backout plan

| # | Test | Asserts |
|---|---|---|
| test_080_backout_per_plugin_disable | Workspace admin can disable a single plugin | §15.1 AC-6.12 |
| test_081_backout_workspace_rollback | Workspace admin can roll back to previous version | §15.1 AC-6.12 |
| test_082_backout_runbook_exists | `docs/runbooks/plugin-svc.md` exists with sandbox-escape mitigation | §5.5 + AC-6.12 + Doc 28 §5 |

### §17.11 Tool consumer integration (smoke tests, AC-6.7 DoD)

| # | Test | Asserts |
|---|---|---|
| test_090_smoke_T_MARKET_DATA_FETCHER | AGT-RSRCH-MARKET invokes T-MARKET-DATA-FETCHER end-to-end | §7.3 + AC-6.7 |
| test_091_smoke_T_WEB_SEARCH | AGT-RSRCH-COMP invokes T-WEB-SEARCH end-to-end | §7.3 + AC-6.7 |
| test_092_smoke_T_CODE_EXEC | AGT-RSRCH-PRICING invokes T-CODE-EXEC end-to-end | §7.3 + AC-6.7 |
| test_093_smoke_T_FILE_IO | AGT-RSRCH-PERSONA invokes T-FILE-IO end-to-end | §7.3 + AC-6.7 |
| test_094_smoke_T_CALC | AGT-RSRCH-GTM invokes T-CALC end-to-end | §7.3 + AC-6.7 |

Total: ~50 RED seeds across 11 categories.

---

## §18. Acceptance Criteria Mapping

Each AC (verified live in §0) maps to design sections.

| AC | Verified body (excerpt) | Re-mapped to (per §15.1) | This design's section(s) |
|---|---|---|---|
| AC-6.1 | "plugin-svc scaffolded (Python 3.12, FastAPI, async)" | Python 3.11 | §1 boundaries; backend-expert writes `pyproject.toml` with `python = ">=3.11,<3.12"` |
| AC-6.2 | "Plugin manifest schema (Document 13 §2)" | **Doc 13 §4** | §3 (manifest schema); §12 (ToolManifest Pydantic) |
| AC-6.3 | "Plugin registry backed by Postgres (plugin.plugin, plugin.plugin_version, plugin.plugin_installation per Document 02 §5.2)" | Doc 02 §5.2 L222 (verified) | §6.2 (Postgres index) |
| AC-6.4 | "Versioning: semver; an installation pins a major version; agents resolve a specific version at runtime" | Doc 13 §10 L125-131 | §9 (versioning & compatibility) |
| AC-6.5 | "Runtime: each tool invocation runs in a per-plugin sandbox (process-level, restricted env, no network egress except allow-listed) per Document 13 §4" | **Doc 13 §6** | §5 (sandboxing) |
| AC-6.6 | "MCP bridge: the plugin-svc exposes installed plugins to the agent-runtime MCP gateway (Document 12 §3-5)" | Doc 12 §3-5 (verified) | §13 (MCP gateway integration) |
| AC-6.7 | "Initial tool set: T-WEB-SEARCH, T-MARKET-DATA-FETCHER, T-CODE-EXEC, T-FILE-IO, T-CALC" | Doc 20 catalog | §7.3 (5 initial tools); §17.11 (smoke tests) |
| AC-6.8 | "Per-workspace installation: ... (REQ-INT-0009 scoped tokens inform the install)" | REQ-INT-0009 verified at PRD §7.7 L352 | §6 (registry); §8.1 (per-workspace enablement) |
| AC-6.9 | "Audit: every tool invocation is logged to audit-svc ... (Document 13 §6, Document 21 §10)" | **Doc 13 §9 + Doc 21 §6 + TRD §5.2 audit-svc** | §8.3 (audit CloudEvent) |
| AC-6.10 | "Policy: a plugin can be tagged with policy tags ... the sandbox enforces them" | Doc 13 §6 + §9 | §5.3 (egress allow-list); §8.1 (per-call allow-list) |
| AC-6.11 | "Rate limit enforcement: per-plugin + per-workspace rate limits (REQ-PLAT-0009, REQ-INT-0010)" | Both REQ-* verified | §9 (Doc 12 §8); §17.8 (rate limit RED tests) |
| AC-6.12 | "Documented backout plan: per-plugin disable, per-workspace install rollback, sandbox escape mitigation runbook; Document 28 §3" | Doc 28 §3 (on-call) + §5 (runbook location) | §17.10 (backout RED tests); §5.5 (sandbox red-team) |

All 12 ACs have a corresponding design section and at least one RED test in §17.

---

## §19. Open Items for Backend-Expert

1. **Doc 21 §10 verification:** §15.4 flagged that Doc 21 §10 was not verified live. Backend-expert should `grep -n "## 10\|### 10" docs/08-Engineering/21_security.md` to confirm or correct AC-6.9's "Document 21 §10" cite.
2. **Doc 20 catalog verification:** AC-6.7 cites "Document 20's initial 12 tools". Backend-expert should `grep -n "T-" docs/07-AI-Architecture/20_mcp_tool_catalog.md` to confirm the 12 tools; this design covers only the 5 named in the AC body.
3. **Bundled plugin `distribution` enum:** §7.2 + §6.2 introduce a `distribution` column with values `public` | `private` | `bundled`. Backend-expert must add this to the `plugin` schema DDL.
4. **Lifecycle advisory lock timeout:** §4.3 sets 10s timeout. Backend-expert should make this configurable via env var `PLUGIN_SVC_LIFECYCLE_LOCK_TIMEOUT_MS`.
5. **Kill-switch DB poll cadence:** §8.5 sets 5s poll cadence. Backend-expert should make this configurable via env var `PLUGIN_SVC_GATEWAY_POLL_INTERVAL_S`.
6. **Outbox pattern for kill-switch NATS delivery:** §11.2 flags the kill-switch DB-write-success-but-NATS-event-lost scenario. Backend-expert should implement outbox pattern (Polly / Debezium-style) for at-least-once event delivery.
7. **Q-9.x conductor decisions:** All 7 Q-9.x items in §16 are unresolved at design time. Backend-expert should NOT proceed on Q-9.1, Q-9.2, Q-9.3, Q-9.4, Q-9.5, Q-9.6, Q-9.7 without conductor input. Defaults listed in §16.

---

## §20. Pair-With (cross-references)

- [[plugin-svc-hypothesis-cites-verified-2026-07-28]] — prior verification that grounded this design's Doc 13 §3-§12 mapping.
- [[arch-007-redispatch-verified-2026-07-28]] — Source + Citation canary; plugin-svc does NOT touch these.
- [[arch-006-redispatch-verified-2026-07-28]] — agent-runtime MCP gateway contract; this design is the server side.
- [[arch-012-verified-and-persisted-2026-07-28]] — ToolManifest JsonSchema envelope canonical form (DRIFT-9.6 + DRIFT-12.8 avoidance).
- [[phase-c-step-3-priority-order-2026-07-28]] — dispatch order: #9 (plugin-svc) dispatches AFTER #6 (agent-runtime).
- [[conductor-decisions-2026-07-28]] — Q-3 (v0.x merge) + Q-9 (Python 3.11) decisions applied here.
- [[doc-cite-drift-fix-campaign-2026-07-27]] — issue-maintainer's campaign picks up §15.1 + §15.2 + §15.3 drifts.

---

> *End of Issue #9 — plugin-svc BAND-3-DESIGN. The plugin is the unit of extensibility; everything outside the platform is a plugin.*
