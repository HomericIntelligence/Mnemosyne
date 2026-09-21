---
name: campaign-handoff-prompt-authoring
license: BSD-3-Clause
description: "Prepare a self-contained handoff across sessions. Use when task state can change during publication or another worker can update the same pull request."
category: tooling
date: 2026-07-05
version: "1.2.0"
user-invocable: false
verification: evidence-bound-review
tags: [handoff, resume-prompt, concurrent-publication, source-identity, operator-continuity]
---

# Campaign Handoff Prompt Authoring

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2026-09-21 |
| Objective | Preserve task progress without replacing newer work with an old status report. |
| Outcome | Readback detected a concurrent update. The handoff kept the newer source and its evidence boundary. |

## When to Use

- A task moves to another session or machine.
- A shutdown or context limit requires a durable checkpoint.
- Another worker can change a pull request (PR) while a handoff is prepared.
- Historical results and current source have different identities.

## Verified Workflow

### Quick Reference

Record the requested outcome, current source, evidence, dependencies, authorization,
and next action. Recheck mutable state before and after publication.
If another worker changes the PR, preserve that change and reconcile the handoff.

### Prepare the handoff

1. State the requested outcome and observable completion conditions.
2. Separate current user requirements from historical conventions and suggested techniques.
3. Link durable specifications, decisions, and evidence that the receiving session can access.
4. Summarize necessary local context when its files or transcript will not be available.
5. Record completed work, current branch and head, unpublished changes, and unresolved findings.
6. Keep each finding's evidence, proposed disposition, and relevant correction.
7. Record actual dependencies. Serialize dependent work, but permit independent progress.
8. Carry forward existing authorization and current repository and host constraints.
9. Name the protected action and source of any approval that remains necessary.
10. Identify the next useful action and how to inspect potentially conflicting workers.

A checkpoint or ownership claim is not proof that a worker is still active.
A missing temporary worktree is not proof that its branch or published work is lost.
Inspect current source references and execution state before another writer starts.

### Publish without replacing concurrent work

Before a PR-body update, read its repository, PR identity, state, source ref,
head, and current body. Keep the intended change separate from that snapshot.
Coordinate shared metadata ownership as well as source-file ownership.

When the provider supports a conditional update, bind the write to its supported
version condition. A head check alone cannot detect a body-only change.
Without conditional updates, a pre-write check cannot make replacement atomic.
Prefer an additive, source-bound note when another writer can update the same body.

After publication, read the PR identity, head, and relevant content again.
A successful API response proves that the request succeeded, not that its content
remains current after a concurrent write.

If the source or body changed, inspect the new content before another write.
Do not restore the old body or repeatedly apply the old update.
Preserve the newer work and reconcile only the missing information.
Use an additive note when it can preserve necessary evidence without another body replacement.
If authorship or the intended result remains ambiguous, stop only the conflicting write.

Update the checkpoint and final report to match the latest observed state.
State that this is an observation, not a guarantee against later changes.

### Keep evidence attached to its source

Keep historical test results and review decisions attached to their exact source.
Do not transfer a passing or failing result to a new head without compatible evidence.
A newer head does not erase valid history for the old head.
Use provider records as authority and handoff text as a guide to those records.

A handoff is an intermediate result unless the user requested the handoff itself.
Continue authorized implementation and verification when that remains the task.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Treat a successful update as final | Used the write response as proof of the published handoff. | Another worker changed the head and body before readback. | Read back identity and content, then preserve newer work. |
| Use an incomplete handoff | Named a task without its findings or accessible evidence. | The receiving session could not locate the necessary context. | Include current state and durable references. |
| Carry historical gates forward | Treated a prior session convention as a current requirement. | Historical process can exceed the user's actual requirements. | Preserve authority with its source and applicability. |

## Results & Parameters

Record the task outcome, source identity, observation boundary, unresolved findings,
durable references, actual dependencies, authorization, and next action.
For a metadata update, also keep the prior body and intended delta until readback.

The observed recovery preserved a concurrent worker's newer PR body and added a
separate status note. It did not validate the new implementation.
See [supporting notes](campaign-handoff-prompt-authoring.notes.md) for evidence limits.

## Verified On

A handoff publication session supplied direct before-and-after observations of
a concurrent PR update. This supports the recovery rule, not a transactional guarantee.
