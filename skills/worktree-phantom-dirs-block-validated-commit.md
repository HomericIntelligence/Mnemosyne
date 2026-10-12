---
name: worktree-phantom-dirs-block-validated-commit
license: BSD-3-Clause
description: "Recover a commit that a whole-tree validator blocks on phantom cache-only directories left in a worktree by a file-deleting checkout move. Use when git status is clean but the commit still fails a tree validator or repository layout gate."
category: tooling
date: 2026-10-12
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [git, worktree, phantom-dirs, pycache, gitignore, pre-commit, tree-validator, layout-gate, checkout, branch-move, commit-failure, untracked]
---

# Worktree Phantom Directories Block a Validated Commit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-12 |
| **Objective** | Recover a commit that fails a whole-tree validator although every git status mode shows a clean tree except the intended changes. |
| **Outcome** | Operational. Removed cache-only phantom directories; the commit hook suite passed and the work was preserved. |
| **Verification** | verified-local on a real incident: a suite of more than 3,000 tests failed exactly 2 layout tests; commit succeeded after cleanup. |

A checkout move (rebase, fast-forward, branch reset, or a new checkout across a
file-deleting change) removes the tracked files that Git owns. It does not
remove unowned leftover content. Directories whose entire remaining content is
ignored, typically `__pycache__` from an interpreter, stay on disk as invisible
phantom directories. Whole-tree validators that require every retained directory
to contain real source then fail the commit. Default `git status` cannot show
these directories because Git tracks files, not directories, and status hides
ignored files.

## When to Use

- A commit in a worktree fails because a repository validator (a test-layout
  gate, a packaging guard, or a "no content-free directories" check) flags
  directories under the tree.
- `git status --porcelain`, `--untracked-files=all`, and
  `git ls-files --others` show nothing beyond the intended changes, yet the
  validator reports real directories by name.
- The branch of the worktree recently moved across a change that deleted
  tracked files under the flagged directories.
- A hook framework shows the last listed hook as Passed, but `git commit`
  still exits nonzero and the visible output has no error near its end.

## Verified Workflow

### Quick Reference

```bash
# 1. Capture the COMPLETE hook output. A tail slice hides the failed hook,
#    because the hook framework runs hooks in parallel and buffers each report.
git commit ... > commit.log 2>&1
echo "EXIT=$?"
grep -nE "Failed|FAILED|Traceback" commit.log

# 2. Confirm each flagged directory holds only ignored cache content.
#    No output means every remaining file is a cache artifact.
find <flagged-dir> -type f ! -path '*__pycache__*' ! -name '*.pyc'

# 3. Remove the cache-only directories. rmdir is safe: it fails if any
#    non-cache content remains.
find <flagged-dir> -type d -name __pycache__ -prune -exec rm -rf {} +
rmdir <flagged-dir>

# 4. Re-run the blocked commit. The hook suite re-runs and passes.
git commit ...
```

Audit alternative for all ignored on-disk content that a whole-tree validator
can see but `git status` cannot:

```bash
git clean -ndX <path>   # dry run; lists ignored files and directories only
```

### Suggested Approach

- Diagnose from complete output, not from a tail slice. The report of a failed
  hook can appear much earlier in the stream than the last passing hook, and
  buffered per-hook output keeps the failure out of the visible tail. Search
  the full log for failure markers before you classify the problem.
- Confirm that removal is safe before any delete. Removal is safe when both
  conditions hold: `find <dir> -type f` prints nothing after you exclude cache
  patterns, and `git ls-files <dir>` is empty. Remove `__pycache__` subtrees
  first, then use `rmdir` on the top-level directory so an unexpected file
  stops the operation instead of being deleted.
- Keep the distinction from admission-side cleanliness: expected generated
  artifacts belong under a reviewed ignore rule or outside the checkout (see
  the related skill below). Phantom leftovers are not expected artifacts. They
  track no content, they weaken no gate, and deleting them changes nothing
  that Git owns.
- If a concurrent session can still write the worktree, coordinate first.
  Evidence of active work includes recent file mtimes, processes whose working
  directory is inside the worktree, and fresh branch reflog entries. Cleanup is
  cheap, but it must not remove files that another session still needs.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Re-run `git commit` without diagnostics | Retried the identical commit and read the output | Exit 1 again; the visible output ended at the last passing hook with no error | Parallel hook execution and per-hook buffering hide the failed hook. Capture complete output to a file and search it. |
| Diagnose from `git status` and `git ls-files` | Verified porcelain and `ls-files --others` were clean except intended files | The phantom directories stayed invisible: Git tracks no directories, and status hides ignored files | Audit ignored on-disk state with `find` or `git clean -ndX` instead of git status modes. |
| Fix the index (re-stage) and commit again | Re-staged the intended files and retired the commit | The validator failure is a property of on-disk directories, not of the index | Remove the phantom directories themselves, then commit. |

## Results & Parameters

### Configuration

```bash
# Positive safety check: prints every non-cache file in a suspect directory.
find <dir> -type f ! -path '*__pycache__*' ! -name '*.pyc'

# Removal sequence for a confirmed cache-only directory tree.
find <dir> -type d -name __pycache__ -prune -exec rm -rf {} +
rmdir <dir>
```

### Expected Output

- The full hook log shows failure markers before cleanup and none after.
- The whole-tree validator passes; in the originating case the suite result
  changed from 2 layout failures to 0 failures across more than 3,000 tests.
- The commit lands and `git status` stays clean.
- Safety bound: delete only directories that contain nothing outside ignored
  cache patterns and that Git does not track.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An automation-pipeline repository with a test-layout validator | Worktree commit recovery after a file-deleting branch move | See [notes](./worktree-phantom-dirs-block-validated-commit.notes.md). |

## References

- [Related skill: checkout admission cleanliness](automation-clean-checkout-intermediate-artifacts.md)
