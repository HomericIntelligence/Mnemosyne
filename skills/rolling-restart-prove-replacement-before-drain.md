---
name: rolling-restart-prove-replacement-before-drain
license: BSD-3-Clause
description: "Prove that a replacement unit can be admitted and is healthy before the old unit stops. Use when: (1) you restart or replace replicas, workers, or jobs of a service while a scheduler or quota limit is full or near full, (2) a service has one serving unit, (3) autoscale and a restart both add surplus units, or (4) a replacement stays pending on a quota."
category: architecture
date: 2026-11-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [restart, rolling-replace, quota, scheduler, availability, autoscale, drain]
---

# Rolling Restart: Prove the Replacement Before You Drain

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-13 |
| **Objective** | Restart or replace service units with no loss of serving capacity when a scheduler or quota limit is full. |
| **Outcome** | Operational. A restart ended the last serving unit, the replacement stayed pending on a quota, and the service was down for many hours. |

## When to Use

- You restart or replace the units of a service (replicas, workers, jobs) and the scheduler or quota is at its limit.
- The service has exactly one serving unit.
- Autoscale and a restart can both add surplus units at the same time.
- A replacement unit is pending and not admitted.

## Verified Workflow

### Quick Reference

```text
1. Read quota headroom and job count.  headroom < 1 new unit -> do not start.
2. Submit the replacement FIRST.
3. Wait until the replacement is admitted AND healthy.
4. Only then stop the old unit.
5. Replacement pending on quota -> wait, report "blocked", do not drain.
```

### Suggested Approach

1. Before the restart, count running and pending units and read the quota headroom. A replacement needs one free slot while the old unit still runs (surge first, drain second).
2. A service with one serving unit never restarts unless the replacement is already running and healthy.
3. If the replacement stays pending, the restart waits. It reports the blocked state with the quota evidence. It does not stop the old unit. Cancel the pending replacement if the wait has no end.
4. Define which action wins when autoscale and a restart both want surplus units. Typical rule: the floor service has priority. A restart surge takes the free slot first; autoscale surplus yields (is stopped or not started) when a floor unit has no slot. Write the rule in the supervisor, not in a runbook only.
5. After the swap, check that the old unit is gone and that the unit count is back to its target.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Stop first, start second | The restart stopped the only serving unit and then submitted the replacement. | The quota was full. The replacement stayed pending and the service was down for hours. | Admission is not certain. Prove it before the drain. |
| Autoscale and restart with no priority | Both added surplus units. | Surplus units filled the quota and the floor service had no slot. | Set one rule for which action wins. |

## Results & Parameters

```yaml
restart_policy:
  precheck: [quota_headroom, running_count, pending_count]
  order: surge_then_drain
  single_unit_service: replacement_must_be_healthy_first
  on_pending_replacement: wait_and_report_blocked   # never drain
  priority: floor_over_autoscale_surplus
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Project-neutral scheduler-backed service | Release and deployment session | A restart on a full quota left no serving unit for many hours. |

## References

- [Scheduler service replacement identity continuity](scheduler-service-replacement-identity-continuity.md)
- [Runtime component checks degrade, they do not stop](runtime-component-checks-degrade-not-stop.md)
