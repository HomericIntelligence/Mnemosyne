---
name: dry-refactoring-plan-assumption-audit
description: "Checklist of hidden assumptions that bite DRY module-consolidation plans before implementation starts. Use when: (1) planning to merge two modules into one canonical, (2) replacing a module with a delegation shim, (3) porting tests from one file to another."
category: architecture
date: 2026-06-13
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [dry, refactoring, module-consolidation, planning, assumptions, shim, __all__, packaging]
---

# DRY Refactoring — Plan Assumption Audit

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Capture the hidden assumptions that invalidated parts of the plan for consolidating `hephaestus/scripts_lib/check_python_version_consistency.py` into `hephaestus/validation/python_version.py` (issue #1189) |
| **Outcome** | Plan produced with 5 unverified assumptions identified post-plan; implementation not yet started |
| **Verification** | unverified — plan not yet implemented or CI-confirmed |

## When to Use

- Planning to merge two modules into one canonical module (DRY consolidation)
- Replacing an existing module with a delegation shim that re-exports from the canonical
- Porting test classes from one file to another during a refactor
- Adding new public functions to an existing module within a package
- Extending a `main()` function with new sub-checks
- Adding a `from packaging.version import Version` (or any ecosystem dependency) to a new function

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```bash
# Before writing the plan, run these audits:

# 1. Check __all__ in affected __init__.py files
grep -n "__all__" hephaestus/<package>/__init__.py

# 2. Find early-exit paths in the target main()
grep -n "return\|sys.exit" hephaestus/<module>.py | head -30

# 3. Count test classes in the file being replaced/shimmed
grep -n "^class Test" tests/unit/<path>/test_<module>.py | wc -l

# 4. Verify dependency is declared
grep "packaging" pyproject.toml

# 5. Find all callers of the function being renamed/consolidated
grep -rn "from hephaestus.scripts_lib import\|from hephaestus.validation import" hephaestus/ tests/ scripts/
```

### Detailed Steps

1. **Audit `__all__` in every `__init__.py` that re-exports from the canonical module.**
   Before adding functions to `validation/python_version.py`, read `hephaestus/validation/__init__.py` in full.
   If it has an explicit `__all__`, the new symbols MUST be added or `from hephaestus.validation import new_function` will raise `AttributeError`.

2. **Trace every early-return path in `main()` before extending it.**
   Open the target `main()` function and list every `return` / `sys.exit` statement.
   Any new sub-checks added after the function body must not be gated behind an early exit that already existed (e.g., `if args.json: ... return 0`).
   Each output-mode branch (JSON, plain text, quiet) must invoke the same set of checks.

3. **Count test classes before deciding the shim strategy.**
   If replacing a test file with an import-only shim, verify that the target test file (`tests/unit/<canonical>/test_<module>.py`) already contains equivalent test classes covering every function from the source file.
   Pytest collects zero tests from an import-only shim — the 400+ lines of test classes do not teleport.

4. **Verify runtime dependencies before adding new imports.**
   For any `import X` inside a new function, confirm `X` appears in `[project.dependencies]` in `pyproject.toml`.
   `packaging` is common in the Python ecosystem but not universal — check before assuming.

5. **Resolve same-name, different-signature collisions explicitly.**
   When the source and destination modules both have a function with the same name but different signatures (e.g., `content: str` vs `path: Path`), the plan must list every caller and state exactly which signature each caller uses and how the migration path works.
   "adapt internally" is not specific enough for implementation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Plan written without reading `validation/__init__.py` | Assumed `__all__` either didn't exist or would be auto-updated | `__init__.py` had an explicit `__all__`; new symbols not listed there silently break `from hephaestus.validation import new_function` | Always `Read` every `__init__.py` that re-exports before writing the plan |
| Plan assumed import-only shim satisfies test coverage | Replaced test file body with `from hephaestus.scripts_lib import ...` | pytest collects zero tests from a file with no `class Test` or `def test_` | Count test classes in the source file; verify they exist in destination before shimming |
| Plan extended `main()` without tracing early exits | Added new sub-checks at the bottom of `main()` | Existing `if args.json: ... return 0` exits before reaching the new checks | List all `return`/`sys.exit` in `main()` before adding code; ensure all output modes run all checks |
| Assumed `packaging` is a declared dependency | Used `from packaging.version import Version` in new function | `packaging` is in the ecosystem but may not be in `[project.dependencies]` | `grep packaging pyproject.toml` before adding the import |
| Named new function same as internal helper | Added `extract_classifiers_python_versions(content: str)` next to existing `_CLASSIFIER_VERSION_RE` regex path | Behavior divergence risk: existing tests may rely on the tomllib path (case-sensitive, exact match) while new function uses regex (potentially case-insensitive) | When two code paths handle the same data, write a test that asserts both paths return identical results before merging |

## Results & Parameters

### Assumption Audit Checklist (copy-paste into plan PR description)

```
## Pre-implementation assumption audit

- [ ] Read `hephaestus/<package>/__init__.py` — does `__all__` exist? New symbols listed?
- [ ] Traced all `return`/`sys.exit` in target `main()` — do all output modes reach new checks?
- [ ] Counted test classes in source test file (`grep "^class Test" | wc -l`) — all present in destination?
- [ ] Verified `packaging` in `pyproject.toml [project.dependencies]`
- [ ] Same-name collision resolved: all callers identified, migration path stated explicitly
```

### Issue #1189 Specific Findings

| Assumption | Status | Correct Answer |
|------------|--------|----------------|
| `validation/__init__.py __all__` doesn't need updating | WRONG | Has explicit `__all__`; 8 new symbols must be added |
| `scripts_lib` test shim satisfies coverage | WRONG | Shim has zero test classes; ported tests must live in `tests/unit/validation/test_python_version.py` |
| JSON mode runs all checks | WRONG | `if args.json: ... return 0` exits before new CI sub-checks |
| `packaging` is a declared dependency | UNVERIFIED | Not checked against `pyproject.toml` before plan was written |
| Same-name function collision is safe | UNVERIFIED | `extract_classifiers_python_versions` name used in both modules with different signatures |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planning phase for issue #1189 (python-version-consistency consolidation) | Plan produced 2026-06-13; implementation pending |
