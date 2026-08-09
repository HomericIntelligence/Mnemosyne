---
name: testing-verification-gate-zero-test-false-pass
description: "Prevent zero-test verification from becoming a false pass. Use when: (1) a wrapper invokes pytest and interprets subprocess return codes, especially code 5, (2) a gate uses name-filtered selection such as `pytest -k`, `ctest -R`, or `go test -run`, (3) CI-log parsing can produce no runnable targets, (4) a test source may be orphaned from its build target, (5) push or merge safety depends on the test gate."
category: testing
date: 2026-08-06
version: "1.2.0"
user-invocable: false
verification: unverified
history: testing-verification-gate-zero-test-false-pass.history
tags: [testing, pytest, ctest, cmake, gtest, verification-gate, false-pass, exit-code-5, no-tests-collected, subprocess, fail-closed, pre-push, signal, timeout, test-count, collect-only, show-only, orphaned-test, planning, plan-review]
---

# Verification Gate: Zero-Test False Pass

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-06 |
| Objective | Ensure a verification wrapper cannot treat an invoked test process that ran no tests as evidence that a change is safe |
| Outcome | Proposed fail-closed boundary: decide any intentionally inapplicable gate before invocation; after pytest starts, only return code 0 succeeds. Code 5 means no tests were collected and must block the guarded push or merge. Name-filtered and orphaned-target gates still need an explicit non-empty-selection proof when their runner can otherwise report success. |
| Verification | unverified — the Hephaestus fix and regression matrix were planned but not implemented or run; the unsafe pre-fix code-5 acceptance and pytest 9.1.1 code-5 behavior were reproduced locally |
| History | [changelog](./testing-verification-gate-zero-test-false-pass.history) |

## When to Use

- A Python wrapper calls pytest through `subprocess.run()` and converts return codes into a push, merge, release, or deployment decision.
- A caller accepts pytest code 5 because a failing test might have been deleted or renamed.
- CI-log parsing, target discovery, or file-existence filtering can produce no runnable node IDs.
- A verification step uses a name-filtered selection such as `pytest -k <expr>`, `ctest -R <regex>`, or `go test -run <regex>`.
- A test file exists on disk but may not be registered in a build target, so the runner can select no tests.
- A compatibility facade duplicates constants or comments that imply a nonzero test-runner result is successful.
- You need regression coverage proving the outer guarded action is never called when verification is empty, interrupted, timed out, or otherwise unsuccessful.

## Verified Workflow

> **Proposed Workflow — Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the implementation tests and CI confirm it. Local reproduction established the pre-fix behavior and pytest's code-5 result, not the completed fix.

The key distinction is whether the safety gate has invoked pytest:

1. **Before invocation**, target discovery may prove that the gate does not apply. A deliberately supported skip must be narrow, explicit, and observable. For example, CI-log parsing followed by file-existence filtering may yield no runnable node IDs.
2. **After invocation**, do not infer why pytest selected nothing. Per pytest's [exit-code reference](https://docs.pytest.org/en/9.0.x/reference/exit-codes.html), code 5 means no tests were collected. It is not proof that verification passed or that a deleted test made the change safe. Only code 0 is successful.

This avoids conflating two materially different states:

- `targets == []` before spawning the process: a caller-owned applicability decision.
- `completed.returncode == 5` after spawning pytest: an unsuccessful verification result.

### Quick Reference

```python
PYTEST_FAILURE_REASONS: dict[int, str] = {
    1: "pytest exit code 1: tests failed",
    2: "pytest exit code 2: test execution interrupted",
    3: "pytest exit code 3: internal error",
    4: "pytest exit code 4: command-line usage error",
    5: "pytest exit code 5: no tests collected",
}

if not runnable_node_ids:
    logger.info("no runnable test targets; skipping before pytest invocation")
    return True

try:
    completed = subprocess.run(pytest_command, check=False, timeout=timeout_seconds)
except subprocess.TimeoutExpired:
    logger.error("test gate timed out; refusing guarded action")
    return False

if completed.returncode != 0:
    reason = (
        f"pytest terminated by signal {-completed.returncode}"
        if completed.returncode < 0
        else PYTEST_FAILURE_REASONS.get(
            completed.returncode,
            f"pytest exited with unexpected code {completed.returncode}",
        )
    )
    logger.error("test gate failed (%s); refusing guarded action", reason)
    return False

return True
```

```bash
# Prefer exact, known node IDs over a fuzzy -k selector.
pytest tests/unit/test_guard.py::TestGuard::test_refuses_empty_verification

# If a runner can exit 0 after a name filter selects nothing, prove selection first.
ctest -R Healthcheck --show-only | grep -qE 'Test #' || {
  echo "FALSE PASS: 0 tests matched"
  exit 1
}
```

### Detailed Steps

1. **Define the applicability boundary before invocation.** Parse logs or discover targets, filter paths that no longer exist, and make any allowed skip decision there. Keep it narrow; do not add a general `allow-no-tests` option or environment-variable bypass.
2. **Invoke exact targets where possible.** Exact pytest node IDs reduce the chance that a fuzzy `-k` expression selects zero tests. They do not justify accepting code 5: renamed functions, empty modules, collection behavior, or stale identifiers can still leave the invocation empty.
3. **Make zero the sole success code after pytest starts.** Diagnose codes 1 through 5 explicitly, negative return codes as signal termination, and all other nonzero values as unexpected failures. Preserve timeout as a separate fail-closed path.
4. **Keep policy at the subprocess owner.** Patch tests through the module that owns `subprocess.run()`. Remove stale constants or comments from compatibility facades so there is one live success predicate.
5. **Test both the helper and guarded-action boundary.** Parameterize pytest codes 0 through 5; add timeout and signal cases; then prove code 5 prevents the outer push, merge, or deploy function from being called and emits `pytest exit code 5: no tests collected`.
6. **Pin the only pre-invocation skips.** Retain tests for empty discovery input and targets removed by file filtering, and assert the subprocess was never invoked in both cases.
7. **For non-pytest runners, verify non-empty registration separately.** If a name-filtered runner returns 0 with no matches, enumerate before execution. For CMake, also prove the test source is wired into a real target; a file on disk is not registration evidence.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Planned to wrap an existing assertion without confirming the test existed | Source search found no matching assertion or test file | Confirm the intended test exists; net-new code needs a net-new test |
| 2 | Described `pytest -k <expr>` selecting zero tests as an exit-0 false pass | A local pytest 9.1.1 probe selected zero tests and returned code 5 | For pytest, the false pass is usually the wrapper accepting code 5; document runner semantics from observed results and official exit-code definitions |
| 3 | Accepted pytest code 5 because the failing test might have been deleted by a fix or rebase | Code 5 only establishes that pytest collected no tests; it does not prove deletion, correctness, or successful verification | Handle deletion or missing targets before invocation; once pytest runs, only code 0 passes |
| 4 | Used the subprocess result as the only regression seam | A helper-only assertion can miss the safety consequence if the caller still pushes | Add a boundary test that asserts the guarded push or merge function is never called |
| 5 | Patched `subprocess.run` through a compatibility facade | The execution moved to an owning module, leaving the patch coupled to a stale re-export | Patch the dependency where the implementation looks it up: the subprocess-owning module |
| 6 | Cited `ctest -R Healthcheck` without checking target registration | An orphaned source file was in no CMake target, so the name filter could select nothing and prove nothing | Verify build-target wiring and enumerate matching tests before trusting a filtered gate |
| 7 | Hard-coded a built binary's relative path in a test | Build output directories and working directories vary | Inject the path through the build system's target-location primitive, such as CMake `$<TARGET_FILE:...>` |

## Results & Parameters

- **Post-invocation success predicate:** `returncode == 0` only.
- **Pytest failure diagnostics:** 1 tests failed; 2 interrupted; 3 internal error; 4 usage error; 5 no tests collected.
- **Process failures:** negative return code means signal termination; unexpected positive nonzero codes remain fail-closed; timeout remains an explicit failure.
- **Permitted skip location:** before subprocess invocation, only after caller-owned discovery and existence filtering produce no runnable targets.
- **Forbidden bypasses:** no general allow-no-tests flag, environment variable, or code-5 exception.
- **Boundary regression:** simulate code 5 with an existing target, assert the guarded action returns false, assert the explicit diagnostic, and assert the push/merge/deploy callable was not invoked.
- **Focused matrix:** codes 0 through 5, timeout, signal termination, and the two pre-invocation no-target cases.
- **Ownership rule:** define the success predicate and patch subprocess execution in the module that owns the call; compatibility facades must not duplicate the policy.
- **Local observations:** pytest 9.1.1 selected 0 of 31 tests for a nonmatching `-k` expression and returned 5; the pre-fix Hephaestus unit test confirmed its wrapper accepted simulated code 5.
- **Overall status:** unverified — implementation and CI validation pending.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectAgamemnon | Issues #143 and #279 planning | Established the broader zero-test and orphaned-target verification risks; no end-to-end execution |
| ProjectHephaestus | CI-fix pre-push gate planning, 2026-08-06 | Static source inspection plus local reproduction of the unsafe pre-fix code-5 acceptance and pytest 9.1.1 zero-selection result; proposed fix not implemented |
