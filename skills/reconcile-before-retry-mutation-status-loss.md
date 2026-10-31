---
name: reconcile-before-retry-mutation-status-loss
description: "Reconcile target state before re-running a mutating command whose terminal status was not observed. Use when output truncation, a broken stream, or a lost exit line leaves a possibly-completed mutation with an unknown result. Also use when an agent runtime restart or a cancelled tool call interrupts an ordered multi-step write, or when a create call to a forge or API returns a server error or times out after the request may have been processed."
category: debugging
date: 2026-10-15
version: "1.1.0"
user-invocable: false
tags:
  - retry
  - reconciliation
  - idempotency
  - delegation
  - automation
---

# Reconcile Before Retry After Mutation Status Loss

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-15 |
| **Objective** | Decide safely whether a mutating command with an unobserved terminal status is complete, needs one bounded re-invocation, or must stop for a human decision. |
| **Outcome** | Successful. State reconciliation plus one idempotent re-invocation produced the terminal status without double-apply. |

## When to Use

Use this skill when:

- A command that changes state (deletes, pushes, moves, writes) has returned to the caller, but its terminal status was never observed.
- The command output was truncated by the display layer, a pipe, or a lost tail line, so you cannot tell success from failure.
- The command is delegated or opaque: its contract forbids you to parse or intercept its output as a completion signal.
- A blind second run could apply the mutation twice or repeat an irreversible step.
- An agent runtime restart or a cancelled tool call interrupts an ordered
  sequence of mutating steps (edits, validations, commits, pushes). The set of
  steps that applied before the interruption is unknown.
- A create call (pull request, issue, comment) returns a server error such as
  HTTP 502, or the connection drops. The create has no transaction contract:
  the request may have been processed before the response was lost.

## Verified Workflow

### Quick Reference

1. Do not re-run immediately.
2. Reconcile the target with read-only checks that cover the command's effect surface.
3. Classify the state, then act once:

| Observed state | Classification | Action |
| -------------- | -------------- | ------ |
| All expected effects present, nothing pending | Consistent-complete | Report completion from state evidence; note the unobserved status as a limit. |
| Some effects present, the rest pending and repetition preserves work | Consistent-partial | Re-invoke at most once, and only when the command is idempotent by design or guards completed work; capture the terminal status. |
| State contradicts both outcomes, or no read-only probe exists | Inconsistent | Stop. Report both hypotheses with evidence for a human decision. Do not retry. |

### Suggested Approach

**Why a blind retry is dangerous.** A truncating harness still ran the command to completion. A
second run can double-apply additive steps or repeat an irreversible one (removals, force pushes,
ref deletes). Even a "safe" tool may fail closed on partially-applied state, and that refusal is
then ambiguous: it proves neither that the first run failed nor that the work remains.

**Reconciliation battery.** Use the command's own read-only or dry-run surfaces plus domain
invariants. For a git cleanup command, a minimal battery is:

```bash
git status --short                 # tree cleanliness
git rev-list --left-right --count HEAD...@{upstream}   # sync with upstream
git worktree prune -vn             # stale metadata that would remain (dry run)
git branch --merged HEAD           # candidates the run should have removed
```

For other domains, prefer an idempotent status endpoint or the tool's own dry-run mode. The
battery must answer: which claimed effects are present, and what work is still pending.

**Bounded re-invocation.** One re-invocation for the terminal status is acceptable when the state
is consistent and repetition preserves work — the command is idempotent by design, refuses on
completed items, or the remaining work is additive-safe. Do not loop: one unknown result, one
reconciliation, at most one re-invocation, then report.

**Delegated commands.** When a contract requires you to propagate the delegated result as-is,
reconciliation is not interpretation: you report the observed state and the unobserved status as
a recorded limit rather than inferring success from output fragments.

**Ordered multi-step writes.** When a restart or cancellation can fall between any two steps of
a planned sequence (edits, validations, commits, pushes, publishes), re-derive every step's state
from the target — never from memory of what ran. Build a per-step sentinel battery: the branch
name, the dirty-file list, and one read-only probe per step (for example, a unique string each
edit adds). Classify each step, then resume at the first unapplied step. An apply tool that
matches exact content fails closed on an already-applied step; treat that refusal as the
consistent-complete classification for that step, not as an error, and continue with the next
unapplied step. For a forge or API create that returns a 5xx or times out, probe existence of
the artifact (list or search for the branch, title, or body hash) before one bounded retry;
create endpoints are usually not guarded, so an unverified retry can duplicate the artifact.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | --------------- |
| Re-run the command at once | The tail line was missing, so failure seemed likely, and the command was started again. | The first run had completed; the second run either double-applies or fails closed, and its result is then misread as new information. | Reconcile state first; re-invoke at most once and only when repetition is safe. |
| Treat truncation as failure | An incomplete log reads like an interrupted process, so follow-up work assumed the mutation was pending. | The harness truncates display, not execution; the mutation had finished, and follow-up edits were based on a false failure premise. | Classify from state evidence, not from log shape. |
| Resume from memory after a runtime restart | After an agent runtime restart during an ordered write sequence, work resumed from the remembered completion point without per-step probes. | Steps that had applied failed closed with no-match refusals, which read as damage; a step believed applied but never written would have been dropped silently, because content validators check format, not lesson completeness. | Memory is not evidence after a restart. Classify every planned step with a sentinel probe, then resume at the first step whose sentinel is absent. |

## Results & Parameters

### Configuration

The decision table from the Quick Reference is the copyable configuration:

| Observed state | Classification | Action |
| -------------- | -------------- | ------ |
| All expected effects present, nothing pending | Consistent-complete | Report from state evidence; record the unobserved status as a limit. |
| Some effects present, repetition preserves work | Consistent-partial | Re-invoke at most once; capture the terminal status. |
| State contradicts both outcomes, or no read-only probe exists | Inconsistent | Stop and report both hypotheses with evidence. Do not retry. |

The budget is fixed: one unknown result, one reconciliation battery, at most one re-invocation.
The method requires at least one trustworthy read-only probe of the effect surface. Where none
exists, treat the result as unobserved and escalate rather than retry. Domain invariants prove
presence or absence of effects, not the wording of the lost status line.

## Verified On

- A repository-cleanup delegation with a truncated stream and a lost exit line: reconciliation
  classified the state as consistent, and one guarded re-invocation returned a clean zero exit.

## References

See `reconcile-before-retry-mutation-status-loss.notes.md` for the incident evidence and generic
reconciliation batteries for other domains.
