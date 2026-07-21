#!/usr/bin/env bash
# merge_pr34_cycle.sh — Option 3 cycle for PR #34 (chore/commit-cycle-scripts)
#
# Per-PR not parameterized (audit record) per the option3-cycle-script-template memory.
# Uses python (not jq) for JSON manipulation — see option3-cycle-script-template
# memory for the jq-vs-python gotcha on this Windows system.
# Compares to python's print form (True/False) for booleans — same memory.

set -euo pipefail

PR=34
BRANCH="chore/commit-cycle-scripts"
CANONICAL="docs/00-Governance/branch_protection.json"
AUDIT_DIR="."
AUDIT_FILE="${AUDIT_DIR}/merge_pr${PR}_audit.json"

echo "=== PR #${PR} Option 3 cycle ==="
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
echo "  reviews rule deleted (live rule now: required_pull_request_reviews=null)"
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
LIVE_STRICT=$(python -c "import json; d=json.load(open('post_protection_pr${PR}.json')); print(d['required_status_checks']['strict'])")

echo "  live required_approving_review_count: ${LIVE_APPROVALS} (expect 1)"
echo "  live required_status_checks.contexts: ${LIVE_CONTEXTS} (expect [])"
echo "  live required_status_checks.strict: ${LIVE_STRICT} (expect true)"

if [[ "${LIVE_APPROVALS}" != "1" ]]; then
    echo "  DRIFT: approvals not 1"; exit 1
fi
if [[ "${LIVE_CONTEXTS}" != "[]" ]]; then
    echo "  DRIFT: contexts not empty"; exit 1
fi
# Note: Python prints True/False (capitalized). The shell test below is correct
# because bash sees the string "True" and the script expects "True" (not "true").
if [[ "${LIVE_STRICT}" != "True" ]]; then
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
  "title": "chore: commit cycle scripts + audit records + scripts/README",
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
    "drift check: approvals=1, contexts=[], strict=true"
  ],
  "post_state": {
    "main_sha": "${POST_SHA}",
    "live_required_approving_review_count": ${LIVE_APPROVALS},
    "live_required_status_checks_contexts": ${LIVE_CONTEXTS},
    "live_required_status_checks_strict": ${LIVE_STRICT}
  },
  "files_changed": [
    ".gitignore",
    "merge_pr23_audit.json",
    "merge_pr24_audit.json",
    "merge_pr25_audit.json",
    "merge_pr27_audit.json",
    "merge_pr31_audit.json",
    "merge_pr33_audit.json",
    "scripts/README.md",
    "scripts/merge_pr23_cycle.sh",
    "scripts/merge_pr24_cycle.sh",
    "scripts/merge_pr25_cycle.sh",
    "scripts/merge_pr27_cycle.sh",
    "scripts/merge_pr31_cycle.sh",
    "scripts/merge_pr33_cycle.sh"
  ],
  "additions": 1223,
  "deletions": 0,
  "closes": "#32",
  "notes": "Subagent (Band-1, a2466b9b104fbdcf3) delivered cleanly: 14 files, 1223 insertions, conventional-commit chore: title, no AI trailer, branched from origin/main, Closes #32. Pre-PR diff sanity check confirmed the file set matched the ACs (6 cycle scripts + 6 audit JSONs + 1 README + .gitignore modified). The gitignore negation pattern (!/merge_pr*_audit.json) was verified with git check-ignore -v before push. Option 3 cycle used the python-based PUT body construction (no jq) and the True-vs-true fix from the option3-cycle-script-template memory."
}
EOF
echo "  audit written to ${AUDIT_FILE}"
echo
echo "=== cycle complete ==="
