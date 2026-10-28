---
name: slurm-qos-group-cap-regression-diagnosis
license: BSD-3-Clause
description: "Diagnose new jobs that stay pending with a QOS group-limit reason while older jobs keep running over the reported limit as a lowered Quality-of-Service (QOS) group cap, and prepare the limit restoration. Use when: (1) new jobs pend with QOSGrpNodeLimit or QOSGrpGRES while running jobs continue, (2) running usage is over the limit that the scheduler reports, or (3) a documented node or GPU budget disagrees with the live QOS limit."
category: debugging
date: 2026-10-28
version: "1.0.0"
user-invocable: false
tags: [slurm, qos, grptres, group-limit, pending-jobs, capacity, sacctmgr, scheduler, cap-regression, fleet]
---

# Slurm QOS Group-Cap Regression Diagnosis

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | Classify a fleet of pending jobs with QOS group-limit reasons as a lowered QOS group cap, bound the change time, and prepare the limit restoration. |
| **Outcome** | Operational. A full production fleet with seven running nodes over a four-node group cap was classified as an external cap reduction, not a demand problem. The live cap, the documented budget, and an earlier captured transcript proved the regression; the restoration command was prepared for the scheduler administrator. |

## When to Use

- New jobs pend with `QOSGrpNodeLimit`, `QOSGrpGRES`, or a similar `QOSGrp*` reason while running jobs continue without change.
- The running usage of one QOS is over the group limit that the scheduler reports for that QOS.
- A documented node or GPU budget for an account disagrees with the live QOS limit.
- A healthy running job is cancelled from outside while the fleet is over a reported cap.

## Verified Workflow

### Quick Reference

```bash
# The live cap for one QOS. GrpTRES is the binding group budget.
sacctmgr -nP show qos <name> format=Name,MaxNodesPerUser,MaxTRESPerUser,GrpTRES

# Which jobs hold the QOS now, with node counts and reasons.
squeue -h -o "%i|%q|%j|%T|%D|%R"

# Per-job accounting for a job that ended unexpectedly.
sacct -j <job-id> -n -o JobID,JobName%20,State,ExitCode,End

# Privileged restoration of the group cap. Takes effect at once.
sacctmgr modify qos <name> set grptres=node=<N>,gres/gpu=<M>
```

### Suggested Approach

1. Treat `QOSGrp*` pending reasons with over-limit running usage as a cap-regression signal, not as normal contention. The scheduler applies a QOS group limit when it admits new work; it does not stop jobs that run already. Running usage over the current limit is therefore possible only when the limit changed after those jobs started. Record this rule before any capacity hypothesis.
2. Read the live cap with `sacctmgr show qos`. An empty `MaxNodesPerUser` with a populated `GrpTRES` means the group TRES is the binding limit. `QOSGrpNodeLimit` points to the node count in `GrpTRES`; `QOSGrpGRES` points to a GRES entry such as `gres/gpu`.
3. Reconcile three sources: the live QOS values, the documented deployment budget, and any earlier captured transcript of the same QOS. A documented budget above the live cap is evidence of an external modification. It is not a demand problem, so do not resolve it by cancelling production work.
4. Bound the change time from the fleet. The latest start time among running jobs that exceed the current cap is a lower bound for the change: the cap changed after that job started. Slurm does not give a QOS edit history to non-administrators, so route the exact who and when to a scheduler administrator with database access.
5. Count every TRES that the cap includes. A job without the capped GRES, such as a CPU-only gateway, still holds a node against a `GrpTRES` node count. Count such jobs with the fleet before you compute free capacity.
6. Examine the shape of the change. `GrpTRES` fields that fall by the same factor, such as node count and GPU count together, suggest a scripted resize or values copied from a sibling QOS. A change to one field alone suggests a direct edit.
7. Expect cleanup of over-limit work after a reduction. A healthy job that ends `CANCELLED` with an external signal during an over-limit period is consistent with a capacity trim. Confirm with `sacct` and the job log before you diagnose an engine fault.
8. Prepare the restoration for the administrator: `sacctmgr modify qos <name> set grptres=node=<N>,gres/gpu=<M>`. The change applies without a controller restart, and pending jobs then schedule in priority order. Demand above the restored cap still queues; state the expected residual queue. Do not cancel running jobs to make room unless the work owner selects that trade.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Contention assumption | Read the pending reasons as normal peak demand and planned to wait. | Running usage stood over the reported group limit, which idle contention cannot produce. | Over-limit running usage proves the cap moved after those jobs started. Classify the cap regression first. |
| User-side audit search | Searched scheduler event records for the QOS edit that lowered the cap. | `sacctmgr show events` records cluster registration, not QOS edits; non-administrators get no edit history. | Bound the change time from the start times of over-limit running jobs. Route the exact who and when to a scheduler administrator. |
| Crash attribution | Read a cancelled serving job as an engine crash because the server log showed no fault. | Accounting showed `CANCELLED` with an external signal while the log was healthy; the fleet was over the lowered cap at that moment. | After a cap reduction, capacity trims end healthy jobs. Check `sacct` state and exit code before you diagnose the engine. |

## Results & Parameters

### Configuration

```yaml
qos_cap_regression:
  live_cap: sacctmgr -nP show qos <name> format=Name,MaxNodesPerUser,MaxTRESPerUser,GrpTRES
  binding_field: GrpTRES when MaxNodesPerUser is empty
  reason_map: {QOSGrpNodeLimit: GrpTRES node, QOSGrpGRES: GrpTRES gres/gpu}
  evidence_sources: [live qos record, documented deployment budget, earlier captured transcript]
  change_time_bound: latest start time among over-limit running jobs
  restoration: sacctmgr modify qos <name> set grptres=node=<N>,gres/gpu=<M>
  restoration_effect: immediate, no controller restart, pending jobs schedule in priority order
```

### Expected Output

- One classification for the pending fleet: lowered group cap, with the live and documented cap values as evidence.
- A lower bound for the change time, from the latest over-limit running start.
- A restoration command with the budget values, ready for a scheduler administrator.
- The expected residual queue after restoration, computed from fleet demand against the restored cap.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production multi-tenant Slurm cluster | A serving fleet pended with `QOSGrpNodeLimit` and `QOSGrpGRES` while seven running nodes stood over a four-node group cap; the documented budget and an earlier transcript showed a ten-node cap. | Cluster-specific identifiers were generalized per privacy policy. See [notes](slurm-qos-group-cap-regression-diagnosis.notes.md). |

## References

- [sacctmgr(1) — manage associations, accounts, and QOS](https://slurm.schedmd.com/sacctmgr.html)
- [Slurm account and partition discovery](slurm-account-partition-discovery.md) — the discovery commands that answer account, partition, and QOS questions.
- [Serving-pool replica outage diagnosis](serving-pool-replica-outage-diagnosis.md) — the branch where replicas die instead of staying pending.
- [Slurm walltime expiry outage diagnosis](slurm-walltime-expiry-outage-diagnosis.md) — the branch where a job disappears at its time limit.
- [Privacy-safe source evidence](slurm-qos-group-cap-regression-diagnosis.notes.md)
