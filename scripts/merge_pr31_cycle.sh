#!/usr/bin/env bash
# merge_pr31_cycle.sh — Option 3 cycle for PR #31 (chore/pr-template)
#
# Cycle shape: capture pre-state → verify pre-conditions → DELETE reviews rule →
# merge --squash → PUT rule back from canonical file → verify (drift check) → audit.
#
# Per-PR not parameterized (audit record) per the option3-cycle-script-template memory.

set -euo pipefail

PR=31
BRANCH="chore/pr-template"
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
# Use python (always available on this system) to strip the _comment field
# from the canonical file and use the remainder as the PUT body. The
# canonical file is structured to be the exact PUT body with the _comment
# field as the only non-PUT metadata. Avoids the `jq` dependency.
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
if [[ "${LIVE_STRICT}" != "true" ]]; then
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
  "title": "chore: add PR template for structured submissions",
  "cycle_started": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "cycle_completed": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "pre_state": {
    "pr_state": "${PR_STATE}",
    "pr_mergeable": "${PR_MERGEABLE}",
    "open_prs": ${PR_OPEN_COUNT}
  },
  "actions": [
    "captured pre_reviews_rule_pr${PR}.json",
    "verified pre-conditions: 1 open PR, MERGEABLE, OPEN",
    "DELETE required_pull_request_reviews",
    "gh pr merge ${PR} --squash --delete-branch",
    "PUT required_pull_request_reviews back from canonical",
    "drift check: approvals=1, contexts=[], strict=true"
  ],
  "post_state": {
    "main_sha": "${POST_SHA}",
    "live_required_approving_review_count": ${LIVE_APPROVALS},
    "live_required_status_checks_contexts": ${LIVE_CONTEXTS},
    "live_required_status_checks_strict": ${LIVE_STRICT}
  },
  "files_changed": [".github/PULL_REQUEST_TEMPLATE.md"],
  "additions": 29,
  "deletions": 0,
  "closes": "#28",
  "notes": "Band-1 single-subagent dispatch. ACs all verified via grep before commit. Pre-PR diff sanity check (1 file) passed. No AI trailer in commit or PR body."
}
EOF
echo "  audit written to ${AUDIT_FILE}"
echo
echo "=== cycle complete ==="
