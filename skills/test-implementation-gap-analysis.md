---
name: test-implementation-gap-analysis
license: BSD-3-Clause
description: "Test-Implementation Gap Analysis — detects gaps between test expectations, implementation, and change claims. Also checks that a commit message or PR description names the behavior the added tests actually exercise, and that delivery claims are bound to the release mechanism that publishes them."
category: testing
date: 2026-04-24
version: "1.3.0"
verification: verified-ci
user-invocable: false
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/test-implementation-gap-analysis.history"
history-cleanup-date: "2026-09-20"
---
# Test-Implementation Gap Analysis

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2025-12-31 |
| Objective | Detect and fix gaps between test expectations and implementation |
| Outcome | SUCCESS - 756 tests passing, 0 warnings |
| Category | testing |
| Source Project | ProjectScylla |

## When to Use This Skill

Use this skill when:
- Tests fail with import errors for missing classes/functions
- Tests exist but implementation is a stub
- Auditing epic/milestone implementation completeness
- Pytest collection warnings appear for production classes
- Python version compatibility issues in tests
- A rebased PR's tests fail with 404/ImportError but the error implies the feature was never implemented (not a conflict issue)
- `git show HEAD --stat` doesn't include the file where the feature should live (routes, handlers, etc.)
- Commit message uses language like "add X endpoint" or "implement Y" but the diff only shows tests
- A commit message or PR description names behavior that the added tests never exercise
- A change claims to deliver a release, a version, or a package update, but the diff has no
  publication input

## Verified Workflow

### Step 1: Run Tests to Identify Scope

```bash
pixi run pytest tests/ -v --tb=short 2>&1 | tail -100
```

Look for:
- Import errors (missing classes/functions)
- NameError (undefined symbols)
- Test failures vs warnings count

### Step 2: Analyze Import Errors First

Import errors block test collection entirely. Fix these first:

```bash
# Find what tests expect vs what exists
grep -n "from scylla.module import" tests/unit/test_file.py
grep -n "class ExpectedClass" src/scylla/module.py
```

### Step 3: Compare Test Expectations to Implementation

Read test file to understand expected API:
```python
# Test expects these to exist
from module import (
    SomeClass,
    some_function,
    SOME_CONSTANT,
)
```

### Step 4: Implement Missing Components

Compare expectations with the requested contract, then implement missing behavior:
- Match function signatures exactly
- Match class attributes and methods
- Match constant values if specified

### Step 5: Fix NameErrors in Existing Code

Common pattern - using wrong class name:
```python
# BEFORE (wrong)
pass_rate=Statistics(**data)

# AFTER (correct - class is actually SummaryStatistics)
pass_rate=SummaryStatistics(**data)
```

### Step 6: Fix Pytest Collection Conflicts

Production classes named `Test*` trigger pytest warnings:
```python
# BEFORE (triggers warning)
class TestOrchestrator:
    pass

# AFTER (no warning)
class EvalOrchestrator:
    pass
```

Rename cascade:
1. Rename class definition
2. Update all imports
3. Update __init__.py exports
4. Update __all__ lists
5. Update type hints
6. Update docstrings

### Step 7: Python Version Compatibility

Python 3.14 changed `subprocess.TimeoutExpired`:
```python
# BEFORE (fails on Python 3.14)
timeout_error = subprocess.TimeoutExpired(cmd="docker", timeout=60, stdout=b"partial")

# AFTER (works on all versions)
timeout_error = subprocess.TimeoutExpired(cmd="docker", timeout=60)
timeout_error.stdout = b"partial"
timeout_error.stderr = b""
```

### Step 8: Detecting PR Description/Diff Mismatch

When a rebased PR's tests fail with 404 or ImportError on a feature the commit message claims was added, verify the diff actually includes the right files before debugging conflict resolution:

```bash
# See the actual files changed in the commit
git show HEAD --stat
```

Compare the output against what the commit message claims was done. If a claimed feature has a test but no implementation file in the stat output, the implementation was never committed.

**Fix pattern:**
1. Run `git show HEAD --stat` to see the actual changed files
2. Compare against what the commit message claims was done
3. For any claimed feature with a test but no implementation: add the missing implementation
4. In this case: add the route to the relevant server/router file, import the needed symbols, commit the fix on the branch

**Specific example (ProjectHermes, 2026-04-24):**
- PR 120: "feat: promote event constants to public API and add GET /events endpoint"
- `git show HEAD --stat` showed: `scripts/register-webhooks.sh`, `src/hermes/publisher.py`, `src/hermes/registrar.py`, `tests/test_events_endpoint.py`
- Missing: `src/hermes/server.py` — the route was never added
- Fix: Added `@app.get("/events")` route to `server.py`, imported `AGENT_EVENTS, TASK_EVENTS` from `publisher`
- Result: All 160 tests passed after the route was added

### Step 9: Verify the Claim Names the Behavior That the Diff Adds

Step 8 checks that claimed code exists in the diff. This step checks the opposite mismatch: a
claim that is broader than the added content, and a delivery claim that no change in the diff can
achieve. Both fail the same way. The reviewer checks the claim against the diff and rejects the
change.

Run these checks before you return a change for review:

1. **Map each clause of the claim to an added artifact.** For each named behavior in the commit
   message or PR description, find the test or the source line that exercises it. A clause with no
   matching artifact is an evidence defect, not a wording defect.
2. **Search the added tests for the claimed terms.** When a claim names a domain term, confirm
   that the added tests use it. Zero matches means the claim describes different code.
3. **Compare the delivery claim with the release mechanism.** When the claim says that a change
   delivers a release, a version, or a package update, identify the step that publishes it. If the
   diff has no version, workflow, or manifest change, and the release mechanism triggers on a tag
   or an equivalent external event, the change cannot deliver that outcome.
4. **Correct the claim or the content.** Correct a broad claim to state what the artifact covers.
   Demote a closing keyword for an issue that this change does not close. When the requested
   outcome is a release, state the publishing step and its owner. Do not add filler code or tests
   to make a claim true.
5. **Remove content that does not serve the corrected claim.** A test that repeats coverage
   already present elsewhere in the suite adds no decision value. Keep one copy.

```bash
# The added tests do not use any term of the claim.
grep -inE "<claimed term 1>|<claimed term 2>" <added test path>

# The diff has no publication input.
git show HEAD --stat | grep -E "version|workflow|manifest|package\.json"
```

**Example (2026-10, tag-driven npm package).** A change added tests for bounded provider output
drain and claimed coverage of an envelope migration. The added tests never named an envelope, and
the package manifest version was already set. The package publishes only when a maintainer pushes a
signed tag that the release workflow verifies. The correction had two parts. First, remove the
duplicate tests. Second, rewrite the claim to name what the tests cover and replace the closing
keyword with a reference. The release stayed with the maintainer.

### Step 10: Verify All Tests Pass

```bash
pixi run pytest tests/ --tb=short
# Should show: X passed, 0 warnings
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | Direct approach worked | N/A | Solution was straightforward |
| Assuming test failure = conflict resolution error | Looked at merge conflicts and rebase output when test returned 404 | The 404 was because the route was never implemented — git show HEAD showed server.py wasn't in the changed files | Always run `git show HEAD --stat` to verify the actual diff matches the commit message claims before debugging conflict resolution |
| Corrected the code to make a broad claim true | A commit message named a migration and a release, so the author added more tests for a different mechanism | The named behavior was already correct, and the publishing step was an external signed-tag push that no diff in the branch could perform | Check the claim scope against the diff first; then correct the claim, not the code, and name the publishing owner |

## Results & Parameters

### Files Modified

| File | Change |
| ------ | -------- |
| `src/scylla/judge/prompts.py` | Full implementation (~300 lines added) |
| `src/scylla/reporting/summary.py` | Fixed NameError |
| `tests/unit/cli/test_cli.py` | Fixed exit code expectations |
| `tests/fixtures/invalid/config/defaults.yaml` | Created missing fixture |
| `tests/unit/test_docker.py` | Fixed Python 3.14 compatibility |
| Multiple files | Renamed `Test*` classes to `Eval*` |
| `pixi.toml` | Fixed `[project]` -> `[workspace]` deprecation |

### Class Renames Applied

| Before | After | Files Updated |
| -------- | ------- | --------------- |
| TestCase | EvalCase | 5 |
| TestOrchestrator | EvalOrchestrator | 4 |
| TestRunner | EvalRunner | 4 |
| TestSummary | EvalSummary | 4 |
| TestProgress | EvalProgress | 3 |
| TestResult | EvalResult | 3 |
| TestSummary (reporting) | EvaluationReport | 3 |

### Metrics

- **Before**: 718 passing, 6+ failing, 7 warnings, 1 import error
- **After**: 756 passing, 0 failing, 0 warnings, 0 errors

## Related Skills

- `pytest-production-class-conflicts` - Deep dive on Test* naming
- `python-version-compatibility` - Handling API changes across versions
- `stub-to-implementation` - Completing stub implementations
