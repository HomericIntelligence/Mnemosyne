---
name: conflicting-co-issued-instructions-escalate-conflict
description: "Report a contradiction between co-issued instructions and execute neither side. Use when one turn delivers an execution contract and a closure ritual together, when a completion or ownership claim has no session evidence, or when a non-interactive host cancels the interactive question tool during escalation."
category: tooling
date: 2026-10-27
version: "1.0.0"
user-invocable: false
tags: [conflicting-instructions, coordinator, escalation, stop-and-report, done-claim, premise-failure, ownership-gate, non-interactive, question-tool, read-only, authorization, automation-loop, closure-ritual, stated-assumptions]
---

# Conflicting Co-Issued Instructions: Escalate the Conflict, Execute Neither

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-27 |
| **Objective** | Stop a worker from doing state-changing work when two instructions in one turn contradict each other, and produce one escalation report that carries the evidence. |
| **Outcome** | Successful — the conflict was reported with zero writes outside the report, and the co-issued closure ritual was completed read-only from the honest record. |

## When to Use

Use this skill when:

- One turn delivers two or more instructions whose authorized actions exclude each other. Example: an execution contract mandates pre-work and phases, and a closure instruction in the same turn forbids other actions and asserts completion.
- A completion claim in an instruction — "the session is Done", "the fix merged", "the plan is approved" — matches zero observable evidence: no run log, artifact, pull request, label change, or test output.
- A closure ritual (summary, learning, sign-off) arrives together with the work contract it should close, so its premise can only be checked against an empty record.
- An ownership or authority question (issue owner, lane owner, branch owner) is unresolved, and the contract carries its own stop-and-report or ambiguity clause.
- The host is non-interactive, so an escalation cannot ask a live question.

## Verified Workflow

### Quick Reference

1. For each co-issued instruction, list the required state-changing actions: label changes, comments, branches, commits, merges, publications, verdict strings.
2. Conflict test: executing one instruction must not violate an explicit constraint of another — a forbidden-action clause, an order clause, or an ownership clause.
3. Bind each instruction's premise to evidence before it authorizes action. A completion or ownership claim is a premise, not a fact.
4. On conflict or premise failure, execute neither instruction. Write one escalation report: both demands, the evidence check, the found state, and the stop clause.
5. Non-interactive hosts cancel the interactive question tool at runtime. Put the decision fork and the selected assumption in the report. Continue on the branch that changes nothing.
6. When a closure ritual accepts an empty-dismissal verdict — "no lesson", "reject", or a fixed fallback string — complete the ritual from the honest empty record after the conflict is recorded. Do not manufacture evidence to satisfy the ritual.

### Suggested Approach

Keep the report in the disposition family that the contract requires — for example its BLOCKED or PARKED form — so the coordinator can route it without interpretation.

Prefer the contract's own stop clause. A worker contract that says "stop and report on ambiguity" authorizes the stop for an instruction conflict. The clause keeps the stop inside the granted scope.

Do not silently select the instruction that arrived last. Silent selection is an unrecorded scope change. If one instruction must control to finish the turn — for example a closure ritual that a read-only completion can satisfy — record the selection as an explicit assumption in the report before you act on it.

Authorization boundaries still apply. A conflict report does not grant mutation authority, and a bare contract does not override host permission rules. Name the missing authority in the report when it is part of the reason for the stop.

When tools are unavailable or the conflict cannot be resolved from evidence, use the closure protocol's documented fallback, report the capability limit, and stop.

### Notes

Sanitized source evidence, the corpus dedupe record, and the escalation-channel error text are in [conflicting-co-issued-instructions-escalate-conflict.notes.md](conflicting-co-issued-instructions-escalate-conflict.notes.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Escalated the conflict through the interactive question tool in a non-interactive host. | The host cancelled the question: the run was non-interactive, so no user answer was possible; the turn produced no decision. | In a non-interactive host, put the fork and the selected assumption in the report body. Do not spend a turn on the interactive tool. |
| 2 | Considered executing the closure ritual first because it arrived last and forbade other actions. | The ritual's completion claim matched zero session evidence; executing it alone would have certified a Done state that never occurred and discarded the contract's required pre-work reporting. | Order of arrival is not authority. Check each instruction's premise against evidence before it controls the turn. |

## Results & Parameters

### Configuration

```yaml
conflict_detected: report-only        # execute neither instruction
premise_unverified: report-only       # completion or ownership claims need evidence
interactive_host: one-targeted-question
non_interactive_host: stated-assumption   # fork and assumption go in the report; least-destructive branch
closure_ritual_on_empty_record: honest-empty-verdict   # only when the ritual accepts it
```

### Expected Output

- One escalation report that names each conflicting instruction, its required or forbidden actions, the premise check result, and the stop clause used.
- Zero writes outside the report channel before a human or a controlling instruction resolves the fork.
- After resolution, the controlling instruction runs from its own start — pre-work included — never from an assumed midpoint.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Coordinator-orchestrated worker host (session-scoped single-issue lane) | One turn co-issued a multi-phase execution contract and a closure ritual over zero session evidence; 2026-10-27 | Sanitized session evidence: [notes.md](conflicting-co-issued-instructions-escalate-conflict.notes.md). |

## References

- [Verify premises before acting](planning-verify-issue-premise-before-implementing.md)
- [Check whether current source already satisfies a stale plan](stale-plan-already-resolved.md)
- [Preserve asynchronous user decisions](async-user-decision-continuity.md)
