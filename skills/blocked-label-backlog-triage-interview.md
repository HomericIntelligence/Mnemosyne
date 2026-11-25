---
name: blocked-label-backlog-triage-interview
license: BSD-3-Clause
description: "Triage every open issue that carries a blocked label by verifying each blocker first, then interviewing the owner once per root cause. Use when a backlog of blocked or plan-blocked issues must be cleared and the owner decides how to unblock each one."
category: tooling
date: 2026-11-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [issue-triage, blocked-label, plan-blocked, backlog, owner-interview, state-labels, replan, supersede]
---

# Blocked-Label Backlog Triage Interview

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Clear a backlog of blocked issues quickly, with owner decisions that are based on checked facts. |
| **Outcome** | 31 blocked issues were grouped by root cause and resolved in four short interview rounds. 6 were closed, 1 was replaced, 18 went back to planning, and 4 stayed blocked with a stated reason. |
| **Verification** | verified-local: the label queries were re-run after the changes and showed only the intended issues. |

## When to Use

- The owner asks to review all issues that carry a blocked, plan-blocked, or implementation-blocked label.
- Many blocked labels are weeks old and the cited blockers may have changed.
- An automation loop marked issues "stuck, needs external feedback" after it repeated the same plan.
- An issue has a blocked label and an accepted-plan label at the same time.

## Verified Workflow

### Quick Reference

```text
1. List open issues per blocked label (one query per label; one issue can have several).
2. For each issue, read the issue state text and the last two comments.
3. Check the state of every issue that a blocker cites (open or closed).
4. Group issues by shared root cause.
5. Ask the owner one question per group, with a recommended default and 2-3 options.
6. Apply the answers. Verify with the same label queries.
```

### Detailed Steps

1. Query each blocked label separately. Report the counts. A label with zero issues is a result.
2. Read only the last comments, not the full thread. The blocker is usually in a "dependency",
   "reconciliation" or "plan review" comment.
3. Before you ask, check the cited dependencies. A shared dependency that is already closed
   unblocks the whole group at once. In the source session, eight issues named one closed
   prerequisite.
4. Classify each blocker, because the question differs:
   - dependency closed: propose "remove the label and replan";
   - premise changed (the artifact or process it needs was retired): propose "close as not planned";
   - code is delivered and only a live proof remains: propose "close as delivered" or "run the proof";
   - automation repeated an identical plan: ask which decision is missing, or propose a full replan;
   - the external input has not arrived (for example a public artifact): keep blocked and record the re-check condition;
   - the plan is accepted but the issue is stale: propose a new issue that restates the defect against the current repository, then supersede the old one.
5. Ask with grouped questions (at most four per round). Put the facts in the question so it
   stands alone. Quote the owner's free-text answer when it adds a requirement (for example
   "do not add flaky tests") and copy it into the issue comment.
6. Apply the answers in one pass. For each issue, post one comment that starts with the agent
   identity and states the owner decision and its date. Closing: use the correct reason
   (completed vs not planned). Replan: remove all blocked labels and set the needs-plan label.
7. Do not start planning runs yourself when a loop owns them. Report which issues now wait on it.
8. Re-run the label queries and report the remaining blocked issues.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Ask per issue | Planned one question for each of 31 issues. | Too many questions; most issues shared three root causes. | Group by root cause and verify dependency state first. |
| Trust the label | Treated each blocked label as a current fact. | One shared blocker had closed weeks before; the labels were stale. | Check cited dependencies before the interview. |
| Read the whole thread | Considered reading every comment. | Slow and noisy. | The last two comments and the state text hold the blocker. |

## Results & Parameters

- Rounds: 4. Questions per round: 3-4. Options per question: 2-3, recommended option first.
- Label queries: `gh issue list --state open --label <label> --json number,title,updatedAt`.
- Last comments: `gh issue view <n> --json labels,comments --jq '.comments[-2:][].body'`.
- Replacement issue: include `Supersedes #N`, the current-code evidence, and an answer to any
  required compatibility question; then close the old issue as not planned with a link.
- Authority and permissions: follow the
  [agent authority and host permissions policy](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md).
  The owner's interview answer is the authority for each close and relabel.

## Related Skills

- `automation-stale-plan-recheck-replans` — how a loop handles a stale accepted plan.
- `blocked-deletion-issue-unbuilt-prerequisites` — one blocked cleanup issue and its prerequisites.
- `architecture-github-labels-as-state-vocabulary` — the label vocabulary this triage edits.
