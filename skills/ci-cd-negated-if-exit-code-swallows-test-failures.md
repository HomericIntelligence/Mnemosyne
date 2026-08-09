---
name: ci-cd-negated-if-exit-code-swallows-test-failures
description: "A CI test harness using `if ! cmd; then rc=$?; fi` reads $? AFTER the negated condition, so rc is always 0 and every failure counts as a pass — the job reports Passed: N, Failed: 0, SUCCESS while tests fail to even compile. Use when: (1) a CI summary says all tests pass but you suspect some never ran or never compiled, (2) auditing shell test-runner loops for exit-code capture bugs, (3) fixing a false-green harness and handling the wave of newly exposed failures, (4) writing a red-green proof that a harness fix actually detects failures."
category: ci-cd
date: 2026-07-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
---

# CI Harness Negated-if Exit-Code Bug Swallows Test Failures

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-16 |
| **Objective** | Explain why a Mojo CI test harness reported "Total: 82, Passed: 82, Failed: 0" and SUCCESS while 9 test files failed to compile, and document the detection, fix, proof, and aftermath protocol |
| **Outcome** | Root cause found (`$?` read after a negated `if !` condition is always 0), harness fixed with direct rc capture plus an accounting guard, fix proven with a deliberate red-green scratch test, 9 previously masked failures exposed and triaged |
| **Verification** | verified-local |

## When to Use

- A CI job summary reports every test passed (`Failed: 0`, SUCCESS) but you suspect some tests never actually ran or never compiled.
- You are auditing a shell test-runner loop (justfile recipe, Makefile, bash script) that iterates files and counts pass/fail via exit codes.
- You see the idiom `if ! <cmd>; then rc=$?; ...` anywhere in CI scripts — it is always a bug.
- You just fixed a false-green harness and a wave of "new" failures appeared — you need the aftermath protocol.
- You need to prove a harness fix actually detects failures (red-green proof) before trusting it.

## Verified Workflow

> Verified locally on 2026-07-16/17 against HomericIntelligence/Odyssey PR #5625 — the fixed
> harness detected 9 Mojo test files that had never compiled; red-green proof runs recorded in
> that PR. CI validation of this skill file itself is pending.

### Quick Reference

```bash
# THE BUG: $? inside the then-branch reads the NEGATED condition's status.
# On failure, `! cmd` succeeds, so $? is 0 — every failure counts as a pass.
if ! mojo run "$f"; then
  test_exit=$?     # ALWAYS 0 here. Failure is silently converted to a pass.
fi

# THE FIX: capture rc directly, outside any negation.
set +e
mojo run "$f"
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  passed=$((passed+1)); echo "PASSED: $f"
else
  failed=$((failed+1)); echo "FAILED (exit $rc): $f"
fi

# ACCOUNTING GUARD: make "neither pass nor fail" impossible.
[ $((passed+failed)) -eq $total ] || { echo "accounting mismatch"; exit 1; }
[ "$failed" -eq 0 ] || exit 1
```

### Detailed Steps

1. **Detection — never trust the job summary.** Pull the ACTUAL job log
   (`gh run view <id> --log`) and grep for per-file evidence: `error:`,
   `failed to parse`, and per-file `PASS`/`FAIL` verdict lines. A summary line like
   `Total: 82, Passed: 82, Failed: 0` is derived from the counters the buggy loop
   maintains — it is not evidence any test executed successfully.
2. **Know what your validators prove.** Glob-coverage validators (e.g. a
   `validate_test_coverage.py` that checks every source file has a matching test file)
   prove MEMBERSHIP, not EXECUTION. A test file can be counted as "covered" while it has
   never compiled.
3. **Audit the loop for the negated-if idiom.** `grep -rn 'if !' justfile Makefile scripts/`
   and inspect every hit that reads `$?` in the then-branch. In
   `if ! cmd; then rc=$?; fi`, `$?` is the exit status of the negated condition, which is
   0 whenever `cmd` failed — the exact inversion of what the author intended.
4. **Apply the fix pattern.** Replace with direct capture: `set +e; cmd "$f"; rc=$?; set -e`,
   then branch on `$rc`, incrementing `passed` or `failed` and printing a per-file
   `PASSED:` / `FAILED (exit N):` line so logs carry per-file evidence forever after.
5. **Add the accounting guard.** After the loop:
   `[ $((passed+failed)) -eq $total ] || exit 1`. This makes a third silent state
   ("neither counted as pass nor fail") structurally impossible.
6. **MANDATORY red-green proof of the harness fix.** Commit a deliberately broken scratch
   test file. Show the OLD recipe reports `Passed: 1 / exit 0` on it and the FIXED recipe
   reports `Failed: 1 / exit 1`. Then remove the scratch file. Document both run IDs in the
   PR — without this proof you have no evidence the fix detects anything.
7. **Aftermath protocol — do NOT mask the exposed failures.** The fix exposes every
   previously masked failure at once (Odyssey: 9 files that had never compiled, including
   broken imports like `from any_tensor import zeros` where `zeros` actually lives in
   `tensor_creation`, a test file with no `main()`, plus genuinely failing tests). Fix
   mechanical breakage (imports, missing `main()`), and leave genuine test failures VISIBLE
   as tracked follow-ups. Expect LAYERED peeling: each fix surfaces the next stratum
   (doc-lint errors under `--Werror`, reserved keywords like `var ref`, etc.).
8. **Grep all siblings for the same defect idiom.** When one file has a defect idiom, the
   files written alongside it usually share it (6 more Odyssey files had the identical
   broken import). Grep the whole tree, not just the file that failed.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust green CI | Relied on "all checks green" plus a glob-coverage validator to conclude tests were healthy | The coverage validator proves a test file EXISTS for each source file, not that it EXECUTED; the harness bug converted every failure into a pass, so the gate was green for weeks over 9 never-compiled files | Only log-level evidence counts: grep the actual job log for per-file compile/run verdicts, never the summary line |
| Blanket regex lint fix | Applied a file-wide regex substitution to fix docstring lint errors in one pass | The `\s*` in the pattern matched past closing quotes and mangled code lines (`from` became `From`, `print` became `Print`) | Make line-targeted edits driven by the lint error list; afterwards grep for damaged keywords (e.g. `^[A-Z]` on lines that should start lowercase) to verify no collateral edits |
| Assume siblings are fine | Fixed the one file that surfaced the broken `from any_tensor import zeros` import and moved on | 6 more files contained the identical broken import — they were generated/written in the same batch | When one file has a defect idiom, grep ALL sibling files for the same idiom before declaring the fix complete |

## Results & Parameters

### Buggy justfile recipe (before)

```bash
# Counts every failure as a pass: $? is the negation's status, always 0 on failure.
for f in $test_files; do
  test_exit=0
  if ! mojo run "$f"; then
    test_exit=$?    # BUG: always 0 here
  fi
  if [ "$test_exit" -eq 0 ]; then passed=$((passed+1)); else failed=$((failed+1)); fi
done
```

### Fixed recipe (after)

```bash
set +e
total=0; passed=0; failed=0
for f in $test_files; do
  total=$((total+1))
  mojo run "$f"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    passed=$((passed+1)); echo "PASSED: $f"
  else
    failed=$((failed+1)); echo "FAILED (exit $rc): $f"
  fi
done
set -e
echo "Total: $total, Passed: $passed, Failed: $failed"
[ $((passed+failed)) -eq $total ] || { echo "ERROR: accounting mismatch"; exit 1; }
[ "$failed" -eq 0 ] || exit 1
```

### Detection greps

```bash
# Find the defect idiom anywhere in the repo
grep -rn 'if !' justfile Makefile scripts/ .github/ | grep -n '\$?'

# Pull real evidence from the CI log instead of the summary
gh run view <run-id> --log | grep -E 'error:|failed to parse|^(PASSED|FAILED)'

# After a regex-based lint fix, check for keyword damage
grep -rnE '^(From|Print|Import|Return) ' <edited-files>
```

### Observed impact (Odyssey PR #5625, 2026-07-16/17)

- Before fix: harness reported `Total: 82, Passed: 82, Failed: 0` and SUCCESS.
- After fix: 9 test files exposed as failing to compile (broken imports, one file with no
  `main()`, genuine failures), masked for weeks.
- Red-green proof: scratch broken test — old recipe `Passed: 1`, exit 0; fixed recipe
  `Failed: 1`, exit 1; scratch file then removed. Run IDs documented in the PR.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Odyssey | PR #5625 — CI Mojo test harness false-green fix, 2026-07-16/17 | Fixed recipe exposed 9 never-compiled test files; red-green proof runs recorded in the PR |
