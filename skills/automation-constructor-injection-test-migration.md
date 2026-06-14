---
name: automation-constructor-injection-test-migration
description: "How to migrate tests when a class switches from importlib/module-level patching to constructor injection (DI). Use when: (1) refactoring a class to use kwarg-injected factory params instead of module-level re-exports, (2) CI fails with stale patch() targets after a DI refactor, (3) ruff C408 fires on dict() calls in new test code."
category: testing
date: 2026-06-14
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: []
---

# Constructor-Injection Test Migration Pattern

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-14 |
| **Objective** | Replace importlib/module-level patching seam with constructor-injection DI in `BaseReviewer` and migrate all tests |
| **Outcome** | Successful — all 3 CI failures fixed; PR #1310 merged green |
| **Verification** | verified-ci |

## When to Use

- Refactoring a class to accept dependencies as keyword-only `__init__` params instead of resolving them via `importlib` or module-level re-exports
- Any test that previously called `patch("module.Symbol")` on a symbol that no longer exists at module scope
- CI fails with `C408 Unnecessary dict call` in test files
- CI fails with `D101`/`D103` missing docstring errors on test helper classes or functions

## Verified Workflow

### Quick Reference

```bash
# After DI refactor: audit ALL patch() usages in affected test files
grep -rn "patch(" tests/unit/automation/test_address_review.py \
  tests/unit/automation/test_pr_reviewer_posting.py \
  tests/unit/automation/test_reviewer_base_contract.py

# Replace stale module-level patches with constructor kwargs
# BEFORE (stale — patches module-level symbol that no longer exists):
# with patch("hephaestus.automation.address_review.WorktreeManager") as m:
#     reviewer = AddressReviewer(opts)

# AFTER (constructor injection):
# reviewer = AddressReviewer(opts, worktree_manager_factory=lambda p, b: mock_wm)

# Fix C408: replace dict() with literals
# dict(key=value)  ->  {"key": value}

# Fix D101/D103: add one-line docstrings to bare test classes and functions
```

### Detailed Steps

1. **Remove old module-level re-exports** from production code (`__all__`, bare imports of collaborators at module scope for test visibility).

2. **Add keyword-only factory params** to `__init__` with production defaults:
   ```python
   def __init__(
       self,
       options,
       *,
       get_repo_root=get_repo_root_real,
       worktree_manager_factory=WorktreeManager,
       status_tracker_factory=StatusTracker,
       log_manager_factory=ThreadLogManager,
   ):
   ```

3. **Audit ALL tests in affected files** for `patch()` calls that targeted the now-removed module-level symbols. Look for patterns like:
   - `patch("hephaestus.automation.address_review.WorktreeManager")`
   - `patch("hephaestus.automation.pr_reviewer.get_repo_root")`

4. **Replace stale `patch()` triples** with direct constructor kwargs (create a `base_deps` fixture):
   ```python
   @pytest.fixture()
   def base_deps(tmp_path):
       """Inject lightweight fakes via constructor kwargs."""
       return {
           "get_repo_root": lambda: tmp_path,
           "worktree_manager_factory": lambda p, b: FakeWorktreeManager(),
           "status_tracker_factory": lambda p: FakeStatusTracker(),
           "log_manager_factory": lambda p: FakeLogManager(),
       }
   ```

5. **Replace `dict()` calls with `{}` literals** to satisfy ruff C408.

6. **Add one-line docstrings** to every bare test class (D101) and test function (D103).

7. **Run full lint locally before pushing**:
   ```bash
   pixi run ruff check tests/unit/automation/
   pixi run mypy tests/unit/automation/
   pixi run pytest tests/unit/automation/ -x
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Push after initial refactor | Changed production code + rewrote test file, pushed | Ruff C408 fired on `dict()` calls; D101/D103 on bare test class and functions | Always lint new test files locally before pushing |
| Lint fix round | Fixed C408 + docstrings, pushed again | `test_dry_run_returns_none` still patched the removed module-level `get_repo_root` import | After any DI refactor, grep all test files for stale `patch("…Symbol")` calls |
| Patch fix round | Replaced the one stale patch with constructor kwargs | All checks green | Mirror the `base_deps` fixture pattern established earlier in the same file |

## Results & Parameters

**Production side** — `BaseReviewer.__init__` signature after refactor:

```python
def __init__(
    self,
    options: ReviewOptions,
    *,
    get_repo_root: Callable[[], Path] = _get_repo_root_default,
    worktree_manager_factory: type[WorktreeManager] = WorktreeManager,
    status_tracker_factory: type[StatusTracker] = StatusTracker,
    log_manager_factory: type[ThreadLogManager] = ThreadLogManager,
) -> None:
```

**Test side** — `base_deps` fixture replaces three-patch blocks:

```python
@pytest.fixture()
def base_deps(tmp_path):
    """Inject lightweight fakes via constructor kwargs."""
    return {
        "get_repo_root": lambda: tmp_path,
        "worktree_manager_factory": lambda _p, _b: FakeWM(),
        "status_tracker_factory": lambda _p: FakeST(),
        "log_manager_factory": lambda _p: FakeLM(),
    }
```

**CI checks fixed** (in order):

1. `ruff` (C408 dict literal) — replaced `dict(k=v)` with `{"k": v}`
2. `mypy` (D101/D103 docstrings) — added one-line docstrings to ConcreteReviewer + 4 test functions
3. `pytest` (stale patch) — replaced `patch("module.WorktreeManager")` with `constructor(worktree_manager_factory=fake)`

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #1310, issue #1194 — BaseReviewer DI refactor | All CI gates green on 2026-06-14 |
