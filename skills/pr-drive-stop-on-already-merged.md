---
name: pr-drive-stop-on-already-merged
description: "Stop a review-and-merge drive at the binding step when the target pull request is already merged. Use when a task says to review a pull request and drive it to merged, before any review round, comment, or auto-merge."
category: ci-cd
date: 2026-10-31
version: "1.0.0"
user-invocable: false
tags: [pull-request, merge-state, review-drive, terminal-state, forge, zero-writes]
---

# Stop a PR Drive When the Target Is Already Merged

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-31 |
| **Objective** | Bind the target pull request lifecycle state before review work. Stop with zero forge writes when the request is already delivered. |
| **Outcome** | Operational. The binding read showed a merged target with a delivered review verdict. The drive stopped before any review round, comment, or merge action. |

## When to Use

- A task says "review pull request N and drive it to merged" or gives a similar end-to-end drive instruction.
- A coordinator relaunches or hands off a pull request drive that another session may have finished.
- A queued batch of drive tasks can contain items that merged while they waited.
- The pull request carries a review-state label, such as an implementation-go marker, from an earlier round.
- You hold a stale claim that the pull request is open, blocked, or waits for review.

## Verified Workflow

### Quick Reference

Bind the lifecycle state before any review, repair, or comment:

```bash
# 1. Read the artifact lifecycle state first.
gh pr view <number> --repo <owner>/<repository> \
  --json state,mergedAt,mergeCommit,headRefOid,labels

# 2. For a merged state, prove the delivery on the target branch.
git merge-base --is-ancestor <merge-commit-oid> <remote>/<default-branch> \
  && echo "merge commit is on the default branch"
```

### Suggested Approach

1. Read the pull request state, merge timestamp, merge commit, head, and state labels
   before you start the review loop. This read is part of artifact binding, not an
   extra step.
2. If the state is open, continue the normal drive: bind the diff, review, repair,
   get the review verdict, then enable auto-merge.
3. If the state is merged, prove the delivery on the target branch. Check that the
   merge commit exists and is an ancestor of the default branch. Compare the merge
   parent with the recorded base when the task records one. Note the review-state
   label as the record of the delivered verdict.
4. Stop with zero forge writes. Do not publish a reviewer round, an author response,
   a status comment, or an auto-merge request. A merged target needs no blocker
   comment: the delivery is on the pull request itself. A "post the blocker and
   stop" rule applies only when the verdict is unreachable or the delivery happened
   somewhere else.
5. Record the session lesson and close the task through its already-complete rule.
   Do not start the review workflow on a closed artifact.

Continue useful work when a step is unavailable. If the merge commit is absent from
the target branch, treat the delivery as not proven and re-check the forge record
before any claim.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Prepare the delivery worktree from the recorded local revision | Used the stale local checkout revision as the start point | The revision was not on the remote, so the worktree helper could not resolve it | Base the delivery worktree on the live default-branch tip; probe the remote read-only first |
| N/A | The stop decision itself was a successful direct attempt. | N/A | No change was necessary. |

## Results & Parameters

### Configuration

Decision table for the binding read:

| Observation | Decision |
| ------- | ------- |
| State is open | Continue the drive from the binding step |
| State is merged; merge commit is an ancestor of the default branch | Stop; zero forge writes; record the lesson |
| State is merged; merge commit is absent from the default branch | Treat delivery as unproven; re-check the forge record |
| State is closed without a merge | Report the terminal state and follow the task rule for delivered or stopped work |

### Expected Output

A stop report contains:

- the observed state, merge timestamp, and merge commit;
- the ancestry proof for the merge commit on the default branch;
- the review-state label that records the delivered verdict; and
- the lesson step that closes the task.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Agent session | Review-and-merge drive task | [Case notes](./pr-drive-stop-on-already-merged.notes.md) |

## References

- [Check if already shipped before writing a plan](planning-check-already-shipped-before-planning.md)
- [Verify PR ready for merge](verify-pr-ready.md)
- [Stale plan already resolved](stale-plan-already-resolved.md)
