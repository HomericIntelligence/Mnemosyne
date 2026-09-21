---
name: async-user-decision-continuity
description: "Preserve one pending user decision across asynchronous replies, automatic continuation, and handoff. Use when duplicate questions or delayed answers can change action authority."
category: tooling
date: 2026-09-21
version: "1.0.0"
user-invocable: false
tags: [asynchronous-input, authorization, pending-decision, handoff]
---

# Preserve asynchronous user decisions

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-09-21 |
| **Objective** | Keep each answer attached to the decision and scope that the user saw. |
| **Outcome** | Duplicate questions were observed to produce conflicting delayed answers. The prevention procedure has not been tested in a controlled replay. |

## When to Use

- A question remains unanswered while independent work continues.
- An automatic continuation or handoff resumes work with a pending question.
- Several replies concern different versions of one decision.
- A delayed reply can authorize a change to behavior or access.

## Verified Workflow

### Quick Reference

Keep one active question for each unresolved decision. Reuse that question while its scope is unchanged.
Match each reply to the question before you use it as authority. Time and automatic continuation do not constitute approval.

### Preserve the pending decision

First, check whether existing instructions already answer the question or authorize the action.
Do not create an approval requirement for work that is already authorized.

If input is necessary, record the protected action, unresolved choice, scope, and question identifier when one is available.
Keep this record in the existing task state or handoff. A separate database or service is not necessary.
Preserve pending questions with the current restrictions when context is summarized.

Do not send another version of an unanswered question because a new turn starts.
Report that the decision remains pending when a status update needs that information.
Continue work that does not depend on the answer.

An optional preference can use a stated default when the active instructions permit it.
A required approval remains pending until the user supplies it. Do not treat silence as that approval.

### Replace a question only when the decision changes

If new evidence changes the action or its scope, mark the earlier question as superseded.
Explain the change in the replacement question. Cancel the earlier request if the interface supports cancellation.
If cancellation is unavailable, retain its identifier so a late answer cannot silently authorize the replacement.
A wording change alone does not require another question.

### Reconcile delayed answers

Match an answer to the quoted question, request identifier, or other available conversation evidence.
Apply it only to the scope that the user answered.
An answer to a superseded question does not authorize a materially different action.
An explicit current user instruction can replace an earlier decision; record that replacement without asking for the same approval again.

If replies conflict, first check their question scopes and any explicit correction.
Do not choose an answer only because it arrived last or permits more work.
If the intended current instruction remains materially ambiguous, ask one reconciliation question.
Pause only the dependent action while that question is pending.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Repeat an unanswered decision | Send several versions of one question during continued work. | Delayed answers included incompatible choices, which made the current decision harder to establish. | Keep one pending request and preserve its identity across turns. |

## Results & Parameters

Use the existing task record to retain these values when relevant:

- Decision identity and protected action.
- Question identifier and scope revision.
- State: pending, answered, or superseded.
- The answer and the scope to which it applies.
- Any explicit instruction that replaces an earlier answer.

Expected result: dependent actions use an applicable user decision, and unchanged pending questions are not duplicated.
This is a proposed prevention rule based on an observed failure. It is not evidence that an implementation enforces the rule.
See [supporting evidence](async-user-decision-continuity.notes.md) for the evidence limits.
