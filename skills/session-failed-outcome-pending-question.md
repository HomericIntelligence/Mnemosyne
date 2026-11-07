---
name: session-failed-outcome-pending-question
license: BSD-3-Clause
description: "Classify a fleet session by its terminal message content, not by its recorded failure outcome. Use when: (1) a monitor or ceremony sweep finds a session whose recorded terminal outcome is a failure label, (2) the session's last message is an operator-question call that never executed, (3) you are deciding to re-dispatch, nudge, rename, or report that session as failed, or (4) a prior finish state must be trusted before completion bookkeeping."
category: tooling
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [opencode, fleet, session, terminal-state, failed-outcome, pending-question, blocked-classification, monitoring]
---

# Session Failed Outcome Pending Question

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Classify a terminal session correctly before re-dispatch, rename, or completion bookkeeping when its recorded outcome says failure. |
| **Outcome** | Operational decision branch — a session recorded with a failure outcome had a pending operator question as its terminal message; classification changed from retryable failure to blocked on an operator decision. |
| **Verification** | verified-local — single live fleet case. |

## When to Use

- A fleet monitor or completion ceremony lists a session whose recorded terminal outcome is a failure label.
- The session's final message contains a question call to the operator that never executed (pending or running state), usually preceded by a summary of completed evidence.
- You plan to re-dispatch the task, send a continuation nudge, rename the session as done, or report it as failed.
- A prior terminal state is the basis for downstream actions such as learning passes, renames, or reports.

## Verified Workflow

### Quick Reference

```text
terminal outcome label = hint, not proof
read the bounded terminal messages before acting:
  success label + final answer text          -> done
  failure label + error trace                -> failed; failure handling
  failure label + unexecuted question call   -> blocked on operator decision
continue messages do not unblock a pending question: report and wait
```

### Suggested Approach

1. For each session with a failure outcome, read a bounded tail of its messages. The
   terminal message content decides the classification, not the outcome word.
2. An unexecuted question call as the terminal message means the agent finished its
   evidence work and asked the operator. The failure label records how the run ended
   (timeout, stop, or a later failed continuation), not the state of the task.
3. Classify that session as blocked on an operator decision. Surface the question header
   and options in the monitor report. Keep its branches and worktrees.
4. Do not send a continuation message. The agent already asked; a nudge produces a
   duplicate question or an answer the operator did not choose. Do not rename it as done;
   its task is not complete.
5. Do not re-dispatch the task. A fresh agent repeats the evidence work that this session
   already completed and asks the same question.
6. Resume only when the operator answers. The answer binds to the original question scope.
7. Only a terminal error trace counts as failure work. Apply normal failure handling to
   those sessions.

This rule composes with busy-flag and completion-record checks: every recorded state is a
hint, and the durable message content decides.

### If a step is unavailable

- Message reads are truncated or fail for the live store: classify as unknown and report;
  do not fall back to the outcome word alone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust the failure outcome word | Classified the session as failed from the recorded outcome alone | The terminal message was an unanswered operator question with completed evidence; the label recorded the run end, not the task state | The outcome label is a hint; the terminal message content is proof |
| Preparation to re-dispatch | Considered a fresh agent for the "failed" research task | The evidence-gathering was finished; only the operator decision was missing, so a re-dispatch repeats expensive work and re-asks the same question | Blocked-on-operator needs the answer, not a new worker |
| Preparation to nudge | Considered a continuation message to the blocked session | A pending question cannot be advanced by the agent itself; the nudge duplicates the ask or forces an unchosen default | Report the pending decision and wait for the operator |

## Results & Parameters

### Configuration

```text
success + final answer            -> done; completion actions allowed
failure + error trace             -> failed; failure handling
failure + unexecuted question     -> blocked; report question; no nudge; no re-dispatch
failure + unreadable tail         -> unknown; report; no classification from the label
```

### Expected Output

- The monitor report separates failed, done, and blocked-on-operator sessions.
- A blocked session keeps its title, branches, and worktrees, and carries the pending
  question header in the report.
- No re-dispatch of completed evidence work, no duplicate questions, no premature done
  renames.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2 session fleet on Linux | Fleet completion sweep: a research session recorded a failure outcome; its terminal message was an unexecuted operator-question call after completed evidence work | Generalized evidence in [notes.md](../skills/session-failed-outcome-pending-question.notes.md) |

## References

- [Related skill: session-batch-status-flag-lies](session-batch-status-flag-lies.md) — the completion record and reply content outrank the busy flag; this entry adds the same rule for the failure-outcome label.
- [Related skill: async-user-decision-continuity](async-user-decision-continuity.md) — keep one pending question per decision; this entry tells the observer how to classify it.
- [Related skill: swarm-agent-status-misread-as-premature-exit](swarm-agent-status-misread-as-premature-exit.md) — misreading a running agent as done; this entry covers misreading a blocked agent as failed.
