---
name: shell-negation-exit-status-capture
license: BSD-3-Clause
description: "Preserve the real command status in shell test and CI harnesses. Use when: (1) a loop uses `if ! command; then status=$?`, (2) summaries report success while commands fail, or (3) pass/fail counters need a non-vacuous accounting invariant."
category: ci-cd
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [shell, bash, exit-status, false-green, ci, test-harness]
---

# Shell Negation Exit-Status Capture

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-07 |
| Objective | Stop shell harnesses from converting command failures into false passes. |
| Outcome | Capture the command's status before applying boolean negation, then validate summary accounting and the final job result. |

## When to Use

- A test loop contains `if ! command; then rc=$?`.
- Per-item logs show failures but the final summary says `Failed: 0`.
- A compiler or test runner may fail before executing the test body.
- CI trusts aggregate counters rather than the command statuses that produced them.

## Verified Workflow

### Quick Reference

```bash
set +e
passed=0
failed=0
total=0

for case_path in "$@"; do
  total=$((total + 1))
  run_case "$case_path"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
  fi
done

set -e
[ $((passed + failed)) -eq "$total" ] || exit 2
[ "$failed" -eq 0 ] || exit 1
```

In `if ! command; then ...`, `$?` inside the branch is the status of the negated condition, not the original failing command. A failure therefore becomes zero before it is stored.

1. Run the command without `!` when its exact status is needed.
2. Temporarily disable immediate exit only around the status-capture region.
3. Capture `$?` immediately; no logging, assignment, or condition may intervene.
4. Count every input exactly once as pass or fail.
5. Assert `passed + failed == total` before emitting the final verdict.
6. Prove the harness with one known-success command and one known-failure command. The latter must make the harness nonzero.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Capture after `!` | Used `if ! run_case; then rc=$?` | The shell stored the negation's successful status, so failures counted as passes | Capture the unmodified command status directly |
| Trust only the summary | Accepted green aggregate output without checking item logs | The aggregation logic itself was defective | Add a red-path proof and an accounting invariant |
| Leave `set -e` enabled around capture | Ran a failing command before assigning its status | The shell exited before the harness could classify the result | Bound `set +e` narrowly around deliberate failure capture |

## Results & Parameters

| Exit | Meaning |
|------|---------|
| `0` | Every case passed and accounting matched |
| `1` | At least one case failed |
| `2` | Harness accounting was internally inconsistent |

The exact nonzero codes are configurable; the durable contract is that a known failing case cannot produce a successful harness result.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Compiler-driven test harness | Per-file test loop | A deliberately failing case exposed the false-green pattern; direct status capture restored correct pass/fail totals. |
