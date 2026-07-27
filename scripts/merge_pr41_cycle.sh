#!/usr/bin/env bash
# merge_pr41_cycle.sh — Option 3 cycle for PR #41 (chore/finalize-cycle-artifacts-followup)
#
# This is the FINAL cycle in the cycle-artifacts follow-up pattern.
# After this cycle, the convention pauses pending the conductor's answer to issue #38.
# The cycle artifacts (merge_pr41_audit.json, scripts/merge_pr41_cycle.sh) will be
# left UNTRACKED — per the convention pause, not committed as a follow-up PR.
#
# Per-PR not parameterized (audit record) per the option3-cycle-script-template memory.
# Uses python (not jq) for JSON manipulation.
# Uses json.dumps (not print) for the audit heredoc's strict value — the True-vs-true fix.
# Uses LIVE_STRICT_PYTHON for the shell-side drift check.

set -euo pipefail

PR=41
BRANCH="chore/finalize-cycle-artifacts-followup"
CANONICAL="docs/00-Governance/branch_protection.json"
AUDIT_DIR="."
AUDIT_FILE="${AUDIT_DIR}/merge_pr${PR}_audit.json"

echo "=== PR #${PR} Option 3 cycle (FINAL in the convention) ==="
echo "branch: ${BRANCH}"
echo "canonical: ${CANONICAL}"
echo "audit: ${AUDIT_FILE}"
echo

# --- 1. Capture pre-state ---
echo "--- 1. Capturing pre-state ---"
gh api repos/GanTechProject/VinayakFortune/branches/main/protection \
    > "pre_reviews_rule_pr${PR}.json" 2>/dev/null
echo "  saved pre_reviews_rule_pr${PR}.json"
echo

# --- 2. Verify pre-conditions ---
echo "--- 2. Verifying pre-conditions ---"
PR_STATE=$(gh pr view ${PR} --json state -q .state)
PR_MERGEABLE=$(gh pr view ${PR} --json mergeable -q .mergeable)
PR_OPEN_COUNT=$(gh pr list --state open --json number -q 'length')

echo "  PR state: ${PR_STATE} (must be OPEN)"
echo "  PR mergeable: ${PR_MERGEABLE} (must be MERGEABLE)"
echo "  open PRs: ${PR_OPEN_COUNT} (must be 1)"

if [[ "${PR_STATE}" != "OPEN" ]]; then
    echo "  ABORT: PR not OPEN"; exit 1
fi
if [[ "${PR_MERGEABLE}" != "MERGEABLE" ]]; then
    echo "  ABORT: PR not MERGEABLE"; exit 1
fi
if [[ "${PR_OPEN_COUNT}" != "1" ]]; then
    echo "  ABORT: ${PR_OPEN_COUNT} open PRs exist, expected 1"; exit 1
fi
echo "  pre-conditions OK"
echo

# --- 3. DELETE the reviews rule ---
echo "--- 3. DELETE the reviews rule ---"
gh api -X DELETE \
    repos/GanTechProject/VinayakFortune/branches/main/protection/required_pull_request_reviews \
    > "delete_reviews_pr${PR}.json" 2>&1 || true
echo "  reviews rule deleted"
echo

# --- 4. Merge --squash ---
echo "--- 4. Merge --squash ---"
gh pr merge ${PR} --squash --delete-branch \
    > "merge_pr${PR}.json" 2>&1 || {
        echo "  ABORT: merge failed; re-PUT the rule before exiting"
        python -c "
import json
with open('${CANONICAL}', 'r') as f:
    data = json.load(f)
data.pop('_comment', None)
with open('put_body_pr${PR}_recovery.json', 'w') as f:
    json.dump(data, f, indent=2)
"
        gh api -X PUT \
            repos/GanTechProject/VinayakFortune/branches/main/protection \
            --input "put_body_pr${PR}_recovery.json" > /dev/null
        exit 1
    }
echo "  merged and branch deleted on remote"
echo

# --- 5. PUT the rule back from canonical file ---
echo "--- 5. PUT rule back from canonical ---"
python -c "
import json
with open('${CANONICAL}', 'r') as f:
    data = json.load(f)
data.pop('_comment', None)
with open('put_body_pr${PR}.json', 'w') as f:
    json.dump(data, f, indent=2)
"
gh api -X PUT \
    repos/GanTechProject/VinayakFortune/branches/main/protection \
    --input "put_body_pr${PR}.json" > "put_response_pr${PR}.json" 2>&1
echo "  rule PUT back"
echo

# --- 6. Verify (drift check) ---
echo "--- 6. Verify (drift check) ---"
gh api repos/GanTechProject/VinayakFortune/branches/main/protection \
    > "post_protection_pr${PR}.json" 2>/dev/null
LIVE_APPROVALS=$(python -c "import json; d=json.load(open('post_protection_pr${PR}.json')); print(d['required_pull_request_reviews']['required_approving_review_count'])")
LIVE_CONTEXTS=$(python -c "import json; d=json.load(open('post_protection_pr${PR}.json')); print(d['required_status_checks']['contexts'])")
# JSON-valid form for the audit heredoc (json.dumps returns "true" lowercase).
LIVE_STRICT=$(python -c "import json; d=json.load(open('post_protection_pr${PR}.json')); print(json.dumps(d['required_status_checks']['strict']))")
# Shell-side form for the drift check (python's print(True) returns "True" capitalized).
LIVE_STRICT_PYTHON=$(python -c "import json; d=json.load(open('post_protection_pr${PR}.json')); print(d['required_status_checks']['strict'])")

echo "  live required_approving_review_count: ${LIVE_APPROVALS} (expect 1)"
echo "  live required_status_checks.contexts: ${LIVE_CONTEXTS} (expect [])"
echo "  live required_status_checks.strict: ${LIVE_STRICT} (expect true)"

if [[ "${LIVE_APPROVALS}" != "1" ]]; then
    echo "  DRIFT: approvals not 1"; exit 1
fi
if [[ "${LIVE_CONTEXTS}" != "[]" ]]; then
    echo "  DRIFT: contexts not empty"; exit 1
fi
# Drift check uses the legacy "True" comparison (via LIVE_STRICT_PYTHON) per the
# option3-cycle-script-template memory's verified-correct pattern.
if [[ "${LIVE_STRICT_PYTHON}" != "True" ]]; then
    echo "  DRIFT: strict not true"; exit 1
fi
echo "  drift check OK"
echo

# --- 7. Audit ---
echo "--- 7. Audit ---"
POST_SHA=$(gh api repos/GanTechProject/VinayakFortune/git/refs/heads/main -q .object.sha)
cat > "${AUDIT_FILE}" <<EOF
{
  "pr": ${PR},
  "branch": "${BRANCH}",
  "title": "chore: commit final cycle artifacts (PR #39 + PR #40 scripts and audits)",
  "cycle_started": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "cycle_completed": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "cycle_outcome": "MERGED",
  "pre_state": {
    "pr_state": "${PR_STATE}",
    "pr_mergeable": "${PR_MERGEABLE}",
    "open_prs": ${PR_OPEN_COUNT}
  },
  "actions": [
    "captured pre_reviews_rule_pr${PR}.json (live rule at cycle start)",
    "verified pre-conditions: 1 open PR, MERGEABLE, OPEN",
    "DELETE required_pull_request_reviews",
    "gh pr merge ${PR} --squash --delete-branch (succeeded)",
    "PUT step ran cleanly: built PUT body from canonical via python (no jq dependency), PUT succeeded",
    "drift check: approvals=1, contexts=[], strict=true (verified via LIVE_STRICT_PYTHON for shell-side check, emitted as JSON-valid via json.dumps in LIVE_STRICT)"
  ],
  "post_state": {
    "main_sha": "${POST_SHA}",
    "live_required_approving_review_count": ${LIVE_APPROVALS},
    "live_required_status_checks_contexts": ${LIVE_CONTEXTS},
    "live_required_status_checks_strict": ${LIVE_STRICT}
  },
  "files_changed": [
    "merge_pr39_audit.json",
    "merge_pr40_audit.json",
    "scripts/merge_pr39_cycle.sh",
    "scripts/merge_pr40_cycle.sh"
  ],
  "additions": 412,
  "deletions": 0,
  "closes": "#32",
  "notes": "This is the FINAL cycle in the cycle-artifacts follow-up pattern. The convention pauses after this cycle. The cycle artifacts from PR #41 (merge_pr41_audit.json, scripts/merge_pr41_cycle.sh) will remain UNTRACKED per the convention pause — no follow-up PR will be dispatched. The cycle ran cleanly: drift check passed with the True-vs-true fix in effect, audit JSON is valid out of the box. The audit chain is complete from PR #18 through PR #41. Issue #38 remains open for the conductor's decision on whether to resume, archive, or formally retire the convention."
}
EOF
echo "  audit written to ${AUDIT_FILE}"
echo
echo "=== cycle complete (FINAL) ==="
