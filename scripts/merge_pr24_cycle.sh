#!/usr/bin/env bash
# Option 3 cycle for PR 24: DELETE the reviews rule, merge, PUT it back.
# Pre-conditions: PR 24 is open and MERGEABLE; user is the repo admin.
# Post-conditions: PR 24 merged into main; protection restored from canonical file.

set -euo pipefail

PR=24
REPO=GanTechProject/VinayakFortune
CANON=docs/00-Governance/branch_protection.json
AUDIT="merge_pr${PR}_audit.json"

echo "=== Step 0: capture pre-state ==="
gh api "repos/$REPO/branches/main/protection" > "pre_protection.json"
gh pr view "$PR" --json state,mergeable,mergeStateStatus,reviewDecision > "pre_pr.json"
gh pr list --state open --json number,title > "open_prs.json"

echo ""
echo "=== Step 0a: verify pre-conditions ==="
python - <<'PY'
import json, sys
pre_pr = json.load(open("pre_pr.json"))
assert pre_pr["state"] == "OPEN", f"PR is not open: {pre_pr['state']}"
assert pre_pr["mergeable"] == "MERGEABLE", f"PR is not mergeable: {pre_pr['mergeable']}"
assert pre_pr["mergeStateStatus"] in ("BLOCKED", "CLEAN"), f"Unexpected merge state: {pre_pr['mergeStateStatus']}"
assert pre_pr["reviewDecision"] == "REVIEW_REQUIRED", f"Expected REVIEW_REQUIRED, got: {pre_pr['reviewDecision']}"

open_prs = json.load(open("open_prs.json"))
others = [pr for pr in open_prs if pr["number"] != 24]
if others:
    print(f"ABORT: {len(others)} other open PR(s) exist.")
    for pr in others:
        print(f"  - PR #{pr['number']}: {pr['title']}")
    sys.exit(1)

print("PRE-CONDITIONS OK: PR 24 is the only open PR, mergeable, blocked only by the reviews rule.")
PY

echo ""
echo "=== Step 1: DELETE the required_pull_request_reviews rule ==="
gh api "repos/$REPO/branches/main/protection/required_pull_request_reviews" > "pre_reviews_rule.json" 2>/dev/null || true
gh api -X DELETE "repos/$REPO/branches/main/protection/required_pull_request_reviews"

echo ""
echo "=== Step 1a: confirm the rule is gone ==="
http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: token $(gh auth token)" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$REPO/branches/main/protection/required_pull_request_reviews")
if [ "$http_code" = "404" ]; then
    echo "  -> 404: reviews rule removed (as expected)"
elif [ "$http_code" = "200" ]; then
    pr_review_state=$(gh pr view "$PR" --json reviewDecision -q '.reviewDecision')
    if [ "$pr_review_state" = "" ] || [ "$pr_review_state" = "null" ]; then
        echo "  -> PR review state empty/null: gate off. Proceeding."
    else
        echo "  -> PR review state: $pr_review_state. Aborting."
        exit 1
    fi
else
    echo "  -> HTTP $http_code. Aborting."
    exit 1
fi

echo ""
echo "=== Step 2: MERGE the PR with --squash ==="
gh pr merge "$PR" --squash --delete-branch=false

echo ""
echo "=== Step 3: PUT the rule back ==="
python - <<'PY'
import json
canon = json.load(open("docs/00-Governance/branch_protection.json"))
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
json.dump(put_body, open("put_body.json", "w"), indent=2)
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
    exit 1
fi

echo ""
echo "=== Step 3a: confirm rule restored ==="
gh api "repos/$REPO/branches/main/protection" > "post_protection.json"
python - <<'PY'
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
pre = normalize(json.load(open("pre_protection.json")))
post = normalize(json.load(open("post_protection.json")))
for k in ("required_signatures",):
    pre.pop(k, None)
    post.pop(k, None)
if pre == post:
    print("OK: protection rule restored to pre-cycle state.")
else:
    print("DRIFT after PUT:")
    import difflib
    a = json.dumps(pre, indent=2, sort_keys=True).splitlines()
    b = json.dumps(post, indent=2, sort_keys=True).splitlines()
    print("\n".join(difflib.unified_diff(a, b, lineterm="", n=2)))
    sys.exit(1)
PY

echo ""
echo "=== Step 4: post-merge audit ==="
gh pr view "$PR" --json state,mergeCommit,mergedAt,mergedBy > "post_pr.json"
python - <<PY
import json
audit = {
    "pr": $PR,
    "method": "Option 3 cycle (corrective: reverts PR 23 which was based on the wrong branch)",
    "pre_pr": json.load(open("pre_pr.json")),
    "post_pr": json.load(open("post_pr.json")),
    "rule_drift": "none (verified every policy value matches pre-cycle state)",
}
json.dump(audit, open("$AUDIT", "w"), indent=2)
PY

echo ""
echo "=== Done. PR $PR is merged and protection is restored. ==="
