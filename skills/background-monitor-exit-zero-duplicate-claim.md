---
name: background-monitor-exit-zero-duplicate-claim
description: "Decide whether a background monitor or periodic refresher task that ended with exit 0 and no output is a benign duplicate instance or a real outage. Use when the same refresher can start more than once and completion notifications report a silent exit."
category: tooling
date: 2026-11-26
version: "1.0.0"
user-invocable: false
tags:
  - monitor
  - background-task
  - exclusive-claim
  - singleton
  - periodic-refresher
  - silent-exit
  - duplicate-instance
  - liveness
  - stale-artifact
---

# Background Monitor Exit 0 — Duplicate Instance or Outage

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-26 |
| **Objective** | Decide whether a monitor task that completed with exit 0 and no output is a benign duplicate that lost an exclusive claim, or evidence that the refresher is down. |
| **Outcome** | Operational — a silent exit-0 completion was a duplicate instance. The claim holder was alive and the refresh artifact was current, so no relaunch was needed. |

## When to Use

- A supervisor or agent harness reports that a background monitor or periodic refresher task completed with exit 0 and produced no output.
- The same refresher was started more than once, for example by repeated launches or a restart during a session.
- Several instances write one output artifact on a fixed interval.
- You must decide whether to treat the silent completion as a failure and start a replacement.

## Verified Workflow

### Quick Reference

```text
An exit-0 completion with no output is benign only when both checks pass:
  1. a claim holder process is alive, and
  2. the refresh artifact is newer than one interval.
If either check fails, start exactly one instance.
```

### Suggested Approach

1. **Do not treat exit 0 as success or as failure by itself.** The process exited cleanly. The exit code says nothing about whether the refresher still runs in another instance.
2. **Find the claim.** Look for the claim record that names the active instance, for example a claim file that holds a process identifier or a generation value. Read it. Do not guess.
3. **Confirm that the claim holder is alive.** Check that the recorded process exists and runs the refresher command. A claim record with a dead process is an outage, not a duplicate.
4. **Confirm that the artifact is fresh.** Compare the artifact or cache timestamp with the expected interval. A fresh artifact shows that the claim holder does the work.
5. **Read the completion as benign only when both checks pass.** Keep the claim holder. Do not start another instance. Record why the silent exit was benign.
6. **Start exactly one instance when either check fails.** Use the same claim mechanism, so the new instance takes the free claim or confirms a live holder.
7. **Prevent duplicates at the source.** Make the refresher take an exclusive claim before it starts work: an exclusive create, an atomic replace, or a generation check. Do not use a file lock on shared storage. An instance that cannot take the claim exits 0 without output.
8. **Log the claim outcome.** Write one line for each result: started, claim held by another instance and exit, stopped. A later silent completion then has a matching log entry.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treating exit 0 with no output as success | Assumed the refresher was healthy because the task exited 0 | Exit 0 shows only that one process ended. The data is stale when no claim holder is alive | Check the claim holder and the artifact freshness, not the exit code |
| Restarting on every silent completion | Started a new refresher when the monitor task ended | The claim holder was still running. Each restart added duplicate instances and log noise | Verify the claim and the artifact before any restart |
| Reading a stale claim record as live | Trusted the claim file without a process check | A claim record can outlive its process. The refresher was down | Require a live process for the recorded claim holder |
| Using a blocking file lock on shared storage | Protected the singleton with a file lock | A file lock on shared storage can wait without a limit | Use an exclusive create, an atomic replace, or a generation check |

## Results & Parameters

### Configuration

```yaml
refresher_singleton:
  claim: exclusive-create-or-generation-check
  duplicate_behavior: exit-zero-with-no-output
  log_events: [started, claim-held-exit, stopped]
  interval_artifact: timestamped-cache-or-record
benign_exit_test:
  require: [claim-holder-alive, artifact-newer-than-interval]
  on_failure: start-exactly-one-instance
```

### Expected Output

- One live claim holder for the refresher.
- A refresh artifact newer than one interval.
- One log line per claim outcome, so a silent exit has a matching cause.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Per-user agent CLI plugin | A periodic model-picker refresher ran as a watched background task. Several instances started within minutes, and one held the exclusive claim. A completion notification reported exit 0 with no output. The claim holder was alive and the cache was current, so the completed task was a duplicate. | See [notes](background-monitor-exit-zero-duplicate-claim.notes.md). |

## References

- [Background agent failure detection and recovery](agent-background-task-failure-recovery.md) — a completion status alone does not prove success
- [Give every service one supervision owner](service-supervision-ownership-parity.md) — start, restart, and liveness ownership