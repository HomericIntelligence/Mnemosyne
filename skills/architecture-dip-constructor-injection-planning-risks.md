---
name: architecture-dip-constructor-injection-planning-risks
description: "Replacing module-level importlib monkeypatching with constructor injection in a class hierarchy (DIP refactor). Use when: (1) planning or executing a DIP refactor that removes _PATCHABLE_DEPENDENCIES / importlib test-seams, (2) reviewing an implementation plan that uses **kwargs forwarding in subclass __init__, (3) assessing risk before migrating 20+ test patch sites to direct injection."
category: architecture
date: 2026-06-13
version: "2.0.0"
user-invocable: false
verification: verified-ci
tags: [DIP, dependency-injection, constructor-injection, importlib, test-seam, monkeypatch, mypy, BaseReviewer, SOLID]
---

# DIP Refactor: Constructor Injection to Replace importlib Test-Seams

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-13 |
| **Objective** | Replace `_resolve_from_subclass_module` + `_PATCHABLE_DEPENDENCIES` importlib test-seam in `BaseReviewer` with keyword-only factory parameters in `__init__` that default to the real collaborators |
| **Outcome** | Fully implemented and merged (PR #1310, issue #1194). 1572 unit tests pass in CI. |
| **Verification** | verified-ci |

## When to Use

- Executing or planning a DIP refactor that replaces module-level monkeypatching (`unittest.mock.patch("module.ClassName")`) with constructor injection
- The class under refactor uses `importlib.import_module(cls.__module__)` + `getattr` to pull collaborators at runtime
- A `_PATCHABLE_DEPENDENCIES` tuple enumerates the names of injectable collaborators
- Subclasses re-export the collaborators in their own `__all__` so `patch("subclass_module.ClassName")` resolves correctly
- You need to migrate 20+ test patch sites to direct injection in a single PR
- Reviewing any plan that uses `**kwargs` forwarding to pass injection parameters through a subclass `__init__`

## Verified Workflow

> **Status**: verified-ci — all steps below were executed for ProjectHephaestus `BaseReviewer`, PR #1310 merged, 1572 unit tests passing.

### Quick Reference

```python
# BaseReviewer injection signature (verified)
def __init__(
    self,
    options: Any,
    *,
    get_repo_root: Callable[[], Any] = _default_get_repo_root,
    worktree_manager_factory: Callable[[], WorktreeManager] = WorktreeManager,
    status_tracker_factory: Callable[[int], StatusTracker] = StatusTracker,
    log_manager_factory: Callable[[], ThreadLogManager] = ThreadLogManager,
) -> None: ...

# Shared test fixture (verified pattern)
@pytest.fixture
def base_deps(tmp_path):
    return dict(
        get_repo_root=lambda: tmp_path,
        worktree_manager_factory=MagicMock(return_value=MagicMock()),
        status_tracker_factory=MagicMock(return_value=MagicMock()),
        log_manager_factory=MagicMock(return_value=MagicMock()),
    )

# Subclass __init__ using **kwargs: Any (verified working with mypy --strict)
class PRReviewer(BaseReviewer):
    def __init__(self, options: Any, **kwargs: Any) -> None:
        super().__init__(options, **kwargs)
```

### Verified Steps

1. **Verify subclass body usage before removing imports**: Read the complete body of every subclass to confirm that `WorktreeManager`, `StatusTracker`, and `ThreadLogManager` are not called directly in body methods. For `address_review.py`: `get_repo_root` was imported for the test-seam re-export but was NOT called anywhere in the module body — this must be confirmed before removing any import, not assumed.

2. **Add factory parameters to `BaseReviewer.__init__`**: Use keyword-only parameters with class-as-default (e.g., `worktree_manager_factory: Callable[[], WorktreeManager] = WorktreeManager`). `get_repo_root` gets a `_default_get_repo_root` module-level function as default (not the imported symbol directly) so tests can inject a `lambda: tmp_path` cleanly. Production call sites (`PRReviewer(options)`) need zero changes.

3. **Delete `_resolve_from_subclass_module` and `_PATCHABLE_DEPENDENCIES`**: Remove the importlib machinery after step 2 is in place and all subclasses forward the new parameters.

4. **Update subclass `__init__` signatures**: Use `**kwargs: Any` (NOT `**kwargs: object`). `**kwargs: object` causes mypy errors because `dict[str, object]` is incompatible with the typed keyword-only factory params. `**kwargs: Any` is opaque to mypy and passes `--strict`. If explicit forwarding is preferred for documentation value, enumerate each param explicitly — both approaches work.

5. **Remove `__all__` re-export blocks from subclasses**: The re-exports (`WorktreeManager`, `StatusTracker`, `ThreadLogManager`, `get_repo_root`) exist solely for the test-seam. Once tests use direct injection, they can be removed entirely. Verify no external callers do `from hephaestus.automation.pr_reviewer import WorktreeManager` before removing.

6. **Remove unused imports from subclasses**: After removing `__all__` re-exports, the module-level imports of `ThreadLogManager`, `StatusTracker`, `WorktreeManager` in the subclass files become unused. Remove them. Do NOT remove imports that are called in the module body (e.g., used in a method).

7. **Rewrite `test_reviewer_base_contract.py`**: The existing contract tests assert `_PATCHABLE_DEPENDENCIES` is exact and that re-exports exist on subclass modules. Both assertions are invalid after the refactor. Replace with tests that verify the injection API: factories default to real classes, injected mocks propagate to the constructed collaborators.

8. **Migrate 20+ test patch sites**: Replace `patch("hephaestus.automation.address_review.WorktreeManager")` etc. with direct injection via the `base_deps` fixture. Add `base_deps` as a shared `@pytest.fixture` per test module; pass `**base_deps` to constructor calls. Patches targeting instance method calls (not construction) are unaffected.

9. **Verify import boundary tests pass**: `test_automation_boundary.py` uses static grep to enforce the automation→library boundary. Adding module-level imports of collaborators to `_reviewer_base.py` is safe because it is in `hephaestus.automation` (product layer), not the base `hephaestus` surface.

10. **Eliminate a category of code-quality-bot noise**: The old `# noqa: F401` re-export imports were flagged by the bot as "unused imports" and raised unresolvable review threads. The DI refactor eliminates this entire category.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| `**kwargs: object` in subclass `__init__` | Use `**kwargs: object` instead of `**kwargs: Any` when forwarding to `super().__init__()` | mypy infers `dict[str, object]` which is incompatible with the typed keyword-only factory params (`Callable[[], WorktreeManager]` etc.) | Use `**kwargs: Any` — it is opaque to mypy and satisfies `--strict` without `@overload` stubs |
| Removing `__all__` without verifying external callers | Drop `WorktreeManager`/`StatusTracker`/`ThreadLogManager` from submodule `__all__` without checking call sites | External code doing `from hephaestus.automation.pr_reviewer import WorktreeManager` would break silently | Grep for all import sites across the codebase before removing re-exports; keep entries if any non-test callers exist |
| Skipping full body read of subclasses | Assumed collaborators were only used at construction time based on reading `__init__` only | In `address_review.py`, `get_repo_root` was imported for the test-seam re-export but NOT called in the module body — the check must confirm actual usage, not assume | Always read the complete file before removing module-level imports or re-exports |
| Not scanning for a third subclass | Assumed only `PRReviewer` and `AddressReviewer` exist | A third subclass that overrides `__init__` without forwarding the new parameters would silently use the old importlib path (if not deleted) or crash (if deleted) | Run `grep -r "BaseReviewer" --include="*.py"` exhaustively before assuming the subclass count is known |
| Explicit param forwarding over `**kwargs` | Enumerate each kwarg explicitly in subclass (original plan recommendation) | More verbose, no mypy benefit over `**kwargs: Any`, more surface to keep in sync as base class evolves | `**kwargs: Any` is the simpler approach; explicit forwarding only adds value if subclasses need to set different defaults or add validation |

## Results & Parameters

### Verified Code Locations

| Symbol | File | Notes |
| -------- | ------ | ------- |
| `BaseReviewer.__init__` injection params | `hephaestus/automation/_reviewer_base.py` | Four keyword-only factory params with production defaults |
| `_default_get_repo_root` | `hephaestus/automation/_reviewer_base.py` | Module-level function used as default for `get_repo_root` param |
| Deleted: `_resolve_from_subclass_module` | was `hephaestus/automation/_reviewer_base.py` | Removed entirely in PR #1310 |
| Deleted: `_PATCHABLE_DEPENDENCIES` | was `hephaestus/automation/_reviewer_base.py` | Removed entirely in PR #1310 |
| Deleted: `__all__` re-export block | was `hephaestus/automation/pr_reviewer.py` | Removed; re-exports existed solely for the test-seam |
| Deleted: `__all__` re-export block | was `hephaestus/automation/address_review.py` | Removed; re-exports existed solely for the test-seam |
| Rewritten: contract test | `tests/unit/automation/test_reviewer_base_contract.py` | Now asserts injection API instead of `_PATCHABLE_DEPENDENCIES` |

### Factory Signatures (Verified)

| Parameter | Type | Default | Notes |
| ----------- | ------ | --------- | ------- |
| `get_repo_root` | `Callable[[], Any]` | `_default_get_repo_root` | Module-level fn wrapping `get_repo_root()` import |
| `worktree_manager_factory` | `Callable[[], WorktreeManager]` | `WorktreeManager` | Zero-arg; instantiates with no args |
| `status_tracker_factory` | `Callable[[int], StatusTracker]` | `StatusTracker` | One positional arg: `num_slots: int` |
| `log_manager_factory` | `Callable[[], ThreadLogManager]` | `ThreadLogManager` | Zero-arg; instantiates with no args |

### Key Invariants

1. `**kwargs: Any` (not `**kwargs: object`) required for mypy compliance when forwarding typed keyword-only params from subclass to base class.
2. `status_tracker_factory` signature MUST be `Callable[[int], StatusTracker]` — `StatusTracker.__init__` requires `num_slots: int`; a zero-arg default crashes at call time.
3. Production call sites need zero changes — `PRReviewer(options)` and `AddressReviewer(options)` still work unchanged because all factory params have defaults.
4. The shared `base_deps` fixture must supply `status_tracker_factory=MagicMock(return_value=MagicMock())` — the mock must accept a positional int arg (MagicMock does by default).

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #1194 — DIP violation fix in BaseReviewer, PR #1310 | 1572 unit tests pass in CI; verified-ci |

## References

- [SOLID Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Python unittest.mock.patch documentation](https://docs.python.org/3/library/unittest.mock.html#patch)
- [ProjectHephaestus Issue #1194](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1194)
- [ProjectHephaestus PR #1310](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1310)
