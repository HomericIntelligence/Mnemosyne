---
name: delegated-cleanup-precondition-recovery
description: "Recover a dependency-locked delegated cleanup run that stops on a precondition: a target tree dirty with other sessions' untracked files, or a dependency checkout that is locally modified or diverged. Use when the delegation exits nonzero with a working-tree cleanliness error, or when the dependency cannot update in place."
category: tooling
date: 2026-11-02
version: "1.0.0"
user-invocable: false
tags:
  - delegation
  - cleanup
  - git
  - worktree
  - precondition
  - retry
  - untracked
  - dependency
---

# Delegated Cleanup Precondition Recovery

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Complete a delegated cleanup after a precondition refusal, without deleting or overwriting other sessions' work. |
| **Outcome** | Successful. Reconciliation plus one retry completed the delegation and preserved every other session's work. |

## When to Use

- The delegation exits nonzero with a precondition error such as a message that
  the working tree has uncommitted changes, while `git status` shows only
  untracked directories that other agent sessions created.
- The delegation's dependency checkout is locally modified, or its branch
  diverged from its remote, so an in-place update would discard local work.
- The delegation contract requires the delegated exit status to be propagated
  as-is, so a precondition must be fixed at its source, not interpreted away.

## Verified Workflow

### Quick Reference

```bash
# Case 1: only untracked temp directories from other sessions.
# Reconcile visibility, not ownership:
printf '<temp-dir-1/>\n<temp-dir-2/>\n' >> .git/info/exclude
git pull --ff-only                  # fast-forward the trunk when it is only behind
git status --porcelain=v1 -b        # success: only the branch line prints

# Case 2: dependency checkout dirty or diverged. Preserve it; clone fresh:
git clone <canonical-upstream-url> <primary-project>/.worktrees/<dependency>-<purpose>
# verify origin URL, clean status, and any contract-required revision before delegation
```

### Suggested Approach

1. Read the refusal before you change anything. A precondition refusal is a
   known-failed status, not an unknown one: nothing ran, so there is no effect
   surface to probe. Reconcile the named precondition; do not re-run first.
2. Untracked is not abandoned. In a checkout with concurrent agent sessions,
   untracked directories can hold another session's active scratch state. Never
   delete or stash them to satisfy a cleanliness gate. Append the exact observed
   paths to the clone-local exclude file instead. This changes no tracked file
   and no shared configuration, and any session can revert it in one edit.
3. Fast-forward a trunk that is only behind. A cleanup tool classifies branches
   against the trunk; a stale trunk can misclassify merged work as unlanded.
   Use fast-forward only. Never merge or rebase the trunk to "catch up".
4. Preserve an unusable dependency checkout. If it is locally modified or
   diverged, do not pull, rebase, or reset it. Prepare a separate clean clone of
   the canonical upstream under the primary project's ignored worktrees
   directory, validate its origin, cleanliness, and any contract-required
   revision, and pass that path to the delegation helper. Remove the scaffolding
   clone afterwards only when it holds no unique work.
5. Retry once, then stop. After reconciliation, re-run the delegation at most
   one time and propagate its exit status as the terminal status. A nonzero
   result after a reconciled retry means cleanup is incomplete: report it with
   the delegated output, do not loop.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| First delegation run on an unreconciled tree | Invoked the helper directly while the target tree held foreign untracked temp directories and a stale trunk | The tool refused with a working-tree cleanliness error and ran nothing | A precondition error is a known failure. Reconcile tree and dependency state first, then retry once |

## Results & Parameters

### Configuration

- Reconciliation gate: `git status --porcelain=v1 -b` prints only the branch line.
- Retry budget: one. One reconciliation, at most one re-invocation.
- Exclusion scope: only the exact paths observed as foreign untracked entries.
  Append them; do not add broad patterns that can swallow later files.

### Expected Output

- Before the retry: clean status, and a dependency clone that passes its
  identity, cleanliness, and revision checks.
- After the retry: the delegation reports the merged worktrees and branches it
  removed, keeps dirty, unlanded, or unverifiable worktrees, and completes
  without branch failures.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A multi-session primary checkout of a production automation project | The delegated cleanup refused on foreign untracked temp directories and a diverged toolchain dependency; one reconciled retry removed the merged feature worktree and branch and preserved every dirty or unlanded worktree | See [notes](./delegated-cleanup-precondition-recovery.notes.md). |

## References

- [Reconcile before retry after mutation status loss](reconcile-before-retry-mutation-status-loss.md) —
  the unknown-terminal-status case; this entry covers known precondition
  refusals where nothing ran.
- [Runbook step chain contract validation](runbook-step-chain-contract-validation.md) —
  the same clone-local exclude technique in a detached worktree.
- [Broad ignore patterns swallow new files](tooling-gitignore-broad-pattern-swallows-new-files.md) —
  why the exclusion lists exact observed paths instead of broad patterns.
