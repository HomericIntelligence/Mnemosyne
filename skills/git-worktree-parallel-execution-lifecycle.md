---
name: git-worktree-parallel-execution-lifecycle
description: "Use when parallel agents need isolated Git state; one issue is split across disjoint owners; worktree creation races across processes; branch ownership, stale, locked, dirty, submodule, or foreign-repository worktrees must be classified; hundreds of stale worktrees need a bulk audit and removal; or cleanup is constrained by preservation and destructive-action policy."
category: tooling
date: 2026-08-06
version: "2.2.0"
license: BSD-3-Clause
verification: unverified
user-invocable: false
tags: [worktree, git, parallel-agents, wave-execution, cleanup, branch-collision, contamination,
  locked-worktree, staged-files, rebase-merge, myrmidon, safety-net, lifecycle, submodule,
  squash-merge, hand-to-user, first-writer-wins, branch-ownership, superseded, porcelain,
  nul-delimited, path-safety, bulk-cleanup, dry-run, archive]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/git-worktree-parallel-execution-lifecycle.history"
history-cleanup-date: "2026-09-20"
---

# Git Worktree Parallel Execution Lifecycle

## Overview

Use one explicit worktree per concurrent writer. A worktree isolates `HEAD` and the index, not
repository-wide refs or remote branch names, so allocation and publication still need ownership
checks. Cleanup is a classification problem: prove repository identity, branch/PR state,
cleanliness, and recoverability before removing anything.

This skill remains `unverified`; it consolidates observed procedures and proposed parser/locking
contracts. Do not treat proposed helpers as shipped APIs without checking the target repository.

Supporting cases and provenance are in
[`git-worktree-parallel-execution-lifecycle.notes.md`](git-worktree-parallel-execution-lifecycle.notes.md).
The complete superseded source is in
[`git-worktree-parallel-execution-lifecycle.history`](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/git-worktree-parallel-execution-lifecycle.history).

## When to Use

- Two or more agents or subprocesses can write in the same repository.
- One issue can be split only after assigning disjoint file ownership and dependencies.
- A branch is already checked out, a remote branch name may collide, or two requests resolve to
  the same writable head.
- A worktree is locked, dirty, missing from `git worktree list`, contains submodules, or appears
  stale after a squash/rebase merge.
- Worktree creation races even though an in-process `threading.Lock` exists.
- Cleanup would require discarding uncommitted work, force-removing a worktree, or deleting a
  branch.
- A write or directory create fails with "No space left on device" while `df` reports ample free
  space, and the worktree root holds hundreds of worktrees.
- Hundreds of worktrees accumulated and only a few dozen have an open pull request.
- Old release trees or evidence directories must be retired by age.

## Verified Workflow

### 1. Establish the isolation and ownership boundary

Fetch before resolving the base, confirm the actual repository root and remote, and reserve unique
branch and path names.

```bash
git fetch origin
git rev-parse --show-toplevel
git remote get-url origin
git ls-remote --exit-code --heads origin <branch>
git worktree list --porcelain -z
```

Create from an immutable or freshly fetched base. Use the worktree directory as the working
directory for every edit and Git command.

```bash
git worktree add -b <unique-branch> <absolute-worktree-path> origin/main
git -C <absolute-worktree-path> status --short --branch
```

Before every commit, assert the branch and ownership scope:

```bash
test "$(git branch --show-current)" = "<unique-branch>"
git status --short
git diff --name-only --cached
```

If several logical items resolve to the same branch, admit exactly one writer. Reuse is safe only
for the requesting item's expected path. Treat later writers as permanently superseded; retrying
cannot create ownership.

### 2. Split work by dependencies and hot files

Map every task to owned paths before dispatch. Run independent owners concurrently, but serialize
tasks that touch the same main/history/index file or depend on a preceding merge. Give every worker
the worktree path, branch, base, owned files, forbidden files, validations, and publication rules.

Do not rely on disjoint files in a shared checkout: branch switches, stash, rebase metadata, and
the shared index can still move another writer's work. Harness-created clones may also hide sibling
branches, so use explicit linked worktrees when cross-branch inspection matters.

### 3. Serialize cross-process allocation

First determine whether contention is among threads or processes. `threading.Lock` protects only
one interpreter. For subprocesses sharing Git metadata and filesystem paths, hold one
repository-scoped advisory file lock across all of these operations:

1. Refresh and parse the worktree inventory.
2. Detect the current branch holder.
3. Decide same-path reuse versus typed ownership rejection.
4. Run `git worktree add`.

The existence check and add must be inside the same lock; otherwise they form a TOCTOU race. Prefer
one reusable `file_lock(path, blocking=True)` context manager over duplicated inline `fcntl.flock`
blocks. A nonblocking acquisition should raise a typed "lock unavailable" outcome, not silently
continue.

### 4. Parse inventory without losing paths

Request `git worktree list --porcelain -z` and parse NUL-delimited attributes into stateful records.
Keep each complete path paired with its branch, HEAD, and `locked` attribute. Never use
`awk '{print $2}'`, shell word splitting, or newline-only records: paths and lock reasons can contain
spaces or newlines.

Before touching a worktree-looking directory, verify both:

```bash
git -C <candidate> remote get-url origin
git worktree list --porcelain -z
```

A directory whose remote differs, or which is absent from the current repository's worktree
inventory, is out of scope even if it lives beneath a familiar build directory.

### 5. Classify before cleanup

For each candidate, record branch, PR state, dirtiness, lock state, submodule presence, and unique
work. Use PR state as the merge authority in squash/rebase repositories; `git branch --merged`,
ahead counts, and `git cherry` can report old commits as unique after their patch shipped under a
new SHA.

```bash
git -C <worktree> status --porcelain
gh pr list --head <branch> --state all --json number,state,url
git cherry origin/main <branch>
git diff --name-status origin/main...<branch>
```

For CLOSED plus `cherry=+`, investigate whether the content landed through another PR and whether
the touched paths still exist on main. For apparent deleted-file drift:

```bash
git cat-file -e origin/main:<path>
```

Success means the path exists on main and the checkout may merely be stale. Inspect untracked
files; do not assume a large dirty count is cache noise. If unstaged edits vanished after a foreign
branch switch, inspect `git stash list` for `WIP on <branch>` and apply the matching stash only in a
fresh owned worktree.

### 6. Apply the least-destructive cleanup action

- Clean and unlocked: move outside the target, then `git worktree remove <path>`.
- Clean and locked: `git worktree unlock <path>`, then remove normally.
- Dirty or uncertain: preserve and ask for a disposition; never auto-commit or auto-discard.
- Foreign repository: leave untouched.
- Initialized submodules: plain removal may fail even after `git submodule deinit`; report that
  force removal is required.
- After successful removals: `git worktree prune`.

Never let a failed `gh` query default to deletion. Capture it explicitly and stop cleanup on error.
Never remove the current working directory; `cd` to the main repository first and use `git -C` for
checks. `git worktree remove` can delete the directory while the calling shell still points into it.
The shell then fails every command with "Working directory does not exist" until you move the
session to an existing directory. An agent host keeps its own working directory separate from the
shell, so moving the session invalidates no committed work. Staged additions survive
`git checkout -- .`; this is one reason discard must be treated as an explicit destructive
operation rather than a casual cleanup step.

If policy blocks `reset --hard`, `clean -fd`, `worktree remove --force`, `rm -rf`, or `branch -D`,
do not work around the guard. Present exact, fully resolved commands and evidence to the user.

#### Capacity failure caused by accumulated worktrees

Use this branch when a write fails with a no-space error but `df -h` shows ample free bytes.

1. Check `df -i` and probe with a small `mkdir` plus `rmdir` in the worktree root. A failed probe
   with free bytes and free inodes points to a per-user, per-directory, or entry-count limit. Name
   the limit as unconfirmed until a quota query proves it.
2. Run the classified cleanup of step 6. Remove only clean worktrees whose work has landed. Keep
   dirty worktrees. Do not hand-delete release or evidence directories to gain space.
3. Removal on a network filesystem is slow. A foreground run can reach the command time limit
   after a small share of the work. Each removal is independent, so a partial result is safe.
   Probe the write again. Then run the remainder in the background with output in a log file.
4. Before any retry, list the worktrees again. Do not repeat a removal from an old list.
5. Check that unrelated running services were not affected before you report the repair.

#### Bulk cleanup of hundreds of stale worktrees

Use this branch when hundreds of worktrees accumulated and only a few dozen have an open pull
request. Do an audit first. Remove nothing until a dry-run list exists.

1. Audit read-only with a script, not by hand. Make one `gh pr list --state all --limit <N> --json
   headRefName,state,number` call. Then, for each worktree, record the branch, the dirty-file
   count, and the PR states. Put each worktree in one class: open PR (keep), merged, closed, no PR,
   or detached HEAD. Print the dry-run list before any removal. Run long removals in the background.
   A bulk tidy tool can exceed a foreground time limit on hundreds of worktrees. A stale-worktree
   mode can need Git 2.36 or newer. Check `git --version` first. If it is older, use your own
   script. An old Git can also reject `git worktree list --porcelain -z`.
2. Removal of a worktree does not delete its branch, so committed work stays safe. Only two items
   are at risk: uncommitted content, and a detached HEAD that no remote branch contains. For such a
   detached HEAD, write a hidden ref before removal:
   `git update-ref refs/archive/<name> <sha>`.
3. Archive the diff of a dirty worktree only if its content is not on trunk. For each changed or
   untracked file, compare `git hash-object <file>` with `git rev-parse origin/main:<path>`.
   Ignore cache and build files (`__pycache__`, `.venv`, `node_modules`, `*.pyc`, `*.log`). If every
   file matches trunk, remove the worktree and keep no archive. If some files differ, save
   `git diff HEAD` and the small untracked files (set size caps) to an archive directory. Then remove
   the worktree. Limit: an equality check misses a squash-merged change that differs a little, so
   some stale archives remain. Offer a follow-up prune of the archives.
4. Guards. Skip each of these:
   - a worktree with recent Git activity (`HEAD` or index mtime within about 2 hours);
   - a locked worktree (do not unlock it without the owner's decision);
   - a release, stage, or deployed tree, and any tree that a running process uses
     (`pgrep -f <path>`);
   - the main checkout and your own worktree.

   Check that each directory still exists when the loop reaches it, because another tool can remove
   it during the run. Do not run `pkill -f <script>` from a shell whose own command line contains
   the pattern. The command kills its own shell.
5. Retire old release trees and evidence by version or date against a cutoff. Keep the current
   release and the previous release, and keep anything unclear near the cutoff. List the candidates
   with their sizes and get approval before you delete. Delete in a background script that logs each
   failure. A directory that another user owns with mode 0700 returns "Permission denied" even for
   a listing. Do not use `chmod` or `sudo` to get around it. Give the exact `rm` command to the
   owner, and verify afterward that the directory is empty.

Measured case: see the notes companion.

### 7. Recover contamination or stranded work

When commits leaked between branches, identify each owner's commits and rebuild from the intended
base in a fresh worktree. Prefer cherry-picking known-good commits to complicated revert chains.
Protect any rewritten remote with the exact observed old head:

```bash
git push --force-with-lease=refs/heads/<branch>:<old-head> origin HEAD:<branch>
```

For uncommitted work on a hijacked shared checkout, export a patch or locate the stash, create a
fresh owned worktree, apply there, and revalidate. Never keep editing after `HEAD` or the branch
changes unexpectedly.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Multiple writers in one checkout | Multiple writers in one checkout | Shared `HEAD`, index, stash, and rebase state contaminate work | One explicit worktree per writer |
| In-process lock around subprocess allocation | In-process lock around subprocess allocation | Each process owns a different lock | One repository-scoped file lock around check and add |
| Path-exists check before locked add | Path-exists check before locked add | Cross-process TOCTOU race | Recheck inventory inside the lock |
| `git cherry` or `--merged` as merge proof | `git cherry` or `--merged` as merge proof | Squash/rebase changes commit identity | Trust live PR state plus content evidence |
| Word-splitting porcelain output | Word-splitting porcelain output | Corrupts paths and record associations | Parse `--porcelain -z` statefully |
| Blind cleanup under build directories | Blind cleanup under build directories | May target another repository | Verify remote and worktree membership |
| Force cleanup of dirty/submodule worktrees | Force cleanup of dirty/submodule worktrees | Destructive and often policy-blocked | Preserve, classify, and hand off exact commands |
| Foreground cleanup of hundreds of worktrees on a network filesystem | Ran the full cleanup in one command with a time limit | The limit ended the run after a few removals | Probe the write, then run the rest in the background and re-list before a retry |
| Branch reuse for a second logical issue | Branch reuse for a second logical issue | Creates two writers for one head | First writer wins; later item is superseded |

## Results & Parameters

Copy-ready worker contract:

```text
worktree: <absolute path>
branch: <unique branch>
base: <immutable SHA or fetched remote ref>
owned paths: <explicit list>
forbidden paths: <explicit list>
verification: <commands>
publication: <push/PR rules>
```

Safety invariants:

1. A writable branch has at most one active owner.
2. Worktree allocation is atomic across processes.
3. Inventory parsing preserves arbitrary paths.
4. Destructive cleanup requires proven scope and explicit authority.
5. A failed remote query never becomes permission to delete.

## Verified On

- Source observations through 2026-08-06; overall status remains `unverified`.
- Compacted for issue #3335 without upgrading evidence. Detailed cases and proposed helper
  contracts are indexed in the notes companion.
