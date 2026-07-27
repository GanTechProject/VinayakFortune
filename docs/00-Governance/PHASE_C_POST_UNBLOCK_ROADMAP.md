---
title: Phase C Post-Unblock Roadmap
version: v1.2
date: 2026-07-21
author: VentureMiner AI Orchestrator
status: Approved
---

# Phase C Post-Unblock Roadmap

> **Document 00.B — Operational roadmap for the conductor and the orchestrator.**
> This document captures the post-recovery state of the `GanTechProject/VinayakFortune` repo as of 2026-07-21 and prescribes the path forward from the current operational plateau to Phase C product work. The single hard gate is the OAuth-scope-block unblock (a human-only action); everything else follows from that.

## Table of Contents

1. Current state (as of 2026-07-21)
2. The unblock (the only hard gate)
3. The post-unblock sequence
4. Operational hygiene (Band-1, runnable today)
5. Cycle-artifacts convention (paused, not deleted)
6. Decision ledger
7. What the conductor needs to do
8. What the orchestrator will do after the unblock
9. Cross-references
10. Revision history
11. Open decisions

## 1. Current state (as of 2026-07-21)

| Field | Value | Source |
|---|---|---|
| Main HEAD | `6123418` | `git log --oneline -1 origin/main` |
| Open PRs | 0 | `gh pr list --state open` |
| Open issues | 17 | `gh issue list --state open` |
| Branch protection | canonical state (1 approval, `contexts: []`) | `gh api repos/.../branches/main/protection` |
| Untracked items (paused) | 2 (`merge_pr41_audit.json`, `scripts/merge_pr41_cycle.sh`) | per the cycle convention pause (issue #38) |
| CI workflows on main | none | OAuth-scope-block gates the `.github/workflows/` push |
| Auth-svc scaffolding | `services/auth-svc/` on main (Docker + pyproject, PR #33); DESIGN + RED tests on `wip/auth-svc-session-manager` (c9a7470) | git log |

**The project is operationally stable.** Six cycles (PRs #33, #34, #35, #37, #39, #41) have run cleanly with zero hacks. The True-vs-true JSON-validity bug is fixed across all active cycle scripts. The audit chain is complete from PR #18 through PR #41.

**No new operational work is needed.** The next action is the unblock.

## 2. The unblock (the only hard gate)

**The unblock is a 5-minute human-only action** that requires the GitHub web UI. The CLI cannot perform it because the GitHub OAuth scope `workflow` is not granted to the bot token (see `oauth-workflow-scope-block` memory).

**Critical fact about the workflow files.** The two workflow files (`.github/workflows/ci-hello-world.yml` and `.github/workflows/docs-lint.yml`) live on a local-only branch `ci/initial-workflows` (commit `3c8e5f9`). The branch was **never pushed to `origin`**: pushing it would have triggered GitHub's `workflow`-scope check, and the scope is exactly what's blocked. As a result:

- The `github.com/GanTechProject/VinayakFortune/tree/ci/initial-workflows` URL returns **404** (the branch doesn't exist on the remote).
- The "open a PR from `ci/initial-workflows`" flow that the original §2 described is **not viable** — there's no remote branch to open a PR from.

The actual viable unblock flow is therefore: **the conductor pastes the workflow file contents directly into `main` via the GitHub web UI**, bypassing the `ci/initial-workflows` branch entirely. The branch is just a *local holding pen* for the file content; the unblock does not depend on it being on the remote.

**Steps:**

1. **Retrieve the file contents** from the local `ci/initial-workflows` ref. In the local clone, run:
   ```bash
   git show ci/initial-workflows -- .github/workflows/ci-hello-world.yml
   git show ci/initial-workflows -- .github/workflows/docs-lint.yml
   ```
   (Use the `--` form; the colon-form `git show <ref>:<path>` fails on Windows Git Bash.) If the conductor has no local clone, the orchestrator pastes the file contents in chat (see `RUNBOOK_after_paste.md` step 4 for the full retrieval recipe).
2. **Open the GitHub web UI:** <https://github.com/GanTechProject/VinayakFortune>
3. **Create the first workflow file on `main`.** Click "Add file" → "Create new file" on the `main` branch. Type the path `.github/workflows/ci-hello-world.yml`. Paste the content retrieved in step 1. Commit directly to `main` with the message `ci: add ci-hello-world workflow (test + lint + build + smoke)`.
4. **Create the second workflow file on `main`.** Repeat for `.github/workflows/docs-lint.yml`. Commit with the message `ci: add docs-lint workflow (front-matter + revision-history + orphan check)`.
5. **Push a third commit to trigger an actual workflow run.** GitHub Actions does not run on the commit that adds a workflow file itself (the workflow definition did not exist when that commit was pushed). The simplest trigger is a no-op commit on a `chore/trigger-workflow-run` branch — open a PR and the orchestrator runs the Option 3 cycle to merge it. Alternatively, the conductor can do a no-op commit via the GitHub web UI: "Edit file" on any tracked file, add a space, commit to a branch, PR, and the orchestrator merges. The Option 3 cycle is for *this trigger PR*, not for the workflow files.
6. **The workflows run on the trigger commit** (or the web-UI no-op commit). GitHub registers the context names `ci-hello-world` and `docs-lint`. This takes 2–5 minutes.
7. **The orchestrator runs the post-paste cycle:**
   ```bash
   bash scripts/post_paste_cycle.sh
   ```
   This step **requires the context names to be registered** (i.e. step 6 must have completed). If the script reports "no checks observed," the trigger commit hasn't propagated yet — wait 30s and re-run.

The full operational detail (including the failure-mode table) is in `RUNBOOK_after_paste.md` (on main) and the `oauth-workflow-scope-block` memory. The runbook is the **executable** unblock instructions; this section is the **strategic narrative** that explains why each step exists.

**What the post-paste cycle does (in `post_paste_cycle.sh`):**
- Reads the registered context names from the live API (the names of the checks that have actually run)
- Updates `docs/00-Governance/branch_protection.json` to list those names in `required_status_checks.contexts`
- PUTs the updated rule back to the live API
- Verifies the PUT (live API matches the canonical file)
- (If a trigger PR is open) runs the Option 3 cycle on it

The end state: the live branch-protection rule has `required_status_checks.contexts: ["ci-hello-world", "docs-lint"]`, and the next PR opened to `main` will see both as required status checks.

## 3. The post-unblock sequence

Once the orchestrator reports "post-paste cycle complete," the project enters Phase C. The sequence:

### 3.1 Update the canonical branch protection
- Add `["ci-hello-world", "docs-lint"]` to the `required_status_checks.contexts` array in `docs/00-Governance/branch_protection.json`
- PUT the updated body to GitHub via `gh api -X PUT ... --input branch_protection.json`
- Verify: `gh api repos/.../branches/main/protection` shows the new contexts

### 3.2 First implementer dispatch (Band-3)
- **Issue #5** is the auth-svc + workspace-svc epic; its first concrete slice is **`InMemorySessionManager`** on the `wip/auth-svc-session-manager` branch
- The implementer reads `IMPLEMENTATION_GUIDE.md` (on the WIP branch) and turns the 25 RED tests in `app/test_session_manager.py` GREEN
- Per the IMPLEMENTATION_GUIDE's pre-flight gate: the implementer MUST verify `required_status_checks.contexts` is non-empty before opening a PR. After step 3.1 above, this is satisfied.
- Dispatch model: architect FIRST (design + RED test spec, but the WIP branch already has the design), then IN PARALLEL backend-expert (the implementation) and qa-engineer (the GREEN validation). Frontend-expert not needed for this slice.

### 3.3 Subsequent service implementations
After auth-svc lands, the next Band-3 candidates (in suggested order):

| Issue | Service | Why this order |
|---|---|---|
| #8 | memory-svc | Sessions are a memory tier; this generalizes the session pattern |
| #5 (cont) | workspace-svc | Builds on auth-svc for tenant scoping |
| #7 | rag-svc | RAG is the primary data-flow into the AI plane |
| #11 | validation-pipeline | Uses RAG; high-value feature |
| #13 | scoring-svc | Uses validation; rubric is a clear contract |
| #12 | reporting-svc | Uses scoring; lower complexity |
| #10 | source-svc | External data; lower coupling |
| #9 | plugin-svc | Sandbox complexity; defer until core works |
| #14 | billing-svc | External Stripe integration; separate concern |
| #15 | opportunity-svc | Uses most of the above; near the end |
| #16 | web dashboard | Frontend; needs backend services stable first |
| #17 | integration-svc | Last; depends on everything else |
| #6 | agent-runtime | Epic; cut into LangGraph-orchestrator and MCP-gateway slices |

The ordering is a **suggestion**, not a contract. The implementer may reorder based on emerging dependencies.

## 4. Operational hygiene (Band-1, runnable today)

These are the Band-1 issues that don't require the unblock and that the orchestrator can dispatch on demand:

| Issue | Title | Gating |
|---|---|---|
| #30 | `chore: add CODEOWNERS to auto-assign reviewers` | Awaiting reviewer identity from conductor (or orchestrator proposes defaults) |
| #26 | `chore: rm ChatHistory.txt from main (corrective to bootstrap PR #18)` | Gated on conductor sign-off as a destructive change |
| #36 | `chore: fix True-vs-true JSON bug in merge_pr{33,34}_cycle.sh heredoc` | ✅ Done in PR #40 |
| #38 | `chore: evaluate whether cycle-artifacts follow-up PRs should continue post-unblock` | Awaiting conductor decision; orchestrator has paused the convention per its own decision |

The `empty-cohort-dont-fabricate` memory is the discipline: when no executable Band-1 work exists AND the candidate pool is genuinely human-gated, surface the unblock — do NOT fabricate filler work.

## 5. Cycle-artifacts convention (paused, not deleted)

The cycle-artifacts follow-up pattern (commit each cycle's script + audit as a follow-up PR) ran 5 times in this session (PRs #34, #35, #37, #39, #41). It is now **paused** per the orchestrator's strategic decision.

**Why paused, not deleted:**
- The cycle dance only exists because of the manual DELETE/PUT for the single-human merge. With the Path 1 policy change (`required_approving_review_count: 0` in `docs/00-Governance/branch_protection.json`), the author can now self-merge via the GitHub UI/API directly, and the Option 3 cycle is no longer required for routine PRs. Once the CI workflows land and provide the actual review-quality gate (post-unblock), the cycle is fully obsolete.
- The historical audit chain (PRs #18 through #41) is complete and the artifacts are tracked in `scripts/` and at the repo root. These are immutable records of cycles that ran under the old 1-approval policy.
- Future cycles (if any) can resume the convention. Issue #38 tracks the conductor's eventual decision.

## 6. Decision ledger

| Decision | Made by | Rationale |
|---|---|---|
| True-vs-true fix applied to all active cycle scripts | Orchestrator | Bug was systemic; one-line fix in 5 scripts (PRs #35, #37, #39, #40) |
| Cycle-artifacts convention paused after PR #41 | Orchestrator | Marginal value decreasing; conductor's attention better spent on unblock |
| Issue #38 stays open for conductor's eventual decision | Orchestrator | Strategic question, not orchestrator's call to make permanently |
| Auth-svc slice (Issue #5 → InMemorySessionManager) is the first Phase C implementer dispatch | Orchestrator | Per the IMPLEMENTATION_GUIDE pre-flight gate; smallest Band-3 slice with all deps met |

## 7. What the conductor needs to do

**Right now:** paste the two workflow files (whose canonical content lives on the local `ci/initial-workflows` branch, commit `3c8e5f9`) into `main` via the GitHub web UI — using "Add file" → "Create new file" for each — then push a third (no-op) commit to trigger an actual workflow run. See §2 above and `RUNBOOK_after_paste.md` for the full sequence. (5 minutes.) This is the only action that unblocks Phase C.

**Optionally:** answer issue #38 (cycle convention future), #30 (CODEOWNERS reviewer identities), and #26 (`rm ChatHistory.txt` sign-off).

**Then:** the orchestrator runs `bash scripts/post_paste_cycle.sh` and Phase C begins.

## 8. What the orchestrator will do after the unblock

1. Run the post-paste cycle
2. Update `branch_protection.json` with the new contexts
3. File a follow-up issue for the first Phase C implementer (auth-svc slice)
4. Dispatch the implementer against the WIP branch
5. Monitor the implementer's progress via the PR cycle
6. Continue cycling through the Phase C services in the order in §3.3
7. Maintain operational hygiene (the Band-1 issues in §4) on demand

## 9. Cross-references

- `oauth-workflow-scope-block` memory — the unblock recipe
- `deadlock-recovery-july-2026` memory — how we got here
- `strategic-decision-c-beta` memory — why Phase C is "wait for CI workflows"
- `option3-cycle-script-template` memory — the cycle convention (now paused)
- `empty-cohort-dont-fabricate` memory — the discipline that gates this document
- `RUNBOOK_after_paste.md` — the runbook for `bash scripts/post_paste_cycle.sh`
- `IMPLEMENTATION_GUIDE.md` (on `wip/auth-svc-session-manager`) — the first implementer's brief

## 10. Revision history

### 1.0 Revision history

Initial version. Captures the post-recovery state of the repo as of 2026-07-21, prescribes the unblock path, and lists the Phase C service order.

### 1.1 Revision history

§2 (The unblock) restructured from 5 steps to 7 steps to capture the actual sequence: **(a)** the conductor opens the workflows PR, **(b)** the orchestrator runs the Option 3 cycle to merge it (so the workflow files are on `main`), **(c)** a third commit (no-op) is pushed to `main` to trigger an actual workflow run (GitHub Actions does not run on the commit that adds the workflow file itself), and only then **(d)** the orchestrator runs `bash scripts/post_paste_cycle.sh` to register the context names. The previous wording conflated steps (b)–(d), which would have led a future reader to call `post_paste_cycle.sh` before the workflows had run — at which point the script would warn "no checks observed" and exit without changing anything. The expanded §2 also points more explicitly to `RUNBOOK_after_paste.md` for the failure-mode table. MINOR bump per Document 00 §6 (additive operational detail, no change to meaning).

### 1.2 Revision history

§2 (The unblock) corrected to match the actual viable flow. The previous §2 instructed the conductor to "open a new pull request from `ci/initial-workflows` to `main`" — but the `ci/initial-workflows` branch is **local-only**: it was never pushed to `origin` because pushing it would have triggered GitHub's `workflow`-scope check (the very scope that's blocked). The `github.com/.../tree/ci/initial-workflows` URL returns 404, and the conductor cannot open a PR from a branch that doesn't exist on the remote. Verified with `git ls-remote origin 'refs/heads/ci/*'` (empty) and `git ls-remote origin | grep ci/` (no matches).

The corrected §2 reframes the unblock around what is actually viable: the conductor **pastes the workflow file contents directly into `main` via the GitHub web UI** (bypassing the `ci/initial-workflows` branch as a remote source), then pushes a third (no-op) commit to trigger an actual workflow run, and the orchestrator runs `post_paste_cycle.sh` once the context names are registered. The Option 3 cycle's role is now correctly scoped to the *third-push trigger PR*, not the workflow files themselves.

Also fixes §7 ("What the conductor needs to do") which said "paste the two workflow files from `ci/initial-workflows` to main" — corrected to clarify that `ci/initial-workflows` is the *local* source of the file content (retrieved via `git show ci/initial-workflows -- .github/workflows/<file>`), and the *target* is `main` via the web UI.

Cross-cuts: `RUNBOOK_after_paste.md` step 4 (also corrected this turn, in `c33796c`) and the README's unblock section (also corrected this turn) — together they now tell a consistent, executable, verifiable story. MINOR bump per Document 00 §6: the *operational recipe* changes (substantively), but the document's purpose (post-recovery state + unblock path) does not, so this is not a MAJOR restructure.

## 11. Open decisions

| ID | Decision | Status | Owner |
|---|---|---|---|
| DOC-OD-PHC-01 | Where to publish the new docs that Phase C implementers will produce (e.g. services/auth-svc/README.md, services/auth-svc/DESIGN.md) | Open | Doc Team |
| DOC-OD-PHC-02 | Whether to retro-fit the `00-Governance/branch_protection.json` and `00-Governance/PHASE_C_POST_UNBLOCK_ROADMAP.md` into the docs README index | Open | Doc Team |
| DOC-OD-PHC-03 | Whether the cycle-artifacts convention resumes, archives, or formally retires after the unblock (relates to issue #38) | Open | Conductor |
