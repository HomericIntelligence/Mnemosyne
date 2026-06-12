---
name: pytest-local-false-failure-inherited-heph-env-vars
description: "Diagnose automation-loop unit tests that fail LOCALLY ONLY because the running loop's shell already exported HEPH_* vars that os.environ.copy() inherits. Use when: (1) automation-loop unit tests that assert a HEPH_* (or any inherited) env var is ABSENT fail locally but pass in CI; (2) you ran the suite from inside the live automation loop whose shell already exported HEPH_LOOP_INDEX / HEPH_*_MODEL etc.; (3) you need to confirm a local-only failure is environment divergence (not a code regression) before editing any code."
category: testing
date: 2026-06-11
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
---

# Pytest Local False-Failure from Inherited HEPH_* Env Vars

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-11 |
| **Objective** | Explain why two `loop_runner._phase_env` unit tests fail locally only — the live automation loop's parent shell exports HEPH_* vars that `os.environ.copy()` inherits, breaking absence-of-env-var assertions that hold only in a clean env like CI |
| **Outcome** | Confirmed environment divergence (not a code defect): both tests pass under `env -u ...`; the PR diff was formatting-only and CI's unit-test matrix is green (ProjectHephaestus PR #1058 / issue #814) |
| **Verification** | verified-local |

## When to Use

- An automation-loop unit test that asserts a `HEPH_*` (or any inherited) env var is ABSENT fails locally but passes in CI.
- You ran the suite from INSIDE the live automation loop, whose own shell already exported `HEPH_LOOP_INDEX`, `HEPH_TOTAL_LOOPS`, `HEPH_PLANNER_MODEL`, `HEPH_REVIEWER_MODEL`, `HEPH_IMPLEMENTER_MODEL`, `HEPH_ADVISE_MODEL`, etc.
- You see errors like `phase plan leaked HEPH_LOOP_INDEX` or `assert 'HEPH_PLANNER_MODEL' not in {...}`.
- You need to confirm a local-only failure is environment divergence — NOT a code regression — BEFORE editing any code or test.
- General signal: a green CI unit-test matrix plus a local-only failure on absence-of-env-var assertions == environment divergence, full stop.

## Verified Workflow

### Quick Reference

Re-run the two failing tests with the inherited HEPH_* vars stripped. If they pass, the failure is environmental, not a code defect:

```bash
env -u HEPH_LOOP_INDEX -u HEPH_TOTAL_LOOPS -u HEPH_PLANNER_MODEL -u HEPH_REVIEWER_MODEL -u HEPH_IMPLEMENTER_MODEL -u HEPH_ADVISE_MODEL \
  pixi run python -m pytest \
  tests/unit/automation/test_loop_runner.py::test_phase_env_loop_index_only_for_drive_green \
  tests/unit/automation/test_loop_runner.py::test_phase_env_model_vars_only_when_non_empty \
  -v --no-cov
```

Expected: `2 passed`. The FULL suite also goes green under the same `env -u ...` prefix.

### Detailed Steps

1. **Identify the symptom.** Exactly two tests fail locally:
   - `tests/unit/automation/test_loop_runner.py::test_phase_env_loop_index_only_for_drive_green` — "phase plan leaked HEPH_LOOP_INDEX"
   - `tests/unit/automation/test_loop_runner.py::test_phase_env_model_vars_only_when_non_empty` — "assert 'HEPH_PLANNER_MODEL' not in {...}"
2. **Read the production code.** `loop_runner._phase_env()` builds its env via `env = os.environ.copy()`, then ADDS `HEPH_LOOP_INDEX` / `HEPH_TOTAL_LOOPS` only for the `drive-green` phase, and `HEPH_*_MODEL` only when the cfg field is non-empty. The tests assert those keys are ABSENT for the `plan` phase / empty cfg — an assertion that holds ONLY when the parent shell has no such vars.
3. **Recognize the divergence.** This session ran INSIDE the live automation loop, whose own environment already exported `HEPH_LOOP_INDEX=1`, `HEPH_TOTAL_LOOPS=1`, `HEPH_PLANNER_MODEL=claude-opus-4-8`, and the other `HEPH_*_MODEL` vars. `os.environ.copy()` faithfully inherits them, so the keys are PRESENT and the absence-assertions fail.
4. **Confirm with `env -u` BEFORE touching code.** Run the Quick Reference command. Both tests pass with the inherited vars stripped — proving environment divergence, not a regression.
5. **Do NOT "fix" the test or `_phase_env`.** The production behavior (copy `os.environ`, add scoped vars) is intentional and the test is correct for a clean env. CI is already green because CI has a clean environment.
6. **Trust the CI log over the local run** when the environment differs — this is the testing-side companion to the broader Hephaestus pattern that the CI log is the source of truth.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treat the 2 `_phase_env` failures as a real regression from the PR | Assumed the formatting-only PR introduced the failures and looked for a code bug | The PR diff was formatting-only and both tests pass in a clean env; CI is green | Check env divergence (`env -u`) before assuming a code bug |
| Edit `_phase_env` or the test to make local pass | Considered changing `_phase_env`'s `os.environ.copy()` behavior or relaxing the absence assertions | Production behavior is intentional and CI is already green; the test is correct for a clean env | Fix the environment (`env -u`), not the code |

## Results & Parameters

**Inherited vars exported by the running automation loop (cause of the false failure):**

```text
HEPH_LOOP_INDEX=1
HEPH_TOTAL_LOOPS=1
HEPH_PLANNER_MODEL=claude-opus-4-8
HEPH_REVIEWER_MODEL=<set>
HEPH_IMPLEMENTER_MODEL=<set>
HEPH_ADVISE_MODEL=<set>
```

**Production code under test (intentional — do NOT edit):**

```python
# hephaestus/automation/loop_runner.py :: _phase_env()
env = os.environ.copy()
# HEPH_LOOP_INDEX / HEPH_TOTAL_LOOPS added ONLY for the "drive-green" phase
# HEPH_*_MODEL added ONLY when the cfg field is non-empty
```

**Repro of the false failure (run from inside the live loop, dirty env):**

```text
tests/unit/automation/test_loop_runner.py::test_phase_env_loop_index_only_for_drive_green
  FAILED — phase plan leaked HEPH_LOOP_INDEX
tests/unit/automation/test_loop_runner.py::test_phase_env_model_vars_only_when_non_empty
  FAILED — assert 'HEPH_PLANNER_MODEL' not in {...}
```

**Expected clean-env result (run under the Quick Reference `env -u ...` prefix):**

```text
2 passed
```

CI status for ProjectHephaestus PR #1058: the `unit-tests` / `test (ubuntu-latest, 3.1x, unit)` jobs are all green because CI has a clean environment with no `HEPH_*` vars exported.
