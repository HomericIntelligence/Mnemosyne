---
name: merged-delivery-resume-audit
license: BSD-3-Clause
description: "Audit a delivery that a peer completed before a resume or takeover, then finish only the missing record steps. Use when a directive says to drive a pull request to a terminal state, a resume directive restates work from an interrupted session, or a red check remains in the check list, and a fresh read shows the artifact already merged. Do not repeat the delivery. Confirm the merge, the closed linked issue, the post-merge record, and the durable-learning step, and post only what is absent."
category: tooling
date: 2026-11-04
version: "1.0.0"
user-invocable: false
tags: [pull-request, merge, resume, interrupted-session, peer-completion, post-merge-record, linked-issue, stale-check, durable-learning, zero-delta]
---

# Merged-Delivery Resume Audit

**Supporting detail:** [notes](./merged-delivery-resume-audit.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-04 |
| **Objective** | Complete a resume or takeover of a delivery directive without repeating work that a peer already merged. |
| **Outcome** | Operational. In the source case, the pull request was already merged when the resumed turn started. The audit confirmed the merge commit, the completed linked issue, and the presence of the post-merge record. The only remaining delta was one absent post-merge comment, which the resume posted. No branch, head, or merge was changed. |

A resume turn can start after a peer merged the pull request. The directive
and its instructions still describe an open pull request. They also still
show a red check from the last run. Both are stale premises.

The rule: **a terminal artifact state replaces the drive steps.** Read the
live state first. Then compute the delta between the delivered state and the
directive contract. Repair only that delta.

## When to Use

- A directive says to drive a pull request to `MERGED`, and a fresh read shows
  `state: MERGED`.
- A turn resumes after an interruption, and a peer may have finished the
  delivery in the gap.
- The check list shows a failure, and the artifact is already merged.
- A merge exists, and you must decide whether the post-merge steps ran.

Do not use this skill for an open pull request. Use the normal drive steps
for an open pull request.

## Verified Workflow

### Quick Reference

```bash
# 1. Fresh read. Do not trust the directive or a prior-turn snapshot.
gh pr view <PR> -R <user>/<repo> --json state,mergedAt,mergeCommit,headRefOid,labels
gh issue view <ISSUE> -R <user>/<repo> --json state,stateReason,closedAt

# 2. List the record comments, and count your own prefix.
gh pr view <PR> -R <user>/<repo> --json comments \
  --jq '[.comments[] | select(.body | contains("[<prefix>]"))] | length'
```

### Suggested Approach

1. **Read the live state before any mutation.** Compare the state of the
   pull request and of the linked issue. Record the merge commit, the merged
   head, and the merge time. Use these values in the report. The directive
   head can be stale.
2. **Treat a red check as a history record, not as a blocker, when the merge
   is final.** A merge is irreversible. A check that failed before or after
   the merge cannot change the state. Record the check, its run, and its time
   in the final record. If the same check is still red on the default branch,
   handle it as separate work. Do not rebase or push a merged branch.
3. **Compute the post-merge delta.** Test each step of the directive contract
   against evidence:
   - the merge commit exists, and the merge state is final;
   - the linked issue closed, with a state reason that shows completion;
   - exactly one post-merge record comment exists from this driver;
   - the durable-learning step ran, with a disposition.

   A pull request merge completes code. It does not complete the bookkeeping
   steps. A peer merge can leave them unexecuted.
4. **Repair only the missing steps.** Post the record comment only when no
   comment with your prefix exists. Name the merged content, the merge
   commit, the linked issue, and any unresolved check. Run the learning step
   when the directive has it, and give its disposition.
5. **Do not repeat delivery.** Do not amend, rebase, re-sign, force-push, or
   merge again. Do not reopen the delivered work. A second mutation can
   produce a new record and a false report of a new delivery.
6. **Stop when the delta is empty.** Report a zero-delta takeover with the
   evidence. Do not post a duplicate comment to show activity.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Act on the directive premise | Prepared a drive from a resume directive that described an unmerged pull request | A peer merged the pull request before the resume turn started. A new push or merge step would have failed or duplicated work. | Read the live forge state first. A directive premise is a claim, not state. |
| Read the check list as current risk | Treated the one red check as a reason to fix the branch | The check ran on a run that the merge did not wait for. The merge was already final. | A red check cannot reverse a terminal merge. Record it. Handle default-branch fallout separately. |
| Report only the merged state | Verified `state: MERGED` and stopped | The post-merge record comment was absent. The bookkeeping step had not run. | Enumerate the contract steps. Repair the missing ones. |

## Results & Parameters

### Configuration

```yaml
fresh_read:
  - pr_state, merged_at, merge_commit, head
  - linked_issue_state, state_reason, closed_at
  - record_comment_count_for_prefix
red_check_after_merge:
  action: record-run-and-time
  forbidden: [rebase, push, second-merge, reopen]
post_merge_delta:
  - merge-commit-present
  - linked-issue-closed-completed
  - one-record-comment-per-driver
  - durable-learning-disposition
zero_delta: report-and-stop
```

### Expected Output

- One merge commit, one merged head, and one merge time in the report.
- The linked issue state with its state reason.
- A count of driver record comments that is not more than one.
- A learning disposition, or a recorded limit.
- No new commits on the merged branch.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared monorepo under a many-lane milestone | Resume after an interruption found a merged pull request with a closed linked issue | See [notes](./merged-delivery-resume-audit.notes.md) for the evidence sequence and the delta. |

## References

- [mid-drive-peer-completion-audit.md](mid-drive-peer-completion-audit.md) — peer completion during an active drive. This skill covers the resume turn that starts after the merge.
- [shared-repo-interruption-yield-to-peer-pr.md](shared-repo-interruption-yield-to-peer-pr.md) — yield after an interruption when a peer delivered the intent.
- [ci-cd-verify-merged-prs-end-to-end.md](ci-cd-verify-merged-prs-end-to-end.md) — content verification of merged pull requests.