---
name: probe-mutation-restore-verification
description: "Run a temporary source-mutation probe that proves a regression test fails without the production change, and prove clean restoration afterward. Use when: (1) a test must fail on the reviewed base commit, (2) the delivery channel is uncommitted worktree state that an automation orchestrator commits, (3) a backup-based restore must be proven against the version-control object database, or (4) a probe cleanup step failed and the mutation may survive in the tree."
category: testing
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags:
  - mutation-testing
  - regression-test
  - base-bound-test
  - worktree
  - git
  - orchestrator-handoff
  - restore-verification
  - clean-tree
  - probe-hygiene
---

# Probe Mutation Restore Verification

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-30 |
| **Objective** | Prove that a regression test fails without the production change by mutating tracked source, and return the worktree to the exact delivered state. |
| **Outcome** | Operational. The probe showed the expected failure (`1 failed, 1 passed`), the source was restored, and restoration was proven by a byte comparison against the committed blob plus an empty diff. One probe attempt initially left the mutation in the tree because the backup target did not exist; the explicit object-database check caught it before handoff. |
| **Verification** | verified-local |

## When to Use

- A review demands a test that fails on the reviewed base commit, and the cheapest proof is to remove or weaken the production branch in place.
- An automation orchestrator commits the worktree state after the agent turn, so an unrestored mutation would enter the reviewed change.
- A restore used a file copy, and trust in the restore must not rest on the copy command's exit status.
- You inherit a tree after probes and must decide whether it is safe to hand off.
- A reviewer asks for evidence that a test is a real regression guard, not a documentation of existing behavior.

## Verified Workflow

### Quick Reference

```bash
# 1. Prefer a scratch copy outside the repository when the probe can run there.
cp -a <worktree> <scratch-root>/probe-copy

# 2. If the probe must mutate in-tree, prepare and check the backup first.
mkdir -p <backup-root>/probe513            # create the target before any mutation
cp src/<changed>.py <backup-root>/probe513/changed.py.orig
cmp src/<changed>.py <backup-root>/probe513/changed.py.orig   # backup is real

# 3. Mutate the minimum branch, then run the focused tests.
.venv/bin/python -m pytest tests/<file>.py::<test> --override-ini="addopts=" -q

# 4. Restore, then prove restoration against the object database, not the copy.
cp <backup-root>/probe513/changed.py.orig src/<changed>.py
git show HEAD:src/<changed>.py | cmp - src/<changed>.py       # must be silent
git diff --quiet -- src/<changed>.py                          # exit 0
git status --short --untracked-files=all                      # no probe residue
```

### Suggested Approach

1. **Prefer a scratch copy.** Copy the repository to a scratch root outside the checkout and mutate there. Use this whenever the probe does not need the delivered worktree's uncommitted state. This removes all risk to the delivered change.
2. **Prepare the backup before the mutation.** Create the backup directory, copy the file, and compare the copy with `cmp` before you change anything. A backup command chained as a fallback (`cp || (mkdir && cp)`) can run after a failed first branch and leave no usable copy.
3. **Mutate the minimum.** Replace only the branch under test, keep the rest of the function intact, and record the exact replacement text. Run only the focused tests that the probe targets.
4. **Restore with proof.** Copy the backup back, then confirm restoration with `git show HEAD:<path> | cmp - <path>` and `git diff --quiet -- <path>`. A successful `cp` is not proof: the source of the copy can itself be stale or wrong.
5. **Treat a failed restore as a stop condition.** If any check in step 4 fails, repair immediately and report the incident. Do not hand off a tree with an unexplained diff.
6. **Report the probe honestly.** State the mutation, the focused result with the mutation in place, and the restoration evidence. A probe result on mutated source is historical evidence, not a result for the delivered head.

Note: keep the probe environment synchronized before the run. A `uv`-managed environment can lose development extras between commands; see `uv-offline-validation-sync-first`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Create the backup in the same compound command as the mutation with fallback chaining: `cp file backup 2>/dev/null \|\| (mkdir -p dir && cp file backup)`. | The first `cp` failed, the fallback `mkdir` did not produce the directory in time, and the restore `cp` later failed with "No such file or directory". The mutated source survived in the tree. | Create and check the backup target before any mutation. A fallback chain is not a backup procedure. |
| 2 | Trust the restore from the copy command's success and from memory of the edit. | The restoration was not proven until an explicit byte comparison against `git show HEAD:<path>` ran; the first restore attempt had failed silently after a broken backup path. | Prove restoration against the version-control object database with `cmp` and an empty diff. Exit status is not evidence. |
| 3 | Run the probe directly in the shared worktree although a scratch copy could have hosted it. | The delivered uncommitted state was put at risk for no benefit, and the restore step became the safety net instead of isolation. | Copy the tree to a scratch root first; mutate in-tree only when the probe needs the delivered uncommitted state. |

## Results & Parameters

### Configuration

```bash
# Probe contract for one tracked source file, generalized:
PROBE_FILE="src/<changed>.py"
BACKUP_DIR="<scratch-root>/probe-backup"

mkdir -p "$BACKUP_DIR"
cp "$PROBE_FILE" "$BACKUP_DIR/$(basename "$PROBE_FILE").orig"
cmp "$PROBE_FILE" "$BACKUP_DIR/$(basename "$PROBE_FILE").orig"
# ... apply the minimum mutation ...
# ... run the focused tests ...
cp "$BACKUP_DIR/$(basename "$PROBE_FILE").orig" "$PROBE_FILE"
git show "HEAD:$PROBE_FILE" | cmp - "$PROBE_FILE"
git diff --quiet -- "$PROBE_FILE"
git status --short --untracked-files=all
```

### Expected Output

- With the production branch removed: the focused test fails with the guard's own message, for example `1 failed, 1 passed`.
- With the production branch in place: the same focused tests pass.
- After restoration: `cmp` is silent, `git diff --quiet` exits 0, and `git status` lists no probe residue.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| An automation-fleet CLI repository | Regression-guard hardening for a key-listing command; probe removed the database branch of the list function | Probe gave `1 failed, 1 passed`; restoration proven with `git show HEAD:` byte comparison (`matches HEAD: True`) and an empty diff; see [notes](probe-mutation-restore-verification.notes.md). |

## References

- [checkout-other-ref-silent-file-clobber](checkout-other-ref-silent-file-clobber.md) — adjacent silent state loss from `git checkout <ref> -- <path>`.
- [automation-clean-checkout-intermediate-artifacts](automation-clean-checkout-intermediate-artifacts.md) — cleanliness gate for the handoff tree.
- [uv-offline-validation-sync-first](uv-offline-validation-sync-first.md) — keep the probe environment synchronized.
