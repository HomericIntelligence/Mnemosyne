---
name: automation-god-package-shim-first-decomposition
description: "Reorganize a flat Python god-package or consolidate always-co-imported modules without breaking imports. Use for shim-first moves, leaf-to-root ordering, __all__ audits, optional-extra boundaries, circular-import review, and whole-suite patch-seam migration."
category: architecture
date: 2026-07-04
version: "3.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: automation-god-package-shim-first-decomposition.history
tags:
  - python
  - refactoring
  - god-package
  - shim
  - imports
  - circular-imports
  - patch-seam
  - optional-extra
---

# Automation God-Package Shim-First Decomposition

## Overview

Move implementation to canonical domain modules while keeping old import paths as thin explicit
re-export shims. Order moves from leaves to orchestrators, audit every import and patch lookup, and
run the whole affected test tree after each slice. The same discipline supports the inverse move:
consolidating a small, always-co-imported cluster into one canonical module.

The small merge and three-module split were verified locally; the proposed 52-file decomposition
was not executed. Case details are in
[automation-god-package-shim-first-decomposition.notes.md](automation-god-package-shim-first-decomposition.notes.md),
and the complete prior version is in
[automation-god-package-shim-first-decomposition.history](automation-god-package-shim-first-decomposition.history).

## When to Use

- A flat package has dozens of co-located modules with recognizable domain clusters.
- Several tiny modules are always imported together and should share one canonical implementation.
- Existing public/internal import paths must remain compatible during migration.
- Tests patch flat module paths and may depend on where moved code resolves a symbol.
- Wildcard shims are proposed without complete and correctly sorted `__all__` declarations.
- Moved modules may import back through the old flat package and create cycles.
- The package is gated by an optional extra whose boundary must remain intact.
- A new subpackage name could shadow an existing module such as `claude.py`.

## Verified Workflow

### 1. Inventory the package and import graph

```bash
find src/package/automation -maxdepth 1 -name '*.py' -print | sort
rg -n 'from package\.automation|import package\.automation' src tests
rg -L '^__all__\s*=' src/package/automation/*.py
```

Record file count, public symbols, internal/private consumers, optional-extra configuration, and
test import mode. Detect proposed directory/module name collisions before creating paths.

Map dependencies and move cycle-free adapters/data leaves before coordinators. A module that imports
the orchestrator is not a leaf even if its filename looks low-level.

### 2. Choose split or consolidation deliberately

- Split when a large flat package contains stable domain clusters and import direction can be made
  hierarchical.
- Consolidate when three or four tiny modules are always co-imported and one canonical owner reduces
  duplication.

Do not combine both directions for unrelated clusters in one review unit. Keep each slice
independently reversible.

### 3. Move implementation and add explicit shims

Preferred shim:

```python
"""Compatibility exports; implementation lives in `.state.review`."""

from .state.review import ReviewState as ReviewState
from .state.review import load_review as load_review

__all__ = ["ReviewState", "load_review"]
```

Explicit `name as name` exports communicate intentional re-export and avoid F401. Let Ruff sort
`__all__` (`RUF022`); comment-grouped ordering is not a reason to fight the canonical sorter.

Use a wildcard shim only when the canonical module defines a complete `__all__` and the repository
explicitly accepts `F401,F403` at that compatibility boundary. Never introduce a blanket file-level
suppression when explicit exports suffice; RUF100 will reject unused suppressions.

### 4. Retarget internal imports without deleting compatibility

Canonical internal code should import canonical modules so the new hierarchy is real. External or
legacy callers may remain on shims during deprecation. Preserve the optional-extra boundary: moving
files must not make top-level library imports eagerly load optional automation dependencies.

After every move, import the old and new paths and prove exported identity:

```bash
python -c 'from package.automation.review_state import ReviewState as old; from package.automation.state.review import ReviewState as new; assert old is new'
```

### 5. Sweep patch seams across the entire test tree

```bash
rg -n 'patch\(|patch\.object|monkeypatch|caplog|importlib\.reload' tests
rg -n 'package\.automation\.(old_module|new_package)' tests
```

Patch where the runtime caller looks up the object:

- canonical moved code calling a sibling uses the canonical target;
- code still executing in the flat module uses the shim target;
- a symbol imported into another module is patched in that consumer;
- reload and `caplog` logger names follow the canonical implementation module.

A shim preserves imports, not arbitrary mocking semantics. Run the whole test tree because a moved
function can be reached transitively from tests outside its original module.

### 6. Validate boundaries and cycles

Read the boundary test before updating it. Confirm its root and exclusions actually include the
new path. Search for canonical modules importing their shims or orchestrators; then execute import
smoke tests, Ruff, type checking, focused tests, and the full automation suite.

### 7. Migrate incrementally

For each leaf-to-root slice:

1. create the canonical package/module;
2. move one implementation unit;
3. add explicit old-path shim;
4. update canonical internal imports;
5. repair all patch/logger/reload seams;
6. run identity, cycle, lint, type, focused, and full-suite checks;
7. commit before proceeding to the next dependency layer.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Move many modules before testing | Import and patch failures become hard to attribute | Move one dependency layer at a time |
| 2 | Use wildcard shims without audited `__all__` | Private or missing names leak unpredictably | Prefer explicit re-exports |
| 3 | Add file-level F401/F403 suppression to explicit shim | Suppression is unused and RUF100 fails | Use `name as name` without noqa |
| 4 | Keep canonical modules importing old shims | Creates cycles and defeats hierarchy | Internal code imports canonical leaves |
| 5 | Patch only the moved module's nearest tests | Transitive tests retain stale lookup paths | Sweep the entire test tree |
| 6 | Assume old patch path follows moved function | Canonical call no longer resolves through shim | Patch the runtime lookup location |
| 7 | Update a boundary allowlist without reading the test | Test may enforce another root or direction | Verify the executable invariant first |
| 8 | Move optional package imports upward | Base install starts requiring optional dependencies | Preserve lazy/extra boundary |

## Results & Parameters

- Proposed full split: 52 flat files into eight domain subpackages; remains unverified.
- Verified merge: three modules became explicit shims over one canonical module; Ruff, mypy, and 145
  focused tests passed locally.
- Verified split: three `*_state.py` modules moved under `state/`; Ruff, mypy, and 2,284 automation
  tests passed locally after four stale patch seams were repaired.
- Patch-seam corollary: a 41-test automation-loop suite passed locally after targeting runtime
  lookup locations.
- Preferred compatibility contract: explicit re-export, sorted `__all__`, identity smoke test.

## Evidence Boundary

Issues #1441, #1443, and #1813 provide local execution evidence only. Issue #1177's large-scale
52-file/eight-subpackage plan is unverified and should be re-inventoried before use.
