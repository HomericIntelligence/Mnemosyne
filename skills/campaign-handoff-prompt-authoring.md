---
name: campaign-handoff-prompt-authoring
license: BSD-3-Clause
description: "Prepare a self-contained handoff when a multi-step task moves to another session or machine. Preserve progress, evidence, dependencies, and authorization so work can continue."
category: tooling
date: 2026-07-05
version: "1.1.0"
user-invocable: false
verification: verified-local
tags:
  - handoff
  - resume-prompt
  - cross-machine
  - serial-campaign
  - epic
  - context-compaction
  - operator-continuity
---

# Campaign Handoff Prompt Authoring

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-05 |
| **Objective** | Write a single self-contained resume prompt that lets a fresh session (no prior transcript) pick up a strictly-serial multi-PR epic campaign mid-flight without re-deriving anything. |
| **Outcome** | Prompt authored and delivered this session (epic #1809 got a status comment; the handoff prompt was handed to the operator). Not yet executed end-to-end on the second machine. |
| **Verification** | verified-local |

## When to Use

- A long-running serial epic (e.g. ProjectHephaestus epic #1809 — a queue-based automation-pipeline rewrite delivered as ~14 strictly-serialized sub-issues #1810→#1823, each `Depends on #prev`) is being driven one PR at a time on one machine and the operator asks to move the work to another machine.
- Context compaction is about to wipe the working memory that makes a serial campaign safe — the same prompt shape doubles as a compaction-survival brief.
- You need the receiving session to continue without: (a) re-reading and re-classifying the in-flight PR's review threads, (b) losing the completion condition that a session-scoped Stop hook was enforcing, or (c) picking up two dependent issues at once (mutual-conflict strand).

## Verified Workflow

A handoff helps the next session continue the requested work without reconstructing the
whole conversation. Adapt its length and order to the task. Include enough evidence to
identify completed work, remaining work, real dependencies, and existing authorization.

### Quick Reference

```text
GOAL: Requested outcome and observable completion criteria.
STATE: Completed work, active branch/head, changes, and unresolved findings.
REFERENCES: Accessible design decisions, source paths, issues, and evidence.
NEXT WORK: Useful next actions and actual dependencies.
AUTHORIZATION: Existing scope and any external permission still needed.
LIMITS: Missing evidence, unavailable tools, and partial blockers.
```

### Detailed Steps

1. Restate the requested outcome. Distinguish user requirements from suggested techniques
   or historical review conventions; do not turn a prior session hook into a new gate.
2. Point to durable artifacts the receiving session can access. Summarize unavailable
   local context rather than assuming account memory or a transcript travels with the task.
3. Record the current source revision and work state. For unresolved findings, retain the
   evidence, proposed disposition, and any relevant fix so the next session can recheck
   changed facts without repeating completed investigation.
4. Describe dependencies that constrain execution. Serialize work when one change depends
   on another; allow independent work to continue when a dependency is blocked.
5. Carry forward existing authorization and applicable repository or host constraints.
   Name the source and protected action for any necessary approval. Do not ask again for
   routine work already authorized by the task.
6. Suggest the next useful action and relevant recovery references. If background work can
   conflict, suggest inspecting its state before starting another writer.
7. Continue toward completion through implementation, correction, and useful verification.
   A handoff, plan, or review round is an intermediate result unless it is the requested output.

The original serial campaign examples and commands are retained in
[the case notes](campaign-handoff-prompt-authoring.notes.md). Their issue numbers, fixed
review sequence, and deployment conditions describe that campaign rather than a general
workflow requirement.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Terse handoff | Wrote `continue epic #1809 from PR #1851` | Receiving session had to re-read the whole PR and re-classify every unresolved thread from scratch — wasted a full context window | Inline the per-thread REAL/FALSE-POSITIVE classification (with fix / refutation) directly in the prompt |
| Relied on the Stop hook | Assumed the "each issue passes /review-pr-strict AND repo passes /repo-analyze-strict-full" goal would carry over | A fresh session on another machine has no session-scoped Stop hook, so it would stop early after one PR | Restate the completion condition explicitly in the prompt body |
| Pointed at "the plan" | Referenced "the plan" without a path | The plan lived in a local `~/.claude/plans` file that does not exist on the other machine — dangling reference | Point only at durable in-repo artifacts (issue bodies, committed docs, the ADR) plus account-level memory files |

## Results & Parameters

A useful handoff lets the receiving session identify the requested outcome, resume the
correct source state, reuse applicable evidence, and choose the next authorized action.
Report uncertainty rather than inventing completion. Preserve task-specific serial
ordering, publication requirements, and authorization when they still apply.

The original prompt was authored and delivered locally. Its execution on the receiving
machine was not verified; this generalized guidance adds no execution claim.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Epic #1809 cross-machine handoff, 2026-07-05 session — prompt authored and delivered to operator; NOT yet executed end-to-end on the second machine (hence verified-local, not verified-ci) | epic #1809 body + project_epic1809_execution_playbook.md |
