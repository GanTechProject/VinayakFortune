# scripts/

Operational scripts used by the orchestrator and CI tooling.

## merge_pr*_cycle.sh - Option 3 cycle scripts

The `merge_pr{18,23,24,25,27,31,33}_cycle.sh` scripts are the **per-PR audit records** of every Option 3 cycle that has been run on the `GanTechProject/VinayakFortune:main` branch. They are not parameterized templates; each is a unique record of the cycle that actually ran at that point in time.

### What is the Option 3 cycle?

The Option 3 cycle is the **legacy single-human merge dance** that was used on this repo while the canonical branch protection had `required_pull_request_reviews.required_approving_review_count: 1`. Under that rule, GitHub's review model blocks self-approval of one's own PR — a single-human author cannot satisfy the 1-approval gate, so the cycle DELETEs the rule, merges, and PUTs it back. With the Path 1 policy change (the canonical file now has `required_approving_review_count: 0`), the cycle is no longer required for routine PRs: the author can self-merge via the GitHub UI/API directly.

The cycle (still works under either policy, used for historical PRs and for any future PRs where the conductor prefers the scripted form):

1. **DELETE** the `required_pull_request_reviews` rule (so self-merge is allowed).
2. **MERGE** the PR (squash, with branch deletion).
3. **PUT** the rule back from the canonical `docs/00-Governance/branch_protection.json` (so the gate is restored).
4. **VERIFY** the live rule matches the canonical file (drift check).

The canonical file's `_comment` block documents the cycle in detail.

### When to use these scripts

- **For a new cycle on a new PR:** copy the most recent cycle script (e.g., `merge_pr33_cycle.sh`), update the `PR=33` constant to the new PR number, update the file-name references (`merge_pr33.json` -> `merge_pr{N}.json`, etc.), update the Python literal `pr["number"] != 33`, and run. See the `option3-cycle-script-template` memory for the gotchas (the `jq`-vs-python environment gotcha, the `True`-vs-`true` type gotcha, the sed-vs-Python-literal gotcha).
- **For an audit/postmortem:** read the script and its sibling `merge_pr{N}_audit.json` to see exactly what happened on that PR.
- **For the canonical file:** see `docs/00-Governance/branch_protection.json` - the cycle's PUT step reads from this file.

### Why per-PR, not a template

See the `option3-cycle-script-template` memory: each script is an audit record of the actual cycle that ran at that point in time. Generalizing to a template loses the historical record.

## merge_pr*_audit.json - per-PR audit records

The `merge_pr{N}_audit.json` files are the post-cycle audit outputs. They record the pre-state, the actions taken, the post-state, and any notes about deviations from the standard cycle. They are siblings of the cycle scripts.

## Other files

- `merge_pr18_cycle.sh` / `merge_pr18_audit.json` / `merge_pr19_audit.json` - the earliest cycle records, already committed in the original `ship merge cycle script + audit` PRs.
- `post_paste_cycle.sh` - the orchestrator's run-after-paste cycle for when the human pastes the workflow files via the GitHub web UI. See `RUNBOOK_after_paste.md` at the repo root for the joint runbook.

## Out-of-scope files

The `pre_*/post_*/put_*/open_*/delete_*.json` files are **gitignored** (see root `.gitignore`). They are per-run cycle intermediates, not audit records, and should not be committed.
