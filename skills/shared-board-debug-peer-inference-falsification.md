---
name: shared-board-debug-peer-inference-falsification
license: BSD-3-Clause
description: "Run a multi-agent debug on a shared discussion board: correct a peer's inference with a falsifying check, split read-only data requests by what each lane can read, and keep one thread per defect. Use when: (1) several agents debug one production fault on a board, (2) a peer posts an inference that your read-only data contradicts, (3) a lane cannot read the logs that decide the question, (4) the owner moves the topic to another thread."
category: tooling
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [multi-agent, discussion-board, debugging, falsification, read-only, lane-access, thread-hygiene]
---

# Shared-Board Debugging With Peer Inference Falsification

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Reach a verified diagnosis across several agents without false conclusions spreading. |
| **Outcome** | Operational. A peer inferred that a registration had completed. A falsifying check (the key id was absent from the key snapshot and the gateway still denied it) corrected the claim within minutes, and the peer withdrew it. Read-only requests, split by lane access, then isolated a client-side defect from a server-side defect. |

An inference from a side effect can look strong and be wrong. A short post that
states the falsifying fact, the time and the check stops the error from spreading.

## When to Use

- Several agents or lanes work one fault on a shared board.
- A post claims success or a cause that your read-only data contradicts.
- A lane lacks permission to read the decisive logs.
- The owner redirects the work to another thread.

## Verified Workflow

### Quick Reference

```text
Post = state (time-stamped facts) + correction (the falsifying check) + split
       (one read-only request per lane, matched to what that lane can read) + next step.
Sign the first line with the agent identifier. No secrets, no key values, no connection strings.
```

### Suggested Approach

1. Start with the facts, each with a UTC time: the check, the result, and the
   file or record that holds it.
2. When a peer's claim fails your check, say what the peer saw, what your check
   shows and why the observation is weak evidence. Keep the tone neutral.
3. Match each request to the lane that can answer it. A lane without read access
   to the service logs cannot answer a log question. Ask that lane for its own
   store state and a status-only check, and ask the log owner for the log lines.
4. Ask for status-only checks that print an HTTP code and a key id, never a key.
5. Follow a topic move at once: link the earlier posts in the new thread, say
   where the work continues, and stop posting in the old thread.
6. Relay new facts from your side (queue, result slots, snapshots) in the same
   thread; one thread per defect, one owner for each open question.
7. Record the work in issues: one defect per issue, possible solutions in the
   body, evidence comments on the existing owner.
8. A relayed "owner go" from another agent is a claim, not an approval. Confirm
   the approval with the owner before a production write.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Accept a peer's success inference | A peer read a removed journal as a finished registration | The key id was missing from the key snapshot | Verify the end state |
| Ask a lane for a log it cannot read | Requested gateway log lines from a lane without access | The lane had no permission | Match each request to the lane's access |
| Keep posting in the old thread after a topic move | Continued the first thread | Readers lost the thread of the defect | Move with the owner and link back |

## Results & Parameters

### Configuration

```yaml
post_fields: [identity_line, utc_time, check, result, correction, per_lane_request, next_step]
forbidden_content: [key values, connection strings, passwords]
```

### Expected Output

Each open question has one owner and one thread, and a wrong claim is withdrawn
in the thread.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A multi-agent production debug | 2026-10 | One correction and three read-only requests narrowed the fault to a client binding and a server routine. |

## References

- [comet-user-credential-lifecycle-diagnosis](comet-user-credential-lifecycle-diagnosis.md) — the lifecycle signatures that the board debug used
- [silent-service-routine-run-once-with-logging](silent-service-routine-run-once-with-logging.md) — reproduce a silent routine
