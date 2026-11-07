---
name: shared-checkout-foreign-working-tree-changes
license: BSD-3-Clause
description: "Preserve uncommitted working-tree changes the current agent did not create before any git operation in that checkout, and gate every destructive cleanup step on re-verified recoverability. Use when git status shows modifications of uncertain provenance, or a cleanup request touches a tree with stacked changes."
category: tooling
date: 2026-11-04
version: "1.0.0"
user-invocable: false
tags:
  - git
  - shared-checkout
  - foreign-state
  - working-tree
  - uncommitted-changes
  - backup
  - destructive-operations
  - worktree
  - verification
  - multi-agent
---

# Shared Checkout Foreign Working-Tree Changes

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-04 |
| **Objective** | Keep uncommitted working-tree changes the current agent did not create from being stranded, carried onto a wrong ref, or destroyed while git work proceeds in the same checkout |
| **Outcome** | Success — foreign change snapshot preserved, unrelated work extracted through a side worktree, destructive cleanup executed only after fresh recoverability checks with owner authority |

## When to Use

- `git status` shows modified or untracked files the current session did not create, or whose
  timestamps or content point at another session, lane, or the human user.
- A task asks for git work in that checkout: advancing branches, extracting changes, switching
  refs, or "fixing the tree".
- A step is about to run `git restore`, `git checkout --`, `git clean`, `git branch -D`,
  `git worktree remove`, or delete backup copies.
- One working tree holds several stacked logical changes that must leave through separate
  branches or PRs.

Do NOT use when the foreign state is a stash entry; use
[shared-checkout-foreign-stash](shared-checkout-foreign-stash.md). Do NOT use for changes the
current session made itself; no provenance question exists there. To recover work already lost to
a concurrent reset, use
[tooling-git-recover-stashed-work-after-concurrent-branch-reset](tooling-git-recover-stashed-work-after-concurrent-branch-reset.md).

## Verified Workflow

### Quick Reference

```bash
# 0. Snapshot BEFORE any git state change. The working tree is the only copy.
mkdir -p <scratch-backup>
cp -rp <modified-and-untracked-files> <scratch-backup>/

# 1. Never switch the parked checkout. Do branch work in a side worktree.
git worktree add <side-path> -b <new-branch> <base-sha>

# 2. Gate every destructive step on fresh evidence; abort on drift.
[ "$(git rev-parse <branch>)" = "$(git rev-parse <remote>/<branch>)" ] \
  || { echo "ABORT: ref drifted"; exit 1; }
```

### Steps

1. **Classify before touching.** Read the diff and the file timestamps. Foreign changes can be
   real, deliberate work — a fix in progress, a diagnostic artifact — not residue. Report what you
   found; do not guess intent from file names.
2. **Snapshot the effect surface.** Copy modified and untracked files to a scratch backup with
   metadata preserved (`cp -rp`). Uncommitted content has no git-level recovery surface: there is
   no reflog for a working tree. This copy is the only recovery point until durable artifacts
   exist.
3. **Park the dirty checkout.** Fetch and push are worktree-neutral and safe from it. Never
   `git checkout` or `git switch` inside it to advance other work: the switch either refuses on
   conflict, strands the changes behind, or silently carries them onto the new ref.
4. **Work from a side worktree.** Bind it to an explicit base SHA, apply only the intended hunks,
   and prove the unrelated changes are absent before committing (`grep` checks plus
   `git diff --stat <base>`). This is also how a stacked tree splits into one-intent branches.
5. **Gate destruction on fresh evidence.** Immediately before each destructive command,
   re-verify: backup copies exist, each branch tip equals its pushed remote tip, and the durable
   artifacts (open PRs or merged work) exist. Abort on any mismatch. An open PR is not fully
   durable — its head can live on a fork whose owner can delete it — so hold backups until the
   work merges, unless the owner accepts the risk explicitly.
6. **Reconcile with authority.** The parked checkout's changes are superseded only when every
   constituent change has a durable home. Reset the tree and delete backups only on the owner's
   explicit instruction, after stating what will no longer be recoverable.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Switch the parked checkout to advance a branch | Would run `git checkout` inside the dirty tree | Foreign changes would carry onto the new ref or block the switch | Park the checkout; use a side worktree bound to a base SHA |
| Restore the tree immediately on a cleanup request | `git restore` + deleting the untracked artifact as the first move | Would destroy the only copy of uncommitted foreign work | Snapshot first, verify durable artifacts, destroy last and on authority |
| Discard backups because PRs are open | Treated "PR open" as durable | An open PR head can live on a fork; deleting the fork kills the head and the PR | Open is not merged; hold backups until merge or documented owner acceptance |
| Commit the combined stacked tree as one PR | The dirty tree held three logical fixes, one of them not mine | One PR would collapse independently reviewable fixes and misattribute authorship | Extract each intent onto its own branch from the base; prove siblings absent |

## Results & Parameters

### Configuration

```console
$ git status --short
 M launcher
 M tests/test.sh
?? attach.out
$ ls -la attach.out    # timestamped today, references a job this session never ran
```

### Expected Output

- The scratch backup holds byte-identical copies of every modified and untracked file before the
  first git mutation (`cp -rp` preserves mtimes for later provenance checks).
- `git worktree list` shows the side worktree; the parked checkout still shows its original dirty
  state at every later inspection.
- The destruction gate prints `ABORT` and stops when any branch tip drifts from its pushed remote
  tip.
- Final `git status` is clean only after reconciliation, and every extracted change traces to a
  PR or a merged commit.

## Verified On

| Context | Details |
| ------- | ------- |
| A shared development checkout on a multi-user host | A second session's uncommitted fix appeared mid-task on top of two stacked feature branches. The tree was snapshotted first, one logical fix was extracted through a side worktree into its own PR, and cleanup ran only after backup presence, remote-tip equality, and open-PR state were re-verified. Backups were held until the owner explicitly directed deletion. |

## References

- [Protect foreign stashes in a shared checkout](shared-checkout-foreign-stash.md)
- [Snapshot the effect surface before mutating shared state](backup-before-state-mutation.md)
- [Port changes across refs without clobbering destination content](checkout-other-ref-silent-file-clobber.md)
- [Classify branch state before recovery or retirement](git-branch-state-triage-and-recovery.md)
- [Turn dirty worktrees into PRs in a resumable batch](dirty-worktree-batch-pr-shipping.md)
