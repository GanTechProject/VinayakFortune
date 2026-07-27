# Mirrors .github/workflows/docs-lint.yml@3c8e5f9; see issue #43.
"""Local docs-lint mirror of .github/workflows/docs-lint.yml.

Runs the 3 checks locally so the orchestrator can verify docs-lint cleanliness
without needing the workflow to actually execute (the workflow is gated on the
OAuth-scope-block unblock, so the local mirror is the canonical pre-merge gate).

Mirrors the workflow exactly:
- Exempts README.md from the revision-history check (per the workflow)
- Lints only docs/**/*.md (the repo-root README.md is not in scope)
"""
import os
import re
import sys
import pathlib

errors = []

# Check 1: every .md has frontmatter (lints all of docs/, not just numbered)
doc_count = 0
for root, _, files in os.walk('docs'):
    for f in files:
        if f.endswith('.md'):
            doc_count += 1
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            if not re.match(r'^---\n.*?\n---\n', content, re.DOTALL):
                errors.append(f'NO_FRONTMATTER: {path}')

# Check 2: every doc has a revision history h3 (exempts README.md)
h3_re = re.compile(r'^### \d+(\.\d+)*\.?\s+Revision history\b', re.MULTILINE)
checked = 0
for root, _, files in os.walk('docs'):
    for f in files:
        if f.endswith('.md'):
            if f == 'README.md':
                continue
            checked += 1
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            if not h3_re.search(content):
                errors.append(f'NO_REVISION_HISTORY: {path}')

# Check 3: every .md in docs/ is referenced from docs/README.md (exempts README.md)
with open('docs/README.md', 'r', encoding='utf-8') as fh:
    readme = fh.read()
for root, _, files in os.walk('docs'):
    for f in files:
        if f.endswith('.md') and f != 'README.md':
            path = pathlib.Path(os.path.join(root, f))
            rel = path.relative_to(pathlib.Path('docs'))
            stem = path.stem
            rel_str = str(rel).replace(os.sep, '/')
            if stem not in readme and rel_str not in readme:
                errors.append(f'ORPHAN: {rel_str}')

print(f'docs: {doc_count} files (lints 1+2), {checked} checked (lints 2 only, README exempted)')
if errors:
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print('All 3 docs-lint checks PASS')
