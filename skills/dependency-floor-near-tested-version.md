---
name: dependency-floor-near-tested-version
description: "Pattern for raising a tool's version floor to match the tested minor version. Use when: (1) a dependency floor is much lower than the CI-resolved version, (2) adding a cross-manifest consistency regression guard for a dev tool, (3) a load-bearing package (pip, setuptools) needs a two-sided bound, not just a floor raise."
category: ci-cd
date: 2026-06-14
version: "1.2.0"
user-invocable: false
verification: verified-ci
history: dependency-floor-near-tested-version.history
tags: []
---

# Dependency Floor Near Tested Version

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-14 |
| **Objective** | Raise a dev tool's floor (e.g., `ruff>=0.1.0`) to match the tested minor (`>=0.15`) and add a cross-manifest regression guard; or add two-sided bounds for load-bearing packages (e.g., pip `>=23.0,<27`) |
| **Outcome** | verified-ci |
| **Verification** | verified-ci |
| **History** | [changelog](./dependency-floor-near-tested-version.history) |

## When to Use

- A dependency floor in `pyproject.toml` or `pixi.toml` is much lower than what the lock resolves (e.g., `>=0.1.0` but lock resolves `0.15.12`)
- A dev tool (ruff, mypy, pytest) has no cross-manifest consistency test in `tests/unit/scripts/test_dependency_floor_consistency.py`
- A pip-install `.[dev]` consumer could land on a version with a different default behavior than CI enforces
- A load-bearing package (pip, setuptools) needs a two-sided bound, not just a floor raise

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm what the lock resolves
grep "name: ruff" pixi.lock   # or grep the conda URL

# 2. Update both manifests together
# pyproject.toml: "ruff>=0.1.0,<1" → "ruff>=0.15,<1"
# pixi.toml [feature.shared.dependencies]: ruff = ">=0.1.0,<1" → ruff = ">=0.15,<1"

# For two-sided bounds (pip, setuptools):
# pixi.toml: pip = "*" → pip = ">=23.0,<27"
# where cap = installed_major + 1 (pip 26.x → <27)

# 3. No lock re-solve needed if lock already satisfies the new floor
# (0.15.12 satisfies >=0.15 — pixi install not required)
# (pip 26.1.2 satisfies >=23.0,<27 — pixi install not required)

# 4a. Add TestRuffConsistency (cross-manifest pattern) to tests/unit/scripts/test_dependency_floor_consistency.py
# 4b. Add TestPipPinning (absolute bounds pattern) for load-bearing packages

# 5. Run verification
pixi run pytest tests/unit/scripts/test_dependency_floor_consistency.py -v
pixi run ruff check hephaestus scripts tests
```

### Detailed Steps

1. Grep the lock to confirm the resolved version: `grep "ruff-" pixi.lock | grep conda`
2. Check all pixi.toml locations: `grep -n "ruff" pixi.toml` — confirm only one entry exists
3. Raise the floor in both `pyproject.toml` and `pixi.toml` to `>=<tested_minor>`
   - For load-bearing packages: set two-sided bound — floor = first stable release with the required feature, cap = `installed_major + 1`
4. Choose the correct test pattern:
   - **Cross-manifest consistency** (dev tools like ruff, mypy): `TestXxxConsistency` reusing `TestPytestConsistency._find_dep(dev_deps, name)` — do NOT copy/duplicate the helper
   - **Absolute bounds enforcement** (load-bearing packages like pip): `TestPipPinning` using `_floor(spec)` and `_upper_cap(spec)` directly — does NOT use `TestPytestConsistency._find_dep()`
5. Verify the lock is still valid (`pixi run pytest` — if the lock satisfies the new floor, no re-solve needed)

### Choosing Between Test Patterns

| Package type | Test class pattern | Helpers used |
|---|---|---|
| Dev tools (ruff, mypy, pytest) | `TestRuffConsistency` — cross-manifest | `TestPytestConsistency._find_dep(dev_deps, name)` |
| Load-bearing (pip, setuptools) | `TestPipPinning` — absolute bounds | `_floor(spec)`, `_upper_cap(spec)` directly |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Hardcoded sentinel test | `assert floor >= Version("0.15")` in a test | Goes stale silently when lock bumps to 0.16.x | Use only cross-manifest comparison — no hardcoded expected values |
| `dep.startswith("ruff")` | Simple prefix check to find ruff in dev_deps list | Would match `ruff-lsp` or other ruff-prefixed packages | Use PEP 508 specifier splitting via the existing `_find_dep(dev_deps, name)` helper |
| Copying `_find_dep` as new per-class helper | Defined `_find_ruff_dep` as verbatim copy of `TestPytestConsistency._find_dep` with `"ruff"` hardcoded | DRY violation; reviewer NOGO'd; `_find_dep` already takes `name` parameter | Call `TestPytestConsistency._find_dep(dev_deps, "ruff")` directly |
| Separate pre-commit script | `scripts/check_ruff_floor_consistency.py` + pre-commit hook | Disproportionate for a single constraint; unit tests already run in CI | The existing `test_dependency_floor_consistency.py` gate is sufficient |
| Rebasing onto main after sibling issue landed | Branch based on older main without `TestRuffConsistency` (from #1201, which landed first) | Rebase conflict in `test_dependency_floor_consistency.py` — add/add conflict on the test class | Rebase onto origin/main, keep both test classes (`TestRuffConsistency` from #1201 and `TestPipPinning` from #1202), then apply ruff auto-fixes surfaced by the rebase |

## Results & Parameters

**Floor target**: `>=<tested_minor>` where tested_minor is the first two version components of the lock-resolved version (e.g., `0.15.12` → `>=0.15`).

**Upper cap (dev tools)**: Keep unchanged (`<1` for ruff, `<3` for mypy) — consistent with existing patterns.

**Upper cap (load-bearing packages)**: `installed_major + 1` (e.g., pip 26.x installed → cap `<27`). Floor = first stable release with the required feature (pip `>=23.0` = first stable PEP 660 editable-install release).

**Test class pattern — ruff/dev-tools** (cross-manifest, reuses existing helper):

```python
class TestRuffConsistency:
    """Tests for ruff floor/cap consistency across pyproject.toml and pixi.toml.

    Note: reads pixi.toml [feature.shared.dependencies] only — if ruff is ever
    added under [feature.lint.dependencies], extend this test to check that key.
    """

    def test_ruff_floor_matches_across_manifests(self, repo_root: Path) -> None:
        with open(repo_root / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
        dev_deps = pyproject["project"]["optional-dependencies"]["dev"]
        # Reuse existing helper — do NOT copy it into a new _find_ruff_dep method
        pyproject_spec = TestPytestConsistency._find_dep(dev_deps, "ruff")
        assert pyproject_spec is not None

        with open(repo_root / "pixi.toml", "rb") as f:
            pixi = tomllib.load(f)
        pixi_shared_spec = pixi["feature"]["shared"]["dependencies"]["ruff"]

        assert Version(_floor(pyproject_spec)) == Version(_floor(pixi_shared_spec)), (
            "ruff floor skew — update both together, see issue #1201."
        )

    def test_ruff_upper_cap_matches_across_manifests(self, repo_root: Path) -> None:
        # same structure as above but using _upper_cap()
        ...
```

**Test class pattern — pip/load-bearing** (absolute bounds, uses `_floor` and `_upper_cap` directly):

```python
class TestPipPinning:
    """Tests that pip is pinned with a floor and an upper cap in pixi.toml.

    pip>=23.0 is required for reliable PEP 660 editable-install support.
    The upper cap (<installed_major+1) prevents silent breakage on major bumps.
    """

    def _get_pip_spec(self, repo_root: Path) -> str:
        with open(repo_root / "pixi.toml", "rb") as f:
            pixi = tomllib.load(f)
        return pixi["dependencies"]["pip"]

    def test_pip_has_floor(self, repo_root: Path) -> None:
        spec = self._get_pip_spec(repo_root)
        floor = _floor(spec)
        assert floor is not None, "pip must have a lower bound in pixi.toml"
        assert Version(floor) >= Version("23.0"), (
            f"pip floor {floor!r} is below 23.0 — PEP 660 editable-install requires pip>=23.0"
        )

    def test_pip_has_upper_cap(self, repo_root: Path) -> None:
        spec = self._get_pip_spec(repo_root)
        cap = _upper_cap(spec)
        assert cap is not None, (
            "pip must have an upper cap in pixi.toml to prevent silent breakage on major bumps"
        )
```

**pixi.toml lookup key**: `pixi["feature"]["shared"]["dependencies"]["ruff"]` (not `feature.lint` — ruff is in `feature.shared`); `pixi["dependencies"]["pip"]` for pip (top-level dependencies section).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1201 planning (plan approved after v1.1.0 DRY fix) | ruff floor >=0.1.0 → >=0.15; lock at 0.15.12 |
| ProjectHephaestus | Issue #1202 / PR #1295 (green CI) | pip pinned `>=23.0,<27`; lock at 26.1.2; `TestPipPinning` added to test_dependency_floor_consistency.py |
