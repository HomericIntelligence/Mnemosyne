---
name: fix-rebased-ci-pr-stack
description: "Fix CI failures in a stacked PR series after rebase onto main. Use when: (1) multiple PRs diverged from main have CI failures from missing files, expired digests, paid-license actions, or unit tests that test the old structure, (2) a unit test patches or mocks a function by name that was renamed/replaced in the same PR (AttributeError: module does not have attribute 'old_name'), (3) a test was written for the old API that the PR itself replaces and now calls the nonexistent old function."
category: ci-cd
date: 2026-05-28
version: 1.1.0
user-invocable: false
verification: verified-local
history: fix-rebased-ci-pr-stack.history
---
## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-28 |
| **Problem** | Multiple PRs in a series all fail CI after the stack diverged from main |
| **Trigger** | Predecessor PR merged to main; downstream branches now missing files, have stale digests, or have test/action mismatches |
| **Context** | 7-PR CI containerization effort; 3 merged, 4 remaining with failures |
| **Outcome** | All 4 branches rebased, code fixes committed, CI queued to verify |
| **Verification** | verified-local |
| **History** | [changelog](./fix-rebased-ci-pr-stack.history) |

## When to Use

1. A series of PRs was created sequentially; earlier ones merged but later ones are behind main
2. CI fails with "file not found" for a file that was added by a predecessor PR
3. A GitHub Action fails with a license error (e.g. `gitleaks/gitleaks-action@v2` requires paid org license)
4. A pinned container image SHA256 digest is stale (docker.io returns "not found")
5. Unit tests assert on the old structure that was changed in the same PR (e.g. number of Dockerfile stages)
6. A rebase introduces a merge conflict between a composite action (newly added to main) and the old inline setup steps
7. `AttributeError: module does not have attribute 'old_function_name'` in a unit test that patches a function which the PR itself replaced/renamed

## Verified Workflow

### Quick Reference

```bash
# 1. Fetch and check divergence
git fetch origin
for branch in br1 br2 br3 br4; do
  echo "=== $branch ===" && git log --oneline origin/main..origin/$branch
done

# 2. Rebase each branch
git switch <branch> && git rebase origin/main
# If pixi.lock conflict: rm pixi.lock && git add pixi.lock && git rebase --continue

# 3. Read CI failure logs
gh run view <run-id> --log-failed 2>/dev/null | tail -80

# 4. Push fixes
git push --force-with-lease origin <branch>
```

### Step 1: Triage all CI failures before touching code

Read the actual failure logs for every failing check before making any changes:

```bash
# Get run IDs for each branch
gh run list --branch <branch> --limit 3 --json databaseId,conclusion,name

# Read failure logs
gh run view <run-id> --log-failed 2>/dev/null | grep -E "(error|Error|FAIL|assert)" | tail -40
```

**Common failure patterns and their root causes:**

| Log Output | Root Cause | Fix |
| ------------ | ------------ | ----- |
| `stat .../ci/Containerfile: no such file or directory` | Predecessor PR not merged; file missing | Rebase onto main |
| `[HomericIntelligence] is an organization. License key is required` | `gitleaks-action@v2` requires paid org license | Replace with gitleaks CLI |
| `failed to resolve source metadata for docker.io/library/node:20-slim@sha256:...not found` | Pinned SHA256 digest is expired/updated | Pull fresh digest |
| `Expected exactly 2 FROM lines ... found 3` | Unit test asserts old Dockerfile structure | Update test for new stage count |
| `BaseRunMetrics usage count: 1` + `result.py:42` | Grep matches docstring using `(deprecated)` not `# deprecated` | Add `grep -v "(deprecated)"` |
| Merge conflict between `setup-pixi` inline steps and composite action | Predecessor PR added composite action to main | Keep composite action (HEAD version) |
| `AttributeError: module 'hephaestus.automation.github_api' does not have attribute 'resilient_call'` | PR replaced `resilient_call` with a circuit breaker but a test still patches the old name | Replace stale `@patch("...resilient_call")` test with one that patches the new function (`_gh_call_impl`) |

### Step 2: Rebase all branches onto main (parallel)

```bash
for branch in br1 br2 br3 br4; do
  git switch $branch
  git rebase origin/main
  # If pixi.lock conflict (common with pixi.toml changes):
  # rm pixi.lock && git add pixi.lock && git rebase --continue
  # pixi lock  # regenerate from scratch after rebase
done
```

**Merge conflict resolution for composite action vs inline steps:**

When `test.yml` has a conflict between `uses: ./.github/actions/setup-pixi` (HEAD from main)
and the old inline `prefix-dev/setup-pixi@v0.9.4` + cache steps (the PR's original commit),
**always keep the composite action (HEAD)**:

```python
# Python-based conflict resolution (safer than sed for multi-line blocks with ${{ }} expressions)
content = open('.github/workflows/test.yml').read()
old = '''<<<<<<< HEAD
      - name: Set up Pixi
        uses: ./.github/actions/setup-pixi
=======
      - name: Install pixi
        uses: prefix-dev/setup-pixi@v0.9.4
        ... (old inline steps)
>>>>>>> <commit-hash>'''
new = '''      - name: Set up Pixi
        uses: ./.github/actions/setup-pixi'''
open('.github/workflows/test.yml', 'w').write(content.replace(old, new))
```

### Step 3: Fix gitleaks paid-license issue

`gitleaks/gitleaks-action@v2` requires `GITLEAKS_LICENSE` for organization repos.
Replace with gitleaks CLI:

```yaml
# BEFORE (fails for org repos without paid license):
      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# AFTER (works for all repos):
      - name: Install gitleaks
        run: |
          GITLEAKS_VERSION="8.21.2"
          curl -sSfL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
            | tar xz -C /usr/local/bin gitleaks

      - name: Run gitleaks
        run: gitleaks detect --source . --verbose
```

**Note**: The pre-commit hook using `gitleaks` repo directly (not the action) is fine —
this only affects the CI workflow job using `gitleaks/gitleaks-action`.

### Step 4: Update stale container image digests

```bash
# Get current digest for the image
docker manifest inspect node:20-slim 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for m in d.get('manifests', []):
    plat = m.get('platform', {})
    if plat.get('os') == 'linux' and plat.get('architecture') == 'amd64':
        print('linux/amd64:', m['digest'])
        break
"
# Output: linux/amd64: sha256:eef3816042c0f522a2ca9655c1947ca6f97c908b0c227aa50e19432646342ab7

# Update in Dockerfile using Python (safer than sed for long lines)
python3 -c "
content = open('docker/Dockerfile').read()
old = 'FROM node:20-slim@sha256:<old-digest> AS node-source'
new = 'FROM node:20-slim@sha256:<new-digest> AS node-source'
open('docker/Dockerfile', 'w').write(content.replace(old, new))
"
```

### Step 5: Fix deprecation guards that match docstrings

When a grep-based deprecation guard catches documentation references:

```bash
# BEFORE (catches docstring "- BaseRunMetrics ... (deprecated)"):
grep -rn "BaseRunMetrics" . --include="*.py" \
  | grep -v "scylla/core/results.py" \
  | grep -v "# deprecated" \
  | grep -v "test_results.py" \
  | wc -l

# AFTER (also excludes "(deprecated)" in docstrings):
grep -rn "BaseRunMetrics" . --include="*.py" \
  | grep -v "scylla/core/results.py" \
  | grep -v "# deprecated" \
  | grep -v "(deprecated)" \
  | grep -v "test_results.py" \
  | wc -l
```

The pattern `- ClassName (module.py) - Legacy dataclass (deprecated)` in docstrings
uses `(deprecated)` not `# deprecated`, so both filters are needed.

### Step 6: Update unit tests for structural Dockerfile changes

When a PR adds a new multi-stage build step (e.g. `AS node-source`), the unit tests
that assert stage count must be updated:

```python
# Key changes in test_dockerfile_layer_ordering.py:

# 1. Stage count assertion
# BEFORE:
assert len(from_indices) == 2  # "Expected exactly 2 FROM lines"
# AFTER:
assert len(from_indices) == 3  # "Expected exactly 3 FROM lines (builder, node-source, runtime)"

# 2. Runtime stage index
# BEFORE: runtime is from_indices[1]
# AFTER:  runtime is from_indices[2]

# 3. Node.js installation pattern
# BEFORE: searches for "nodesource" (curl|bash pattern)
# AFTER:  searches for "COPY --from=node-source" (multi-stage copy)
nodejs_idx = _first_line_containing(lines, "COPY --from=node-source")
```

### Step 7: Fix stale tests that patch a replaced function

When a PR refactors function A → B (rename, API replacement, inlining), any test that
patches the old name with `@patch("module.A")` will fail immediately with
`AttributeError: module 'module' does not have attribute 'A'`.

```bash
# Identify: grep for @patch decorators referencing the old function name
grep -rn "@patch.*old_function_name" tests/
# Also check for: from module import old_function_name  (will be ImportError)

# Fix: update @patch target to the new function and update assertions
# BEFORE:
@patch("hephaestus.automation.github_api.resilient_call")
def test_resilient_call_invoked_with_correct_parameters(self, mock_resilient):
    mock_resilient.return_value = mock_result
    result = _gh_call(["issue", "view", "123"], max_retries=6)
    call_kwargs = mock_resilient.call_args[1]
    assert call_kwargs["circuit_breaker_name"] == "gh_cli"  # old API

# AFTER:
@patch("hephaestus.automation.github_api._gh_call_impl")
def test_circuit_breaker_wraps_gh_call_impl(self, mock_impl):
    mock_impl.return_value = mock_result
    result = _gh_call(["issue", "view", "123"], max_retries=6)
    call_args, call_kwargs = mock_impl.call_args
    assert call_args[0] == ["issue", "view", "123"]  # new API
    assert call_kwargs["max_retries"] == 6
```

**Key insight**: When a PR introduces a new implementation layer (e.g., circuit breaker
wrapping a renamed inner function), update the test to patch the NEW inner function rather
than the deleted outer helper.

### Step 8: Handle merge ordering dependencies

For PRs with hard ordering constraints (PR A must merge before PR B can pass CI):

```bash
# Option 1: Wait for A to merge, then rebase B
# Use when: B's CI failure is entirely due to missing image/artifact
# Example: PR #1497 (ci-container-workflows) needs scylla-ci:latest image
#          which is built and pushed by PR #1494 (ci-image-workflow)

# After A merges, trigger image build manually:
gh workflow run ci-image.yml
# Wait for GHCR push, then rebase B:
git switch B-branch && git rebase origin/main && git push --force-with-lease

# Option 2: Add fallback to make B's CI pass independently
# Use when: the dependency can be made optional
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Expecting rebase alone to fix PR #1494 | Rebased ci-image-workflow without checking if CI Image job had other issues | CI Image build was previously failing due to missing Containerfile from unmerged predecessor — rebase fixes this specific case | Always read the actual log line to confirm root cause before assuming rebase is sufficient |
| Using `grep -v "# deprecated"` alone | The deprecation guard excluded `# deprecated` comments but not docstring `(deprecated)` markers | Docstrings use `(deprecated)` notation, not `# deprecated` bash comment style | Both patterns must be excluded; read the exact matching line from CI logs |
| Assuming docker manifest inspect gives single digest | Used `d.get('manifests', [{}])[0].get('digest')` without filtering by platform | Multi-arch manifests list all platforms; index[0] may not be linux/amd64 | Filter by `os==linux && architecture==amd64` explicitly |
| Using sed for multi-line conflict resolution | Conflict block in test.yml contained `${{ hashFiles('pixi.lock') }}` which breaks shell variable expansion | Shell interpolation corrupts `${{ }}` expressions in GitHub Actions YAML | Use Python `str.replace()` for conflict resolution in YAML files with GHA expressions |
| Expecting the stale test to pass after rebase | A test patching `resilient_call` (the old API) was expected to continue working after the PR replaced it with a circuit breaker | The attribute `resilient_call` was deleted; `@patch` on a nonexistent attribute raises AttributeError at test-collection time, not at test-run time | When a PR replaces a module-level name, grep for `@patch("module.old_name")` and `from module import old_name` in all tests; update them alongside the implementation |

## Results & Parameters

### Gitleaks CLI version (verified working)
```
GITLEAKS_VERSION="8.21.2"
```

### node:20-slim digest (linux/amd64, pinned 2026-03-15)
```
sha256:eef3816042c0f522a2ca9655c1947ca6f97c908b0c227aa50e19432646342ab7
```

### PR merge order for CI containerization stack
```
#1492 (setup-pixi composite)  ← merged
#1493 (ci/Containerfile)      ← merged
#1495 (Podman local scripts)  ← merged
#1494 (ci-image-workflow)     ← fixes: rebase only (Containerfile now exists)
#1496 (security-hardening)    ← fixes: gitleaks CLI + stale digest + test updates
#1498 (ci-robustness)         ← fixes: deprecation grep excludes (deprecated)
#1497 (ci-container-workflows) ← blocks on #1494 (needs scylla-ci:latest on GHCR)
```

### Python pattern for resolving YAML merge conflicts with GHA expressions
```python
content = open('.github/workflows/test.yml').read()
# Use literal strings with str.replace() — never shell heredoc or sed
old = '<<<<<<< HEAD\n      ...\n=======\n      ...\n>>>>>>> <hash>'
new = '      - name: Set up Pixi\n        uses: ./.github/actions/setup-pixi'
open('.github/workflows/test.yml', 'w').write(content.replace(old, new))
```
