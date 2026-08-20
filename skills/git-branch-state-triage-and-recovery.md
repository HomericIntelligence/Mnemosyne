---
name: git-branch-state-triage-and-recovery
description: >-
  Diagnose and recover stale, orphaned, diverged, prematurely merged, closed-PR, rewritten-SHA,
  or contaminated stacked branches. Use before rebasing, discarding, replaying, or opening a PR
  when branch identity, ancestry, PR ownership, or the unique patch is uncertain.
category: tooling
date: 2026-07-13
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: git-branch-state-triage-and-recovery.history
tags: [git, branch, triage, recovery, stale, superseded, orphan, diverged, merge-base,
  cherry-pick, unrelated-histories, consolidation, squash-merge, stash, auto-merge,
  follow-up-branch, force-with-lease, closed-pr, replacement-pr, stacked-pr, backup-ref,
  exact-head, concurrent-trunk, artifact-provenance]
---

# Git Branch State Triage and Recovery

## Overview

Recover the intended patch, not the historical branch shape. First bind the local branch to its
live PR and exact remote head, then distinguish content already on trunk from work that is truly
unique. Squash and rebase merges rewrite commit identity, so ancestry and `git cherry` are evidence,
not final authority.

Case evidence is indexed in
[`git-branch-state-triage-and-recovery.notes.md`](git-branch-state-triage-and-recovery.notes.md).
The complete superseded source is archived in
[`git-branch-state-triage-and-recovery.history`](git-branch-state-triage-and-recovery.history).

## When to Use

- The remote tracking ref disappeared or the branch is far behind trunk.
- `merge-base` is absent, a branch contains many HEAD-only files, or consolidation changed paths.
- A PR merged while review/fixes were in progress, or a merged branch has new uncommitted work.
- A closed PR cannot be reopened, but its head can be recovered into a replacement PR.
- A merged PR's branch looks unique because commit SHAs were rewritten.
- A stacked child includes unrelated commits and must be rebuilt from its current parent.

## Verified Workflow

### 1. Capture live ownership and immutable recovery points

Do not mutate first. Fetch, record the local/remote tips, query the PR by the actual head branch,
and create a backup ref when a rewrite may follow.

```bash
git fetch origin
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git merge-base HEAD origin/main || true
git branch backup/<branch>-<timestamp> HEAD
gh pr list --head <branch> --state all \
  --json number,state,headRefName,headRefOid,baseRefName,url
```

Use `headRefName` from GitHub; never derive a PR branch from an issue number. Re-read `headRefOid`
before pushing rewritten history.

### 2. Classify the state

| State | Evidence | Recovery direction |
| --- | --- | --- |
| Superseded | PR merged or patch/content already on trunk | Stop; do not rebase or duplicate |
| Orphan | No common ancestor | Export the intended patch, recreate from trunk |
| Diverged | Common base exists; local/remote tips differ | Reset/rebuild from the chosen tip, cherry-pick intended commits |
| Prematurely merged | Old PR is merged; later commits are missing | Fresh trunk branch; replay only missing commits |
| Merged branch with uncommitted follow-up | PR identity is spent; working tree has a new delta | Stash, fresh trunk branch, pop and verify |
| Closed unmerged | Head is recoverable but reopen is refused | Rebase/rebuild and open a replacement PR |
| Contaminated stacked child | Child diff contains parent-unrelated commits | Rebuild child from rebased parent |

Use both two-dot and triple-dot views deliberately:

```bash
git log --oneline origin/main..HEAD
git diff --stat origin/main..HEAD
git diff --stat origin/main...HEAD
git cherry origin/main HEAD
```

Two-dot answers what tree delta would be applied now. Triple-dot describes change since the merge
base and becomes noisy when merge strategy rewrites history. For squash-merged work, search trunk
by PR number/subject and verify the resulting tree or markers. A merged PR plus equivalent content
is stronger evidence than ahead count or `cherry=+`.

### 3. Prove whether apparent work is unique

For modified working-tree files, compare bytes or content against trunk; zero unique lines across
all files means the delta may already have shipped. For many branch-only paths after consolidation,
compare counts at the fork point, branch head, and trunk, then inspect whether trunk replaced or
absorbed the old files.

```bash
git diff --name-status origin/main...HEAD
git log --diff-filter=D --oneline origin/main -- <old-path>
git cat-file -e origin/main:<path>
git grep -n '<stable-marker>' origin/main
```

Do not discard based on counts alone. Preserve with a stash or backup ref before any authorized
destructive operation.

### 4. Recover by state

#### Orphan or diverged branch

List and inspect candidate commits, recreate from current trunk in an isolated worktree, then
cherry-pick only the intended commits in dependency order. If commit history is unusable, produce a
reviewable patch and apply it to the new branch. Resolve conflicts according to current trunk
semantics, not by restoring the old whole tree.

```bash
git switch -c <fresh-branch> origin/main
git cherry-pick <sha1> <sha2>
```

#### Old PR merged during review

The old branch is no longer a PR update target even if a push succeeds. Create a fresh branch at
current trunk and replay only commits absent from trunk. Inspect the two-dot patch for inversions of
concurrent changes. If an artifact embeds a source SHA, rebuild it from the replayed source and
verify both embedded revision and digest.

#### Merged current branch with uncommitted follow-up

```bash
git stash push -u -m 'follow-up from merged <branch>'
git switch -c <fresh-follow-up> origin/main
git stash pop
git status --short
```

Re-run the complete validation suite, make a signed/DCO commit if required, and open a linked new
PR. Never append a new change to a branch whose PR is already merged.

#### Closed PR cannot reopen

Confirm the PR is CLOSED rather than MERGED, preserve the exact old head, rebase or rebuild against
current trunk, and push with an explicit lease:

```bash
git push --force-with-lease=refs/heads/<branch>:<old-head> origin HEAD:<branch>
```

If GitHub still refuses reopen, create a replacement PR from that recovered branch and link the old
PR. Do not create a duplicate if the two-dot delta is empty or already on trunk.

#### Contaminated stacked child

Record the parent and child heads, preserve a backup ref, rebase the parent first, create a clean
child at the rebased parent, and cherry-pick only child-owned commits. Verify the final child range
against the parent, not against trunk, until the dependency is removed.

### 5. Verify and publish

Before push, inspect `git diff <intended-base>..HEAD`, changed paths, commit signatures/trailers,
and focused/full tests. Re-read the remote head and use an exact force-with-lease if rewriting.
After push, ensure the PR head, base, and current-head checks match the recovered commit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Rebase before classification | Rebase before classification | Can resurrect superseded work or erase recovery context | Capture refs and classify first |
| Trust `git cherry`/ahead count | Trust `git cherry`/ahead count | Squash/rebase merges rewrite SHAs | Pair live PR state with content evidence |
| Use only triple-dot diff | Use only triple-dot diff | Rewritten ancestry produces a noisy false delta | Inspect two-dot application delta too |
| Push follow-up work to a merged PR branch | Push follow-up work to a merged PR branch | The branch identity is spent | Fresh branch from current trunk |
| Replay the whole old tree | Replay the whole old tree | Reverts concurrent trunk changes | Replay only missing commits semantically |
| Assume branch name from issue | Assume branch name from issue | Existing PR may use another head | Read `headRefName` from GitHub |
| Bare `--force-with-lease` | Bare `--force-with-lease` | May not protect the observed head | Pin the branch and old OID explicitly |
| Rebuild child from trunk | Rebuild child from trunk | Loses intended stack dependency | Rebuild from the rebased parent |

## Results & Parameters

Triage report contract:

```text
local head: <oid>
remote head: <oid>
trunk head: <oid>
merge base: <oid or none>
PR: <number/state/base/head>
two-dot delta: <summary>
triple-dot delta: <summary>
classification: <state>
preservation ref: <ref>
recovery action: <bounded action>
verification: <commands/results>
```

Never call a branch superseded solely because it is old, or unique solely because it is ahead.
The decision requires both repository history and content-level proof.

## Verified On

- Verified-local branch recovery cases through 2026-07-13.
- Compacted for issue #3335; evidence status was preserved without promotion.
