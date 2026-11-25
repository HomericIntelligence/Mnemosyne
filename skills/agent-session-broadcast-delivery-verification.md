---
name: agent-session-broadcast-delivery-verification
description: "Resume many stopped or completed agent sessions with one continuation prompt, and prove each session accepted it. Use when a directive requires a batch continuation, or a batch send reports success but delivery is unproven."
category: tooling
date: 2026-11-25
version: "1.0.0"
user-invocable: false
tags: [agent-sessions, broadcast, resume, delivery, verification, batch, orchestration]
---

# Agent Session Broadcast Delivery Verification

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Deliver one continuation prompt to many stopped or completed agent sessions, and prove that each target session accepted the prompt and started a turn. |
| **Outcome** | successful |

## When to Use

Use this skill for these conditions:

- A directive requires one continuation prompt to all recent sessions that did not end with a defined wrap-up step.
- Many stopped or completed agent sessions must resume in one batch.
- A batch send command reports success, but each session must prove that it accepted the prompt.
- The batch spans more than one agent host, and each host has a different resume mechanism.

## Verified Workflow

### Quick Reference

| Rule | Reason |
| ------ | -------- |
| Define "ended with X" from the last user message only | An earlier occurrence of X does not prove that the session ended with X |
| Exclude the orchestrator session from the batch | A continuation prompt to the sender can create a loop |
| Probe one target per host before fan-out | One probe shows the admission response and the failure mode without a large rollback |
| Use the durable non-interactive path for each host | Interactive attach and picker commands cannot run a batch unattended |
| Verify the prompt in the durable session store | A send command exit status shows admission, not execution |
| Treat an authentication failure as a discard | The turn fails and the prompt is not accepted; a retry before re-authentication fails the same way |

### Suggested Approach

1. Build the candidate set from the durable session store of each host. Select top-level sessions unless the directive includes delegated sessions. Use a recent-activity window, not a creation-time window.
2. Apply the end condition to the last user message only. Exclude the orchestrator session. Record the excluded identifiers and the reason.
3. Probe one target for each host. Send a real continuation prompt to one session, then confirm the result in that session's store before you continue.
4. Send with the durable path for each host. These path types are known to work:
   - a local server prompt endpoint that durably admits the input and schedules agent-loop execution;
   - a queue command that stores the message and resumes the thread;
   - a background resume command that returns immediately and starts the session as a background agent.
   Do not use an interactive attach, resume picker, or terminal UI for a batch.
5. Check the running state before you resume a session. A resume of a session that is still running starts a copy with a new session identifier. If a copy starts, record the original-to-copy mapping, treat the copy as the resumed worker, and prevent the original and the copy from writing the same files.
6. Confirm delivery for each target in the durable session store. The prompt must be the latest user message, and a new turn must start. A send command exit status, a printed acknowledgement, or a queue entry alone is not evidence that the agent started work.
7. Classify the store state after the send: running, completed turn, failed or blocked, or prompt absent. Report the count for each class and each host.
8. On an authentication failure, the prompt is discarded, not queued. Restore the authentication first, then resend. Do not retry the batch before the authentication is restored.
9. Keep the exact failed identifiers and timestamps. A batch can overlap an external configuration change; the timestamps and identifiers let you retry only the failed targets.
10. Do not change another tool's configuration to repair an authentication failure. Report the failure and the exact recovery step for the owner.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Trusted the send command result as proof of delivery | The command exit status showed that the host admitted or queued the input; it did not show that a turn started | Read the durable session store and confirm the latest user message and the new turn |
| 2 | Retried sessions after a login failure | The failed turn had a login or time-limit error, and the host had discarded the prompt | Re-authenticate first, then resend |
| 3 | Resumed every target without a running-state check | Sessions that were still running started copies with new identifiers, which created two workers for one task | Check running state first; bind the copy as the worker and record the mapping |

## Results & Parameters

### Configuration

```yaml
batch_rules:
  end_condition: last_user_message_only
  orchestrator_excluded: true
  probe_targets_per_host: 1
  delivery_source_of_truth: durable_session_store
  required_evidence: latest_user_message_and_new_turn
  state_classes: [running, completed, auth_discard, prompt_absent]
  running_session_resume: forks_copy
```

### Expected Output

A per-host table with the candidate count, the delivered count, and the count for each state class. Then a list of failed identifiers with the failure class and the exact recovery step. A successful batch has a store record for every target, not only a successful send command.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Session batch | 73 top-level sessions in a 24-hour window across three agent hosts | 65 accepted and proved; 8 discarded by authentication expiry. See [notes](agent-session-broadcast-delivery-verification.notes.md). |

## References

- [Parallel Agent Swarm Dispatch Patterns](parallel-agent-swarm-dispatch-patterns.md)
- [Agent Background Task Failure Recovery](agent-background-task-failure-recovery.md)