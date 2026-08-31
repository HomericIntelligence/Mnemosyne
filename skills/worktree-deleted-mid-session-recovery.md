---
name: worktree-deleted-mid-session-recovery
license: BSD-3-Clause
description: "Use this skill when a linked Git worktree path is missing or the current directory is invalid. It classifies recoverable refs and per-worktree state before metadata cleanup, repair, or reconstruction."
category: ci-cd
date: 2026-06-23
version: "2.0.0"
user-invocable: false
verification: verified-local
history: worktree-deleted-mid-session-recovery.history
tags:
  - git
  - worktree
  - cwd
  - FileNotFoundError
  - recovery
  - prune
  - repair
  - stale-metadata
  - detached-head
  - index
  - checkpoint
---

# Worktree Deleted Mid-Session Recovery

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-06-23 |
| **Objective** | Recover a missing linked worktree without overstating which data Git can restore |
| **Outcome** | Restore persisted Git state and identify state that needs separate recovery |
| **Verification** | verified-local against official Git documentation and a disposable repository |

A missing worktree path can invalidate a shell's current directory. Programs
that call `getcwd` can then fail before they perform their work.

Git keeps administrative data for each linked worktree in the common
repository. `git worktree prune` removes eligible administrative entries whose
registered paths are already missing. It does not delete a working-tree
directory. If a worktree moved, repair its registration instead of pruning it.

Re-adding a verified local branch creates a fresh worktree and index at the
commit that the shared branch ref names. It does not reconstruct a prior index,
a detached per-worktree `HEAD`, unstaged changes, untracked files, ignored
files, or other worktree-only state.

## When to Use

- The current directory no longer exists, and `pwd`, `Path.cwd()`, or
  `os.getcwd()` fails.
- `git worktree list` shows a registered path that is absent from the file
  system.
- `git worktree add` reports that a branch belongs to a missing worktree.
- You must determine what remains recoverable after a worktree path disappears.
- You need a durable checkpoint before unattended work or external review.

## Verified Workflow

### Quick Reference

```bash
# Move to a directory that exists.
cd "<repository-root>"

# Inspect the registration and verify the shared branch ref.
git -C "<repository-root>" worktree list --porcelain -z
test ! -e "<registered-worktree-path>"
git -C "<repository-root>" reflog show --all --format='%H %gd %gs'
git -C "<repository-root>" show-ref --verify "refs/heads/<branch>"
git -C "<repository-root>" rev-parse "refs/heads/<branch>"

# Only after you classify every reported candidate, preview and prune metadata.
git -C "<repository-root>" worktree prune --dry-run --verbose --expire now
git -C "<repository-root>" worktree prune --verbose --expire now

# Recreate and verify the branch checkout.
git -C "<repository-root>" worktree add "<replacement-path>" "<branch>"
git -C "<replacement-path>" branch --show-current
git -C "<replacement-path>" rev-parse HEAD
git -C "<replacement-path>" status --short
```

### Detailed Steps

1. **Move to an existing directory.** Use an absolute repository path. Do this
   before you run a tool that resolves the current directory.

2. **Inspect the registration.** Read `git worktree list --porcelain -z`.
   Compare each registered path with the file system. Automation must preserve
   the NUL-delimited records. Verify the expected shared ref separately. Do not
   infer which process removed or moved the path from a stale registration.

3. **Classify all recoverable state before prune.** Use these categories:

   - A verified shared ref, such as a local branch, tag, or stash.
   - A commit that only a per-worktree `HEAD` or reflog records, such as a
     detached commit.
   - State that only the per-worktree index records.
   - Unstaged, untracked, or ignored bytes that only the worktree contains.
   - A worktree on moved or temporarily unavailable storage.

   The porcelain `HEAD` field shows the current commit for each worktree. Also
   inspect all reflogs before prune:

   ```bash
   git -C "<repository-root>" reflog show --all --format='%H %gd %gs'
   ```

   Review entries named `worktrees/<worktree-id>/HEAD@{...}` for the affected
   worktree. These entries can name earlier detached commits that the worktree
   list does not show. Preserve each needed commit with a shared ref before
   prune:

   ```bash
   git -C "<repository-root>" cat-file -e "<recorded-head>^{commit}"
   git -C "<repository-root>" branch "recovery/<name>" "<recorded-head>"
   ```

   If the per-worktree index can contain unique staged state, stop before
   prune. Prune removes that index and its pathname-to-object mappings. The
   blob objects are not erased immediately, but they can become unreachable
   and can later be garbage-collected. Use approved object or backup recovery
   before metadata cleanup.

4. **Stop for a locked or moved worktree.** A lock can indicate offline or
   removable storage. Locate or mount that storage first. If the worktree moved
   and is accessible, repair the registration:

   ```bash
   git -C "<repository-root>" worktree repair "<moved-worktree-path>"
   ```

   Do not unlock, prune, or use double force until you know the data
   disposition.

5. **Preview every prune candidate.** `git worktree prune` operates on all
   eligible missing entries, not only the target entry. `--expire now` includes
   a recently stale registration. Review every line from the dry run. If any
   candidate has unclassified state, stop. Use the same `--verbose` and
   `--expire now` options for the actual prune.

6. **Re-add only a verified shared branch.** Do not use `--force` to bypass a
   live registration. If another existing worktree owns the branch, stop.
   Re-adding creates a fresh index from the commit at `refs/heads/<branch>`.

7. **Verify the reconstructed state.** Confirm the current branch, the
   worktree `HEAD`, the shared branch ref, and the status. The worktree `HEAD`
   and shared branch ref must name the same commit. Do not claim that re-add
   restored state that was not reachable from the verified ref.

8. **Restore a stash separately.** Inspect it before you apply it. Only when
   you also intend to restore its staged state, use `--index`.

   ```bash
   git -C "<replacement-path>" stash list
   git -C "<replacement-path>" stash show --stat --include-untracked \
     "<stash-reference>"
   git -C "<replacement-path>" stash show --patch --include-untracked \
     "<stash-reference>"
   git -C "<replacement-path>" stash apply --index "<stash-reference>"
   ```

9. **Create a checkpoint before a session boundary.** A commit on a named
   branch is stronger than a stash. When repository policy permits it, push
   the branch. Add only reviewed paths.

   ```bash
   git -C "<worktree-path>" status --short
   git -C "<worktree-path>" add "<reviewed-path>"
   git -C "<worktree-path>" commit -m "chore: checkpoint work"
   git -C "<worktree-path>" rev-parse HEAD
   ```

   If a commit is not permitted, use a verified stash as a temporary
   checkpoint:

   ```bash
   git -C "<worktree-path>" stash push --include-untracked \
     -m "checkpoint before session boundary"
   git -C "<worktree-path>" stash list
   ```

   `--include-untracked` does not include ignored files. Only when you
   intentionally need those files and policy permits their storage, use
   `--all`. A digest can verify retained bytes, but it does not preserve them.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Blaming prune for directory deletion | Treated stale metadata as proof that prune removed the working tree | Prune removes eligible administrative entries for paths that are already missing | Investigate the actor that removed or moved the path separately |
| Re-adding before metadata cleanup | Retried add or considered force | Git still assigned the branch to the missing registration | Classify state, preview prune, and remove only eligible stale metadata |
| Assuming re-add restores all work | Expected a fresh checkout to contain prior staged, unstaged, or untracked state | Add creates a fresh index from a ref; it does not reconstruct prior per-worktree state | Classify every persistence boundary first |
| Pruning before preserving unique state | Removed a per-worktree `HEAD`, reflog, or index before recovery | Detached commits and index mappings can be the only names for unique data | Preserve or recover unique state before prune |
| Treating a locked path as stale | Unlocked or forced a missing locked registration | The worktree could be moved or temporarily offline | Locate storage and use repair when applicable |
| Reviewing only the target path | Assumed prune affected one registration | Prune processes every eligible missing registration | Review and classify every dry-run candidate |

## Results & Parameters

| State | Recovery action |
| --- | --- |
| Commit reachable from a verified local branch | Re-add that branch at a replacement path |
| Commit reachable only from per-worktree `HEAD` or reflog | Create a shared recovery ref before prune |
| Stash entry | Inspect it and apply the selected stash separately |
| Possible unique staged state | Stop before prune and recover the per-worktree index mappings |
| Worktree-only bytes | Use an approved backup or file-system recovery source |
| Moved or offline worktree | Restore access and run `git worktree repair` |
| Eligible stale registration | Review all dry-run candidates, then prune with the same options |

Recovery is successful only when all of these conditions are true:

- The replacement or repaired path appears in `git worktree list`.
- The worktree `HEAD` matches the intended verified ref.
- The status and all remaining recovery limits are understood.
- Tools no longer fail because of an invalid current directory.
- The result does not claim recovery of bytes that were never persisted.

## References

- [`git-worktree` documentation](https://git-scm.com/docs/git-worktree)
- [Git repository layout](https://git-scm.com/docs/gitrepository-layout)
- [`git-stash` documentation](https://git-scm.com/docs/git-stash)
- [`git-fsck` documentation](https://git-scm.com/docs/git-fsck)
- [`git-prune` documentation](https://git-scm.com/docs/git-prune)
