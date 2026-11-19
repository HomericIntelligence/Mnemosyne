---
name: goal-defer-error-notification-fallback
license: BSD-3-Clause
description: "End a goal-driven turn safely when the shell-deferral call errors or the goal is already in a limit state and a background shell holds the pending result. Use when: (1) the deferral tool call returns an error state, (2) the goal flips to a token or usage limit between turns while a watcher shell runs, (3) you are tempted to poll the shell output or to re-issue the deferral in a loop, (4) you are unsure whether the native completion notification arrives without a successful deferral, or (5) the goal's completion gate keeps re-firing while its pending condition is another party's action that you cannot perform and each status check finds no change."
category: tooling
date: 2026-11-07
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [goal-mode, deferral, background-shell, budget-limit, native-notification, fallback, opencode, human-blocked, completion-gate]
---

# Goal Defer Error Notification Fallback

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Leave a goal in a recoverable state when the turn ends with a background shell pending and the deferral path is unavailable. |
| **Outcome** | Successful — the deferral call returned an error and the goal moved to a budget limit; the session ended each turn with a state summary, and the background shell's native completion notification resumed the work. |
| **Verification** | verified-local — single live case on a goal-mode agent host with a long-running validation watcher shell. |

## When to Use

- The deferral tool call for a background shell returns an error state instead of registering.
- The goal moves to a budget or usage limit while the turn that holds the deferral call is still running, so no further deferral attempt is possible.
- A watcher shell whose result the goal needs runs in the background, and you consider polling its output file to pass the time.
- You are deciding whether to retry the deferral call, relaunch the watcher, or declare the goal blocked when only the deferral failed.
- The goal gate blocks every stop while the pending condition is a human-only action (for example, a privileged step on another host), and repeated status checks keep returning "no change".

## Verified Workflow

### Quick Reference

```text
1. Try the deferral once with the live shell identifier.
2. Deferral errors, or the goal is already limited -> stop; do not loop the call.
3. End the turn with a state summary that names the shell identifier,
   the pending condition, and the next action for the resume turn.
4. Do not poll the shell output. The native completion notification for the
   shell resumes the session without a registered deferral.
5. On the notification, check the goal state first. Active -> continue.
   Limited -> report and wait. Cancelled -> stop.
6. No notification after the shell is gone -> read the goal state; if it
   lists the shell as awaited, release the stale deferral and continue.
```

### Suggested Approach

1. Try the deferral once. It is the sanctioned binding between the goal and the shell.
2. Treat an error state on the call as terminal for this turn. The failure does not prove
   that notification is impossible; it proves only that the binding did not register.
3. Make the watcher shell self-contained. It must print the final result, the evidence,
   and the next-step hint to its own output stream. The resume turn reads that output; no
   in-memory state is required.
4. End the turn with a summary, not with silence. Name the shell identifier, the condition
   it waits on, its estimated duration, and the exact action the notification should
   trigger. A later resume turn, possibly with fresh context, reconstructs the plan from
   this summary.
5. Do not poll the shell output file. Polling spends the limited turns that forced the
   fallback and adds no information that the completion notification does not deliver.
6. On the native completion notification, read the goal state before acting:
   continue when it is active, report and wait when it is limited again, and stop when it
   is cancelled.
7. If the completion notification never arrives, query the goal state. A stale awaited-shell
   record, confirmed against a dead shell process, is released with the release call; then
   work continues from the watcher output.

This fallback concerns continuity, not correctness of the pending work. The deferred
condition still gates the goal: a shell result that does not satisfy it resumes only for
reporting, not for claiming completion.

### Pending condition is another party's action

Use this branch when no watcher result is pending. The gate needs an action that only another
party can perform, and you have already asked for it.

1. Name the exact action, the actor, and the check that proves it once, in one `needs input`
   line. Repeat that line unchanged on a forced turn. Do not add new analysis.
2. Count a status check as evidence only if its answer can differ. Repeating an identical
   check in the same minute adds no information. Run one check per forced turn at most, and
   skip it when the previous check is recent.
3. Put the check in a self-contained watcher that exits when the external state changes
   (a new comment, a changed label, a merged request). Its exit is the wake-up signal.
   Give it a long timeout. Do not start a new watcher for each forced turn.
4. Never report success on your own advice or posts. Success needs the other party's own
   report or an independent state change.
5. If the action is outside your authority or tools, do not look for a workaround. Ask the
   user to act or to clear the goal.

### If a step is unavailable

- The goal query itself is unavailable: keep summaries in the transcript and wait for the
  notification. Do not invent goal state.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Loop the deferral call in one turn | Re-issued the deferral after its error state | The same error state repeated; the goal then moved to a budget limit, so no further call was possible | One failed deferral is terminal for the turn; end with a named-pending summary instead |
| End the turn with no resume contract | Considered stopping after the errored deferral without a summary | A later resume turn starts with fresh context and no plan; the watcher result has no consumer | The summary is the resume contract: shell identifier, pending condition, next action |
| Poll the watcher output to stay productive | Read the shell output while limited | Each poll spends the scarce turns and returns an unfinished result | Wait for the native completion notification; it resumes the session without a deferral |
| Re-check external state on every forced turn | Ran the same status query each time the gate re-fired while waiting for a human-only action | Several hundred identical checks, each with the same unchanged result and the same status line | One precise `needs input` line, then an event-driven watcher; spend a turn on a check only when the answer can change |

## Results & Parameters

### Configuration

```text
deferral attempt      -> once per turn, with the live shell identifier
on error or limit     -> end the turn; summary names shell and pending condition
watcher shell         -> self-contained; prints final result and evidence
resume order          -> goal state check, then shell output, then action
lost notification     -> goal state lists awaited shell; confirm dead; release, resume
```

### Expected Output

- Each limited turn ends with a summary that names the watcher and the pending condition.
- The native completion notification resumes the session; the resume turn reads the
  watcher output and continues or reports.
- No relaunched watcher, no polling loop, no duplicate deferral error rows.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode goal-mode on Linux (v2.2 series) | Engine bring-up session whose goal depended on a multi-hour cluster validation watcher; the deferral call errored and the goal moved to a budget limit across several turns | Generalized evidence in [notes.md](../skills/goal-defer-error-notification-fallback.notes.md) |

## References

- [Related skill: detached-launch-survives-harness-restart](detached-launch-survives-harness-restart.md) — the same watch-and-survive requirement on the process side.
- [Related skill: async-user-decision-continuity](async-user-decision-continuity.md) — preserve a pending decision across turns; this entry covers a pending shell result.
