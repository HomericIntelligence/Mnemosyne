---
name: shared-pending-cap-starves-guaranteed-tier
license: BSD-3-Clause
description: "Keep a guaranteed capacity floor from waiting behind a shared pending-submission cap. Use when: (1) a reconciler or autoscaler limits unready or pending submissions with one budget, (2) a pool has a guaranteed tier and an elastic or low-priority tier, (3) a pool is below its floor but no guaranteed job is submitted, or (4) one pending low-priority job is the only job in the queue."
category: architecture
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags: [scheduler, reconciler, autoscaling, floor, pending-cap, starvation, priority-tiers, capacity]
---

# Shared Pending Cap Starves the Guaranteed Tier

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Make a guaranteed replica floor launch at once, even when elastic work is pending. |
| **Outcome** | Operational. The floor deficit was counted apart from the shared pending budget, and a behavior test covered it. |

## When to Use

- A reconcile loop computes `available = max_pending - unready_in_flight`, and the count of
  unready work includes every tier.
- A pool has a guaranteed floor (high-priority jobs) and an elastic part (low-priority or
  preemptible jobs).
- The pool is below its floor, the queue holds only a pending elastic job, and the loop submits
  nothing. A manual submit of the guaranteed job starts in about one minute.
- An operator raised the desired count and nothing changed after the loop ran again.

## Verified Workflow

### Quick Reference

Two budgets, not one:

```text
guaranteed_missing = floor - guaranteed_held      # not capped by the pending budget
elastic_new        = min(elastic_missing, max_pending - elastic_pending)
```

`guaranteed_held` counts live guaranteed jobs plus accepted guaranteed submissions that the
scheduler does not list yet. This stops a duplicate submit.

### Suggested Approach

1. Find the symptom in the loop first. Compare the queue (a pending low-priority job only) with
   the desired count. Do not suspect a node, quota, or circuit-breaker limit before you read the
   arithmetic of the pending budget.
2. Count the guaranteed deficit from guaranteed holdings only. Elastic or low-priority work must
   not reduce it. A preemptible job is not capacity that the pool can rely on.
3. Apply the pending cap to the elastic part only. Keep the cap there to avoid a flood of
   low-priority submits.
4. Include accepted but not yet listed guaranteed submissions in `guaranteed_held`. A scheduler
   lists a new job after a delay. Without this term the loop submits again each pass.
5. Use the same count at every site that reports or gates on the floor deficit (for example a
   "blocked" report). Search for the old term (`len(live)`) and replace it, or the old and new
   counts disagree.
6. Test the contract: a floor of 1, one pending elastic job, no guaranteed job. Expect one
   guaranteed submit. Add two more cases: no second submit on the next pass, and no submit when
   an accepted guaranteed submission is hidden from the queue. Confirm that the first test fails
   without the fix.
7. Leave the floors, the account node limit, and the breaker alone. The failure backoff of a
   tracked attempt is a separate gate and stays.

If you must bring the pool up before the fix is released, submit the guaranteed job by hand with
the same script, the guaranteed partition, and a node that already hosts the pool. The scheduler
preempts the low-priority job that holds the GPUs.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Set the desired count | Ask the control service to start the pool with one replica. | The count was already satisfied in the loop's view. The pending elastic job used the single pending slot, so no guaranteed submit happened. | A desired-count change does not bypass a shared cap. Read the cap arithmetic. |
| Blame the account node limit | The account was at its node limit, so room looked like the cause. | A guaranteed job preempts lower tiers and starts at once. The limit was not the gate. | Test by a manual guaranteed submit before you conclude that room is missing. |

## Results & Parameters

### Configuration

```text
max_pending                = 1   # default pending budget; applies to the elastic part only
guaranteed_held            = live_guaranteed + accepted_not_yet_listed_guaranteed
guaranteed_submit_count    = max(0, floor - guaranteed_held)
```

### Expected Output

- A pool below its floor gets guaranteed submits on the next pass, with a pending elastic job
  in the queue.
- No duplicate submit on the following pass.
- Elastic submits stay capped by the remaining pending budget.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private inference-serving control plane | A model pool stayed below its floor after a replica failure. | Fix and behavior test merged into the reconciler. |

## References

- [Pipeline auxiliary lane capacity isolation](pipeline-auxiliary-lane-capacity-isolation.md)
- [Serving-lane zero-floor demotion](serving-lane-zero-floor-demotion.md)
