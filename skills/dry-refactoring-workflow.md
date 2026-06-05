---
name: dry-refactoring-workflow
description: Complete TDD-driven workflow for identifying and eliminating code duplication
  by extracting reusable helper methods. Covers private module extraction patterns,
  test structure mirroring enforcement, and cryptographic commit signing requirements
  in PR workflows.
category: architecture
date: 2026-06-04
version: 1.1.0
user-invocable: false
verification: verified-ci
history: dry-refactoring-workflow.history
---
# DRY Refactoring Workflow

Complete TDD-driven workflow for identifying and eliminating code duplication by extracting reusable helper methods.

## Overview

| Attribute | Details |
| ----------- | --------- |
| **Date** | 2026-06-04 |
| **Objective** | TDD-driven extraction of duplicated code into reusable helper modules, with emphasis on private module placement, test structure mirroring, and cryptographic commit signing |
| **Outcome** | ✅ v1.0.0 (Feb 2026): Eliminated token aggregation duplication. v1.1.0 (Jun 2026): Extended with private module patterns, test mirroring enforcement, signing requirements. |
| **Primary Issues** | #642 (original), #739 (private module extraction), #917 (pr-policy signing) |
| **Primary PRs** | #714 (original), #900+ (refactoring PRs) |
| **History** | [changelog](./dry-refactoring-workflow.history) |

## When to Use This Skill

Use this workflow when you encounter:

- **Code duplication**: Same logic appears in 2+ methods
- **DRY violations**: Identical patterns that should be abstracted
- **Refactoring tasks**: Need to improve code maintainability
- **Follow-up issues**: Code review identified duplication to fix

**Trigger phrases**:

- "Extract duplicate [X] logic"
- "Consolidate [X] code"
- "DRY violation in [method names]"
- "Create helper method for [pattern]"
- "Extract duplicated function calls into a helper module"
- "Private helper module placement — where should `_helper.py` go?"
- "How to structure tests for root-level private modules?"
- "Duplicated `importlib.metadata.version()` calls — consolidate into helper"

## Verified Workflow

### Phase 1: Analysis & Planning

1. **Identify duplication** - Find exact duplicate code blocks

   ```bash
   # Search for the pattern
   grep -n "pattern" path/to/file.py
   ```

2. **Verify identical logic** - Confirm both instances do the same thing
   - Check for any subtle differences
   - Note any conditional variations

3. **Choose placement** - Place helper near related private methods
   - After similar helper methods
   - Before the methods that will use it
   - Maintain logical grouping

### Phase 2: Test-Driven Development

**IMPORTANT**: Always write tests BEFORE implementing the helper method.

1. **Create test file** if it doesn't exist

   ```python
   # tests/unit/<module>/test_<class>.py
   from pathlib import Path
   from unittest.mock import MagicMock
   import pytest

   @pytest.fixture
   def mock_config() -> ConfigClass:
       """Create mock config for testing."""
       return ConfigClass(
           required_field="value",
           # Add all required fields
       )
   ```

2. **Write comprehensive tests**
   - Empty/None input case
   - Single item case
   - Multiple items case
   - Edge cases (zeros, special values)

3. **Run tests to verify they fail**

   ```bash
   pixi run python -m pytest tests/unit/<module>/test_<class>.py -v
   ```

   - Confirm `AttributeError: object has no attribute '<method>'`

### Phase 3: Implementation

1. **Extract helper method**

   ```python
   def _helper_method(self, input_data: dict[K, V]) -> Result:
       """Brief description of what this does.

       Args:
           input_data: Description of the input

       Returns:
           Description of the return value. Explain edge case behavior
           (e.g., "Returns empty Result if input_data is empty").
       """
       from functools import reduce  # Import at function level if needed

       if not input_data:
           return Result()  # Handle empty case

       return reduce(
           lambda a, b: a + b,
           [v.attribute for v in input_data.values()],
           Result(),  # Identity element
       )
   ```

2. **Run tests to verify implementation**

   ```bash
   pixi run python -m pytest tests/unit/<module>/test_<class>.py -v
   ```

   - All new tests should pass

### Phase 4: Refactoring

1. **Update first call site**

   ```python
   # Before:
   from functools import reduce
   result = reduce(
       lambda a, b: a + b,
       [v.attribute for v in data.values()],
       Result(),
   ) if data else Result()

   # After:
   result = self._helper_method(data)
   ```

2. **Update second call site** - Same transformation

3. **Run full test suite**

   ```bash
   pixi run python -m pytest tests/unit/<module>/ -v --tb=short -x
   ```

   - Verify no regressions

### Phase 5: Quality Checks

1. **Run pre-commit hooks**

   ```bash
   pre-commit run --files path/to/modified/files
   ```

   - Fix any formatting issues
   - Address type checking errors

2. **Verify all checks pass**

   ```bash
   pre-commit run --files path/to/modified/files
   ```

### Phase 6: Commit & PR

1. **Stage changes**

   ```bash
   git add path/to/implementation.py tests/unit/path/test_file.py
   ```

2. **Create descriptive commit**

   ```bash
   git commit -m "$(cat <<'EOF'
   refactor(module): Extract duplicate [X] logic

   Extract duplicate [description] from method1() and method2()
   into a new helper method _helper_name().

   This refactoring:
   - Eliminates code duplication (DRY principle)
   - Improves maintainability
   - Provides comprehensive test coverage
   - Maintains identical functionality

   Changes:
   - Add _helper_name() helper method in file.py:LINE1-LINE2
   - Refactor method1() to use new helper (line N)
   - Refactor method2() to use new helper (line M)
   - Add comprehensive unit tests in test_file.py

   All X tests pass with no regressions.

   Closes #ISSUE

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

3. **Push and create PR**

   ```bash
   git push -u origin BRANCH-NAME

   gh pr create \
     --title "refactor(module): Extract duplicate [X] logic" \
     --body "PR_BODY" \
     --label "refactoring"

   gh pr merge --auto --rebase PR_NUMBER
   ```

### Phase 7: Private Module Extraction (NEW in v1.1.0)

When extracting duplicates spans multiple modules, create a **private helper module** with leading-underscore naming:

1. **Place as a leaf module at package root** to avoid circular imports:

   ```text
   hephaestus/
   ├── __init__.py
   ├── _version_lookup.py          # Private helper — leaf module, not a package
   ├── agents/
   ├── utils/
   └── ...
   ```

   **Why not a package?** Private packages (`_internal/`) with `__init__.py` can trigger circular imports if imported from multiple sibling modules that also depend on the package.
   Leaf modules (`_version_lookup.py`) avoid this by having no sub-modules.

2. **Store module-level constants in the helper** — especially PyPI distribution names that must NOT be guessed or normalized:

   ```python
   # hephaestus/_version_lookup.py
   """Internal helper for version resolution via importlib.metadata."""

   from importlib.metadata import PackageNotFoundError, version as _pkg_version

   # CRITICAL: This is the literal [project].name from pyproject.toml
   # importlib.metadata does NOT normalize between distribution and import names
   _DIST_NAME = "HomericIntelligence-Hephaestus"

   def lookup_version() -> str:
       """Resolve package version from installed metadata.

       Returns:
           Version string from most recent git tag, or "unknown" if not found.
       """
       try:
           return _pkg_version(_DIST_NAME)
       except PackageNotFoundError:
           return "unknown"
   ```

3. **Test structure mirroring** — Root-level private modules must have tests in a logical sub-package:

   ```text
   tests/unit/
   ├── version/
   │   ├── __init__.py
   │   └── test_version_lookup.py    # Test for hephaestus/_version_lookup.py
   └── ...
   ```

   **Pre-commit enforcement:** `test_*.py` files CANNOT live directly under `tests/unit/`. They must be in sub-directories that mirror the package structure. This enforces organization and catches orphaned test files.

4. **Cryptographic commit signing requirement** — All commits in PRs must be signed:

   ```bash
   # Commit with mandatory -S flag
   git commit -S -m "refactor: consolidate duplicate version resolution

   Extract duplicated importlib.metadata.version() calls into
   _version_lookup helper module.

   Key learnings:
   - Private modules use leading underscore (_module.py)
   - Store PyPI dist name as module constant (not guessed at runtime)
   - Root-level helpers go in tests/unit/category/ for test organization
   - All commits must be cryptographically signed (-S)
   - pr-policy CI gate validates every commit at GraphQL layer

   Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"

   # Verify commit was actually signed
   git log -1 --pretty=format:'%G?'   # Must print 'G', not 'N' or 'B'
   ```

   **CI validation:** The `pr-policy` required-check gate validates commit signatures at the GraphQL layer before allowing merge. Unsigned commits block auto-merge even if all other checks pass.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Place private helper in a sub-package (`_internal/__init__.py`) | Created `hephaestus/_internal/_version_lookup.py` to group private modules | Triggers circular imports when multiple sibling modules try to import from `_internal`, each bringing their own transitive dependencies that refer back to `_internal` | Use **leaf modules** for private helpers: `_version_lookup.py` (no sub-modules). Packages add layers that create circular paths. |
| Guess PyPI distribution name at runtime from `__name__` or import path | Tried `_dist_name = __name__.split(".")[0]` or `__package__.replace("_", "-").title()` | `importlib.metadata` does NOT normalize distribution names. The name must match the literal `[project].name` value from pyproject.toml exactly. Guessing produced `KeyError` or `PackageNotFoundError`. | Store the PyPI distribution name as a module-level constant in the helper. Do not derive it; it is arbitrary and may differ from the import path. Document the dependency: "Update this constant if [project].name changes in pyproject.toml". |
| Place test for `_version_lookup.py` directly under `tests/unit/` | Created `tests/unit/test_version_lookup.py` | Pre-commit hook `test-file-placement` rejected it — `test_*.py` files cannot live directly under `tests/unit/`. They must be in logical sub-directories that mirror the package structure. | Create `tests/unit/version/` sub-directory and place the test there. This enforces test organization and makes it clear which part of the codebase the test covers. |
| Omit the `-S` flag when committing in a sub-agent dispatch | Ran `git commit -m "..."` without `-S` in a sub-agent shell | The pr-policy CI gate validates commit signatures at the GraphQL layer (via GitHub's `/graphql` API). Commits without valid signatures are flagged as `verification.reason: "unsigned"`, which blocks auto-merge even if all other checks pass. | **Always** use `git commit -S` when creating commits that will be pushed to a PR. The pr-policy gate is non-negotiable for ProjectHephaestus and similar repos. Pre-warm GPG by signing a test commit before agent dispatch if needed. |
| Compare version strings across files to assert "single source" | Wrote drift-check that compared `pyproject.toml` version to `__init__.py` version as strings | After hatch-vcs, `pyproject.toml` no longer has a static `[project].version` field — it declares `dynamic = ["version"]`. String comparisons fail because the field doesn't exist. | Validate the **invariant** (hatch-vcs is configured correctly), not string equality. Check: `dynamic = ["version"]` is present, `[tool.hatch.version].source == "vcs"`. See `hatch-vcs-pyproject-auto-versioning-setup.md` skill. |
## Results & Parameters

### Code Changes

**Files Modified**: 2

- `scylla/e2e/runner.py` - Implementation
- `tests/unit/e2e/test_runner.py` - Tests

**Lines Changed**: +173 / -18

### Test Coverage

**New Tests**: 4 unit tests

- `test_empty_tier_results()` - Empty dict handling
- `test_single_tier_result()` - Single item aggregation
- `test_multiple_tier_results()` - Multi-item aggregation
- `test_zero_token_stats()` - Zero value handling

**Regression Tests**: 467 E2E tests passed

### Helper Method Pattern

```python
def _aggregate_token_stats(self, tier_results: dict[TierID, TierResult]) -> TokenStats:
    """Aggregate token statistics from all tier results.

    Args:
        tier_results: Dictionary mapping tier IDs to their results

    Returns:
        Aggregated token statistics across all tiers. Returns empty
        TokenStats if tier_results is empty.
    """
    from functools import reduce

    if not tier_results:
        return TokenStats()

    return reduce(
        lambda a, b: a + b,
        [t.token_stats for t in tier_results.values()],
        TokenStats(),
    )
```

### Key Implementation Details

1. **Import placement**: `from functools import reduce` inside method
2. **Empty handling**: Explicit check with early return
3. **Identity element**: Empty `TokenStats()` as third parameter to `reduce`
4. **Type hints**: Complete signature with proper types
5. **Docstring**: Clear description with Args and Returns sections

## Success Metrics

| Metric | Value |
| -------- | ------- |
| Duplication eliminated | 2 instances → 1 helper |
| Lines saved | ~15 lines per call site |
| Test coverage | 4 comprehensive tests |
| Regression tests | 467 tests pass |
| Pre-commit checks | All pass |
| Time to implement | ~30 minutes |

## Related Skills

- `token-stats-aggregation` (evaluation) - Token aggregation pattern
- `dry-consolidation-workflow` (architecture) - General consolidation workflow
- `codebase-consolidation` (architecture) - Finding duplicates

## Tags

`refactoring`, `dry-principle`, `helper-methods`, `tdd`, `code-quality`, `python`, `pytest`, `private-modules`, `test-structure`, `git-signing`, `importlib-metadata`

## Version History

- **v1.1.0** (2026-06-04): Added Phase 7 covering private module extraction patterns, test structure mirroring enforcement, cryptographic commit signing, PyPI distribution name handling. Verified via ProjectHephaestus issue #739.
- **v1.0.0** (2026-02-15): Initial release covering token aggregation extraction with TDD workflow.
