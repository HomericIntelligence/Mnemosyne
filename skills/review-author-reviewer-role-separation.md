---
name: review-author-reviewer-role-separation
description: "Keep the reviewer role and the author role separate in an automated pull-request review-and-fix workflow that uses several subagents. Use when: (1) a reviewer agent has findings that need author answers, (2) a terminal GO must stay valid after a rebase or base merge, (3) a clean review is refused at delivery for a digest drift or a forked reviewer-state chain, (4) a chained publish command can reuse a stale payload, or (5) a force push, rebase, or sequence-number collision must be handled."
category: tooling
date: 2026-10-27
version: "1.0.0"
user-invocable: false
tags:
  - pr-review
  - review-exchange
  - role-separation
  - self-approval
  - head-bound-verdict
  - force-push
---

# Review Author and Reviewer Role Separation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-27 |
| **Objective** | Keep the independent reviewer separate from the author in a multi-agent review-and-fix loop. |
| **Outcome** | Operational. Derived from one live review-and-fix session. Evidence is in the notes file. |

## When to Use

- A review-and-fix workflow uses a reviewer agent, a fixer agent, and a coordinator.
- A reviewer has findings and the author answers are available (for example in the author's own PR comment).
- The head of a reviewed PR moved after a terminal GO.
- A clean source review is refused at delivery.
- You must publish several reviews with a chained command, or you must rebase or force push.

## Verified Workflow

### Quick Reference

```text
reviewer (fresh context)  -> findings -> returns "blocked: needs author response"
fixer                     -> fixes findings -> publishes author response (sanctioned path)
new reviewer (fresh)      -> reviews the NEW head -> delivers verdict
```

### Suggested Approach

1. **Never mix roles.** The reviewer agent must not write or publish the author response, the author-event carrier, or answers to findings on the author's behalf. This applies even when the answers come from the author's own PR comment. A fresh-context reviewer that publishes the author answers and the verdict is flagged as self-approval by permission classifiers, and it loses independence. Return a blocked result "needs author response" instead. A separate fixer fixes the findings and publishes the author response through the sanctioned path. A new reviewer in a fresh context then reviews the new head and delivers the verdict.
2. **Bind a terminal GO to one head.** A rebase, a merge of the base branch, or any push moves the head. The earlier GO is then invalid, and auto-merge pinned to the old head is cancelled. Re-review the new head after such a change. Do not re-review a PR whose terminal GO already covers its current head.
3. **Handle a delivery refusal after a clean source review.** The binding can be refused for two reasons: a linked-issue digest drifted after a later issue comment, or an older unfinished exchange makes the reviewer-state history a forked chain. Do not edit digests or tooling. Do not hand-write a carrier. Do not fake a human-decision or reframe event: the human-decision event only accepts risk or selects a closure for named findings, and it cannot say that one exchange supersedes another. The only sanctioned fallback needs explicit owner authority. After a real source review, render the terminal state with the exchange reducer, publish that rendered carrier directly, and verify the readback.
4. **Make chained publish commands fail closed.** Treat a failed head check or repository check as fatal. Use a fresh per-run directory for payload files. Run from the repository directory. Stop at the first failed check. Re-check the head before every write.
5. **Handle history changes with care.**
   - A force push needs explicit owner permission. Push with a lease pinned to the expected remote commit. Never push the default branch.
   - A plain rebase of a branch that contains merge commits drops the changes made inside those merges. Rebuild the net diff as clean commits.
   - After a rebase, renumber colliding sequence numbers (decision records, migrations) and update every reference.
   - If the base branch already holds the change, drop the duplicate commits. Do not push an empty branch. Report it so the owner can close the PR as superseded.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Reviewer answers findings | A fresh-context reviewer published the author answers and the verdict. | A permission classifier flagged it as self-approval. | Return "needs author response". Let a fixer publish the answers. |
| Reuse of a payload file | A chained command reused a payload file in a shared temporary directory. | A stale duplicate review was published twice. Published reviews cannot be deleted. | Use a fresh per-run directory and stop on the first failed check. |
| Fake exchange event | A human-decision event was considered to supersede an older exchange. | The event cannot express supersession. | Use owner authority and the reducer-rendered carrier. |
| Plain rebase | A rebase of a branch with merge commits. | Changes made inside the merges were lost. | Rebuild the net diff as clean commits. |

## Results & Parameters

### Configuration

```yaml
reviewer_may_publish_author_response: false
reviewer_context: fresh_per_round
verdict_scope: exact_head
re_review_when_head_moves: true
re_review_when_go_covers_head: false
force_push: owner_permission_and_lease_pinned_to_expected_commit
```

### Expected Output

- The reviewer publishes only reviewer states and verdicts.
- The fixer publishes only author responses.
- Each GO covers the current head of the PR.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Anonymized automated PR review-and-fix workflow | One session with several subagents | See [notes](review-author-reviewer-role-separation.notes.md). |

## References

- [Terminal carrier sole publisher](review-exchange-terminal-carrier-sole-publisher.md)
- [Head refresh and carrier repair](review-exchange-head-refresh-carrier-repair.md)
- [Rebase and skip duplicate merged commits](git-rebase-skip-duplicate-merged-commits.md)
