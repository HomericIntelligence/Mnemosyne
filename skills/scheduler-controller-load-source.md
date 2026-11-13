---
name: scheduler-controller-load-source
description: "Find which caller loads a batch-scheduler controller (Slurm-like) before you propose a fix. Use when someone asks where controller calls come from, or proposes caching before the call rate per caller is known."
category: tooling
date: 2026-11-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [slurm, scheduler, controller, rpc, load, diagnosis, sdiag, proc-sampling]
---

# Find the Source of Scheduler Controller Load

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-13 |
| **Objective** | Name the callers that load the scheduler controller, with rates and times, before you change any caller. |
| **Outcome** | Operational. One diagnosis showed that the since-reset average hid an earlier burst. |

## When to Use

- Someone asks where controller calls come from.
- Someone proposes caching or rate limits for scheduler queries before the call rate per caller is known.
- Controller counters show high load, and you cannot tell if the load is current.

## Verified Workflow

### Quick Reference

```bash
# 1. Per-user RPC counters: read twice, then subtract
sdiag --all > a.txt; sleep 60; sdiag --all > b.txt     # compare the per-user sections
# 2. Short-lived clients: sample /proc at a high rate for a short window on each node
# 3. Read the code for loops that call the scheduler
# 4. Bounded read-only logger: each minute, record counter delta + job count
```

### Suggested Approach

1. Read the controller's per-user RPC counters twice. Use the delta divided by the interval.
   The average since the counter reset can hide an earlier burst: one measured average was
   about 30 times the current rate.
2. Sample new client processes from `/proc` at a high rate (tens of samples per second) for a
   short window on each node. A process list at 0.5 s steps misses short-lived clients.
3. Read the code for loops that call the scheduler (polling loops, per-item status calls,
   retry loops) before you blame a component.
4. Run a bounded, read-only logger. Each minute it records the counter delta and the job
   count, with a time stamp, so you can match a burst to a time. Give it an end time.
5. Choose the fix (cache, batch, slow a poll) only after you know the rate per caller.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Cache first | Proposed caching of scheduler queries | The call rate per caller was not known; the cache could target the wrong caller | Measure rate per caller first |
| Since-reset average | Read the counters once | The average hid an earlier burst (about 30 times the current rate) | Use the delta between two reads |
| Process list at 0.5 s | Looked for the client with `ps` | Short-lived clients start and end between samples | Sample `/proc` at a high rate |

## Results & Parameters

### Configuration

```yaml
counter_read: "twice; delta / interval"
proc_sampling: "high rate, short window, every node"
logger: {mode: read-only, interval: 1m, fields: [counter_delta, job_count], bounded: true}
```

### Expected Output

- A table of callers with calls per minute from the delta, and a time for each burst.
- A list of code paths that call the scheduler in a loop.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed compute cluster | Controller load diagnosis, 2026-11 | Delta read, `/proc` sampling and a minute logger found the caller before any cache change. |

## References

- [slurm-job-content-attribution](slurm-job-content-attribution.md) - identify what a live job runs.
