---
name: local-test-failures-env-pollution-not-ci
description: "Integration/unit tests can fail locally for environmental reasons that never occur in CI: a stale console-script binary picked up by shutil.which() from a sibling checkout, and HEPH_*/config env vars leaked into the interactive shell that pollute os.environ.copy()-based tests. Use when: (1) a test fails locally but the same job is green in CI, (2) shutil.which() in a test resolves a binary from another worktree/checkout, (3) a _phase_env / os.environ.copy() test asserts a var is absent but it's present, (4) deciding whether a local red is a real regression before committing."
category: testing
date: 2026-06-11
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
---

# Local Test Failures from Env Pollution, Not CI

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-11 |
| **Objective** | Distinguish environmental local-only test failures (stale `shutil.which()` binary from a sibling checkout; leaked `HEPH_*` shell vars polluting `os.environ.copy()` tests) from real code regressions, before committing a fix. |
| **Context** | ProjectHephaestus PR #1016 / issue #723, working inside a git worktree at `build/.worktrees/issue-723`. After the one real code fix, the full local pytest run showed failures that were NOT code regressions. |
| **Outcome** | Both classes of failure traced to the local environment; production code was correct; full suite green once the env was scrubbed and the worktree's own bin was put first on PATH (3516 passed, 18 skipped, coverage 84.93%). |
| **Verification** | verified-local |

## When to Use

- A test fails locally but the same job is green in CI, and you are deciding whether it's a real regression before committing.
- A `shutil.which()`-based test resolves a binary from another worktree/checkout instead of the one under test.
- A `_phase_env` / `os.environ.copy()` test asserts an env var is ABSENT but the assertion fails because the var is present.
- You are about to "fix" code to make a local-only red go green and want to rule out environment pollution first.

## Verified Workflow

A test red locally but green in CI is **environmental until proven otherwise** — do NOT edit code first. Two distinct environmental causes surfaced here.

### Failure 1 — stale console-script binary via `shutil.which()`

- The test `tests/integration/test_cli_entry_points.py::TestMaxWorkersValidation::test_automation_loop_rejects_zero_max_workers` calls `shutil.which("hephaestus-automation-loop")`, runs it with `--max-workers 0`, and asserts the process exits non-zero with `"invalid choice"` (argparse `choices=range(1, 33)`).
- It failed locally because `shutil.which` resolved the binary from the ROOT checkout's pixi env (`/home/.../ProjectHephaestus/.pixi/envs/default/bin`), which was on a DIFFERENT/older branch lacking the `add_max_workers_arg` validation. That stale binary skipped argparse validation and instead reached gh repo-detection logic, failing on a gh 404/token error instead of the expected argparse error.
- **Diagnosis that proved it** — import the module two ways and compare `__file__`:
  - From the worktree cwd, `python -c "import hephaestus.automation.loop_runner as lr; print(lr.__file__)"` resolves the WORKTREE file (cwd is on `sys.path`).
  - But the installed console-script wrapper runs with the entry-point's site-packages on the path, resolving the ROOT checkout copy. Running the binary's interpreter from a neutral cwd revealed the staleness:

    ```bash
    cd /tmp && /home/.../ProjectHephaestus/.pixi/envs/default/bin/python \
      -c "import hephaestus.automation.loop_runner as lr; print(lr.__file__)"
    # -> /home/.../ProjectHephaestus/hephaestus/...  (ROOT checkout, where add_max_workers_arg was absent)
    ```

- **Resolution** — put the worktree's own pixi env bin FIRST on PATH, then re-run:

  ```bash
  export PATH="$WORKTREE/.pixi/envs/default/bin:$PATH"
  hash -r
  ```

  The regression test then passes. This confirms the fix is correct and that CI — which installs the package fresh from the PR branch — was already green for `integration-tests`.

### Failure 2 — leaked `HEPH_*` env vars pollute `os.environ.copy()` tests

- The tests `test_phase_env_loop_index_only_for_drive_green` and `test_phase_env_model_vars_only_when_non_empty` assert that `loop_runner._phase_env(...)` does NOT contain `HEPH_LOOP_INDEX` / `HEPH_PLANNER_MODEL` for certain phases.
- They failed locally because the interactive shell already had `HEPH_LOOP_INDEX`, `HEPH_PLANNER_MODEL`, `HEPH_REVIEWER_MODEL`, `HEPH_IMPLEMENTER_MODEL`, `HEPH_ADVISE_MODEL`, `HEPH_TOTAL_LOOPS`, `HEPH_TRUNK_GITHASH`, and `HEPH_WORK_REPORT` exported (leaked from a prior automation-loop run). `_phase_env` builds on `os.environ.copy()`, so the pre-set vars made the "should be absent" assertions fail.
- **Proof it's environmental** — re-run under a scrubbed env; both pass:

  ```bash
  env -u HEPH_LOOP_INDEX -u HEPH_TOTAL_LOOPS -u HEPH_PLANNER_MODEL \
      -u HEPH_REVIEWER_MODEL -u HEPH_IMPLEMENTER_MODEL -u HEPH_ADVISE_MODEL \
      -u HEPH_TRUNK_GITHASH -u HEPH_WORK_REPORT \
      pixi run python -m pytest tests/unit/automation/test_loop_runner.py -k _phase_env
  ```

  CI has a clean env, so they pass there.

### Quick Reference

Reusable diagnostic recipe:

1. A test red locally but green in CI is **environmental until proven otherwise** — do not "fix" the code.
2. For `shutil.which()`-based tests: run `which <binary>` and confirm it points inside the current worktree's `.pixi/envs/default/bin`; if not, prepend it to PATH and `hash -r`. Diagnose module staleness by importing from a neutral cwd (`cd /tmp`) and printing `__file__`.
3. For `os.environ.copy()`-based tests asserting a var is ABSENT: grep the env (`env | grep HEPH_`); re-run the failing tests under `env -u VAR ...` to confirm. The production code is fine; the shell is polluted.
4. Only after BOTH checks come back environmental, proceed to commit. Re-run the FULL suite in a clean env (`env -u ...` plus worktree-first PATH) and require it green (here: 3516 passed, 18 skipped, coverage 84.93%).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treat the regression-test failure as a real argparse-validation bug | Inspected/considered editing the `--max-workers` argparse validation because the test asserting `"invalid choice"` was red | The worktree source DID validate — `_parse_args(['--max-workers', '0'])` raised `SystemExit(2)`; the failure came from a stale ROOT-checkout binary resolved by `shutil.which()` on PATH, not from the code under test | Verify WHICH file/binary is actually executing (import from a neutral cwd, print `__file__`; check `which <binary>`) before editing code. |
| Treat the `_phase_env` failures as a code regression | Considered changing `_phase_env` / `os.environ.copy()` handling because the "var should be absent" assertions were red | They were caused by leaked `HEPH_*` shell vars feeding `os.environ.copy()`; the code was correct and CI (clean env) was green | Reproduce under a scrubbed env (`env -u VAR ...`) before changing code; an absent-var assertion that fails locally usually means the shell, not the code, set the var. |

## Results & Parameters

- **Resolution PATH ordering**: `export PATH="$WORKTREE/.pixi/envs/default/bin:$PATH"; hash -r` makes `shutil.which()` resolve the worktree binary instead of the sibling ROOT checkout's.
- **Scrub list for `HEPH_*` pollution**: `HEPH_LOOP_INDEX`, `HEPH_TOTAL_LOOPS`, `HEPH_PLANNER_MODEL`, `HEPH_REVIEWER_MODEL`, `HEPH_IMPLEMENTER_MODEL`, `HEPH_ADVISE_MODEL`, `HEPH_TRUNK_GITHASH`, `HEPH_WORK_REPORT` (all leaked from a prior automation-loop run).
- **Clean full-suite result**: 3516 passed, 18 skipped, coverage 84.93% — required green before commit.
- **Verification level**: verified-local. Validated by re-running each failing test under the corrected PATH and scrubbed env; CI `integration-tests` and unit jobs were already green on the PR branch.

### Cross-references

- Reinforces the prior memory **"always work in a worktree when the automation loop runs"** — the automation loop runner resets/uses the shared checkout, so edits must live in an isolated `git worktree`; this skill shows a second-order hazard of that setup (the sibling checkout's stale binary on PATH).
- Reinforces the prior memory **"pixi env re-solve can drop the editable install"** — both failures stem from worktrees sharing/competing over `.pixi/envs/default`; when in doubt about which code is live, verify the resolved `__file__` and `which <binary>` rather than trusting the install.
- Related skill: `git-worktree-sys-path-precedence-issue` (why subprocess-spawned console scripts can load stale code from the main repo). This skill is the test-failure-triage companion: deciding whether a local red is that staleness (or env pollution) versus a real regression, before editing.
