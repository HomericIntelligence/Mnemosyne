---
name: pin-action-shas-to-commit
description: 'Pin GitHub Actions version tags to full commit SHAs for supply chain
  security. Use when: (1) workflow or composite action files use mutable tags like
  @v6 or @0.35.0, (2) a security audit flags unpinned action references, (3) adding
  regression tests to prevent future unpinned refs.'
category: ci-cd
date: 2026-03-25
version: "2.0.0"
user-invocable: false
verification: verified-local
history: pin-action-shas-to-commit.history
tags:
  - github-actions
  - supply-chain
  - security
  - sha-pinning
---

# Pin Action SHAs to Commit

## Overview

| Item | Details |
|------|---------|
| Date | 2026-03-25 |
| Objective | Replace all mutable version tags in GitHub Actions `uses:` references with pinned commit SHAs |
| Outcome | Zero mutable tags across all workflow and composite action files, with regression tests |
| Verification | verified-local |
| History | [changelog](./pin-action-shas-to-commit.history) |

## When to Use

- Any `uses:` reference in `.github/workflows/*.yml` or `.github/actions/*/action.yml` uses a mutable tag (`@v6`, `@v5`, `@0.35.0`)
- A security audit or OpenSSF Scorecard flags unpinned action references
- Dependabot or StepSecurity reports supply chain risks from mutable tags
- Adding a new third-party action to any workflow file
- You want to add regression tests to prevent future unpinned refs from being merged

## Verified Workflow

### Quick Reference

```bash
# 1. Find all unpinned external refs
grep -rn '@v[0-9]' .github/
grep -rn 'uses:' .github/ --include='*.yml' | grep -v '@[0-9a-f]\{40\}' | grep -v '\./'

# 2. Resolve SHA for a tag (handles both lightweight and annotated tags)
gh api repos/OWNER/REPO/git/ref/tags/TAG --jq '.object | {sha, type}'
# If type=tag, dereference: gh api repos/OWNER/REPO/git/tags/SHA --jq '.object.sha'

# 3. Replace in file
# uses: owner/action@<40-char-sha>  # vX.Y.Z

# 4. Verify no mutable tags remain
grep -rn '@v[0-9]' .github/  # should return nothing
```

### Detailed Steps

1. **Identify ALL unpinned references** across both workflows and composite actions:

   ```bash
   # Mutable v-tags (e.g. @v6, @v5)
   grep -rn '@v[0-9]' .github/

   # Bare semver tags (e.g. @0.35.0) -- often missed!
   grep -rn 'uses:' .github/ --include='*.yml' | grep -v '@[0-9a-f]\{40\}' | grep -v '\./'
   ```

2. **Build a unique action+tag list** from the grep output. Example:

   | Action | Tag |
   |--------|-----|
   | `actions/checkout` | `v6` |
   | `actions/cache` | `v5` |
   | `aquasecurity/trivy-action` | `0.35.0` |

3. **Resolve commit SHAs** using batch script:

   ```bash
   for repo_tag in "actions/checkout:v6" "actions/cache:v5" "aquasecurity/trivy-action:0.35.0"; do
     repo="${repo_tag%%:*}"
     tag="${repo_tag##*:}"
     obj_type=$(gh api "repos/${repo}/git/ref/tags/${tag}" --jq '.object.type')
     obj_sha=$(gh api "repos/${repo}/git/ref/tags/${tag}" --jq '.object.sha')
     if [ "$obj_type" = "tag" ]; then
       commit_sha=$(gh api "repos/${repo}/git/tags/${obj_sha}" --jq '.object.sha')
     else
       commit_sha="$obj_sha"
     fi
     echo "${repo}@${tag} -> ${commit_sha}"
   done
   ```

4. **Edit each file**, replacing tag with SHA + trailing version comment:

   ```yaml
   # Before
   uses: actions/checkout@v6

   # After
   uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6
   ```

   **Important**: Skip local action refs (`uses: ./.github/actions/...`) -- these reference local code, not external supply chain.

5. **Verify no mutable tags remain**:

   ```bash
   grep -rn '@v[0-9]' .github/
   # Expected: no output

   # Also verify all SHA-pinned refs have version comments
   grep -rn '@[0-9a-f]\{40\}' .github/ --include='*.yml' | grep -v '#'
   # Expected: no output
   ```

6. **Add regression tests** (pytest, parametrized over all .github/ YAML files):

   ```python
   """tests/unit/ci/test_workflow_pinning.py"""
   import re
   from pathlib import Path
   import pytest

   _PROJECT_ROOT = Path(__file__).resolve().parents[3]
   _GITHUB_DIR = _PROJECT_ROOT / ".github"
   _USES_RE = re.compile(r"^\s*-?\s*uses:\s*(.+)$")
   _YAML_FILES = sorted(_GITHUB_DIR.rglob("*.yml"))

   def _extract_external_uses(path):
       results = []
       for i, line in enumerate(path.read_text().splitlines(), 1):
           m = _USES_RE.match(line)
           if m and not m.group(1).strip().startswith("./"):
               results.append((i, m.group(1).strip()))
       return results

   @pytest.mark.parametrize("f", _YAML_FILES, ids=[str(p.relative_to(_PROJECT_ROOT)) for p in _YAML_FILES])
   def test_no_mutable_vtags(f):
       for lineno, val in _extract_external_uses(f):
           assert not (re.search(r"@v\d+", val) and "#" not in val), f"{f}:{lineno}: {val}"

   @pytest.mark.parametrize("f", _YAML_FILES, ids=[str(p.relative_to(_PROJECT_ROOT)) for p in _YAML_FILES])
   def test_sha_refs_have_comments(f):
       for lineno, val in _extract_external_uses(f):
           assert not (re.search(r"@[0-9a-f]{40}", val) and "#" not in val), f"{f}:{lineno}: {val}"

   @pytest.mark.parametrize("f", _YAML_FILES, ids=[str(p.relative_to(_PROJECT_ROOT)) for p in _YAML_FILES])
   def test_no_bare_semver(f):
       for lineno, val in _extract_external_uses(f):
           assert not (re.search(r"@\d+\.\d+", val) and not re.search(r"@[0-9a-f]{40}", val)), f"{f}:{lineno}: {val}"
   ```

## Key Distinctions

- **Composite actions** live at `.github/actions/<name>/action.yml` and are often missed in pinning passes that focus only on `.github/workflows/`
- **Lightweight tags** (type: `commit`) -- returned SHA is directly the commit SHA
- **Annotated tags** (type: `tag`) -- returned SHA is a tag object; dereference with second API call
- **Bare semver tags** (e.g. `@0.35.0`) are also mutable -- don't only grep for `@v[0-9]`
- **Local action refs** (`uses: ./.github/actions/setup-pixi`) reference local code, NOT external supply chain -- skip these
- **README/docs examples** are prose, not live references -- leave as-is

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Searching only `.github/workflows/` | Ran grep scoped to workflow files | Missed composite action files under `.github/actions/` | Always scope search to all of `.github/` not just workflows |
| Assuming issue plan was accurate about file locations | Trusted issue description about which files existed | Composite action files existed but weren't listed | Always verify with `grep -rn` rather than trusting issue descriptions |
| Grepping only for `@v[0-9]` | Only searched for version tags starting with `v` | Missed bare semver tags like `@0.35.0` (aquasecurity/trivy-action) | Also grep for bare semver patterns: `@[0-9]+\.[0-9]` |

## Results & Parameters

**Batch SHA resolution script:**

```bash
for repo_tag in "actions/checkout:v6" "actions/cache:v5" "actions/upload-artifact:v7" \
  "codecov/codecov-action:v5" "aquasecurity/trivy-action:0.35.0" "prefix-dev/setup-pixi:v0.9.4"; do
  repo="${repo_tag%%:*}"; tag="${repo_tag##*:}"
  obj_type=$(gh api "repos/${repo}/git/ref/tags/${tag}" --jq '.object.type')
  obj_sha=$(gh api "repos/${repo}/git/ref/tags/${tag}" --jq '.object.sha')
  if [ "$obj_type" = "tag" ]; then
    sha=$(gh api "repos/${repo}/git/tags/${obj_sha}" --jq '.object.sha')
  else sha="$obj_sha"; fi
  echo "${repo}@${tag} -> ${sha}"
done
```

**Pinned reference format:**

```yaml
uses: owner/action@<40-char-sha>  # vX.Y.Z
```

**Verified SHAs (as of 2026-03-25):**

| Action | Tag | Commit SHA |
|--------|-----|-----------|
| `actions/checkout` | `v6` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` |
| `actions/cache` | `v5` | `668228422ae6a00e4ad889ee87cd7109ec5666a7` |
| `actions/upload-artifact` | `v7` | `bbbca2ddaa5d8feaa63e36b76fdaad77386f024f` |
| `codecov/codecov-action` | `v5` | `1af58845a975a7985b0beb0cbe6fbbb71a41dbad` |
| `aquasecurity/trivy-action` | `0.35.0` | `57a97c7e7821a5776cebc9bb87c984fa69cba8f1` |
| `prefix-dev/setup-pixi` | `v0.9.4` | `a0af7a228712d6121d37aba47adf55c1332c9c2e` |
| `actions/github-script` | `v8` | `ed597411d8f924073f98dfc5c65a23a2325f34cd` |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | PR #3971, issue #3342 | Composite actions only (v1.0.0) |
| ProjectScylla | PR #1561, issue #1534 | Full repo-wide pinning + regression tests (v2.0.0) |
