---
name: automation-god-package-shim-first-decomposition
description: >-
  Use when: (1) a flat Python sub-package has grown to 40+ co-located .py files
  (god-package) and needs reorganization into domain sub-packages without breaking
  any existing import sites, (2) planning a shim-first migration where the original
  module paths remain as thin re-export shims after symbols are moved to new
  sub-packages, (3) determining migration ordering for a package with an internal
  import graph (adapters first, orchestrators last), (4) verifying that every
  moved module defines __all__ before relying on wildcard re-exports in shims,
  (5) auditing for circular import risk when shims and moved modules both reference
  each other, (6) decomposing a flat package that is gated behind an optional
  install extra (e.g. [automation]) so the library/product boundary is preserved.
category: architecture
date: 2026-06-12
version: "1.0.0"
user-invocable: false
tags:
  - python
  - refactoring
  - god-package
  - shim-pattern
  - sub-package
  - migration
  - import-compatibility
  - automation
  - flat-to-hierarchical
  - circular-imports
  - __all__
  - optional-extra
---

# Automation God-Package Shim-First Decomposition

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-12 |
| **Objective** | Decompose a 52-file flat god-package (hephaestus/automation/, 25,403 LOC) into 8 domain sub-packages while preserving all existing import sites via backward-compatible shim files |
| **Outcome** | Plan written for ProjectHephaestus issue #1177; NOT YET EXECUTED — all workflow steps are proposals, not verified results |
| **Trigger** | Flat package directory with 40+ .py files, single-level imports from many callers, identifiable domain clusters, optional-extra gating, existing shim proof-of-concept (prompts/) |

## When to Use

Apply this skill when any of the following is true:

- A Python sub-package has **40+ co-located .py files** with distinct domain clusters
- The package is imported by many external callers whose import paths **must not change**
- An existing **shim / re-export proof-of-concept** already exists in the package (e.g., a `prompts/` sub-directory with a backward-compat `prompts.py` shim)
- The package has a **lazy `__getattr__`** in its `__init__.py` and you want to preserve that boundary
- The package is **gated behind an optional install extra** and you must preserve that gate
- You need a **leaf-to-root migration ordering** to avoid creating circular imports during the migration
- You are planning (not yet executing) a migration and need to enumerate **unverified assumptions** for reviewer focus

## Verified Workflow

> **Verification level: unverified** — This workflow was designed during planning for
> ProjectHephaestus issue #1177. It has not been executed. Treat every step as a proposal
> until a "Verified On" entry is added below.

### Quick Reference

```text
Decision tree for flat god-package decomposition:

  40+ flat .py files, identifiable domains?
  └─ YES → Shim-First Migration (this skill)
       ├─ Step 0: Pre-flight checks (run BEFORE any file moves)
       │    ├─ grep -L '__all__' hephaestus/automation/*.py  → must be EMPTY
       │    ├─ grep -rn 'importmode' pyproject.toml           → note actual mode
       │    └─ audit internal relative imports in files to move
       ├─ Step 1: Create domain sub-package directories + __init__.py stubs
       ├─ Step 2: Move modules in leaf-to-root order (adapters first, orchestrators last)
       ├─ Step 3: Convert each original .py to a shim (from .sub.module import * + __all__)
       ├─ Step 4: Run full test suite after EACH move (not batch)
       └─ Step 5: Validate with scripts/validate_plugins.py equivalent (project-specific)

Leaf-to-root ordering for packages with internal import graph:
  adapters/ → claude/ → state/ → reviewers/ → phases/ → planner/ → implementer/
  (imports flow toward right; move left-most first to avoid dangling references)
```

### Step 0: Pre-flight Checks (MUST Run Before Any File Moves)

These checks validate assumptions the shim pattern relies on. Skipping them causes
silent breakage that is hard to diagnose after the fact.

**Check 1: Every module to be moved must define `__all__`**

```bash
# This must produce ZERO output before proceeding
grep -L '__all__' hephaestus/automation/*.py
```

Why: The shim pattern uses `from hephaestus.automation.adapters.github_api import *`.
Without `__all__`, wildcard import exports all names, including private `_` symbols —
worse than the pre-shim state. For any file without `__all__`, either:
- Add an explicit `__all__` before moving, OR
- Use explicit per-symbol re-exports in the shim instead of `*`

**Check 2: Verify the actual pytest `--import-mode` setting**

```bash
grep -A5 '\[tool.pytest.ini_options\]' pyproject.toml | grep -E 'importmode|addopts'
```

Why: The plan assumes `importmode = importlib`. If the project uses the default
`prepend` mode, test file locations within the package matter differently. Confirm
before assuming test files must be moved alongside modules.

**Check 3: Audit internal relative imports for circular-import risk**

For every file X being turned into a shim, check whether any file in the new
sub-package imports from X (which would create a shim→sub-package→shim cycle):

```bash
# For each moved module, check for imports back to the original flat path
module="github_api"
grep -rn "from hephaestus.automation.${module}" hephaestus/automation/adapters/
grep -rn "from \. import ${module}" hephaestus/automation/adapters/
```

**Check 4: Verify shared-ownership claims for borderline files**

Before placing a file at the top level (shared ownership claim), verify by reading it:

```bash
# Verify _stage_context.py is actually imported by both phases/ and implementer/
grep -rn 'stage_context\|_stage_context' hephaestus/automation/
```

**Check 5: Verify re-exported function names exist in moved modules**

If verification criteria reference specific function names (e.g. `call_graphql`,
`run_git`), confirm those names exist in `__all__` before writing the criteria:

```bash
python3 -c "
import ast, pathlib
for f in pathlib.Path('hephaestus/automation').glob('*.py'):
    src = f.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == '__all__':
                    print(f'{f.name}: {ast.literal_eval(node.value)}')
"
```

### Step 1: Map Domain Clusters

Enumerate files by domain cluster before any structural changes:

```bash
# Count and list files by inferred domain prefix
ls hephaestus/automation/*.py | xargs -n1 basename | sort | head -60
wc -l hephaestus/automation/*.py | sort -rn | head -20
```

Proposed sub-packages for a typical automation pipeline package:

| Sub-package | Content | Moved-from patterns |
| ----------- | ------- | ------------------- |
| `adapters/` | External API wrappers (GitHub, git) | `github_api.py`, `git_utils.py`, `graphql_*.py` |
| `claude/` | LLM invocation wrappers | `claude_*.py`, `invoke_*.py` |
| `state/` | Shared state, context, stores | `*_state.py`, `*_context.py`, `*_store.py` |
| `reviewers/` | Code review automation | `reviewer*.py`, `review_*.py` |
| `phases/` | Stage/phase runners | `*_phase*.py`, `stages.py` |
| `planner/` | Planning pipeline | `planner*.py`, `plan_*.py` |
| `implementer/` | Implementation pipeline | `implementer*.py` |
| `ui/` | Terminal/curses UI | `curses*.py`, `*_ui.py` |

**Files that may need shared placement** (borderline): Any file imported by 3+
domain clusters belongs at the top level, not in any single sub-package. Verify
with `grep -rn 'import <filename>' hephaestus/automation/` before deciding.

### Step 2: Create Sub-Package Structure

```bash
# Create each sub-package directory with an empty __init__.py
for subpkg in adapters claude state reviewers phases planner implementer ui; do
    mkdir -p "hephaestus/automation/${subpkg}"
    touch "hephaestus/automation/${subpkg}/__init__.py"
done
```

The `__init__.py` files start empty; they are populated during Step 4.

### Step 3: Move Modules in Leaf-to-Root Order

Move one module at a time. Never move a module before all modules it imports have
already been moved (or are staying at the top level).

```bash
# Example: move github_api.py to adapters/
git mv hephaestus/automation/github_api.py hephaestus/automation/adapters/github_api.py
```

After moving, update the module's own `from . import X` / `from hephaestus.automation.X`
imports to use the new location — but do NOT update callers yet (that's the shim's job).

### Step 4: Create Shim Files

For each moved module, replace the original path with a thin shim:

**Option A: Wildcard shim** (requires `__all__` in moved module — VERIFY FIRST):

```python
# hephaestus/automation/github_api.py  (shim — replaces original)
"""Backward-compatibility shim. Real implementation in adapters/github_api.py."""
# ruff: noqa: F401, F403
from hephaestus.automation.adapters.github_api import *  # noqa: F401, F403
from hephaestus.automation.adapters.github_api import __all__
```

**Option B: Explicit per-symbol shim** (safer; use when `__all__` is absent or opaque):

```python
# hephaestus/automation/github_api.py  (shim — replaces original)
"""Backward-compatibility shim. Real implementation in adapters/github_api.py."""
from hephaestus.automation.adapters.github_api import (  # noqa: F401
    call_graphql as call_graphql,
    get_pr_diff as get_pr_diff,
    # ... enumerate all public symbols
)

__all__ = [
    "call_graphql",
    "get_pr_diff",
    # ...
]
```

Option B is preferred because it:
1. Does not depend on the moved module defining `__all__`
2. Makes the shim's public surface explicit (visible to static analysis)
3. Does not accidentally export private symbols

**The `prompts/` sub-directory** in `hephaestus/automation/` is the existing proof-of-concept
for this pattern (28 symbols, verified working). Examine it before writing the first shim.

### Step 5: Update Sub-Package `__init__.py`

For each sub-package, decide whether to aggregate exports in `__init__.py`:

```python
# hephaestus/automation/adapters/__init__.py
# Option 1: Transparent (no aggregation) — callers must use full path
#   from hephaestus.automation.adapters.github_api import call_graphql

# Option 2: Aggregated — all sub-module symbols accessible at adapters level
from hephaestus.automation.adapters.github_api import (  # noqa: F401
    call_graphql as call_graphql,
)
```

Recommendation: Start with Option 1 (transparent) to minimize the blast radius of
circular import risk. Aggregation in `__init__.py` can be added later.

### Step 6: Run Tests After Each Move

```bash
# After each individual module move + shim creation:
pixi run pytest tests/unit/automation/ -q -x   # stop at first failure
pixi run pytest tests/integration/ -q -x
```

Never batch multiple moves before testing. If a circular import is introduced,
the error will point to the specific shim, not to a confusing multi-file chain.

### Step 7: Verify Backward Compatibility

For each shim, verify the original import path still works:

```bash
python3 -c "
# Verify each original import path still resolves
from hephaestus.automation.github_api import call_graphql
from hephaestus.automation.git_utils import run_git
# etc.
print('All shims resolve correctly')
"
```

### Step 8: Update `test_automation_boundary.py`

Verify the boundary test is not affected by the reorganization:

```bash
# Read the test to confirm LIB_ROOT excludes hephaestus/automation/
grep -n 'LIB_ROOT\|automation' tests/unit/test_automation_boundary.py | head -20
pixi run pytest tests/unit/test_automation_boundary.py -v
```

### Step 9: Final Structural Verification

```bash
# New sub-package directories exist
ls hephaestus/automation/*/

# Original flat .py shims still present
ls hephaestus/automation/*.py | wc -l   # count unchanged or increased

# No wildcard imports (unless __all__ verified)
grep -rn 'from hephaestus.automation.*import \*' hephaestus/automation/*.py

# Full test suite passes
pixi run pytest tests/ -q
pixi run ruff check hephaestus/ tests/
pixi run mypy
```

## Unverified Assumptions (Risks for Reviewer Focus)

These seven assumptions were NOT directly verified during planning for issue #1177.
A reviewer or implementer should check each one before executing the migration.

| # | Assumption | Risk if Wrong | Verification Command |
| --- | ---------- | ------------- | -------------------- |
| 1 | Every moved module defines `__all__` | Wildcard shim exports private `_` symbols | `grep -L '__all__' hephaestus/automation/*.py` — must be empty |
| 2 | `pytest --import-mode=importlib` is the actual mode | `prepend` mode may not require moving test files alongside modules | `grep -A5 '\[tool.pytest.ini_options\]' pyproject.toml` |
| 3 | `_stage_context.py` is imported by both `phases/` and `implementer/` (shared ownership) | It belongs in `implementer/` if only used there | `grep -rn '_stage_context\|stage_context' hephaestus/automation/` |
| 4 | `call_graphql` and `run_git` are exported names in their modules | Verification criterion tests a false green | `python3 -c "from hephaestus.automation.github_api import call_graphql"` (pre-move) |
| 5 | `test_automation_boundary.py` scans only `LIB_ROOT` (excludes automation/) | Reorganization could break boundary test | `grep -n 'LIB_ROOT' tests/unit/test_automation_boundary.py` |
| 6 | No existing internal relative imports within moved files point back at the flat package | Shim circular imports result | Per-file audit: `grep -n 'from hephaestus.automation import\|from \. import' <file>` |
| 7 | Creating `hephaestus/automation/claude/` does not shadow the `claude` top-level CLI | Unlikely, but unverified | `python3 -c "import claude"` before and after (confirm it's a CLI binary, not a Python package) |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A (plan only) | N/A — no execution attempts yet | N/A | All entries in this section are unverified proposals until a "Verified On" entry is added |

## Results & Parameters

### Scale Parameters (ProjectHephaestus issue #1177)

| Parameter | Value |
| ---------- | ----- |
| Source directory | `hephaestus/automation/` |
| Total LOC | 25,403 |
| Total files | 52 flat .py files |
| % of source tree | 54.4% |
| Proposed sub-packages | 8 |
| Existing shim proof-of-concept | `prompts/` sub-directory (28 symbols) |
| Optional-extra gate | `HomericIntelligence-Hephaestus[automation]` |
| Lazy `__getattr__` pattern | `automation/__init__.py` (established pattern) |

### Leaf-to-Root Migration Ordering (Proposed)

```text
Round 1 (no internal deps):   adapters/     — github_api, git_utils, graphql helpers
Round 2 (deps on adapters):   claude/       — LLM invocation wrappers
Round 3 (deps on adapters):   state/        — shared state, stores, context
Round 4 (deps on state):      reviewers/    — review automation
Round 5 (deps on reviewers):  phases/       — stage/phase runners
Round 6 (deps on phases):     planner/      — planning pipeline
Round 7 (deps on planner):    implementer/  — implementation pipeline (largest)
Shared (top-level stays):     top-level     — _stage_context.py, any file with 3+ importers
```

### Shim Template (Explicit Variant — Preferred)

```python
"""Backward-compatibility shim for <module_name>.

Real implementation: hephaestus.automation.<subpkg>.<module_name>
This file is retained so existing import sites need no changes.
"""
# ruff: noqa: F401
from hephaestus.automation.<subpkg>.<module_name> import (
    PublicClass as PublicClass,
    public_function as public_function,
    PUBLIC_CONSTANT as PUBLIC_CONSTANT,
)

__all__ = [
    "PublicClass",
    "public_function",
    "PUBLIC_CONSTANT",
]
```

### Shim Template (Wildcard Variant — Only When `__all__` Verified)

```python
"""Backward-compatibility shim for <module_name>.

Real implementation: hephaestus.automation.<subpkg>.<module_name>
REQUIRES: hephaestus.automation.<subpkg>.<module_name> defines __all__
"""
# ruff: noqa: F401, F403
from hephaestus.automation.<subpkg>.<module_name> import *  # noqa: F401, F403
from hephaestus.automation.<subpkg>.<module_name> import __all__
```

### Pre-Flight Checklist (Copy-Paste)

```bash
# 1. All modules define __all__ (must produce ZERO output)
grep -L '__all__' hephaestus/automation/*.py

# 2. pytest import mode
grep -A5 '\[tool.pytest.ini_options\]' pyproject.toml | grep -E 'importmode|addopts'

# 3. _stage_context.py importers
grep -rn '_stage_context\|stage_context' hephaestus/automation/ | grep -v '_stage_context.py'

# 4. call_graphql export name
python3 -c "from hephaestus.automation.github_api import call_graphql; print('OK')"

# 5. boundary test scope
grep -n 'LIB_ROOT\|automation' tests/unit/test_automation_boundary.py | head -20

# 6. claude/ sub-package shadow risk
python3 -c "import claude; print(type(claude), getattr(claude, '__file__', 'no __file__'))"
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Plan written for issue #1177 (not yet executed) | Verification level: unverified; all workflow steps are proposals |

## References

- [ProjectHephaestus issue #1177](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1177) — source issue for this skill
- [python-module-decomposition-and-refactor-patterns.md](python-module-decomposition-and-refactor-patterns.md) — single-module decomposition (Phase 11/12 for CLI extraction and sibling-cycle fixes)
- [python-circular-import-symbol-extraction.md](python-circular-import-symbol-extraction.md) — leaf-module extraction for circular import errors
