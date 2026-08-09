---
name: architecture-worker-pool-bounded-completion-recovery
description: "Use when: (1) bounding a staged worker-pool pipeline whose stage queues and completion queue can grow without limit, (2) a worker must publish a completion without blocking even when the coordinator is stalled, (3) rejected queue work must remain durably recoverable and observable with metrics disabled, (4) replacing queue wake sentinels with capacity-neutral signalling, or (5) designing saturation alerts that distinguish a full backlog from an actual rejected enqueue."
category: architecture
date: 2026-07-24
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - worker-pool
  - pipeline
  - bounded-queue
  - completion-queue
  - backpressure
  - saturation
  - durable-recovery
  - graceful-shutdown
  - observability
---

# Worker-Pool Pipelines: Bounded Completion Recovery

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Objective** | Bound every stage and worker-completion queue by the worker window while keeping rejected work recoverable, observable, and shutdown-safe. |
| **Outcome** | Proposed architecture and test contract captured from a ProjectHephaestus pipeline change request. No implementation or pipeline test has been run. |
| **Verification** | `unverified` — validate the implementation's fault paths and restart recovery before promoting this workflow. |

## When to Use

- A coordinator has stage queues plus a worker-completion queue, and any of them is unbounded or uses an unbounded overflow deque.
- Workers may finish faster than the coordinator consumes results, so a completion callback must never block on `put()`.
- The service must preserve restart authority in a durable journal/ledger instead of treating an in-memory overflow structure as recovery state.
- Signal/shutdown handling currently inserts a wake sentinel into the same bounded completion queue as worker results.
- Operators need to distinguish a queue that is merely full from a queue that actually rejected an enqueue or completion publication.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a design hypothesis until the implementation and fault-path tests pass.

## Verified Workflow

> **Warning:** This heading is retained for marketplace validation. The workflow below is proposed, not verified.

### Quick Reference

```python
# One capacity governs all in-memory work ownership.
C = max(1, config.parallel_repos * config.max_workers)

stage_queues = {stage: StageQueue(capacity=C) for stage in StageName}
completion_q = CompletionQueue(capacity=C)

def admit(item: WorkItem) -> bool:
    return (
        len(in_flight) < C
        and inflight_per_repo[item.repo] < max(1, config.max_workers)
    )

# A worker never blocks in its completion callback.
if not completion_q.offer((handle, result)):
    shutdown.set()  # coordinator still owns terminalization
```

### Detailed Steps

1. **Derive one explicit work window.** Let `C = max(1, parallel_repos * max_workers)`, using the same expression as the worker-pool size. Construct every stage queue and the result queue with capacity `C`; reject invalid capacities below one. Global admission must guarantee `len(in_flight) < C` before submitting work. Per-repository admission remains a separate cap.

   This gives the completion proof: each admitted, non-cancelled handle produces at most one result, so at most `C` normal completions can be waiting. Do not rely on eventual coordinator progress to justify the bound.

2. **Make stage enqueue transactional.** `StageQueue.push(item)` returns `False` rather than silently evicting or retaining overflow. On a failed push, record saturation immediately. Only after the first successful enqueue should the coordinator mark the item seen, add it to the item list, initialize entry metadata, or increment seed/pass bookkeeping. For an already tracked item, set its intended stage and park it resumable; reject a new seed rather than retaining it in another in-memory deque.

3. **Give completion publication a bounded, non-blocking failure path.** A `CompletionQueue(capacity=C)` should use `put_nowait()` for ordinary `(handle, result)` entries. If full, retain the exact pair in a separate bounded rejection mailbox of capacity `C` and return `False`; a worker merely logs and sets the shared shutdown request. The worker must not mutate coordinator-owned `in_flight`, park work, or discard the rejected handle.

   If the rejection mailbox is also full, atomically set an overflow marker. It is a catastrophe signal, not a place to retain another result. The coordinator can then terminalize every remaining in-flight item rather than waiting forever for a completion it can no longer observe.

4. **Keep wake signals out of the completion capacity.** Use an out-of-band `threading.Event` or equivalent binary latch for signal wakes. Repeated requests coalesce: setting the latch twice does not consume two result slots. Clear/process the latch in the coordinator's wait loop without inserting a fake handle into the completion queue.

5. **Drain completion rejections before ordinary results.** At each coordinator tick, retrieve `(rejections, mailbox_overflowed)` before consuming normal completions. For every rejection, remove that exact handle from `in_flight`, release its per-repository accounting, record a saturation event, and park that item resumable in the durable recovery model. Then begin a grace-bounded shutdown.

   If the mailbox overflow marker is set, record a fatal saturation event and immediately park all remaining in-flight items. Do not wait for the normal grace period: a lost completion must not orphan a handle or prevent process termination.

6. **Make the durable journal the restart authority.** A rejection must not depend on an overflow deque or metrics scrape for recovery. Record `queue_saturated` directly through the coordinator's JSONL/event-log path even when the metrics endpoint is disabled. Mark already tracked work resumable at its intended stage, so a fresh coordinator can reconstruct it from the unchanged durable GitHub journal or equivalent external ledger.

7. **Separate backlog alerts from rejection alerts.** Keep the compatibility alert name `queue_depth_exceeds`, but evaluate it against capacity:

   ```python
   depth * 100 >= capacity * queue_depth_threshold
   ```

   Treat `queue_depth_threshold` as a percentage in `[0, 100]`; default `100` means a non-empty queue alerts when full, not when it has already rejected work. Emit a separate critical `queue_saturated` alert only when `saturated_queues` contains an actual rejected stage or completion enqueue. Export capacities, depths, monotonic rejection totals, and this tick's saturated queues in the observability snapshot.

8. **Give every external shutdown a deadline.** A signal handler and any other caller that requests shutdown must set or preserve a grace deadline and set the coalesced wake latch. Preserve first-signal graceful and second-signal immediate semantics, but do not let a non-signal shutdown enter an unbounded wait.

9. **Test normal and fault capacity paths deterministically.** Start with contract tests for `C`, invalid capacities, FIFO behavior, global admission, checked reinsertions, and no overflow deque. Fill `C` completion-result slots while requesting concurrent wakes repeatedly; the result depth must remain `C`. Force a normal completion rejection and assert the coordinator removes the exact handle, parks that item resumable, writes JSONL `queue_saturated` with metrics disabled, shuts the pool down, and returns without waiting for grace expiry. Then force rejection-mailbox overflow and assert every live handle is parked. Finally seed a fresh coordinator from the unchanged durable journal and prove recovery.

### Acceptance Commands

```bash
cd <project-root>

# Capacity, admission, wake coalescing, and bounded queue contracts
uv run pytest <pipeline-test-dir>/test_queues.py <pipeline-test-dir>/test_backpressure.py \
  -k 'capacity or admission or bounded or wake' -v

# Completion rejection, fatal mailbox overflow, and termination
uv run pytest <pipeline-test-dir>/test_backpressure.py <pipeline-test-dir>/test_worker_pool.py \
  <pipeline-test-dir>/test_coordinator_shutdown.py \
  -k 'saturation or rejection or overflow or durable or termination' -v

# Backlog and saturation must be independently observable
uv run pytest <observability-test-dir>/test_alerts.py <pipeline-test-dir>/test_coordinator.py \
  -k 'backlog or saturation or observability' -v
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Queue wake sentinel | Insert a synthetic wake handle into the bounded result queue. | A wake occupies a completion slot, invalidating the `C`-result bound and permitting the `C + 1` failure case. | Use a coalesced out-of-band binary latch for wakes. |
| Unbounded overflow deque | Keep rejected stage items in a coordinator-owned overflow deque. | It hides pressure, reintroduces unbounded memory, and makes volatile state an accidental recovery authority. | Reject new seeds; park already tracked work resumable using the durable journal/ledger. |
| Worker-only shutdown | Have a rejected worker callback set shutdown and leave the coordinator to drain normal results. | The coordinator can retain the exact rejected handle in `in_flight` and wait until grace expiry for a result it never received. | Retain the rejected `(handle, result)` in a bounded mailbox and drain it before normal completions. |
| Metrics-only saturation | Emit saturation solely through optional metrics/alerts. | With metrics disabled, operators and restart tooling lose the only record of rejected work. | Write `queue_saturated` directly through the durable JSONL/event-log path. |
| Absolute depth threshold | Compare raw queue depth with a fixed threshold while capacities vary. | "Full" becomes unreachable or inconsistent across deployments. | Evaluate backlog as a percentage of measured queue capacity and reserve saturation for actual rejection. |

## Results & Parameters

### Capacity and ownership invariants

| Invariant | Required rule |
|-----------|---------------|
| Work window | `C = max(1, parallel_repos * max_workers)` |
| Stage queue capacity | Every stage queue has capacity `C`. |
| Completion capacity | Normal completion queue has capacity `C`; global admission keeps in-flight handles below `C`. |
| Rejection mailbox capacity | Separate mailbox has capacity `C`; its overflow marker triggers immediate terminalization of all live work. |
| Wake capacity | Coalesced binary latch is outside the result queue and consumes no completion capacity. |
| Worker ownership | Worker reports rejection and requests shutdown only; coordinator removes handles, releases accounting, and parks work. |
| Recovery authority | Durable journal/ledger remains authoritative; in-memory queues and metrics are never recovery state. |

### Expected observability signals

```json
{
  "queue_capacities": {"planning": 4, "completion": 4},
  "queue_depths": {"planning": 4, "completion": 0},
  "rejection_totals": {"planning": 1, "completion": 0},
  "saturated_queues": ["planning"]
}
```

- `queue_depth_exceeds`: backlog warning at the configured percentage of capacity; default `100` fires at full capacity.
- `queue_saturated`: critical event only after an enqueue or completion publication is rejected.
- A JSONL `queue_saturated` record is mandatory even when `metrics_port=0` or equivalent metrics export is disabled.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Proposed queue-backpressure and completion-recovery change | Design request only; implementation and acceptance tests remain pending. |
