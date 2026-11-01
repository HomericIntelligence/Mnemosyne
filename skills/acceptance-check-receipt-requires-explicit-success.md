---
name: acceptance-check-receipt-requires-explicit-success
description: "Require each acceptance or stop-rule check to print an explicit success or failure receipt. Use when: (1) a procedure, gate, or runbook says a check passes when it prints nothing, (2) a check wraps a command whose failure leaves empty stdout, such as an archive extract, a pipe into a hashing or diff tool, or a filtered listing, (3) a clean-worktree check must also prove no tracked, staged, or untracked leftover exists, or (4) a documented path binding or citation must still exist at the committed revision."
category: testing
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - acceptance-criteria
  - fail-open
  - fail-closed
  - silent-pass
  - empty-stdout
  - bash
  - shell-check
  - git-status
  - porcelain
  - cat-file
  - runbook
  - stop-rule
  - stale-path-binding
---

# Acceptance Check Receipt Requires Explicit Success

**Supporting cases:** [notes](./acceptance-check-receipt-requires-explicit-success.notes.md)

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-01 |
| **Objective** | Stop a procedure that treats empty check output as a pass from passing when its input is missing. |
| **Outcome** | Five findings on one acceptance-criteria procedure were fixed: a guard for an absent archive directory, an explicit success or failure receipt, a clean check with full `git status` coverage, an `absent` value for a missing git blob, and a re-bound document path. A staged run proved each branch. |

## When to Use

- A procedure says "the check prints nothing when it passes", "silence means success", or "the cut stops when a check prints output".
- A check runs a pipeline whose first stage can fail without writing to stdout: `git archive | tar -x`, `git show | sha256sum`, `command | diff -rq`, or `find ... |` into a filter.
- A "clean checkout" check must catch an untracked leftover workaround file, not only a tracked modification.
- A documented path binding (a `git:<rev>:<path>` digest, a cited decision record, a `git show` target) must resolve at the committed revision.

Do not use this rule to make a check print noise on every run. The goal is one receipt per failure, and silence on success.

## Verified Workflow

### Quick Reference

```bash
# Print a receipt when the producer of a pipeline can fail and leave stdout empty.
git archive "$REV" "$DIR" | tar -x -C "$T"
[ -d "$T/$DIR" ] || echo "input not present at $REV"   # receipt, not silence
diff -rq "$T/$DIR" "$INSTALLED" | ...                    # compare only after the guard

# Hash a git blob and report an explicit absence, not the empty-stream digest.
git cat-file -e "$REV:$PATH" 2>/dev/null || { echo absent; return; }
git show "$REV:$PATH" | sha256sum | cut -c1-64

# Cover the full worktree state: modifications, staged changes, deletions, untracked files.
git status --porcelain --untracked-files=all --no-renames | cut -c4- | while read -r q; do
  exempt "$q" || echo "DIRTY $q"
done

# Prove a documented path still exists at the committed revision before you rely on it.
git cat-file -e "$REV:$DOC_PATH" && echo "path present" || echo "path missing"
```

### Suggested Approach

1. Classify the check. A pass is silent, a failure prints a line. Any command whose failure leaves stdout empty makes the check fail open.
2. Put one guard before each such command. Assert the input exists and print a receipt on the standard output stream, not only on stderr. A consumer that reads stdout, or a stop rule that scans stdout, never sees a stderr message.
3. Guard the empty-stream case for a hashing or comparison pipeline. For git objects, test existence with `git cat-file -e` and emit an explicit absence value. An absent value must match what the record schema expects, so the fallback branch is reachable.
4. Cover the whole state, not part of it. Replace a diff-against-HEAD check with a status check that includes untracked files, then strip the two-character status prefix before you compare paths.
5. Re-verify every documented path binding and citation against the committed revision. A file move or a deleted document tree makes the old binding fail at run time with a confusing error.
6. Run the changed blocks in a staged harness. Build a throwaway repository with the bad input, the empty input, and the good input. Require that each bad case prints its receipt and the good case prints nothing.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| 1 | Rely on `diff` or `sha256sum` stderr to signal a missing input. | The stop rule reads stdout. Stderr output leaves the check looking passed and the cut does not stop. | Emit the receipt on stdout with an explicit condition test before the pipeline runs. |
| 2 | Hash `git show rev:path` directly. | A missing blob gives empty input and the digest of the empty string. The record then shows a mismatch instead of an absence, and the absence fallback is unreachable. | Test the object first with `git cat-file -e` and return the absent value. |
| 3 | Use `git diff --name-only HEAD` as the clean check. | The command lists tracked changes only. An untracked leftover worktree file passes. | Use `git status --porcelain --untracked-files=all --no-renames` and strip the status prefix. |

## Results & Parameters

### Configuration

```text
Receipt form    one stdout line per failure; no line on success
Absence value   the literal the record schema already expects, for example absent
Status read     git status --porcelain --untracked-files=all --no-renames | cut -c4-
Blob existence  git cat-file -e <rev>:<path> 2>/dev/null
```

### Expected Output

- Bad input: one receipt line on stdout, and the stop rule fires.
- Good input: no output.
- A missing git object: the record reports the absence value, not a hash mismatch.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal release procedure | A release-cut acceptance procedure with six review findings | Five fixes passed a staged harness of the changed blocks. See [notes](acceptance-check-receipt-requires-explicit-success.notes.md). |

## References

- [Stale documentation audit and broken reference repair](stale-documentation-audit-and-broken-reference-repair.md)
- [Bash script and jq failure modes](bash-script-and-jq-failure-modes.md)