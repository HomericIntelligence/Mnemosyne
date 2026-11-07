---
name: producer-side-congestion-window
description: "Throttle a queued background producer with a signal-driven congestion window. Use when a producer that holds its own backlog floods a shared gateway, proxy, or scheduler queue, and its per-request retries amplify the overload."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - congestion-control
  - backpressure
  - aimd
  - producer-throttle
  - queue-saturation
  - closed-loop
---

# Producer-Side Congestion Window

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Stop a backlog-holding producer from flooding a shared gateway: gate its dispatch with a signal-driven congestion window instead of a fixed concurrency ceiling and unbounded retries. |
| **Outcome** | Successful: merged, CI green, reviewed twice at exact head with all findings closed. Production deploy/config application is operator work outside this entry. |

## When to Use

- A background producer (batch runner, poller, scheduler worker) holds its own backlog in memory or storage and dispatches at a fixed concurrency ceiling.
- Downstream congestion signals exist — a dedicated queue-full or queue-timeout code, 429, 5xx, transport faults — but the producer retries each retryable signal per request with no bound on the accumulated wait, so congestion cannot drain its demand.
- Interactive users see queue-full or worker-unavailable errors while the producer keeps its fixed ceiling busy.
- Parked work (a retry in its backoff sleep, or a request waiting on a server-directed admission grant) must not consume the capacity that non-parked principals need.

## Verified Workflow

### Quick Reference

```python
# One classification per attempt, exactly once, before the retry decision.
signal = classify(outcome)          # QUEUE_FULL | OVERLOAD | NONE

# AIMD window, clamped to [min_window=1, max_window]:
if signal is QUEUE_FULL:            # dedicated queue-full / queue-timeout code
    window = min_window             # the queue is full: stop pushing
elif signal is OVERLOAD:            # 429, 5xx, transport fault
    window = max(min_window, window // 2)
else:                               # completion (not a wait outcome)
    if completed_since_growth >= window:
        window = min(window + 1, max_window)

# At most one decrease per cooldown interval: a burst of 64 answers to one
# stalled gateway collapses the window one time, not 64 times.

# The dispatch gate counts HUNGRY tasks only:
hungry = live_tasks - parked_tasks  # parked = backoff sleep or server-directed wait
dispatch_ok = hungry < capacity     # capacity = min(config.max_inflight, window)
```

### Suggested Approach

List what the window adapts, then wire the mechanics listed below. Order matters
only where a later rule depends on the gate existing.

1. **Keep the backlog with the producer.** Treat the downstream queue as traffic,
   not storage. A producer that already holds its work items needs a throttle on
   the drain rate, not another queue. For the complementary receiver side —
   bounded stage and completion queues inside the service — see
   [architecture-worker-pool-bounded-completion-recovery](architecture-worker-pool-bounded-completion-recovery.md).

2. **Classify each attempt outcome once, against a named signal table.** The
   worthwhile decision is differentiating queue-saturated from overloaded:

   | Outcome | Signal | Window action |
   | ------- | ------ | ------------- |
   | Dedicated queue-full / queue-timeout code | `QUEUE_FULL` | reset to floor |
   | 429, 503, other 5xx, transport unreachable | `OVERLOAD` | halve, floor-bound |
   | Success, or terminal client error | `NONE` | counts one completion |
   | Server-directed wait (Retry-After hint), registration/state poll 404, cancellation | `NONE` | excluded from completions |

   The last row is load-bearing: a wait answer is evidence of saturation, not
   throughput. Counting it as a completion re-grows the window during sustained
   saturation and defeats the closed loop.

3. **Choose AIMD mechanics with a cool-down.** Additive increase of one slot per
   completed window of successes, up to the old fixed ceiling. Multiplicative
   decrease on congestion, at most once per cool-down interval (a few seconds),
   because N in-flight requests can report overload in the same instant.
   The floor is one dispatch, never zero: zero deadlocks throughput.
   RFC 5681 documents the substrate this pattern adapts.

4. **Gate hungry tasks, not live tasks.** A task is parked while it sleeps its
   backoff or waits on a server-directed admission grant. Parked tasks hold no
   execution slot; counting them in the gate lets one parked task monopolize the
   producer's whole budget and starve other principals. The gate therefore uses
   `live - parked`, and real execution stays bounded by the slot accounting
   beneath it.

5. **Keep ticket accounting symmetric by construction.** Raise exactly one
   dispatch ticket per task at creation. Release exactly once, unconditionally,
   in the task's exit path (first statement, before any `await`). Never release
   at a mid-life handoff such as slot acquisition: releasing there leaks one
   ticket per success and permanently closes the gate within N requests.
   The observable invariant — the ticket counter returns to zero at idle — is
   the test to write.

6. **Bound every wait with one global budget.** Retry backoff sleeps and
   capacity waits behind the window charge the same accumulated-wait budget for
   one request. Charge at the wait site, not in the backoff scheduler, because a
   server-directed wait carries its own duration hint and returns before the
   scheduler's budget check. On exhaustion, land a terminal outcome instead of
   parking forever. Keep `0`/unset as an explicit unbounded escape hatch.

7. **Gate credit holders too when admission is server-mediated.** If the
   deployment issues capacity credits or tokens, the window must still gate
   credit holders before they occupy an execution slot. Otherwise the whole
   throttle is silently disabled in exactly the deployment mode that has the
   strongest admission path — in practice, the production one.

8. **Treat server-side defenses as depth, not substitute.** Priority classes,
   per-tenant queue caps, and credits complement this pattern. A server queue
   can only reject, and rejections become user-visible errors; a producer-side
   window reduces pressure silently before any user sees one.

9. **Test behaviors, not wiring.** Window transition per signal class; one
   decrease per cool-down burst; the parked-task starvation regression; terminal
   outcome on an exhausted wait budget; the ticket counter at zero at idle;
   recovery back to the ceiling at the next dispatch cycle.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Fixed ceiling with unbounded retries | Keep the historical `max_inflight` and per-request backoff. | Retries re-dispatch into the same flood; congestion cannot drain demand. | Retry policy alone is not congestion control; the dispatch rate itself must close the loop. |
| Gate on live tasks including parked waiters | Lower the same counter whether a task executes or parks. | A parked (credit/backoff-waiting) task monopolized the budget; fairness tests that pin non-monopolization regressed. | Count hungry tasks (live minus parked); parked work must hold no place in the window. |
| Release the dispatch ticket at slot acquisition | Clear the ticket where the task takes its engine slot. | One ticket leaked per success; the gate closed permanently after `max_inflight` requests. | One raise at creation, one unconditional release in the exit path, before any await. |
| Count wait answers as completions | Treat server-directed waits and registration polls like successes. | The window re-grew during a sustained flood. | Waits are neutral and excluded from increase completions. |
| Budget only backoff sleeps | Charge accumulated waits only on retry sleeps. | A request behind a halved window parked without a bound while finalization waited on it. | One wait budget covers all wait sites, with a terminal outcome on exhaustion. |

## Results & Parameters

### Configuration

```yaml
congestion_window:          # enable/disable; default on
  min_window: 1             # dispatch floor, never 0
  decrease_cooldown_s: 5.0  # at most one decrease per interval
wait_budget_s: 3600         # accumulated retry + capacity wait per request; 0 = unbounded
ceiling:                    # the pre-existing fixed concurrency cap; unchanged meaning
```

Recommended telemetry: current window, cumulative decreases, cumulative floor
hits. Low-cardinality gauges only.

### Expected Output

- Interactive users stop seeing queue-full errors during batch floods; the
  producer's pressure drops before any user-visible rejection.
- Batch throughput recovers to the ceiling automatically: each window of
  completions adds one dispatch slot, so recovery takes `sum(1..max_window)`
  completions from the floor.
- Telemetry shows the window tracking saturation events instead of a flat line.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An inference-gateway batch runner | Merged feature PR, green CI, two exact-head GO reviews, one major finding (credit-mode gate) closed by design | Safe evidence in [producer-side-congestion-window.notes.md](producer-side-congestion-window.notes.md). |

## References

- [RFC 5681: TCP Congestion Control](https://www.rfc-editor.org/rfc/rfc5681) — the public AIMD substrate this pattern adapts.
- [architecture-worker-pool-bounded-completion-recovery](architecture-worker-pool-bounded-completion-recovery.md) — the complementary receiver side: bounded queues inside the service.
- [planning-bounded-queue-eviction-durability-ordering](planning-bounded-queue-eviction-durability-ordering.md) — bounded-collection eviction and failure-shape decisions.
