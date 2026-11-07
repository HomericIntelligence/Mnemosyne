---
name: pr-drive-post-merge-closeout-steps
description: "Prove and steer the issue-link state of a pull request. Use when you open a drive PR or resume one: decide whether the body must close its issue with a standalone 'Closes #N' or must keep it open with 'Refs #N' when the issue's plan needs later evidence, prove the result with closingIssuesReferences before you submit, and complete the remaining post-merge steps when the target is already merged."
category: ci-cd
date: 2026-10-31
version: "1.1.0"
user-invocable: false
sharing: public
verification: execution-observed
tags: [pull-request, merge-state, review-drive, post-merge, closeout, lesson, zero-writes, resumption, execution-observed, closing-keyword, closingIssuesReferences, refs, issue-link]
---

# Prove the Issue Link, Start at the First Unfinished Step

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-31 |
| **Objective** | Give a drive pull request the issue-link state that its plan needs, prove that state before you submit, and start an already-merged target at its first unfinished step. |
| **Outcome** | Operational. A link claim that matches the forge, and a merged target that gets only the remaining writes, are both required. |

## When to Use

- You open a drive pull request and must decide between `Closes #N` and `Refs #N`.
- The brief, the issue, and the plan disagree on whether the merge must close the issue.
- The body discusses the closing keyword, quotes it, or drops it into a code span.
- A drive task starts or resumes and the first binding read shows `state: MERGED`.
- The drive instructions name steps that run after the merge, such as a confirmation of the merge and the linked issue, a merge summary comment, or a lesson record.
- A prior session merged the pull request, but you cannot tell which closeout steps it finished.

## Verified Workflow

### Quick Reference

Pick the link state from the plan, then prove it with the API. Do not trust prose:

```bash
# 1. Decide: a standalone line closes the issue; a Refs line keeps it open.
#    Use Closes only when the merge must complete the issue.
# 2. Prove the actual link state before you submit. totalCount 0 means no link.
gh api graphql -f query='query { repository(owner: "<owner>", name: "<repo>") {
  pullRequest(number: <number>) { closingIssuesReferences(first: 10) { totalCount } } } }' \
  --jq '.data.repository.pullRequest.closingIssuesReferences'

# 3. After merge, bind the closeout evidence.
gh pr view <number> --repo <owner>/<repository> \
  --json state,mergedAt,mergeCommit,headRefOid,closingIssuesReferences
gh issue view <issue> --repo <owner>/<repository> --json state,stateReason,closedAt
```

### Suggested Approach

1. **Choose the link state from the plan, not from the brief template.** Use `Closes #N` when the merge must complete the issue. Use `Refs #N` when the plan or a recorded decision defers evidence, a deploy, or an operator step to after the merge. An issue that must stay open needs `Refs`, and the PR body states why. When two sources disagree, follow the latest approved plan and the recorded decision, and say so in the PR body.
2. **Prove the result with `closingIssuesReferences`.** A body-text search is a hint, not proof. GitHub does not link a closing keyword inside a code span, so a backticked `Closes #N` in explanatory prose can make a body grep report a clue that the forge does not have. Confirm `totalCount` against the outcome you chose.
3. **Do not cite superseded approaches as current guidance.** A withdrawn review finding, an earlier plan revision, or a prior PR can set a precedent that a newer decision replaces. Read the authority record before you copy it.
4. Treat `state: MERGED` as proof of the deliverable. Do not review the code, rebase, push, or enable auto-merge.
5. Separate the steps of the drive task into delivery steps and closeout steps. Closeout steps run after the merge. They are the merge confirmation, the linked-issue check, the merge summary, and the lesson.
6. Stop with zero forge writes only when every closeout step is already complete, or when the drive task lists no closeout steps. A "stop when already merged" rule governs delivery work. It does not cancel a closeout step that the task requires.
7. Read the evidence for each closeout step. For the issue check, require `state: CLOSED` with the expected `stateReason`. A merge does not always close a linked issue: the reference can be missing from the merge target, a closing keyword can be absent, or the keyword can sit in a code span and never link.
8. Write only the missing closeout items. Prefix each comment with the drive marker that the task defines. Do not repeat a summary comment that already exists.
9. Run the lesson step through its own workflow. It needs an isolated worktree, a duplicate search, and its publication path. Do not treat the post-merge comment as the lesson.
10. Report the terminal state, the merge commit, the link state before the merge, and the exact closeout steps you completed.

If the linked issue is open after the merge, record that finding on the pull request or look for an authorized owner. Do not close an unrelated issue to make the state look complete.

Use the main rule when the request is ambiguous: a merged pull request whose closeout steps are complete needs no comment. A closeout comment adds no value when no reader must act on it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read "do not stop at a verdict" as delivery-only | Planned to stop at the merge and skip the remaining closeout steps | The task named closeout steps after the merge, so a stop left required work undone | Read the full step list and complete every step that the task names |
| Called the post-merge summary comment the lesson step | Treated one summary comment as both the merge record and the lesson | A short merge summary is not a durable, duplicate-checked lesson entry | Run the lesson workflow as a separate operation with its own delivery path |
| Followed the brief template's `Closes` against an approved plan that deferred evidence | Pointed the merge at an issue whose criteria needed operator logs and a deploy | The merge would close an issue that still had open acceptance work; the plan and a recorded decision required `Refs` | Choose the link keyword from the plan, state the reason in the body, and prove it |
| Wrote an explanatory sentence with a backticked closing keyword, then grepped the body | Body grep matched, so the body text reported a closing link | GitHub does not link a keyword inside a code span; the API reported zero linked issues | Prove the link with `closingIssuesReferences`, not with prose search |

## Results & Parameters

### Configuration

Decision table for the link state:

| Situation | Body line | Proof |
| ------- | ------- | ------- |
| The merge completes every acceptance criterion | `Closes #N` on its own line | `closingIssuesReferences` contains `N` |
| The plan defers evidence, a deploy, or an operator step to after the merge | `Refs #N`, with the reason in the body | `closingIssuesReferences` is empty |
| Policy gate requires a literal `Closes #N` line | `Closes #<split issue>` plus `Refs #N` | `closingIssuesReferences` contains the split issue only |

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
- the chosen link keyword and the proven `closingIssuesReferences` result;
- the linked issue state and its closure reason;
- each closeout step and its evidence; and
- the lesson outcome, with a pull request link or a recorded limit.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Agent session | Pull request drive that resumed after a merge | [Case notes](./pr-drive-post-merge-closeout-steps.notes.md) |
| Agent session | Drive PR that used `Refs` under an approved plan and proved it with the API | [Case notes](./pr-drive-post-merge-closeout-steps.notes.md) |

## References

- [Post-merge stop rule](pr-drive-stop-on-already-merged.md)
- [Check if already shipped before writing a plan](planning-check-already-shipped-before-planning.md)
- [Label-gated workflow re-run replays the old payload](github-auto-merge-ci-gating-merge-method.md)
- [Automation review authorization: CI boundary](automation-review-authorization-ci-boundary.md)