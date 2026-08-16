---
name: coverage-omit-orchestration-pure-function-testing
license: BSD-3-Clause
description: "How to replace whole-module coverage omissions and import/test-name proxies with hermetic behavior tests plus explicit per-module coverage metrics. Use when: (1) orchestration modules are excluded because they touch agents, GitHub, Git, subprocesses, clocks, or terminals, (2) a proxy test proves only that a module was imported or named, (3) line and branch floors need unambiguous enforcement."
category: testing
date: 2026-08-05
version: "2.0.0"
user-invocable: false
verification: unverified
tags: [coverage, hermetic-tests, orchestration, cobertura]
history: coverage-omit-orchestration-pure-function-testing.history
---

# Promoting Omitted Orchestration Modules to Executable Coverage

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Replace whole-module coverage omissions and import/test-name proxies with hermetic behavior tests and explicit per-module coverage floors |
| **Outcome** | Reviewed implementation contract captured; execution and CI validation remain pending |
| **Verification** | unverified |
| **History** | [changelog](./coverage-omit-orchestration-pure-function-testing.history) |

## When to Use

- Coverage excludes complete orchestration modules because their normal path invokes live agents, GitHub, Git, subprocesses, a wall clock, or a terminal.
- A validation test considers an omitted module justified when a test merely imports it or has a matching filename.
- A coverage-floor checker automatically chooses branch coverage when positive and otherwise falls back to line coverage.
- A migration cohort includes renamed or retired modules that must be reconciled with their current executable owners.
- You need to remove omissions without weakening a repository-wide gate or depending on external services.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the canonical coverage report and CI confirm it.

### Quick Reference

```bash
# 1. Reconcile the planned cohort against the current tree.
find <source-root> -type f -name '*.py' | sort
rg '<retired-symbol>|<replacement-symbol>' <source-root> <docs-root> <tests-root>

# 2. Add hermetic behavior tests before changing coverage configuration.
<package-manager> pytest <focused-behavior-tests> -v

# 3. Promote omissions and floors as one configuration change.
# coverage.toml
# [coverage.modules]
# "orchestration/target.py" = { minimum = 70, metric = "line" }

# 4. Generate the same Cobertura artifact CI consumes and run the real checker.
mkdir -p build
<package-manager> pytest <unit-tests> --cov=<package> \
  --cov-report=xml:build/coverage.xml
<package-manager> <coverage-checker> \
  --coverage-file build/coverage.xml --config coverage.toml
```

### Detailed Steps

1. **Reconcile the cohort against the current tree.** For every planned module, record whether its source still exists, moved, split, or was retired. A retired facade should stay absent; place the floor on the surviving executable owner and add an assertion that the obsolete source does not reappear.

2. **Write hermetic behavior tests before editing omissions.** Exercise orchestration bodies through injected seams rather than importing modules for side effects. Patch or inject all external boundaries:

   | Boundary | Hermetic substitute | Behavior to assert |
   |----------|---------------------|--------------------|
   | Agent provider | Fake result, raised provider error, or resume failure | Dispatch, normalization, fallback, bounded retry |
   | GitHub API/CLI | Patched call returning structured fixtures | Scope, pagination, union, deduplication, per-item failure containment |
   | Git/subprocess | Fake completed process and repository state | Branch selection, retry limits, no-commit outcome |
   | Clock | Patched monotonic/time/sleep | Refresh and timeout behavior without wall-clock delay |
   | Terminal | Fake screen plus patched curses functions | Rendering, unavailable dependency, resize recovery |

3. **Make the enforced metric explicit.** New module floors should select `line` or `branch`; legacy entries may retain an `auto` mode during migration. Explicit branch selection must use a zero branch rate as zero, never as a signal to fall back to line coverage.

   ```python
   def select_metric(metric: str, line_rate: float, branch_rate: float) -> tuple[str, float]:
       if metric == "line":
           return "line", line_rate
       if metric == "branch":
           return "branch", branch_rate
       if metric == "auto":
           return ("branch", branch_rate) if branch_rate > 0 else ("line", line_rate)
       raise ValueError(f"unsupported coverage metric: {metric!r}")
   ```

4. **Test metric boundaries through the public checker.** A 70% line floor needs regressions proving 69% fails and 70% passes. Also prove that an explicit branch floor fails at 0% branch coverage even if line coverage is 99%. Assert that diagnostics name the selected metric.

5. **Freeze omissions by exact equality.** Compare the configured omit list with the complete allowed list, including order when configuration stability matters. Prefix checks and substring checks are bypassable by alternate glob spellings. An exact contract rejects every extra whole-module pattern regardless of how the coverage engine interprets it.

6. **Promote configuration atomically.** In one change, remove the whole-module omissions, add explicit floors for every reconciled source, replace the proxy tests with behavior/floor contracts, and update documentation. Do not leave a state where measured modules lack floors or floors target still-omitted files.

7. **Use the canonical Cobertura pipeline.** Generate coverage with the same test selection, source root, branch setting, and XML path as required CI. Run the repository's coverage-checker CLI rather than a custom XML script. Confirm every configured filename appears in the XML; a missing path is a configuration error, not zero coverage.

8. **Rollback configuration as a unit if a floor cannot be met hermetically.** Restore the prior omit list, module-floor entries, and omit-contract tests together. Keep useful behavior tests. Do not lower the agreed floor merely to finish the migration.

## Verified Workflow

No end-to-end workflow is verified yet. The executable procedure is intentionally documented under **Proposed Workflow** until the canonical report and CI pass. This explicit placeholder is retained because Mnemosyne's current skill validator requires the `Verified Workflow` heading even for `verification: unverified` skills.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Import/test-name proxy | Treated a test import and a matching test function name as evidence that an omitted module was covered | Imports can execute none of the orchestration body and do not contribute measurable behavior while the source remains omitted | Replace naming proxies with Cobertura floors plus assertions over observable behavior |
| Pure helpers while keeping whole modules omitted | Tested parsers and predicates but left orchestration sources outside the denominator | The tests improved correctness but could not prove or enforce execution of the omitted modules | Inject live boundaries and measure the complete source module |
| Automatic zero-branch fallback | Used branch coverage when positive and line coverage when branch rate was zero | An explicit branch floor could pass using a high line rate even though no branches executed | Distinguish explicit `branch` from legacy `auto`; zero is a real branch measurement |
| Prefix-based omit guard | Rejected only omit entries beginning with a known source prefix | Alternate globs such as `*/orchestration/target.py` bypassed the check | Require exact equality with the complete allowed omit list |
| Floor on retired source | Carried a historical module name into the coverage configuration | Retired files never appear in Cobertura XML, so the floor cannot measure current behavior | Map retired facades to the surviving owner and assert the retired path remains absent |
| Hand-rolled XML verification | Parsed selected XML attributes outside the real coverage-checker CLI | It can diverge from production path matching, threshold conversion, and diagnostics | Generate the canonical artifact and invoke the same checker CI uses |
| Lowered floor to complete migration | Reduced a below-floor threshold after removing omissions | It changes the acceptance contract instead of improving behavior coverage | Roll back the promotion unit and retain the new tests until the agreed floor is met |

## Results & Parameters

### Generic configuration contracts

```toml
[tool.coverage.run]
branch = true
source = ["<package>"]
omit = [
    "*/tests/*",
    "*/__init__.py",
]

[coverage.modules]
"orchestration/target.py" = { minimum = 70, metric = "line" }
"orchestration/branchy_target.py" = { minimum = 70, metric = "branch" }
```

```python
ALLOWED_OMITS = ["*/tests/*", "*/__init__.py"]

assert configured_omits == ALLOWED_OMITS
assert module_floors["orchestration/target.py"] == {
    "minimum": 70,
    "metric": "line",
}
```

### Metric regression matrix

| Floor | Line rate | Branch rate | Expected |
|-------|-----------|-------------|----------|
| `minimum = 70, metric = "line"` | 69% | 99% | Fail |
| `minimum = 70, metric = "line"` | 70% | 0% | Pass |
| `minimum = 70, metric = "branch"` | 99% | 0% | Fail |
| `minimum = 70` (legacy auto) | 99% | 0% | Pass on line; migrate deliberately |

### ProjectHephaestus issue #2371 reconciliation example

Eleven historical sources remain executable and should receive 70% line floors: `implementer.py`, `planner.py`, `ci_driver.py`, `pr_discovery.py`, `ci_check_inspector.py`, `ci_fix_orchestrator.py`, `post_merge_processor.py`, `loop_runner.py`, `loop_repo_manager.py`, `curses_ui.py`, and `audit_reviewer.py`. The retired twelfth facade, `address_review.py`, maps to `address_review_core.py`, whose parsing behavior remains executable.

The migration contract is:

- Every surviving source is present and every configured module path appears in Cobertura XML.
- The retired facade is absent and its current owner is present.
- Every cohort entry has `{ minimum = 70, metric = "line" }`.
- The coverage omit list equals only the generic test and package-initializer exclusions.
- Agent, GitHub, Git, subprocess, clock, and terminal behavior is exercised through injected substitutes.
- The canonical unit-test XML and coverage checker pass before the migration is called complete.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2371 reviewed implementation contract (2026-08-05) | Unverified: implementation, canonical coverage report, and CI remain pending |
