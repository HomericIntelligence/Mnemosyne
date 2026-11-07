---
name: session-batch-status-flag-lies
license: BSD-3-Clause
description: "Check the completion record, not the host busy flag, before a batch waits on an agent session. Use when a fan-out loop waits for each session to report idle and one stuck flag stops every remaining batch."
category: tooling
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [agent-orchestration, batch, fan-out, status-flag, stale-state, completion-detection, session]
---

# Session Batch Status Flag Lies

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Keep a fan-out batch moving when the host keeps a session marked busy after its turn has already finished |
| **Outcome** | Successful — the stuck flag was found on many sessions, and a record-based completion check released batches that the flag had blocked |
| **Verification** | verified-local — reproduced on a live agent host across many sessions |

## When to Use

- A loop sends one prompt to each session in a batch and then waits for the batch to become idle.
- The loop reads a host status field, such as a busy marker, to decide that a turn is still running.
- One session keeps the whole batch waiting, or the loop reaches its deadline with most sessions finished.
- Sessions were interrupted, the host restarted, or a turn ended while an error was written.

## Verified Workflow

A busy marker is a hint, not proof. A host can set it and never clear it. Treat the
completion record as the authority, and treat the busy marker as a weak signal only.

1. Read the completion record for each session. This is the recorded turn outcome and its
   timestamp, not the busy marker.
2. Compare the moment the turn started with the moment the completion record was written. If
   the completion record is older than the busy marker, the marker is stale.
3. Prefer the newest durable signal in the session: a finished turn record, a completed reply,
   or the newest message time.
4. Confirm that a reply belongs to your own prompt. Read the assistant message that follows
   your prompt, because later turns and sub-agents can replace the newest message.
5. Decide per session, not per batch. Release each session that has a completion record and
   let the rest continue.
6. Bound the wait on activity, not on the marker. Use the newest message time to detect a live
   turn, and treat a long gap with no new messages as finished or stalled.
7. Verify the reply content before you act on it. A finished turn can still hold a refusal, an
   error, or a question for the operator.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Wait on the busy marker alone | The loop polled the session busy marker and slept until it cleared | The marker stayed set long after the turn finished, so the batch waited while every reply was already present | Read the completion record and the newest message time instead |
| Read the newest message in the session | Took the last assistant message as the reply to the prompt | Later turns and sub-agents wrote after the prompt, so the check read an unrelated reply and rejected a completed turn | Bind the reply to the prompt by reading forward from it |
| Treat every completed turn as a success | Renamed or recorded each session whose turn had finished | Some finished turns held a refusal, an error, or a question, and a few agents could not perform the task at all | Verify the reply content before you record the result |

## Results & Parameters

| Parameter | Rule |
| --------- | ---- |
| Completion authority | The recorded turn outcome and the newest message time; not the busy marker |
| Staleness test | Completion record older than the busy marker means the marker is stale |
| Reply binding | The assistant message after your own prompt, for your own model |
| Wait bound | The newest message time, with a no-activity threshold per session |
| Batch release | Per session, so one stuck marker cannot block the batch |
| Result acceptance | Require the expected result in the reply text, not only a finished turn |

### Evidence

A fan-out loop sent the same instruction to about two thousand agent sessions in groups of
twenty. The loop treated the host busy marker as the completion signal. The marker was set
again and never cleared for sessions that had already finished, and one such session stopped
the whole batch. Reading the recorded turn outcome and the newest message time showed which
sessions had finished and which were still live. Several sessions that looked busy had
complete replies. A second defect appeared on review: sessions that answered in a different
result schema, or could not perform the task at all, were recorded as successful until the
reply text was checked.