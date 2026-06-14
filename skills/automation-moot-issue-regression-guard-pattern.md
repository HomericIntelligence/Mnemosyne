---
name: automation-moot-issue-regression-guard-pattern
description: "Use when a follow-up or auto-generated issue's concrete premises (file names, class names, function names, PR references) do not match the actual codebase state — i.e. the code described never existed or was never merged. Instead of fabricating the missing modules (YAGNI/KISS violation) or closing with no artifact, convert the already-satisfied invariant into a machine-checkable regression-guard test using ast.parse. Use when: (1) every grep for issue-cited symbols returns zero hits; (2) the upstream PR the issue references does not exist (gh pr view → 'Could not resolve'); (3) the issue describes a refactor across modules that a grep confirms live in only one place already; (4) implementing the literal request would create dead code or phantom modules."
category: testing
date: 2026-06-14
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - moot-issue
  - false-premise
  - auto-generated
  - follow-up-issue
  - regression-guard
  - ast-parse
  - dry-invariant
  - yagni
  - dead-code
  - premise-verification
---

# Moot Issue → AST Regression-Guard Pattern

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-14 |
| **Objective** | Handle auto-generated follow-up issues whose every concrete premise (class names, file names, PR numbers, duplication claims) is false against the actual codebase — without fabricating dead code or closing with no CI artifact |
| **Outcome** | Successful — PR #1346 shipped 2 regression-guard tests that assert the already-satisfied DRY invariant is preserved permanently |
| **Verification** | verified-ci |

Auto-generated follow-up issues (e.g., issues spawned from PR review threads of PRs that were
never merged) describe code that does not exist. A planner that trusts the issue body will either:

1. **Fabricate the missing modules** — creating dead code that the codebase never needed (YAGNI/KISS violation).
2. **Close with no artifact** — leaving the "already-satisfied" invariant unchecked; a future PR can re-introduce the duplication with zero CI gate.

The correct response is a third path: **verify premises first, then convert the already-satisfied
invariant into an AST-level regression guard** that fails CI if the invariant is ever violated.

## When to Use

- An issue's body names specific files (`ci_check_inspector.py`, `pr_discovery.py`) or classes
  (`CICheckInspector`) that yield zero results from `grep -rln` across the whole repo.
- An issue references "Fixes #N" or "Follow-up from #N" but `gh pr view N` returns
  `"Could not resolve to a PullRequest"` — the upstream PR was never merged.
- The issue claims a symbol (`FAILING_CHECK_CONCLUSIONS`, `_pr_is_failing`) is defined in
  multiple places, but `grep -rn "def _pr_is_failing\|FAILING_CHECK_CONCLUSIONS\s*="` finds
  exactly one definition.
- Implementing the literal request (creating `pr_predicates.py`, `ci_check_inspector.py`, etc.)
  would introduce modules with no callers — dead code by construction.
- The issue describes a DRY refactor (consolidate N definitions into 1), but there is already
  exactly 1 definition.

## Verified Workflow

### Quick Reference

```bash
# 1. Verify every cited file, class, function, and PR against reality
grep -rln "CICheckInspector" hephaestus/     # → 0 results → class does not exist
grep -rln "ci_check_inspector" hephaestus/   # → 0 results → file does not exist
gh pr view 1289                               # → "Could not resolve to a PullRequest"

# 2. Verify the DRY claim: count actual definitions
grep -rn "FAILING_CHECK_CONCLUSIONS\s*=" hephaestus/   # → exactly 1 hit
grep -rn "^def _pr_is_failing" hephaestus/             # → exactly 1 hit

# 3. Identify the one true definition's home file
grep -rln "FAILING_CHECK_CONCLUSIONS\s*=" hephaestus/  # → hephaestus/automation/ci_driver.py

# 4. Write AST regression-guard tests that assert the invariant is maintained
# (see pattern below)

# 5. Run the tests to confirm they pass and cover the invariant
pixi run pytest tests/unit/automation/test_ci_gate.py -v -k "SingleDefinition"
```

### Detailed Steps

#### Step 1 — Verify every concrete premise before writing a single line of code

For every named entity in the issue body (files, classes, functions, constants, PRs):

```bash
# Check files
grep -rln "<cited_filename>" hephaestus/
# Check classes
grep -rn "class <CitedClass>" hephaestus/
# Check functions
grep -rn "def <cited_function>" hephaestus/
# Check constants
grep -rn "<CITED_CONSTANT>\s*=" hephaestus/
# Check upstream PR
gh pr view <N> --json number,state,title 2>&1
```

If **every** check returns zero hits or a resolution error, the issue's premises are false.
Stop here. Do not start any implementation.

#### Step 2 — Verify the actual state of the invariant

The issue asserts some invariant (e.g., "this symbol is duplicated in 3 places; consolidate").
Measure the actual state:

```bash
# Count definitions — the "consolidation" may already be done
grep -rn "^def <function_name>" hephaestus/ | wc -l          # count function defs
grep -rn "<CONSTANT_NAME>\s*=" hephaestus/ --include="*.py"  # count assignments
```

If the count is already 1 (or otherwise satisfies the issue's desired end-state), the invariant
is satisfied but there is no CI gate preventing future drift.

#### Step 3 — Write AST regression-guard tests

Use `ast.parse` (not regex or grep) to scan the package and assert the already-satisfied
invariant. `ast.parse` handles renames, is immune to comment noise, and is self-documenting.

```python
import ast
from pathlib import Path
import pytest


class TestFailingCheckPredicateSingleDefinition:
    """Regression guard: assert each predicate/constant has exactly ONE definition
    in the automation package. Failure here means a future PR introduced duplication
    that violates the DRY invariant this issue was filed to protect."""

    _AUTOMATION_DIR = Path(__file__).parents[3] / "hephaestus" / "automation"

    def _count_assignments(self, target: str) -> list[Path]:
        """Return paths of automation modules that assign to *target* at module level."""
        hits: list[Path] = []
        for py_file in self._AUTOMATION_DIR.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name) and t.id == target:
                            hits.append(py_file)
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Name) and node.target.id == target:
                        hits.append(py_file)
        return hits

    def _count_function_defs(self, name: str) -> list[Path]:
        """Return paths of automation modules that define a function named *name*."""
        hits: list[Path] = []
        for py_file in self._AUTOMATION_DIR.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == name:
                    hits.append(py_file)
        return hits

    def test_failing_check_conclusions_defined_exactly_once(self) -> None:
        """FAILING_CHECK_CONCLUSIONS must have exactly one module-level assignment."""
        hits = self._count_assignments("FAILING_CHECK_CONCLUSIONS")
        assert len(hits) == 1, (
            f"Expected exactly 1 definition of FAILING_CHECK_CONCLUSIONS, "
            f"found {len(hits)}: {[str(p) for p in hits]}"
        )
        assert hits[0].name == "ci_driver.py"

    def test_pr_is_failing_defined_exactly_once(self) -> None:
        """_pr_is_failing must have exactly one function definition."""
        hits = self._count_function_defs("_pr_is_failing")
        assert len(hits) == 1, (
            f"Expected exactly 1 definition of _pr_is_failing, "
            f"found {len(hits)}: {[str(p) for p in hits]}"
        )
        assert hits[0].name == "ci_driver.py"
```

**Key choices in the AST pattern:**

- `ast.parse` + `ast.walk` over `rglob("*.py")` — no hardcoded paths, scans the whole package
- Catches both `ast.Assign` (bare `X = ...`) and `ast.AnnAssign` (typed `X: T = ...`)
- Asserts both the COUNT (exactly 1) and the HOME FILE (must be in `ci_driver.py`)
- The assertion message includes the list of violating files, so CI output is actionable
- SyntaxError catch is defensive — a broken `.py` file should not suppress the guard

#### Step 4 — Place the tests in the appropriate existing test class

Do not create a new test file unless there is truly no appropriate existing class.
Look for the test class that already covers the module containing the one true definition:

```bash
# Find the test file for the canonical module
grep -rln "ci_driver\|CiDriver" tests/unit/
```

Add the new test class to that file, or as a new class in the nearest-scope test module.

#### Step 5 — Verify and document

```bash
# Confirm the guard tests pass (invariant currently satisfied)
pixi run pytest tests/unit/automation/test_ci_gate.py::TestFailingCheckPredicateSingleDefinition -v

# Confirm the full suite still passes (no regressions)
pixi run pytest tests/unit/automation/ -v --tb=short
```

### Comment on the issue

After the PR is created, post a comment explaining what was found and why the approach differs
from a literal implementation:

```bash
gh issue comment <N> --body "$(cat <<'EOF'
Investigated all premises of this issue against `main`:

- `CICheckInspector` class: 0 grep hits — does not exist
- `ci_check_inspector.py`: 0 grep hits — file does not exist
- PR #1289 (the upstream): `gh pr view 1289` → "Could not resolve to a PullRequest" — was never merged
- `FAILING_CHECK_CONCLUSIONS`: 1 definition (ci_driver.py) — DRY invariant already satisfied
- `_pr_is_failing`: 1 definition (ci_driver.py) — DRY invariant already satisfied

The issue was auto-generated from a PR that was never merged, describing code that was never
introduced. Implementing the literal request would create dead code (YAGNI violation).

Instead, PR #<N> adds 2 AST regression-guard tests that assert the already-satisfied DRY
invariant is preserved permanently. If a future PR introduces duplicate definitions, CI will fail.
EOF
)"
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust the issue body and create `pr_predicates.py` | Started outlining a new leaf module that re-exports `FAILING_CHECK_CONCLUSIONS` and `_pr_is_failing` | `grep -rln` returned 0 hits for all cited files and classes; `gh pr view 1289` → "Could not resolve" — the entire issue premise was fabricated | Always verify every concrete named entity (files, classes, functions, PRs) before writing a line of code. A moot issue takes 2 minutes to detect and 30 minutes to guard; it takes hours to undo fabricated modules |
| Close the issue with no artifact | Considered closing as "issue premises false, nothing to implement" | Leaves the already-satisfied invariant unchecked; a future PR can re-introduce duplication with no CI gate | "Already satisfied" is not the same as "permanently enforced". Convert satisfaction into a regression guard |
| Use string grep instead of ast.parse for the guard | Initially considered `grep -rn "FAILING_CHECK_CONCLUSIONS"` in a shell-based test | Grep matches comments, docstrings, and import lines — not just assignments. A future `from ci_driver import FAILING_CHECK_CONCLUSIONS` line would produce a false positive | `ast.parse` + `ast.walk` distinguishes assignments from imports/references; it is definition-aware, not string-aware |

## Results & Parameters

### Decision tree for moot follow-up issues

```
Received a follow-up or auto-generated issue:
│
├─ 1. Verify every named entity (files, classes, functions, constants, PRs)
│   ├─ ALL exist in codebase → standard implementation path
│   └─ ANY returns 0 hits or resolution error → issue premise is suspect
│       └─ Verify ALL remaining entities
│           ├─ SOME exist → partial-stale issue; apply stale-plan-already-resolved skill
│           └─ NONE exist → issue is moot (auto-generated from un-merged PR)
│               └─ Proceed to step 2
│
├─ 2. Measure the actual invariant state
│   ├─ Invariant already satisfied (exactly 1 definition) → step 3
│   └─ Invariant not satisfied (multiple definitions exist) → implement normally
│       (the issue found a real problem despite having false file-name premises)
│
├─ 3. Write AST regression-guard tests
│   ├─ Use ast.parse + ast.walk over rglob("*.py")
│   ├─ Assert count == 1 AND home file == expected
│   └─ Add actionable assertion message listing violating files
│
└─ 4. Create PR + comment on issue explaining findings
```

### AST scanning pattern parameters

| Parameter | Value for #1345 | Generalisation |
|-----------|-----------------|----------------|
| Scan root | `Path(__file__).parents[3] / "hephaestus" / "automation"` | Adjust parents[N] depth based on test file location |
| Node types | `ast.Assign` (bare) + `ast.AnnAssign` (typed) | Add `ast.AugAssign` for `X += ...` if needed |
| Home file assertion | `assert hits[0].name == "ci_driver.py"` | Name the canonical module explicitly |
| SyntaxError handling | `continue` (skip broken files, don't suppress guard) | Do not raise — a broken `.py` is a separate lint concern |
| rglob pattern | `"*.py"` | Add `exclude` filter for `__pycache__` or `_version.py` if performance matters |

### Key commands

| Goal | Command |
|------|---------|
| Verify a file exists | `grep -rln "<filename>" hephaestus/` |
| Verify a class exists | `grep -rn "class <ClassName>" hephaestus/` |
| Count constant definitions | `grep -rn "<CONST>\s*=" hephaestus/ --include="*.py"` |
| Count function definitions | `grep -rn "^def <fn>" hephaestus/` |
| Verify upstream PR exists | `gh pr view <N> --json number,state,title 2>&1` |
| Run guard tests only | `pixi run pytest <test_file>::<TestClass> -v` |

### Related skills

- `planning-check-already-shipped-before-planning` — the case where code DOES exist but is
  already fixed; this skill covers the case where code was NEVER introduced
- `stale-plan-already-resolved` — the case where line numbers drifted; overlapping trigger
  but different response (close with comment vs. add regression guard)
- `planning-follow-up-issue-line-number-drift` — line number drift within an existing file;
  this skill covers the case where the files themselves do not exist
- `gitignored-scratch-dir-regression-guard` — another regression-guard pattern (pre-commit
  hook via git ls-files); this skill uses AST-level pytest tests instead

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1345 — "Follow-up from #1289: 2 item(s) (core, safety)" | PR #1346: 2 AST regression-guard tests added to `tests/unit/automation/test_ci_gate.py`; all 1659 automation tests pass; verified-ci |
