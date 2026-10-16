---
name: shell-negation-exit-status-capture
license: BSD-3-Clause
description: "Preserve the real command status in shell harnesses, retry wrappers, and CI. Use when: (1) a loop uses `if ! command; then status=$?`, (2) summaries report success while commands fail, (3) pass/fail counters need a non-vacuous accounting invariant, or (4) a retry wrapper decides success by matching command output text instead of the exit status."
category: ci-cd
date: 2026-08-07
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [shell, bash, exit-status, false-green, ci, test-harness, retry, idempotency]
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
- A retry wrapper decides whether an attempt succeeded by `grep`-ing the command's output rather than by testing `$?`.
- A wrapper re-runs a **mutating** command (create, comment, push, tag, publish, delete) after an ambiguous result.

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

### Retry wrappers: classify by exit status, never by output text

A retry loop that tests `if echo "$out" | grep -q MARKER` throws away the one signal that is
authoritative. Output text is a **presentation** artifact: it is produced by the tool, its wording
changes between versions, and — critically — an error message frequently contains the very token the
wrapper greps for.

```bash
# WRONG: the outcome is inferred from output text.
for attempt in 1 2 3; do
  out=$(mutating_call 2>&1) || true
  if echo "$out" | grep -q "created"; then ok=1; break; fi
done

# RIGHT: the exit status decides; output is only ever reported.
for attempt in 1 2 3; do
  out=$(mutating_call 2>&1); rc=$?          # capture immediately
  if [ "$rc" -eq 0 ]; then ok=1; break; fi
done
```

Two failure modes follow from the wrong form, and both are silent:

| Defect | Mechanism | Consequence |
| ------ | --------- | ----------- |
| False negative | The success token differs from what was grepped (a URL value, a ref name, a different verb). | The loop "fails" an attempt that already succeeded and **re-runs the mutation**, producing a duplicate: a second comment, a second tag, a second publish. |
| False positive | The rejection message *contains* the success token (ref updates and rejections both print a `from -> to` arrow; errors are echoed with their text). | The loop declares **success on a rejected write** and skips the recovery it owed, so the failure is reported to the requester as done. |

**Contract for a mutating retry wrapper:**

1. Capture `$?` on the line immediately after the command. No assignment, pipe, or logging may
   intervene.
2. Branch on the status alone. Capture output into a variable for reporting; never `grep` it.
3. Test the exit status **before** the first retry decision, not only at the end.
4. A status of `0` is necessary but not sufficient for a mutating call that is safe to assume: when
   the wrapper cannot distinguish "rejected" from "accepted", read the target back (see below).

**Read back before retrying a mutation.** After an ambiguous or apparently failed mutation, query the
target with a read-only call before re-running anything. If the effect is already present, the first
attempt succeeded — report completion from that evidence and remove the duplicate if one was created.
Only re-invoke once when the read shows the effect is absent AND the operation is idempotent or
guards completed work. If no read-only probe exists, or the state matches neither hypothesis, stop
and report both with evidence instead of retrying.

This is the same rule as the counter case above, applied to a different consumer: in both, the exit
status is the signal and everything else is commentary. When the status is genuinely unobservable —
output truncated by a display layer, or a delegated command whose contract forbids parsing output —
reconciliation is the only recovery, and the wrapper must not guess from partial text.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Capture after `!` | Used `if ! run_case; then rc=$?` | The shell stored the negation's successful status, so failures counted as passes | Capture the unmodified command status directly |
| Trust only the summary | Accepted green aggregate output without checking item logs | The aggregation logic itself was defective | Add a red-path proof and an accounting invariant |
| Leave `set -e` enabled around capture | Ran a failing command before assigning its status | The shell exited before the harness could classify the result | Bound `set +e` narrowly around deliberate failure capture |
| Grep the output for the success token | Classified a retry attempt with `if echo "$out" \| grep -q "created"` after a create call | The wrapper's marker never matched the value the command actually printed, so a successful create was judged a failure and **re-run**, leaving two comments on the target | Branch on `$?`. Output text is presentation, not status, and is not a stable success signal |
| Grep a token the error message also contains | Classified a ref update with `grep -qE "new branch|->"`, matching the arrow that a *rejection* also prints | The wrapper reported "PUSH OK" for a push the remote had **rejected**, and the rejection was never investigated | A rejection message contains the same tokens as a success. Test the status; on nonzero, report the rejection instead of asserting success |

## Results & Parameters

| Exit | Meaning |
|------|---------|
| `0` | Every case passed and accounting matched |
| `1` | At least one case failed |
| `2` | Harness accounting was internally inconsistent |

The exact nonzero codes are configurable; the durable contract is that a known failing case cannot produce a successful harness result.

### Retry wrapper contract

| Rule | Why it is REQUIRED |
| ---- | ------------------- |
| Classify an attempt by `$?`, captured on the immediately following line | It is the only authoritative completion signal the process reports |
| Never `grep` the output for a success marker | Output is presentation: its wording varies, and rejection messages repeat success tokens |
| Test the status before the first retry decision | A late exit check still permits a duplicate mutation on the first attempt |
| Read the target back before re-running a mutation | A status of `0` on an ambiguous mutating call cannot prove the effect landed |
| Re-invoke at most once, and only when idempotent or guarded | A second run on an already-applied mutation double-applies or repeats an irreversible step |
| Stop and report when no read-only probe exists | Guessing converts an unknown outcome into a wrong one |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Compiler-driven test harness | Per-file test loop | A deliberately failing case exposed the false-green pattern; direct status capture restored correct pass/fail totals. |
| Agent session, remote write retries | Retry wrapper around a comment-create call, then a ref-update call | A marker-based success check posted the comment twice (false negative); the duplicate was found by listing the target's comments and removed. The same pattern reported success for a rejected ref update (false positive) because the rejection text carried the matched arrow. Both were replaced with status capture plus a read-back before retry. **verified-local** (both defects reproduced and corrected in session). |

## References

- `reconcile-before-retry-mutation-status-loss` (companion entry, tracked separately) — the complementary half: when the terminal status is genuinely unobservable (truncated output, or an opaque delegated command), reconcile target state before retrying. This entry covers preventing the ambiguity in the case where the status *is* available.
