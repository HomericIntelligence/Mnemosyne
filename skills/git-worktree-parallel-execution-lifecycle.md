---
name: git-worktree-parallel-execution-lifecycle
description: "Use when parallel agents need isolated Git state; one issue is split across disjoint owners; worktree creation races across processes; branch ownership, stale, locked, dirty, submodule, or foreign-repository worktrees must be classified; or cleanup is constrained by preservation and destructive-action policy."
category: tooling
date: 2026-08-06
version: "2.0.0"
license: BSD-3-Clause
verification: unverified
user-invocable: false
history: git-worktree-parallel-execution-lifecycle.history
tags: [worktree, git, parallel-agents, wave-execution, cleanup, branch-collision, contamination,
  locked-worktree, staged-files, rebase-merge, myrmidon, safety-net, lifecycle, submodule,
  squash-merge, hand-to-user, first-writer-wins, branch-ownership, superseded, porcelain,
  nul-delimited, path-safety]
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
[`git-worktree-parallel-execution-lifecycle.history`](git-worktree-parallel-execution-lifecycle.history).

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
checks. Staged additions survive `git checkout -- .`; this is one reason discard must be treated as
an explicit destructive operation rather than a casual cleanup step.

If policy blocks `reset --hard`, `clean -fd`, `worktree remove --force`, `rm -rf`, or `branch -D`,
do not work around the guard. Present exact, fully resolved commands and evidence to the user.

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
