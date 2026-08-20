---
name: tooling-force-push-blocked-reopen-as-fresh-branch
description: "Use when a harness blocks force-push after a branch conflict or rebase. Prefer merging current main into the existing feature branch so the next push is a normal fast-forward; if already rebased, preserve the verified tree only through an explicitly authorized reconciliation; if PR identity may change, push a fresh remote ref and open a replacement PR with complete linkage and checks."
category: tooling
date: 2026-07-06
version: "3.0.0"
verification: verified-ci
license: BSD-3-Clause
user-invocable: false
history: tooling-force-push-blocked-reopen-as-fresh-branch.history
tags:
  - git
  - force-push
  - rebase
  - merge
  - fast-forward
  - sandbox
  - pull-request
  - worktree
---

# Force-Push Blocked: Preserve the PR or Reopen Safely

## Overview

Some harnesses deny every force-push spelling at command admission. Redirection does not change an
argv denial, and destructive recovery commands may be blocked too. The safest solution is usually
to avoid rewriting the remote branch: merge current main into it, verify both ancestry relations,
and perform a plain fast-forward push. A fresh ref and replacement PR is the fallback when PR
identity does not need to survive.

Verification remains `verified-ci`. Detailed incidents and state transitions are in the
[notes](./tooling-force-push-blocked-reopen-as-fresh-branch.notes.md); the byte-preserved source and
prior changelog are in [history](./tooling-force-push-blocked-reopen-as-fresh-branch.history).

## When to Use

- The harness rejects `git push --force` and `--force-with-lease` before Git runs.
- CI fails on the synthetic merge commit because main acquired formatting or lint drift after the
  feature branch was cut.
- A stacked dependency merged, the child PR retargeted to main, and the branch became conflicted.
- A clean local rebase exists but updating the old remote ref would require force.
- Review history, PR number, stack position, or auto-merge state makes preserving the branch useful.
- Standard restore/reset commands are prohibited and a file must be reconstructed from a known ref.
- A replacement PR is acceptable, but its issue linkage and canonical status must remain clear.

## Decision Table

| State | Choose | Why |
| --- | --- | --- |
| Not rebased; repository squash-merges; same PR should remain | **A0: merge main into feature** | No history rewrite or force token; ordinary fast-forward push |
| Already rebased; verified tree retained; environment and user permit reconciliation | **A: authorized tree-preserving merge** | Same PR/branch with remote tip as ancestor |
| Fresh PR acceptable | **B: new remote ref and replacement PR** | No force needed for a nonexistent ref |
| Denial came from Git/remote rather than harness | Neither | Diagnose lease, permission, or protection failure directly |
| Repository requires linear/rebase-only feature history | Do not use A0 blindly | A merge commit may violate policy; obtain an allowed update path |

## Safety and Invariants

1. Confirm the failure is command-admission denial, not Git’s `rejected` or `remote rejected`.
2. Never disguise or encode a prohibited force command. Choose a workflow whose graph permits a
   normal push.
3. Read merge policy before A0. It is appropriate when feature-branch merge commits are accepted
   and the repository squash-merges the PR.
4. Preserve the exact remote tip before graph changes and fetch current refs.
5. Prove `origin/<branch>` is an ancestor of `HEAD` before a plain push.
6. Prove `origin/main` is an ancestor of `HEAD` and inspect the PR diff.
7. For an already-rebased checkpoint, prove the reconciled tree equals that checkpoint before
   committing. Do not reconstruct it from memory.
8. Destructive state changes require explicit authority and a resolved target. If reset/checkout is
   prohibited, do not attempt Option A; use A0 or B.
9. A replacement PR must preserve title/body intent, issue-closing semantics, review context, and
   required validation. Closing a PR disarms its auto-merge request.
10. Leave orphan-ref cleanup to the repository’s guarded cleanup workflow.

## Verified Workflow

### 1. Diagnose the denial and repository policy

Harness denial signals:

- rejection happens immediately, before a permission prompt or network interaction;
- the message is from the harness, not Git;
- both force variants are denied identically.

```bash
git fetch origin
git status --short --branch
git rev-parse HEAD
git rev-parse origin/<branch>
gh api repos/OWNER/REPO --jq \
  '{squash:.allow_squash_merge,rebase:.allow_rebase_merge,merge:.allow_merge_commit}'
```

If Git reports a stale lease, missing permission, or branch-protection rejection, fix that actual
problem instead of using this skill.

### 2. Option A0 — merge current main into the existing branch

Use this first when the branch has not been rebased and feature merge commits are compatible with
repository policy.

```bash
git fetch origin
git merge origin/main --no-edit
# resolve conflicts as ordinary file edits, then stage only intended paths
<formatter-or-fixer> <affected-paths>
git add <affected-paths>
git commit -S -s -m "chore: merge main and reconcile checks"

git merge-base --is-ancestor origin/<branch> HEAD
git merge-base --is-ancestor origin/main HEAD
git diff --stat origin/main...HEAD
git push origin HEAD:<branch>
```

Both ancestry commands must return zero. The first proves the push is fast-forwardable; the second
proves the branch includes current main. Review the three-dot PR diff and rerun required checks.

When restore/checkout commands are unavailable, reconstruct one tracked file as data, inspect it,
then stage it deliberately:

```bash
git show origin/main:path/to/file > path/to/file
git diff -- path/to/file
```

Do not use this to overwrite unrelated user changes; confirm the exact target and intended source
first.

### 3. Option A — reconcile an already-verified rebased tree

This option preserves the same PR only when all of the following hold:

- the rebased checkpoint SHA is still reachable and fully validated;
- the remote tip SHA was recorded;
- the required graph/tree manipulation is allowed and explicitly authorized;
- the final tree can be proven byte-identical to the checkpoint.

Conceptually, create a merge whose parents include the stale remote tip and current main, resolve
every path to the verified rebased checkpoint, and verify:

```bash
# Destructive reset and checkpoint checkout require explicit authority and resolved SHAs/paths.
git switch <branch>
git reset --hard origin/<branch>
git merge origin/main --no-edit
git checkout <rebased-sha> -- <each-conflicted-path>
git add <each-conflicted-path>
git diff --cached <rebased-sha> --stat  # MUST be empty before commit
git commit -S -s --no-edit
git merge-base --is-ancestor origin/<branch> HEAD
git merge-base --is-ancestor origin/main HEAD
git diff --stat origin/main...HEAD
git push origin <branch>
```

If any required recovery command is denied, or the checkpoint cannot be proven, stop using A. Do
not improvise destructive commands; use A0 from a preserved pre-rebase branch or choose B.

### 4. Option B — create a fresh ref and replacement PR

Confirm the candidate ref does not exist, then push once:

```bash
git ls-remote --heads origin <branch>-rebased  # must return no ref
git push origin HEAD:<branch>-rebased
```

Before closing anything, capture the original PR’s title, body, issue linkage, reviews, labels, and
check state. Open the replacement and only then make the old PR clearly point forward:

```bash
gh pr view <old-pr> --json title,body,url,state,reviews,labels
gh pr create --repo OWNER/REPO --base main --head <branch>-rebased \
  --title '<same title>' --body-file <preserved-body-file>
gh pr comment <old-pr> --body 'Superseded by #<new-pr>; replacement preserves the verified content on current main.'
gh pr close <old-pr>
```

The replacement body must retain the repository’s exact issue-linking form such as `Closes #N`.
Re-run required checks and re-arm auto-merge only when authorized by the task. Verify both PR states
and the linked issue; do not delete the old remote ref during delivery.

### 5. Final verification

```bash
gh pr view <canonical-pr> --json state,headRefOid,mergeable,mergeStateStatus,autoMergeRequest
gh pr checks <canonical-pr>
git diff --check origin/main...HEAD
git log --show-signature --oneline origin/main..HEAD
```

For A0/A, confirm the canonical PR number did not change. For B, confirm the old PR is closed with a
forward link and the new PR body still links the issue. A second rewrite of the fresh ref would
again require force; if further work is necessary, choose another new ref or obtain an authorized
canonical update path.

## Examples

### Main acquired formatter drift

The feature branch was clean, but CI tested its merge with a newer main that contained formatting
drift. Merging main into the branch surfaced the drift, the formatter corrected it, both ancestry
checks passed, and a plain push updated the same PR.

### Stacked PR became conflicted

After a parent PR merged, a child became dirty. Where the already-rebased tree could be proven and
reconciliation was permitted, a merge preserved the child’s content and branch identity. Where
identity was expendable, a new `-rebased` ref and replacement PR avoided force entirely.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Failure 1 | Force or force-with-lease | Harness rejects the argv before Git runs | Build a fast-forward graph or use a new ref |
| Failure 2 | Redirect stderr | Redirection occurs after command admission | Change the workflow, not the output stream |
| Failure 3 | Encode `-f` or disguise argv | Attempts to bypass policy and remains fragile | Never bypass; use A0/A/B |
| Failure 4 | Rebase first for ordinary main drift | Creates a needless force requirement | Merge main into the feature branch first |
| Failure 5 | Use blocked reset/restore commands | Cannot complete and risks state loss | Preserve checkpoints; use A0/B or request authority |
| Failure 6 | Skip the tree-equality proof in A | Can ship a conflict resolution different from the validated tree | Require an empty cached diff to the checkpoint |
| Failure 7 | Close before creating the replacement | Leaves no canonical PR and disarms automation | Create/verify replacement, then close with forward link |
| Failure 8 | Omit issue-closing text | Replacement no longer satisfies policy or closes the issue | Preserve body semantics exactly |
| Failure 9 | Merge main in a rebase-only repo | Feature merge commit may violate policy | Verify merge policy or obtain another allowed path |
| Failure 10 | Delete old refs during delivery | Adds destructive, unnecessary failure surface | Use guarded cleanup later |
## Results & Parameters

| Parameter | Contract |
| --- | --- |
| A0 precondition | Feature merges allowed and PR squash-merge policy confirmed |
| Plain-push proof | `origin/<branch>` is an ancestor of `HEAD` |
| Current-base proof | `origin/main` is an ancestor of `HEAD` |
| Option A proof | Cached tree diff to verified rebased checkpoint is empty |
| Option B ref | Remote ref does not exist before the one-time push |
| Replacement PR | Same intent and issue linkage; old PR points to new canonical PR |

## Output Contract

Report the denial classification, chosen option and why, recorded SHAs, ancestry and tree proofs,
canonical PR/issue URLs, signed-commit evidence, required-check state, and any orphaned ref delegated
to cleanup. Never claim a plain push is safe without the remote-tip ancestry proof.

## Companions

- [Case notes](./tooling-force-push-blocked-reopen-as-fresh-branch.notes.md)
- [Version history and superseded snapshot](./tooling-force-push-blocked-reopen-as-fresh-branch.history)
