---
name: dry-refactoring-plan-assumption-audit
description: "Checklist of hidden assumptions that bite DRY module-consolidation and shim-collapse plans before implementation starts. Use when: (1) planning to merge two modules into one canonical, (2) replacing a module with a delegation shim that re-exports from the canonical, (3) porting tests from one file to another, (4) extending a main() function with new sub-checks, (5) consolidating two functions with the same name but different signatures, (6) the issue proposes BUILDING a delegation mechanism (__getattr__, frozenset, orchestrator) that a prior refactor may already have shipped."
category: architecture
date: 2026-06-30
version: "2.2.0"
user-invocable: false
verification: unverified
history: dry-refactoring-plan-assumption-audit.history
tags: [dry, refactoring, module-consolidation, planning, assumptions, shim, __all__, packaging, test-delegation, signature-collision, getattr, test-seam, stale-mechanism]
---

# DRY Refactoring — Plan Assumption Audit

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Capture the hidden assumptions that invalidated parts of the plan for consolidating `hephaestus/scripts_lib/check_python_version_consistency.py` into `hephaestus/validation/python_version.py` (issue #1189) |
| **Outcome** | Plan produced; NOGO on first version; revised plan addresses all 5 failure modes |
| **Verification** | unverified — plan not yet implemented or CI-confirmed |
| **History** | v1.0.0: initial 5-assumption capture. v2.0.0: revised with concrete fix patterns for signature collision and test delegation. v2.1.0: add R2 findings — DOTALL regex crosses TOML sections, wrong test count stated in plan. v2.2.0 (planning-only, unverified): add stale-PROPOSED-MECHANISM failure mode + test-seam survival verification + scope-out-the-risky-half pattern (issue #1439). See [changelog](./dry-refactoring-plan-assumption-audit.history). |

## When to Use

- Planning to merge two modules into one canonical module (DRY consolidation)
- Replacing an existing module with a delegation shim that re-exports from the canonical
- Porting test classes from one file to another during a refactor
- Adding new public functions to an existing module within a package
- Extending a `main()` function with new sub-checks
- Adding a `from packaging.version import Version` (or any ecosystem dependency) to a new function
- Two modules share a function name with different signatures
- Extracting values from structured config files (TOML, YAML) using regex — always verify section-boundary behavior with a cross-section test case
- **The issue proposes inventing a delegation mechanism (`__getattr__` forwarding, a delegate `frozenset`, an "extract an Orchestrator/Coordinator") — grep the target module first; a PRIOR refactor may already have built it, making the real work an EXTENSION, not an invention**
- The refactor's safety rests on a Python-semantics claim about `mock`/`patch.object` interacting with `__getattr__`/`__getattribute__`/descriptors — prove it with a runnable snippet and find the existing regression test that already locks it in
- The issue bundles a cheap-safe change with an expensive-risky one (e.g., "collapse shims" AND "introduce a second coordinator class") — quantify the coupling and decline the risky half in-plan with the numbers

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

# 6. Find same-name functions across both modules
grep -rn "^def <function_name>" hephaestus/<module_a>.py hephaestus/<module_b>.py

# 7. STALE-MECHANISM CHECK — does the mechanism the issue tells you to BUILD already exist?
#    (a prior refactor may have shipped it; the real work is then EXTENSION, not invention)
grep -n "__getattr__\|DELEGATE\|_LAZY\|frozenset\|Orchestrator\|Coordinator" <target.py>

# 8. Re-derive the wrapper COUNT from disk — do NOT trust the count in the issue body
grep -nE "^    def _[a-z_]+\(self" <target.py> | wc -l   # explicit shims still present

# 9. Quantify the back-reference coupling before accepting a "extract a second coordinator" ask
grep -con "self\._log\|self\._save_state\|impl\._log\|impl\._save_state" <target.py>
```

### Detailed Steps

1. **Audit `__all__` in every `__init__.py` that re-exports from the canonical module.**
   Before adding functions to `validation/python_version.py`, read `hephaestus/validation/__init__.py` in full.
   If it has an explicit `__all__`, the new symbols MUST be added or `from hephaestus.validation import new_function` will raise `AttributeError`.

2. **Trace every early-return path in `main()` before extending it.**
   Open the target `main()` function and list every `return` / `sys.exit` statement.
   Any new sub-checks added must not be gated behind an early exit that already existed (e.g., `if args.json: ... return 0`).
   Fix: move ALL check calls before the format-branching block, then use results in both JSON and text paths.
   Each output-mode branch (JSON, plain text, quiet) must invoke the same set of checks.

3. **Test delegation shims must import test CLASSES, not just symbols.**
   If replacing a test file with an import-only shim, the shim must import the test **classes** themselves:
   ```python
   # CORRECT: pytest re-discovers imported test classes at module scope
   from tests.unit.validation.test_python_version import TestFoo, TestBar

   # WRONG: pytest collects zero tests from import-only shims of non-test symbols
   from hephaestus.scripts_lib.check_python_version_consistency import extract_pyproject_versions
   ```
   Count `grep "^class Test" | wc -l` in the source test file; verify they all exist in the destination before shimming.

4. **Verify runtime dependencies before adding new imports.**
   For any `import X` inside a new function, confirm `X` appears in `[project.dependencies]` in `pyproject.toml`.
   `packaging` is common in the Python ecosystem but not universal — check before assuming.

5. **When two modules share a function name with incompatible signatures, add a new name — do not alias.**
   If the canonical module has `extract_pyproject_versions(path: Path)` and the source module has
   `extract_pyproject_versions(content: str)`, a shim alias re-exporting the path version under the
   string name causes silent behavioral regression: `"".is_file()` returns `False`, so every
   string-content call returns `{}`.

   Fix pattern:
   - Keep `extract_pyproject_versions(path: Path)` unchanged for existing callers in the canonical module.
   - Extract a private helper `_extract_versions_from_text(content: str)` that both implementations delegate to.
   - Add a new public function `extract_pyproject_versions_str(content: str)` in the canonical module that
     calls `_extract_versions_from_text`.
   - In the shim, alias `extract_pyproject_versions_str as extract_pyproject_versions` so the source module's
     callers get the string-based version without renaming their calls.
   - Add both names to `__all__` in `validation/__init__.py`.

   ```python
   # canonical module (validation/python_version.py)
   def _extract_versions_from_text(content: str) -> dict[str, ...]:
       """Shared implementation — used by both public entry points."""
       ...

   def extract_pyproject_versions(path: Path) -> dict[str, ...]:
       """Existing callers use this; unchanged."""
       content = path.read_text()
       return _extract_versions_from_text(content)

   def extract_pyproject_versions_str(content: str) -> dict[str, ...]:
       """New entry point for callers that already have the file content."""
       return _extract_versions_from_text(content)

   # shim (scripts_lib/check_python_version_consistency.py)
   from hephaestus.validation.python_version import (
       extract_pyproject_versions_str as extract_pyproject_versions,  # preserve caller contract
       ...
   )
   ```

6. **(planning-only — unverified) Audit whether the issue's PROPOSED MECHANISM already exists before designing it.**
   A refactoring issue's *proposed solution* can be as stale as its evidence/counts. Before planning to
   "build" a delegation mechanism, grep the target for it:
   ```bash
   grep -n "__getattr__\|DELEGATE\|_LAZY\|frozenset\|Orchestrator\|Coordinator" <target.py>
   ```
   If a prior PR already shipped `__getattr__` forwarding plus a `_..._DYNAMIC_DELEGATES` frozenset, the real
   work is **extending the existing mechanism to the remaining explicit shims**, not inventing it. Re-derive the
   wrapper COUNT from disk (`grep -nE "^    def _[a-z_]+\(self" | wc -l`) — the count in the issue body is a
   snapshot and is frequently wrong (e.g., "25" when only 18 explicit shims remain because earlier ones were
   already collapsed).

7. **(planning-only — unverified) Empirically verify the test-seam survival claim before relying on it.**
   When a refactor's safety rests on "`patch.object(obj, '_method')` still intercepts a method now resolved via
   `__getattr__`," prove it with a runnable snippet AND find the pre-existing regression test that locks it in.
   `patch.object` sets an *instance attribute* that shadows `__getattr__` for the duration of the context and is
   deleted/restored on `__exit__`, so ~all existing `patch.object` call sites keep working with zero edits. Look
   for an existing test like `test_patch_object_still_intercepts_dynamic_delegate`; if one exists, the seam is
   already locked in.

8. **(planning-only — unverified) Scope OUT the high-risk half of a multi-part proposal with grep-counted evidence, not assertion.**
   When an issue bundles a cheap-safe change (collapse shims into `__getattr__`) with an expensive-risky one
   ("extract a second Orchestrator/Coordinator"), quantify the coupling before accepting the risky half. If the
   facade is the context object every SRP collaborator references back through (`impl._log` 35×, `impl._save_state`
   18×, plus `state_mgr`/`worktree_manager`/`status_tracker`/`options`), a second coordinator forces rewriting that
   back-reference woven through every phase and `StageContext`. Decline it in-plan with the numbers rather than
   attempting it to satisfy the issue text.

9. **(planning-only — unverified) A `== EXACT_SET` contract test is the real migration cost when the seam is preserved.**
   Because the seam survives, ~150 `patch.object` call sites need ZERO changes; the only test churn is one
   exact-set assertion (`PHASE_DELEGATES == _PHASE_RUNNER_DYNAMIC_DELEGATES`). This localizes the migration to a
   single source of truth but MUST be updated in lockstep with the delegate set or it goes red — a feature, not a
   burden.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Plan claimed "no signature change needed" | Shim re-exported `extract_pyproject_versions(path)` under the same name as the source module's `extract_pyproject_versions(content)` | `"".is_file()` returns `False`; every string-content caller received `{}` silently | When same-name collision exists, a shim alias at the wrong layer is a silent regression — add a new name instead |
| Import-only test shim | Replaced test file body with `from hephaestus.scripts_lib import extract_pyproject_versions` | pytest collects zero tests; 400+ lines of test classes do not teleport via non-test symbol imports | Test delegation shims must import test classes: `from tests.unit.validation.test_python_version import TestFoo, TestBar` |
| Added new sub-checks after `if args.json:` | Placed new `check_*` calls after an existing `if args.json: ...; return 0` block | JSON callers exit before reaching the new checks; CI never sees the new coverage | List all early exits in `main()` first; move check calls above the format-branching block |
| Did not update `validation/__init__.py __all__` | Added 8+ new functions to `python_version.py` without updating the package's `__init__.py` | `from hephaestus.validation import new_function` raises `AttributeError` even though the function exists | Grep all `__init__.py` files that import from the modified module; add every new symbol to `__all__` |
| Assumed `packaging` is a declared dependency | Used `from packaging.version import Version` in a new function | `packaging` may not be in `[project.dependencies]`; runtime `ImportError` on CI | `grep packaging pyproject.toml` before adding the import |
| R2 — DOTALL regex crosses TOML sections | Ported `_extract_versions_from_text` inherited `re.DOTALL` from `_extract_via_regex:113`. With DOTALL, `\[tool\.mypy\].*?python_version` lazy-matches past blank lines and `[tool.other]` headers — `test_mypy_version_not_crossed_from_other_section` fails. | Fix: use scripts_lib's section-bounded negative-lookahead `\[tool\.mypy\]\n(?:(?!\[).+\n)*?python_version` instead. `_extract_via_regex` now delegates to `_extract_versions_from_text`, eliminating the DOTALL regex entirely. | Always use section-bounded negative-lookahead `(?:(?!\[).+\n)*?` for TOML section extraction — never `re.DOTALL` across sections. |
| R0/R1 — Wrong test count stated as "44" | Plans stated "44 test functions" but actual scripts_lib test file has 35 functions / 9 classes. | Count test functions by direct grep before writing the plan (`grep -c "def test_" file`). | Verify counts by reading the actual file before stating them in a plan. |
| #1439 (planning-only) — Issue's PROPOSED MECHANISM was already shipped | Issue #1439 proposed "replace 25 wrappers with `__getattr__` forwarding" and "extract an Orchestrator" — treating both as net-new work. | `__getattr__` forwarding + a `_PHASE_RUNNER_DYNAMIC_DELEGATES` frozenset ALREADY existed (prior PRs #714/#597); the "25" count was stale (only ~18 explicit shims remained). Designing the mechanism from scratch would have duplicated existing code. | Before planning a refactor, grep the target for the proposed mechanism (`grep -n "__getattr__\|DELEGATE\|_LAZY\|frozenset"`) and re-derive counts from disk. The real work is often EXTENSION, not invention. |
| #1439 (planning-only) — Bundled high-risk half accepted by assertion | The issue also asked for a second coordinator class (`ImplementerOrchestrator`); a naive plan would attempt it to satisfy the text. | The facade is the context object all 5 SRP phase-collaborators reference back through (`impl._log` 35×, `impl._save_state` 18×, + `state_mgr`/`worktree_manager`/`status_tracker`/`options`); a second coordinator forces rewriting that back-reference through every phase + `StageContext`. | Quantify coupling with grep counts and DECLINE the risky half in-plan with the numbers; don't attempt it just because the issue bundled it with a cheap-safe change. |
| #1439 (planning-only) — UNVERIFIED "no new mypy errors / no orphaned imports" | Plan asserted that deleting 18 typed shim methods leaves no mypy errors or orphaned imports, relying on `__getattr__ -> Any` being the established pattern. | NOT verified — pytest/ruff/mypy were never run against the change; a deleted method's type import can become unused, and line numbers (586–785) are a snapshot that WILL drift. | Treat "no new type errors after deletion" as a RISK, not a fact, until `ruff check` + `mypy` actually run post-deletion; re-confirm shim bodies/line ranges on disk immediately before editing (stale-anchor guard). |

## Results & Parameters

### Assumption Audit Checklist (copy-paste into plan PR description)

```
## Pre-implementation assumption audit

- [ ] Read `hephaestus/<package>/__init__.py` — does `__all__` exist? New symbols listed?
- [ ] Traced all `return`/`sys.exit` in target `main()` — do all output modes reach new checks?
- [ ] Counted test classes in source test file (`grep "^class Test" | wc -l`) — shim imports test classes (not symbols)?
- [ ] Verified `packaging` in `pyproject.toml [project.dependencies]`
- [ ] Same-name collision resolved: path-vs-string identified, `_extract_versions_from_text` helper added, shim aliases new name?
```

### Issue #1189 Specific Findings

| Assumption | Status | Correct Answer |
|------------|--------|----------------|
| `validation/__init__.py __all__` doesn't need updating | WRONG | Has explicit `__all__`; 9 new symbols must be added |
| `scripts_lib` test shim satisfies coverage | WRONG | Shim must import test classes; zero tests collected from symbol-only imports |
| JSON mode runs all checks | WRONG | `if args.json: ... return 0` exits before new CI sub-checks; move checks before branch |
| `packaging` is a declared dependency | UNVERIFIED | Not checked against `pyproject.toml` before plan was written |
| Same-name `extract_pyproject_versions` collision is safe to shim | WRONG | `path: Path` vs `content: str` — shim at wrong layer returns `{}` silently; fix = `extract_pyproject_versions_str` + `_extract_versions_from_text` helper |

### Issue #1439 Specific Findings (planning-only — unverified)

> Added in v2.2.0. This is a planning artifact: no code was executed against the repo change.
> A 12-line Python semantics-probe snippet was run to confirm `patch.object` vs `__getattr__`,
> but that snippet does NOT validate the #1439 refactor itself.

| Assumption (from issue #1439) | Status | Correct Answer |
|-------------------------------|--------|----------------|
| Must BUILD `__getattr__` forwarding + a delegate frozenset | WRONG | Already shipped by prior PRs #714/#597 (`_PHASE_RUNNER_DYNAMIC_DELEGATES`); real work = EXTEND to ~18 remaining explicit shims |
| "25 wrappers" to collapse | WRONG | Only ~18 explicit shims remain (others already collapsed); re-derive count from disk |
| Should also extract an `ImplementerOrchestrator` | DECLINED IN-PLAN | Facade is the back-reference context for 5 collaborators (`impl._log` 35×, `impl._save_state` 18×); second coordinator would rewrite every phase + `StageContext` — high risk, scoped out |
| `patch.object(impl, '_method')` still intercepts via `__getattr__` | VERIFIED (snippet + existing test) | `patch.object` sets a shadowing instance attr restored on `__exit__`; `test_patch_object_still_intercepts_dynamic_delegate` already locks it in; ~150 call sites need ZERO edits |
| No new mypy errors / no orphaned imports after deleting 18 typed methods | UNVERIFIED | ruff/mypy never run; reviewer/implementer MUST run them post-deletion — a deleted method's type import can become unused |
| Shim bodies are pure 1:1 forwards; line range 586–785 | SNAPSHOT — WILL DRIFT | Read once; plan flags a re-confirm-on-disk step before editing (stale-anchor guard) |
| `executor.submit(self._implement_issue, ...)` binds identically via `__getattr__` at submit time | ASSERTED, NOT EXERCISED | Behavior-identical claim not validated by running the suite |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planning phase for issue #1189 (python-version-consistency consolidation) | v1.0.0 plan NOGO'd; v2.0.0 revised plan addresses all 5 failure modes; implementation pending |
| ProjectHephaestus | Planning phase for issue #1439 (collapse explicit phase-runner shims in `implementer.py` into existing `__getattr__` delegation) | v2.2.0 planning-only/unverified: stale-PROPOSED-MECHANISM trap, test-seam survival verified by snippet + existing regression test, second-coordinator half scoped out with grep-counted coupling; pytest/ruff/mypy NOT run |
