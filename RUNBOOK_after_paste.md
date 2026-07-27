# Runbook: After the workflow paste

> **Audience:** the human (conductor) and the orchestrator, working together.
> **Trigger:** the human has just pasted `.github/workflows/ci-hello-world.yml` and `.github/workflows/docs-lint.yml` into `main` via the GitHub web UI's "Add file" → "Create new file" form.
> **Goal:** verify the workflows land cleanly, register the context names in the canonical branch-protection rule, and unblock the auth-svc implementer.

## What the human does (in the web UI)

For each of the two workflow files:

1. Open the GitHub web UI.
2. Click "Add file" → "Create new file".
3. Type the path: `.github/workflows/ci-hello-world.yml` (then `docs-lint.yml` for the second one).
4. Paste the file content. The canonical source is the `ci/initial-workflows` branch (commit `3c8e5f9`), which exists **only in the local clone** (it was never pushed to `origin` because its single commit adds the workflow files themselves and the OAuth scope block prevents that). The reliable way to retrieve the contents is therefore **local, not web-UI**:
   - **Primary (local clone, recommended):** in the local clone, run
     ```bash
     git show ci/initial-workflows -- .github/workflows/ci-hello-world.yml
     git show ci/initial-workflows -- .github/workflows/docs-lint.yml
     ```
     The `--` is mandatory on Windows; the colon-form `git show <ref>:<path>` is parsed as a path separator by Git Bash and fails. Copy the file body (everything after the `diff --git` / `+++` lines / `@@` hunk header — the leading `+` markers are diff artifacts, not part of the file content).
   - **Fallback (no local clone):** if you do not have a local clone of this repo, ask the orchestrator to paste the file contents into the chat. The orchestrator reads from the local `ci/initial-workflows` ref and pastes both files in full.
   - **The GitHub web UI "View file" path does not work** — the branch is not pushed to the remote, so navigating to `github.com/GanTechProject/VinayakFortune/tree/ci/initial-workflows` shows a 404. Do not waste time looking for it there.
5. Commit directly to `main` with a clear message:
   - "ci: add ci-hello-world workflow (test + lint + build + smoke)"
   - "ci: add docs-lint workflow (front-matter + revision-history + orphan check)"

After both files are committed, the workflows run automatically on the second commit (GitHub Actions does not run on the commit that adds the workflow file itself — it runs on the next push to main).

## What the human does next

The workflows need a third push to register their context names. The simplest third push is a no-op commit:

```bash
# In the local clone, on a feature branch off main:
git checkout -b chore/trigger-workflow-run
# Edit a comment in any tracked file (e.g. add a single line to
# docs/00-Governance/branch_protection.json's _comment array).
git commit -m "chore: trigger workflow run after paste"
gh pr create --title "chore: trigger workflow run after paste" --body "..."
# Then the orchestrator runs the Option 3 cycle to merge it.
```

Alternatively, the human can do a no-op commit via the GitHub web UI: "Edit file" on any tracked file, add a space, commit. The push triggers both workflows.

After the third push, both workflows run, and GitHub registers the context names. The orchestrator can now register them in the canonical branch-protection rule.

## What the orchestrator does

Once the workflows have run at least once, the orchestrator runs:

```bash
bash scripts/post_paste_cycle.sh
```

This script:

1. Reads the registered context names from the live API (the names of the checks that have run).
2. Updates `docs/00-Governance/branch_protection.json` to list those names in `required_status_checks.contexts`.
3. PUTs the updated rule back to the live API.
4. Verifies the PUT (live API matches the canonical file).
5. (If the human wants the orchestrator to merge the third-push PR) runs the Option 3 cycle on it.

If the observed context names list is empty, the script warns and exits without changing anything. Push a commit, wait for the workflows to run, re-run the script.

## Expected timeline

| Step | Who | Wall time |
|---|---|---|
| Paste two workflow files | human | 5 min |
| Push a third commit to trigger runs | human | 1 min |
| Workflows run | GitHub | 2-5 min (ci-hello-world builds Docker + smoke; docs-lint is faster) |
| Register context names | orchestrator (`post_paste_cycle.sh`) | 30 s |
| Open the trigger PR (if not done via web UI) | orchestrator | 1 min |
| Merge the trigger PR via Option 3 cycle | orchestrator | 30 s |

Total: ~10 min from paste to fully-protected main with CI gates live.

## What success looks like

After the cycle, the live branch-protection rule on `main`:

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["ci-hello-world", "docs-lint"]
  },
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    ...
  },
  ...
}
```

And the next PR opened to `main` (e.g., the auth-svc implementer) shows both `ci-hello-world` and `docs-lint` as required status checks. A PR with red checks cannot be merged (the merge button is blocked). A PR with green checks is ready for the Option 3 cycle.

## What failure looks like

| Failure | Symptom | Recovery |
|---|---|---|
| Workflow file has a YAML syntax error | The workflow itself does not run; the "no checks observed" warning fires | Edit the file via the web UI, commit, re-run `post_paste_cycle.sh` |
| `actions/checkout@v4` is no longer the latest | Deprecation warning in the workflow run, not a hard failure | Bump to `@v5` in a follow-up commit |
| `ci-hello-world` smoke test fails (image does not become healthy) | Workflow run shows red on the `Smoke-test the image` step | Inspect the CI logs; the docker logs are preserved in the output. Fix the image (probably a Dockerfile change), push a new commit, re-run |
| `docs-lint` finds a missing revision-history subsection | Workflow run shows red on `Verify each doc has the canonical Revision history subsection` | Either fix the doc to add the subsection, or update the canonical regex in `docs-lint.yml` if the doc legitimately uses a different form. Push a new commit. |
| Branch protection PUT fails | Script exits with "Branch UNPROTECTED" | Run `gh api -X PUT repos/GanTechProject/VinayakFortune/branches/main/protection --input put_body.json` manually with retries |

## What this runbook is NOT

- This runbook is not a substitute for the IMPLEMENTATION_GUIDE.md for the auth-svc subset. That guide is for the implementer; this runbook is for the human and the orchestrator at the moment of the unblock.
- This runbook does not cover the `git rm ChatHistory.txt` cleanup (issue #26). That's a separate decision the human owns.

## Related

- `oauth-workflow-scope-block` (memory) — why the paste-via-web-UI is the unblock
- `docs/00-Governance/branch_protection.json` — the canonical rule file
- `scripts/post_paste_cycle.sh` — the orchestrator's post-paste cycle
- `services/hello-world/requirements-dev.txt` — the file the ci-hello-world workflow caches (path is hard-coded in the workflow)
