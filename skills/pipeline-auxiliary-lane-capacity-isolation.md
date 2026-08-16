---
name: pipeline-auxiliary-lane-capacity-isolation
license: BSD-3-Clause
description: "Use when: (1) a queue pipeline moves slow optional or terminal work into a new stage but it still stalls primary work, (2) one global permit spans every queue, (3) a single worker pool lets post-processing consume primary capacity, or (4) cleanup must wait for asynchronous post-processing without leaking resources."
category: architecture
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [pipeline, queue, concurrency, worker-pool, capacity, backpressure, cleanup, post-processing]
---

# Pipeline Auxiliary-Lane Capacity Isolation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Prevent slow terminal or optional work from consuming the worker and permit capacity reserved for primary pipeline stages. |
| **Outcome** | A source-verified design rule, state model, and concurrency test pattern for an independently bounded auxiliary lane with a cleanup barrier. |
| **Verification** | verified-local by tracing a bounded queue pipeline whose stage queues shared one worker pool and whose global permit was released only after terminal cleanup. |

## When to Use

- A long-running learning, reporting, indexing, notification, or artifact-publication step delays unrelated primary work.
- A proposed fix adds a queue or stage but leaves the new work on the same executor.
- One global live-item permit remains held while an item waits in the auxiliary stage.
- A one-worker configuration must continue primary work while post-processing is still running.
- Branch, worktree, lease, or temporary-resource cleanup must happen only after post-processing reaches a terminal outcome.
- The auxiliary backlog must remain bounded and restart-safe.

## Verified Workflow

### Quick Reference

```text
Primary lane (C workers / C permits):
intake -> plan -> execute -> verify -> terminal handoff

Auxiliary lane (L workers / B permits):
post-process -> cleanup -> release auxiliary permit

Atomic handoff:
reserve auxiliary slot -> publish compact record -> release primary permit
```

The load-bearing rule is:

> A separate queue is not a separate concurrency lane unless it has independent
> worker capacity and independent live-work accounting.

### Detailed Steps

1. **Trace every capacity boundary before changing the stage graph.** Identify:
   the executor that runs each job, the permit held by each live item, queue
   capacity, completion-channel capacity, and the exact permit-release point.
   If the new stage shares any primary bottleneck, it can still stall primary
   work.

2. **Represent post-processing as an immutable compact record.** Copy only the
   identifiers, result, cleanup lease, and bounded context that the auxiliary
   work needs. Do not retain large diffs, logs, or mutable primary-stage state
   in a long-lived backlog.

3. **Create independently bounded capacity.** Give the auxiliary lane its own:
   worker count, queue/backlog limit, live-work permits, in-flight accounting,
   metrics, and shutdown ownership. A shared completion channel is acceptable
   only when its capacity is at least the maximum combined in-flight count and
   every completion retains its owning-lane identity.

4. **Transfer ownership destination-first.** Reserve an auxiliary slot and
   publish the compact record before releasing the primary permit. If the
   destination is full, retain exactly one bounded handoff intent on the source
   lease and apply backpressure. Never use an unbounded spill list.

5. **Keep producer stages non-blocking.** A producer records a deterministic
   post-processing intent and continues or terminates its primary work. Only the
   auxiliary stage submits the slow job.

6. **Make auxiliary work idempotent and restartable.** Key each intent from
   immutable source facts. Persist or reconstruct `pending`, `claimed`, and
   terminal `succeeded`/`failed` state. On restart, rebuild unfinished auxiliary
   work instead of replaying terminal side effects.

7. **Put cleanup behind a terminal barrier.** Cleanup begins only when every
   required auxiliary intent is terminal. Terminal includes bounded retry
   exhaustion: an optional post-processing outage must not retain resources
   forever. Record the auxiliary failure separately from the already-final
   primary business result.

8. **Prove concurrency with a real barrier test.** Run one primary worker and
   one auxiliary worker. Block the auxiliary job on an event, submit a second
   primary item, and assert that its primary job starts before the event is
   released. Also assert distinct worker identities. Sequential logs or an
   inline fake executor do not prove isolation.

9. **Test saturation and shutdown.** Fill the auxiliary backlog, prove bounded
   backpressure without item loss, then verify graceful and immediate shutdown
   preserve both lanes as resumable. Idle detection must include every queue,
   executor, timer, retained handoff, and cleanup operation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Add one more stage queue | Slow work moved to a new queue while using the original executor and permit. | A queue changes ordering, not execution capacity; a one-worker run still serialized behind the slow job. | Isolate both worker capacity and live-work permits. |
| Increase only the shared executor size | Extra threads were added without reserving capacity by lane. | Auxiliary jobs could occupy every thread during a burst, starving primary work. | Independent concurrency needs a dedicated pool or enforceable lane reservation. |
| Release the primary permit before destination admission | The item was removed from primary accounting before its auxiliary record was accepted. | A full destination or crash could lose ownership and cleanup state. | Reserve destination first, then release source ownership atomically. |
| Wait forever for successful post-processing | Cleanup required success rather than a terminal outcome. | A persistent provider failure leaked worktrees, leases, or temporary resources. | Bound retries, record failure separately, and release the cleanup barrier on terminal exhaustion. |
| Assert concurrency from logs | Tests inspected two completion records from a fake or shared worker. | Sequential execution can produce similar logs and fake executors do not exercise scheduling. | Use real workers plus a barrier/event and assert primary progress while auxiliary work is blocked. |

## Results & Parameters

### Configuration

```yaml
primary_workers: C
auxiliary_workers: L
auxiliary_queue_capacity: B
completion_capacity: ">= C + L"
post_processing_retry_limit: bounded
```

Choose `L >= 1`. Choose a finite `B` from the acceptable retained-record memory
budget and expected arrival/service rates; do not infer it from the number of
stage names. When `B` fills, destination-first backpressure is the correct
behavior.

### Expected Output

- A blocked auxiliary job occupies only an auxiliary worker.
- At least one unrelated primary job starts while that auxiliary job remains blocked.
- Main and auxiliary queue depth and in-flight counts are independently visible.
- No cleanup job begins before all required intents are terminal.
- Cleanup runs after success and bounded failure.
- No live item disappears during saturation, restart, or shutdown.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Generic bounded queue pipeline | Source-level architecture analysis | Verified the failure mechanism by tracing shared executor ownership, global permit lifetime, terminal cleanup ordering, and the one-worker scheduling consequence. Implementation validation remains a required follow-up for each adopting pipeline. |

## References

- [Terminal versus retry routing budgets](pipeline-routing-budget-terminal-vs-retry-paths.md)
