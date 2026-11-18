---
name: pr-prose-closing-keyword-closes-followup-issue
description: "Keep a pull request from closing an issue that it does not finish. Use when you write, delegate, or review a pull request title or body that names more than one issue, when a follow-up issue exists for work the pull request leaves open, or when an issue closed at merge and its work is not done."
category: tooling
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags: [pull-request, closing-keyword, auto-close, follow-up-issue, issue-tracking, review]
---

# Pull-Request Prose That Closes a Follow-Up Issue

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Make the set of issues that a merge closes equal to the set that the change finishes. |
| **Outcome** | Operational. Observed once on one forge; the verification command and the phrasing rule worked in a later pull request. |

## When to Use

- You write a pull request body that mentions a follow-up, a related, or a dependency issue.
- You give pull request text to an agent or a template, and the text names issues.
- You review a pull request before merge, and the change leaves part of its work to another issue.
- An issue closed as completed at merge, and its work is not done.

## Verified Workflow

### Quick Reference

Read the closing set that the forge detected, not the text that you wrote:

```bash
gh pr view <pr> --json closingIssuesReferences --jq '[.closingIssuesReferences[].number]'
```

The list must equal the issues that the change finishes. Run it again after every edit of the title or body.

### Suggested Approach

1. Know what the forge scans. It reads the pull request title and body, and the commit
   messages that reach the default branch (a squash merge uses the pull request text). A closing
   verb (close, fix, resolve, in any tense or case) before an issue number closes the issue.
   A colon between them is enough. The match is not limited to a line that starts with the
   keyword. It applies when the pull request targets the default branch.
2. Write the intended closings on their own lines, one issue each: `Closes #N`.
3. Name every other issue with a phrase that has no closing verb before the number:
   `see #N`, `refs #N`, `tracked in #N`. Do not write a noun such as "the durable fix: #N".
   Rephrase it: "the durable change is tracked in #N".
4. Before merge, compare the detected closing set with the intended set. If it has an extra
   issue, edit the text and read the field again. Do not merge until the sets are equal.
5. When you give the text to an agent, put rules 2 and 3 in the brief, and check the field
   after the agent opens the pull request. A brief that said "one closing line; refer to other
   issues with `see #N`" gave a pull request that closed only the intended issue.
6. After merge, check that each follow-up issue is still open. A forge closes it as completed
   and posts no warning.
7. If a follow-up closed by mistake, reopen it with a comment that names the cause (the
   merge text matched a closing verb) and says that the work is not done. Editing the merged
   text does not reopen it.

If your tracker or review process binds a review to an issue, an extra comment on a reviewed
issue can change its record. Do the reopen after the review closes, or record the note on the
pull request.

Related entries cover the opposite failure, where a merge does not close the intended issue
(`pr-drive-post-merge-closeout-steps`) and the use of the same field to find existing work
(`github-issue-workflow-and-preflight-gates`).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Name the follow-up in a sentence | Wrote "the larger refactor is the durable fix: #N" to point to the follow-up issue | The forge read "fix: #N" as a closing reference. The merge closed the follow-up as completed while its work was open | Use `see`, `refs`, or `tracked in` for every issue that the change does not finish |
| Trust the closing line | Read the body by eye and found one `Closes #N` | Prose in another sentence also closed an issue; the line was not the full closing set | Read the forge's structured field. It lists every detected closing reference |
| Check only for a missing link | Confirmed after merge that the intended issue closed | The check does not see an extra issue that closed | Also check that each follow-up issue is still open |

## Results & Parameters

- Detected closing set: `closingIssuesReferences` in `gh pr view --json`.
- Safe non-closing phrases: `see #N`, `refs #N`, `tracked in #N`.
- Observed on GitHub. Other forges have similar closing-keyword rules; their exact word lists
  and punctuation rules were not checked here. Read their documentation before you reuse the phrase list.
