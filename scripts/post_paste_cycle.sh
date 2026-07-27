#!/usr/bin/env bash
# Post-paste cycle: the orchestrator's flow once the human has pasted
# the two workflow files (.github/workflows/ci-hello-world.yml and
# .github/workflows/docs-lint.yml) via the GitHub web UI.
#
# Pre-conditions (all of these must be true before running):
#   1. The two workflow files exist on `main` -- verify with:
#        gh api repos/$REPO/contents/.github/workflows/ci-hello-world.yml
#        gh api repos/$REPO/contents/.github/workflows/docs-lint.yml
#      (The conductor pastes the files directly into `main` via the
#      GitHub web UI per PHASE_C_POST_UNBLOCK_ROADMAP.md §2 -- there
#      is NO "workflow files PR"; the OAuth `workflow` scope block
#      prevents the bot from opening one, and the paste-into-main
#      path bypasses that gate.)
#   2. The workflows have run at least once on a commit PAST the
#      workflow-file-arrival commit. (GitHub Actions does not run on
#      the commit that adds the workflow file itself -- the
#      conductor must push a third (no-op) commit to trigger an
#      actual run, per RUNBOOK_after_paste.md.) Verify with:
#        sha=$(gh api "repos/$REPO/commits/main" --jq '.sha')
#        gh api "repos/$REPO/commits/$sha/check-runs" \
#          | python -c "import json,sys; print('\n'.join(sorted({c['name'] for c in json.load(sys.stdin)['check_runs']})))"
#      This is the *job-name* check_run list, NOT the workflow
#      name. The `required_status_checks.contexts` field matches
#      against check_run names (job names) in the GraphQL merge
#      gate's `statusCheckRollup.contexts.nodes` array, NOT
#      workflow names. Using workflow names (e.g. `ci-hello-world`,
#      `docs-lint`) is a known merge-blocker trap: the API
#      accepts the PUT but the merge then fails with
#      "GraphQL: N of N required status checks are expected
#      (mergePullRequest)" because the rollup only contains
#      check_run nodes, not workflow-level check_suite nodes.
#      (or read observed_contexts.txt after Step 1 below).
#   3. The canonical docs/00-Governance/branch_protection.json has
#      `required_status_checks.contexts: []` -- this script's job is
#      to populate it from the observed check names.
#
# NOTE: this script does NOT care about the open-PR count. It does
# no DELETE on the reviews rule; that is the merge_prN_cycle.sh
# script's job. The post-paste cycle and the merge cycle are
# independent: a third (no-op) commit push may be merged by a
# separate merge_prN_cycle.sh run before, after, or instead of
# running this script.
#
# What this script does:
#   1. Reads the registered context names from the live branch-
#      protection API.
#   2. Updates the canonical docs/00-Governance/branch_protection.json
#      with those context names in `required_status_checks.contexts`.
#   3. PUTs the updated rule back to the live API.
#   4. Verifies the PUT succeeded (the rule on the live API matches
#      the canonical file).
#   5. (Optional, when there is a workflow-files PR open) runs the
#      Option 3 cycle on that PR to merge it.
#
# Usage:
#   bash scripts/post_paste_cycle.sh [TRIGGER_PR_NUMBER]
#
# If no PR number is passed, the script does steps 1-4 only (no
# merge). This is the right mode for the very first run after the
# human pastes, when the third-commit-trigger PR may have already
# been merged by a separate merge_prN_cycle.sh invocation, or when
# the conductor did the third-commit trigger via the GitHub web UI
# directly (web-UI no-op commits work because they don't need a
# reviews-rule bypass -- they go through the normal merge path with
# the conductor's own admin override on a single-human repo, OR via
# a separate merge_prN_cycle.sh). In practice the conductor pastes
# the workflow files via web UI, pushes a no-op third commit (also
# via web UI or a separate trigger PR), and the orchestrator then
# runs this script to register the contexts in branch_protection.
#
# Note on "self-merge": the canonical branch protection now has
# required_approving_review_count: 0 (Path 1 policy change), so the
# author can self-merge via the GitHub UI/API directly. The legacy
# "1-approval + enforce_admins" rule was structurally unsatisfiable
# on a single-human repo (the only writer is the only candidate
# reviewer, and they are always the PR author). Going forward, the
# two viable paths for the third-commit trigger PR are:
#   (a) The conductor merges via the GitHub UI/API directly (0
#       approvals are trivially satisfied; the PR-required + CI-
#       required gates remain).
#   (b) The orchestrator runs the Option 3 cycle (DELETE reviews
#       rule, merge, PUT it back). This is what
#       merge_prN_cycle.sh does. The cycle is optional now (it was
#       mandatory under the pre-Path-1 unsatisfiable 1-approval rule).
# This script implements (b) for the trigger PR via Step 5 below;
# Step 5 invokes merge_pr${TRIGGER_PR_NUMBER}_cycle.sh if a PR
# number is provided.
#
# This script is idempotent: re-running it is safe. If the canonical
# file already lists the registered contexts, step 2 is a no-op. If
# the live rule already matches the canonical file, step 3 is a no-op.

set -euo pipefail

PR="${1:-}"
REPO="GanTechProject/VinayakFortune"
CANON="docs/00-Governance/branch_protection.json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=== Step 0: capture pre-state ==="
gh api "repos/$REPO/branches/main/protection" > pre_protection.json
echo "  pre_protection.json saved"

echo ""
echo "=== Step 1: read registered context names from the live API ==="
# The classic branch-protection API does not expose the *registered*
# context names directly -- only the *required* ones (the `contexts`
# list inside `required_status_checks`). The registered names come
# from the checks endpoint, which lists every check that has run on
# the most recent commits.
gh api "repos/$REPO/branches/main/protection/required_status_checks" \
    > live_required_status_checks.json
echo "  current required contexts: $(python -c "import json; d=json.load(open('live_required_status_checks.json')); print(d.get('contexts', []))")"

# To get the registered context names (the ones GitHub will accept
# in the `contexts` list and that the merge GraphQL gate matches
# against), we read the **check_runs** for the latest commit on
# `main`. The `check_runs` array on a commit is a GitHub check_run
# (job-level), and the `name` field of a check_run is the job's
# `name:` (e.g. `test + lint + build`), NOT the workflow's `name:`
# (e.g. `ci-hello-world`).
#
# Why this matters: GitHub's `required_status_checks.contexts` array
# is matched against `statusCheckRollup.contexts.nodes` in the
# GraphQL merge gate. That rollup contains **check_run nodes** (job
# names), not check_suite nodes (workflow names). Using workflow
# names in `contexts` makes the API accept the PUT but the merge
# then fails with "GraphQL: N of N required status checks are
# expected (mergePullRequest)" — the rollup never has a node with
# the workflow name, so the gate can never be satisfied.
#
# Why we read check-runs per-commit, not embedded in commits?per_page:
# The embedded `check_runs` array on commits?per_page is **empty
# under the OAuth-app `gh` credential** (the same scope that can
# create PRs but not write `.github/workflows/*`). The dedicated
# `commits/{sha}/check-runs` endpoint returns the job-level
# check_run list regardless of credential, because the check_runs
# primitive is on a different API surface than the contents API
# that the OAuth-app scope blocks. Empirically verified 2026-07-27:
# under the OAuth-app credential, `commits?per_page=10` returns
# `check_runs: []` for every commit, while `commits/{sha}/check-runs`
# returns the full list of completed check_runs.
sha=$(gh api "repos/$REPO/commits/main" --jq '.sha')
echo "  latest main SHA: $sha"
gh api "repos/$REPO/commits/$sha/check-runs" \
    | python -c "
import json, sys
d = json.load(sys.stdin)
contexts = sorted({c['name'] for c in d.get('check_runs', []) if c.get('name')})
print('\n'.join(contexts))
" > observed_contexts.txt
echo "  observed check_run names from latest commit:"
sed 's/^/    /' observed_contexts.txt
if [ ! -s observed_contexts.txt ]; then
    echo "  WARN: no check_run names observed yet. The workflows may"
    echo "  not have run on any commit. The contexts list will be"
    echo "  preserved from the canonical file (Step 2 below preserves"
    echo "  existing entries) until at least one push to main happens"
    echo "  after the workflows land and re-running this script."
fi

echo ""
echo "=== Step 2: build the new canonical file ==="
python <<PY
import json
# CRITICAL: open with encoding='utf-8'. Python on Windows defaults
# to cp1252 in text mode, which double-encodes the canonical's §
# byte (UTF-8 c2 a7) as cp1252 chars 'Â' + '§' on read.
# On write, json.dumps(ensure_ascii=False) then re-encodes those
# two chars as 4 bytes (c3 82 c2 a7), mojibaking the §. Verified
# 2026-07-27.
canon = json.load(open("$CANON", encoding="utf-8"))
observed = [l.strip() for l in open("observed_contexts.txt") if l.strip()]
# Preserve the strict flag and the existing contexts list if it's
# non-empty (in case this script is being re-run after a previous
# partial state). The new entries are the observed context names.
existing = canon.get("required_status_checks", {}).get("contexts", [])
merged = list(dict.fromkeys(existing + observed))  # preserve order, dedupe
canon["required_status_checks"] = {
    "strict": True,
    "contexts": merged,
}
# Write with explicit LF line endings. Python's json.dump on Windows
# defaults to os.linesep (CRLF) which drifts from main's LF canonical
# form, producing noisy diffs on the next commit (see pre-push-eol-preflight).
# ensure_ascii=False preserves the literal UTF-8 § byte that the
# canonical file uses (json.dumps with default ensure_ascii=True
# escapes non-ASCII as Â§ instead of preserving the raw byte).
out = json.dumps(canon, indent=2, ensure_ascii=False) + '\n'
with open("$CANON", "w", encoding="utf-8", newline="") as f:
    f.write(out)
print(f"  new required_status_checks.contexts: {merged}")
PY

echo ""
echo "=== Step 3: PUT the rule back from the canonical file ==="
python <<'PY'
import json
# encoding='utf-8' on read AND write: same Windows-cp1252 trap as Step 2.
canon = json.load(open("docs/00-Governance/branch_protection.json", encoding="utf-8"))
put_body = {
    "required_status_checks": canon["required_status_checks"],
    "enforce_admins": canon["enforce_admins"],
    "required_pull_request_reviews": canon["required_pull_request_reviews"],
    "restrictions": canon.get("restrictions"),
    "required_linear_history": canon["required_linear_history"],
    "allow_force_pushes": canon["allow_force_pushes"],
    "allow_deletions": canon["allow_deletions"],
    "block_creations": canon["block_creations"],
    "required_conversation_resolution": canon["required_conversation_resolution"],
    "lock_branch": canon["lock_branch"],
    "allow_fork_syncing": canon["allow_fork_syncing"],
}
with open("put_body.json", "w", encoding="utf-8") as f:
    json.dump(put_body, f, indent=2, ensure_ascii=False)
PY

put_attempt=1
put_max=3
while [ $put_attempt -le $put_max ]; do
    if gh api -X PUT "repos/$REPO/branches/main/protection" --input put_body.json > /dev/null 2>&1; then
        echo "  -> PUT succeeded on attempt $put_attempt."
        break
    fi
    echo "  -> PUT attempt $put_attempt failed. Retrying..."
    sleep $((put_attempt * 3))
    put_attempt=$((put_attempt + 1))
done
if [ $put_attempt -gt $put_max ]; then
    echo "ERROR: PUT failed after $put_max attempts. Branch UNPROTECTED."
    echo "Manual recovery: gh api -X PUT repos/$REPO/branches/main/protection --input put_body.json"
    exit 1
fi

echo ""
echo "=== Step 4: verify the PUT ==="
gh api "repos/$REPO/branches/main/protection" > post_protection.json
python <<'PY'
import json, sys
def normalize(o):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k in ("url", "contexts_url", "html_url", "restrictions"):
                continue
            if v is None:
                continue
            v2 = normalize(v)
            if isinstance(v2, dict) and set(v2.keys()) == {"enabled"}:
                out[k] = v2["enabled"]
            else:
                out[k] = v2
        out.get("required_status_checks", {}).pop("checks", None)
        return out
    if isinstance(o, list):
        return [normalize(v) for v in o if v is not None]
    return o

# Compare the post-PUT live state against the canonical file (which
# is what we just PUT).
canon = json.load(open("docs/00-Governance/branch_protection.json", encoding="utf-8"))
post = normalize(json.load(open("post_protection.json", encoding="utf-8")))
post.pop("required_signatures", None)

# Build the "expected" post-state from the canonical file.
expected = {
    "required_status_checks": canon["required_status_checks"],
    "enforce_admins": canon["enforce_admins"],
    "required_pull_request_reviews": canon["required_pull_request_reviews"],
    "required_linear_history": canon["required_linear_history"],
    "allow_force_pushes": canon["allow_force_pushes"],
    "allow_deletions": canon["allow_deletions"],
    "block_creations": canon["block_creations"],
    "required_conversation_resolution": canon["required_conversation_resolution"],
    "lock_branch": canon["lock_branch"],
    "allow_fork_syncing": canon["allow_fork_syncing"],
}
expected = normalize(expected)

if expected == post:
    print("OK: live rule matches canonical file (every policy value matches).")
else:
    print("DRIFT after PUT:")
    import difflib
    a = json.dumps(expected, indent=2, sort_keys=True).splitlines()
    b = json.dumps(post, indent=2, sort_keys=True).splitlines()
    print("\n".join(difflib.unified_diff(a, b, lineterm="", n=2)))
    sys.exit(1)
PY

echo ""
echo "=== Step 5 (optional): merge the third-commit-trigger PR via Option 3 cycle ==="
if [ -z "$PR" ]; then
    echo "  no PR number provided. Skipping merge. (Re-run with the"
    echo "  third-commit-trigger PR number to merge it.)"
else
    echo "  running Option 3 cycle on PR #$PR..."
    if [ -f "scripts/merge_pr${PR}_cycle.sh" ]; then
        bash "scripts/merge_pr${PR}_cycle.sh"
    else
        echo "  no cycle script found for PR #$PR. Either create one"
        echo "  (modeled on scripts/merge_pr18_cycle.sh) or run the"
        echo "  Option 3 cycle inline."
        exit 1
    fi
fi

echo ""
echo "=== Done. Contexts registered (or no new ones observed). ==="
echo "  The canonical branch_protection.json now lists the registered"
echo "  context names. Future PRs to main will be gated on those checks."
echo "  If the contexts list is empty, push any commit to main to"
echo "  trigger the workflows and re-run this script."
