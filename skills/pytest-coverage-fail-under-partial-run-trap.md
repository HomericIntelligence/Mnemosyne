---
name: pytest-coverage-fail-under-partial-run-trap
description: "[tool.coverage.report] fail_under = X in pyproject.toml fires for EVERY pytest invocation, not just full-suite runs. Partial test runs (e.g., `pytest -m integration`, single test class, single file) measure coverage of only what they execute, naturally producing lower numbers and tripping the global gate even when the full suite is well above threshold. Use when: (1) integration-only CI job fails with 'Required test coverage of X.0% not reached' but full-suite coverage is fine, (2) running a single pytest file or class trips coverage gate, (3) you suspect coverage failure caused by recently-added gate and partial test selection rather than real coverage regression, (4) deciding whether to put coverage gate in pyproject.toml's [tool.coverage.report] vs in CI workflow's --cov-fail-under flag."
category: testing
date: 2026-05-07
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [pytest, coverage, fail-under, ci, integration-tests, partial-runs, coverage-gate]
---

# pytest fail_under Trips on Partial Test Runs

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-07 |
| **Objective** | Document the non-obvious failure mode where `[tool.coverage.report].fail_under` fires for any pytest invocation, including partial test selections |
| **Outcome** | Discovered + worked around in ProjectHermes during a 31-PR rebase swarm; codified here so future sessions don't waste a wave debugging it |
| **Verification** | verified-ci — observed in CI logs across multiple PRs and reproduced locally |

## When to Use

- A CI job runs `pytest -m integration` (or `pytest -m "not integration"`, or `pytest tests/specific.py`) and fails with `FAIL Required test coverage of X.0% not reached. Total coverage: <X-2>%`
- The full-suite `pytest` run on the same codebase shows much higher coverage (e.g., 96%) but a partial run shows lower
- You're deciding where to put the coverage gate: in `pyproject.toml` (applies to every invocation) vs in CI workflow YAML (`--cov-fail-under=X`, applies only to that step)
- A recently-merged PR added `fail_under = X` to pyproject.toml without verifying integration-only runs hit that threshold
- A bisect of "why is CI failing" lands on a coverage-gate failure that doesn't make sense given the actual coverage of the codebase

## Verified Workflow

### Quick Reference

The fix has two viable shapes; pick based on intent:

```toml
# Option A: Remove gate from pyproject.toml. Put it ONLY in CI on the full-suite step.
# pyproject.toml:
[tool.coverage.report]
# fail_under = 80   <- DELETE this
precision = 2
```

```yaml
# .github/workflows/ci.yml — only the FULL-suite step has the gate:
- name: Unit tests (full suite)
  run: pixi run pytest -m "not integration" --cov-fail-under=80
- name: Integration tests
  run: pixi run pytest -m integration -v   # NO --cov-fail-under here
```

```bash
# Option B: Pass --no-cov on partial pytest runs to disable coverage measurement (and gate) for them
pixi run pytest -m integration --no-cov
```

```bash
# Option C: Add tests so partial runs hit the threshold (real but slow)
# Identify uncovered modules during integration runs:
pixi run pytest -m integration --cov | tail -20
# Add @pytest.mark.integration tests for the lowest-covered modules until threshold met
```

### Why This Happens

`coverage.py` measures code that ran during the current pytest invocation. It does NOT
accumulate across runs (without explicit `--cov-append`). When pytest configuration
includes `fail_under` (either via `[tool.coverage.report] fail_under = X` in
pyproject.toml OR `--cov-fail-under=X` on the CLI), the gate fires after each invocation
based on THAT invocation's measurement.

For a 633-statement codebase:

- Full suite (`pytest`): runs every test → covers ~96% of statements → passes
- Integration only (`pytest -m integration`): runs ~80 integration tests → covers ~78% of
  statements → trips a `fail_under = 80` gate
- Single class (`pytest tests/foo.py::TestBar`): runs ~5 tests → covers ~50% of statements
  → trips even harder

### Symptom Signature in CI Logs

```text
FAIL Required test coverage of 80.0% not reached. Total coverage: 78.52%
```

The number after "Total coverage:" is THIS invocation's coverage, NOT the full-suite
number. If you see this from a job whose name contains "Integration", "specific file",
or anything other than "full suite", suspect a partial-run trap.

### Diagnostic Commands

```bash
# What's the actual coverage of a partial run?
pixi run pytest -m integration --cov | tail -25

# What's the actual coverage of the full suite?
pixi run pytest --cov | tail -25

# Where is the gate configured?
grep -rn "fail_under\|cov-fail-under" pyproject.toml .github/workflows/ pytest.ini setup.cfg 2>/dev/null
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Lowered `fail_under` from 80 to 78 to "match current coverage" | Edit pyproject.toml's `[tool.coverage.report]` block | Made a passing CI cover up the real bug (gate-trap on partial runs); next time someone ran full suite they'd see it pass at 96%, then run integration alone and see 78% with no explanation | Don't lower the gate — fix the configuration so the gate only applies to runs where it makes sense |
| Added `# fmt: off` and other linter pragmas | Tried to silence coverage output | `fail_under` is enforced by coverage.py, not by linters; pragmas don't help | The gate is a coverage.py feature; only coverage.py config or CLI flags affect it |
| Removed `[tool.coverage.report]` from pyproject.toml entirely | Wholesale delete | Removed unrelated configuration (precision, exclude_lines) along with `fail_under` | Surgical: only remove the `fail_under` line, keep the rest of `[tool.coverage.report]` |
| Trusted that "the gate worked yesterday on main" | Assumed if it merged once, it stays correct | The PR that ADDED the gate (e.g., a coverage-tracking improvement PR) may have been tested on full-suite runs only, never on integration-only runs; the failure mode only manifests after the gate-PR lands AND a partial-run CI job runs | When merging a PR that adds a coverage gate, verify CI passes on EVERY pytest invocation in the workflow, not just the most-prominent one |

## Results & Parameters

### Recommended Configuration

```toml
# pyproject.toml — coverage settings WITHOUT a fail_under gate
[tool.coverage.run]
source = ["mypackage"]

[tool.coverage.report]
precision = 2
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:"]
# DO NOT put fail_under here — it applies to every pytest invocation
```

```yaml
# .github/workflows/<ci>.yml — gate ONLY on the full-suite job
jobs:
  unit-tests:
    steps:
      - name: Unit tests (full suite, gated)
        run: pixi run pytest -m "not integration" --cov-fail-under=80

  integration-tests:
    steps:
      - name: Integration tests (no gate — partial run by design)
        run: pixi run pytest -m integration -v
```

### Coverage Measurement Reference

```text
Run command                              | Tests run     | Cover  | Gate-safe at fail_under=80?
-----------------------------------------|---------------|--------|------------------------------
pytest                                   | All           | 96.52% | YES
pytest -m "not integration"              | Unit only     | 92%    | YES
pytest -m integration                    | Integ only    | 78.52% | NO (partial-run trap)
pytest tests/test_one_class.py::Test     | 5 tests       | 50.39% | NO (extreme partial-run)
pytest --cov-append (after multiple runs)| Cumulative    | 96.52% | YES (with --cov-append)
```

### Detection in CI

After any CI failure with "Required test coverage of X% not reached":

1. Check the **job name** that failed. If it's "Integration", "Smoke", or any other partial-selection job → partial-run trap.
2. Run the same command locally; observe the partial-coverage number.
3. Compare to full-suite local run; if full-suite passes, it's the trap.
4. Apply Option A (move gate to CI workflow) or Option B (`--no-cov` on partial jobs).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/ProjectHermes | 2026-05-07: PR #475 added `--cov-fail-under=80` + `fail_under = 80`; subsequent integration-only CI jobs began failing at 78.52% | Worked around by adding @pytest.mark.integration tests in tests/test_integration_coverage.py to push integration-only coverage above 80%. Real fix (move gate to CI-only) deferred to follow-up. |
