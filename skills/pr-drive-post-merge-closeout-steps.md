---
name: pr-drive-post-merge-closeout-steps
description: "Complete the remaining post-merge steps of a pull request drive when the target is already merged. Use when a drive task starts or resumes after the merge, and you must decide whether to stop with zero forge writes or to close the documented closeout steps: confirm merge and issue closure, post the merge summary, and record the lesson."
category: ci-cd
date: 2026-10-31
version: "1.0.0"
user-invocable: false
sharing: public
verification: execution-observed
tags: [pull-request, merge-state, review-drive, post-merge, closeout, lesson, zero-writes, resumption, execution-observed]
---

# Post-Merge Closeout Steps for a PR Drive

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-31 |
| **Objective** | Start a merged pull request drive at its first unfinished step, and decide between a zero-write stop and the documented closeout writes. |
| **Outcome** | Operational. A merged target with an unfinished closeout step needs the remaining writes, not a stop. |

## When to Use

- A drive task starts or resumes and the first binding read shows `state: MERGED`.
- The drive instructions name steps that run after the merge, such as a confirmation of the merge and the linked issue, a merge summary comment, or a lesson record.
- You must decide between a zero-write stop and the remaining closeout writes.
- A prior session merged the pull request, but you cannot tell which closeout steps it finished.
- The linked issue may still be open, closed as not-planned, or unlinked.

## Verified Workflow

### Quick Reference

Bind the merge state, then read the closeout evidence before you write:

```bash
# 1. Bind the merge and its head.
gh pr view <number> --repo <owner>/<repository> \
  --json state,mergedAt,mergeCommit,headRefOid,closingIssuesReferences

# 2. Read the linked issue state.
gh issue view <issue> --repo <owner>/<repository> \
  --json state,stateReason,closedAt

# 3. Find which closeout writes already exist.
gh pr view <number> --repo <owner>/<repository> --json comments \
  -q '.comments[] | "\(.createdAt) \(.author.login): \(.body[0:200])"'
```

### Suggested Approach

1. Treat `state: MERGED` as proof of the deliverable. Do not review the code, rebase,
   push, or enable auto-merge.
2. Separate the steps of the drive task into delivery steps and closeout steps. Delivery
   steps are review, repair, checks, and merge. Closeout steps run after the merge. They
   are the merge confirmation, the linked-issue check, the merge summary, and the lesson.
3. Stop with zero forge writes only when every closeout step is already complete, or when
   the drive task lists no closeout steps. A "stop when already merged" rule governs delivery
   work. It does not cancel a closeout step that the task requires.
4. Read the evidence for each closeout step. For the issue check, require
   `state: CLOSED` with the expected `stateReason`. A merge does not always close a linked
   issue: the reference can be missing from the merge target, or a closing keyword can be
   absent.
5. Write only the missing closeout items. Prefix each comment with the drive marker that the
   task defines. Do not repeat a summary comment that already exists.
6. Run the lesson step through its own workflow. It needs an isolated worktree, a duplicate
   search, and its publication path. Do not treat the post-merge comment as the lesson.
7. Report the terminal state, the merge commit, and the exact closeout steps you completed.

If the linked issue is open after the merge, record that finding on the pull request or look
for an authorized owner. Do not close an unrelated issue to make the state look complete.

Use the main rule when the request is ambiguous: a merged pull request whose closeout
steps are complete needs no comment. A closeout comment adds no value when no reader must
act on it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read "do not stop at a verdict" as delivery-only | Planned to stop at the merge and skip the remaining closeout steps | The task named closeout steps after the merge, so a stop left required work undone | Read the full step list and complete every step that the task names |
| Called the post-merge summary comment the lesson step | Treated one summary comment as both the merge record and the lesson | A short merge summary is not a durable, duplicate-checked lesson entry | Run the lesson workflow as a separate operation with its own delivery path |

## Results & Parameters

### Configuration

Decision table for a merged target:

| Observation | Decision |
| ------- | ------- |
| Merged; no closeout step is named in the task | Stop with zero forge writes |
| Merged; every named closeout step is complete | Stop with zero forge writes |
| Merged; the linked issue is open or closed with an unexpected reason | Record the finding; do not close an unrelated issue |
| Merged; a named closeout step is incomplete | Complete only the missing steps |
| Merged; the merge commit is absent from the default branch | Treat delivery as unproven; re-check the forge record |

### Expected Output

A closeout report contains:

- the observed state, merge timestamp, and merge commit;
- the linked issue state and its closure reason;
- each closeout step and its evidence; and
- the lesson outcome, with a pull request link or a recorded limit.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Agent session | Pull request drive that resumed after a merge | [Case notes](./pr-drive-post-merge-closeout-steps.notes.md) |

## References

- [Stop a PR drive when the target is already merged](pr-drive-stop-on-already-merged.md)
- [Check if already shipped before writing a plan](planning-check-already-shipped-before-planning.md)
- [Label-gated workflow re-run replays the old payload](github-auto-merge-ci-gating-merge-method.md)
- [Automation review authorization: CI boundary](automation-review-authorization-ci-boundary.md)