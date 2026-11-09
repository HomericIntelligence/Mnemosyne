---
name: slurm-qos-group-cap-regression-diagnosis
license: BSD-3-Clause
description: "Diagnose new jobs that stay pending with a QOS group-limit reason while older jobs keep running over the reported limit as a lowered Quality-of-Service (QOS) group cap, and prepare the limit restoration. Use when: (1) new jobs pend with QOSGrpNodeLimit or QOSGrpGRES while running jobs continue, (2) running usage is over the limit that the scheduler reports, (3) a documented node or GPU budget disagrees with the live QOS limit, (4) running usage stands exactly at the group limit with no over-limit job, so the cap is legitimately saturated and the remedy is capacity arithmetic, co-location, or a cap raise instead of a restoration, (5) you must decide whether the service or the scheduler owns the node-count limit and must report a refusal, or (6) a job held at QOSGrpNodeLimit while nodes that the account already uses have free capacity or run lower-tier jobs, and you must test co-location and preemption instead of assuming them."
category: debugging
date: 2026-10-28
version: "1.2.0"
user-invocable: false
tags: [slurm, qos, grptres, group-limit, pending-jobs, capacity, sacctmgr, scheduler, cap-regression, co-location, placement-exclusions, fleet, replica-count, node-count-ownership, refusal-reporting]
---

# Slurm QOS Group-Cap Regression Diagnosis

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | Classify a fleet of pending jobs with QOS group-limit reasons as either a lowered QOS group cap or legitimate saturation at an intact cap, bound any change time, prepare the matching remedy, and name the owner of the node-count limit. |
| **Outcome** | Operational. A full production fleet with seven running nodes over a four-node group cap was classified as an external cap reduction, not a demand problem. The live cap, the documented budget, and an earlier captured transcript proved the regression; the restoration command was prepared for the scheduler administrator. A later session on the same QOS classified the opposite branch: usage exactly at the intact cap, so the pending pool needed capacity arithmetic and co-location analysis instead of a restoration. An owner decision then set the ownership rule: the service requests replicas, the scheduler owns the node limit, and the recorded cap is report-only. The code change that applies this rule is not yet recorded. |

## When to Use

- New jobs pend with `QOSGrpNodeLimit`, `QOSGrpGRES`, or a similar `QOSGrp*` reason while running jobs continue without change.
- The running usage of one QOS is over the group limit that the scheduler reports for that QOS.
- Running usage stands exactly at the group limit with no over-limit job, and new jobs of the same QOS stay pending behind it.
- A pending job refuses hosts that visibly have free resources, and the pending job's submission carries an exclude list.
- A documented node or GPU budget for an account disagrees with the live QOS limit.
- A healthy running job is cancelled from outside while the fleet is over a reported cap.
- You must decide whether the service that requests replicas or the scheduler owns the node-count limit, or how a scheduler refusal reaches an operator.
- A job is held at `QOSGrpNodeLimit` while nodes that the account already uses show free capacity or run lower-tier jobs of other tenants.

## Verified Workflow

### Quick Reference

```bash
# The live cap for one QOS. GrpTRES is the binding group budget.
sacctmgr -nP show qos <name> format=Name,MaxNodesPerUser,MaxTRESPerUser,GrpTRES

# Which jobs hold the QOS now, with node counts and reasons.
squeue -h -o "%i|%q|%j|%T|%D|%R"

# Per-job accounting for a job that ended unexpectedly.
sacct -j <job-id> -n -o JobID,JobName%20,State,ExitCode,End

# Why one pending job cannot reach a host: the reason and the exclude list
# that a coordinator baked into the submission.
scontrol show job <job-id> | grep -E "JobState|Reason|ExcNodeList|ReqTRES"

# Privileged restoration of the group cap. Takes effect at once.
sacctmgr modify qos <name> set grptres=node=<N>,gres/gpu=<M>
```

### Suggested Approach

1. Treat `QOSGrp*` pending reasons with over-limit running usage as a cap-regression signal, not as normal contention. The scheduler applies a QOS group limit when it admits new work; it does not stop jobs that run already. Running usage over the current limit is therefore possible only when the limit changed after those jobs started. Record this rule before any capacity hypothesis. Usage that stands exactly at the limit is the other branch: the cap is intact and saturated, so the regression workflow does not apply. Classify the branch from the usage ratio before you select a remedy, and use the saturation branch below for the at-limit case.
2. Read the live cap with `sacctmgr show qos`. An empty `MaxNodesPerUser` with a populated `GrpTRES` means the group TRES is the binding limit. `QOSGrpNodeLimit` points to the node count in `GrpTRES`; `QOSGrpGRES` points to a GRES entry such as `gres/gpu`.
3. Reconcile three sources: the live QOS values, the documented deployment budget, and any earlier captured transcript of the same QOS. A documented budget above the live cap is evidence of an external modification. It is not a demand problem, so do not resolve it by cancelling production work.
4. Bound the change time from the fleet. The latest start time among running jobs that exceed the current cap is a lower bound for the change: the cap changed after that job started. Slurm does not give a QOS edit history to non-administrators, so route the exact who and when to a scheduler administrator with database access.
5. Count every TRES that the cap includes. A job without the capped GRES, such as a CPU-only gateway, still holds a node against a `GrpTRES` node count. Count such jobs with the fleet before you compute free capacity.
6. Examine the shape of the change. `GrpTRES` fields that fall by the same factor, such as node count and GPU count together, suggest a scripted resize or values copied from a sibling QOS. A change to one field alone suggests a direct edit.
7. Expect cleanup of over-limit work after a reduction. A healthy job that ends `CANCELLED` with an external signal during an over-limit period is consistent with a capacity trim. Confirm with `sacct` and the job log before you diagnose an engine fault.
8. Prepare the restoration for the administrator: `sacctmgr modify qos <name> set grptres=node=<N>,gres/gpu=<M>`. The change applies without a controller restart, and pending jobs then schedule in priority order. Demand above the restored cap still queues; state the expected residual queue. Do not cancel running jobs to make room unless the work owner selects that trade.

### Saturation Branch: Usage at an Intact Cap

Run this branch when no running job is over the limit and new jobs of the same QOS stay pending.

1. Do the capacity arithmetic in nodes before you propose any remedy. Convert each pool's protected floor to its node footprint: a multi-node replica counts every node it spans, and a zero-GRES service job, such as a gateway, counts its node against a `GrpTRES` node count. If the floor sum alone exceeds the cap, no placement policy can satisfy it: the cap must rise or a floor must drop. State the deficit, for example `floors 5 nodes against cap 4`, to the administrator with the raise request.
2. Identify the binding dimension. Compare each `GrpTRES` entry with current usage. A node count can bind while GPU headroom remains, so a GPU-based remedy does not help.
3. Use same-node co-location as the only placement that adds capacity inside an exhausted node cap. Jobs of one account that share one node count once against a node-count `GrpTRES`, so a zero-GRES service job's node can host a GPU job without a node-count increase, while the host fits the whole request. Verify the host fit from the scheduler's own allocation counters, not from the job's request alone: other tenants on a shared node can hold the GPUs and memory that the request needs.
4. Test co-location with a pin instead of reasoning about it. Pin the held job to a node that already runs a job of the same QOS: `scontrol update JobId=<id> ReqNodeList=<node>`. A held job does not look at shared nodes on its own: the QOS check runs before node selection. If the pending reason changes from `QOSGrpNodeLimit` to `Resources`, the QOS counts that node once, and the job now competes for the node's resources. Do not state a node-counting rule as fact before this test. Clear the pin with an empty `ReqNodeList=` if the job must run anywhere.
5. Read the preemption setup before you expect an eviction. Run `scontrol show config | grep -i preempt`, read `PriorityTier` and `PreemptMode` of the job's partition and of each partition that holds the blocking jobs, and read the QOS `Preempt` column. With partition-priority preemption, a job in a higher-tier partition requeues jobs of lower-tier partitions, but only after it is past the QOS limit; in the measured case the pin was enough, the lower-tier jobs on the node were requeued, and the pinned job started within about a minute. Jobs of other tenants in the same partition tier are not preempted. They block the node until they end, and a freed half node can go to such a job when your job exits. Size the fit with all three counters per node (GPUs, CPUs, and memory); Slurm counts requested memory, not used memory, so sum each job's request.
6. Read the pending job's exclude list before you name any host as available. A serving coordinator can cancel a partial packed placement whose host cannot hold the complete cohort, quarantine that host, and render `--exclude=<nodes>` into every later submission. A host with visible free GPUs is then unreachable for that pool. The coordinator's placement or drift logs record the fit failure, and the exclusion list on the newest pending job names the quarantined hosts. A partial co-location also may not help: when the pool floor needs a full cohort on one host, a single co-located replica still leaves the rest of the floor to schedule onto a new node.
7. Select the remedy from the arithmetic: a cap raise for the administrator when the floors are all required, a floor reduction or retirement when a pool can yield, or a full-cohort co-location when one host can hold it. Report the residual queue for each option.

### Ownership Branch: Replica Request Versus Node Budget

Run this branch when you select the remedy for a service that requests replicas, or when you review a service that refuses a start before submission.

1. Separate the replica request from the node footprint. A replica request is a requested value: a count per model or pool. Replicas of one model can share a node by GPU slice, so the node count depends on how the scheduler packs them. Do not derive a node count from a replica count before submission.
2. Select one owner for each limit. The scheduler owns the node and GPU limit through its QOS group cap. The service owns the replica request and the diagnostics. If both refuse, the service refusal hides the scheduler message and turns a capacity fact into a startup error.
3. Keep a measured cap as a report record. A record of `sacctmgr` output may inform an alert or a report. Mark it report-only and do not let it refuse a start. A recorded cap is a measurement at one time, and it goes stale without notice.
4. Submit the requested value and let the scheduler answer. A start above the recorded cap must reach submission, because the real grant can differ from the record and the QOS can have a higher limit than the record shows.
5. Report the refusal from the scheduler with the job id, the partition, the QOS, and the scheduler message. These four fields make a real cap limit diagnosable. A message with no job id cannot be traced to a pending job.
6. Prove the ownership branch with one behavior test: a start whose requested set is above the recorded cap proceeds to submission. Add no test that scans the source for a node-count formula. Review covers that rule.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Contention assumption | Read the pending reasons as normal peak demand and planned to wait. | Running usage stood over the reported group limit, which idle contention cannot produce. | Over-limit running usage proves the cap moved after those jobs started. Classify the cap regression first. |
| User-side audit search | Searched scheduler event records for the QOS edit that lowered the cap. | `sacctmgr show events` records cluster registration, not QOS edits; non-administrators get no edit history. | Bound the change time from the start times of over-limit running jobs. Route the exact who and when to a scheduler administrator. |
| Crash attribution | Read a cancelled serving job as an engine crash because the server log showed no fault. | Accounting showed `CANCELLED` with an external signal while the log was healthy; the fleet was over the lowered cap at that moment. | After a cap reduction, capacity trims end healthy jobs. Check `sacct` state and exit code before you diagnose the engine. |
| Free-host assumption | Recommended co-locating a pending replica on a host that visibly had free GPUs. | The coordinator had quarantined that host after a cohort-fit failure and rendered it into every later submission's exclude list; the replicas it did place there were cancelled within minutes of allocation. | A host is available only when both the scheduler and the coordinator allow it. Read the pending job's exclude list and the coordinator's placement logs before you name a target. |
| Pre-flight budget refusal | Made the deployment start refuse a requested replica set that was larger than a recorded node and GPU cap, and asked the administrator to raise the cap. | The recorded cap was a measurement, not an admission gate, and replicas share nodes, so the derived node count was not the scheduler's node count. The decision changed to submit and report the scheduler answer. | The scheduler owns the node limit. Keep the cap as a report record and surface the scheduler refusal. |
| Counting-rule assumption | Told the owner that the QOS counts one node per job, even on a node it already counted, to explain a held job. | The pin test changed the reason from `QOSGrpNodeLimit` to `Resources` at once, so a shared node counts once; the held job was blocked because no counted node had room, and it never reached placement. | State a counting rule only after a pin test. Report the cause as missing room on the counted nodes, and name the tenants or tiers that hold it. |

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
qos_cap_saturation:
  classification: usage exactly at the cap with no over-limit job means an intact, saturated cap
  floor_arithmetic: sum each pool's floor node footprint, including multi-node replicas and zero-GRES service nodes
  binding_dimension: compare each GrpTRES entry with usage; a node count can bind while GPU headroom remains
  co_location: same-account jobs on one shared node count once against a node-count GrpTRES; verify the host fit from scheduler allocation counters
  exclusion_check: scontrol show job <id> ExcNodeList plus the coordinator's placement logs name the quarantined hosts
  co_location_test: scontrol update JobId=<id> ReqNodeList=<node already in the QOS>; reason QOSGrpNodeLimit -> Resources means the node counts once
  preemption_check: scontrol show config | grep -i preempt; PriorityTier and PreemptMode per partition; QOS Preempt column; other tenants in the same tier are not preempted
  fit_counters: per node GPUs, CPUs, and requested memory (not used memory)
  remedies: [administrator cap raise, floor reduction or retirement, full-cohort co-location on one host]
qos_cap_ownership:
  service_owns: replica request and refusal diagnostics
  scheduler_owns: node and GPU limit through the QOS group cap
  recorded_cap: report-only measurement; never an admission gate
  refusal_report_fields: [job id, partition, qos, scheduler message]
  behavior_proof: a requested set above the recorded cap reaches submission
  excluded_proof: a source scan for a node-count formula; review covers that rule
```

### Expected Output

- One classification for the pending fleet: lowered group cap, with the live and documented cap values as evidence.
- A lower bound for the change time, from the latest over-limit running start.
- A restoration command with the budget values, ready for a scheduler administrator.
- The expected residual queue after restoration, computed from fleet demand against the restored cap.
- For the saturation branch: the binding `GrpTRES` dimension, the floor-sum deficit, the co-location options with their host-fit evidence, the coordinator-quarantined hosts from the exclude list, and the residual queue for each remedy.
- For the ownership branch: the named owner of the replica request and of the node limit, the report-only cap record, and the scheduler refusal with job id, partition, QOS, and message.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production multi-tenant Slurm cluster | A serving fleet pended with `QOSGrpNodeLimit` and `QOSGrpGRES` while seven running nodes stood over a four-node group cap; the documented budget and an earlier transcript showed a ten-node cap. | Cluster-specific identifiers were generalized per privacy policy. See [notes](slurm-qos-group-cap-regression-diagnosis.notes.md). |
| Production multi-tenant Slurm cluster | A model-replica pool pended with `QOSGrpNodeLimit` while running usage stood exactly at the intact four-node cap; co-located placements were cancelled within minutes by a coordinator cohort-fit guard, and later submissions excluded the quarantined hosts. | Cluster-specific identifiers were generalized per privacy policy. See [notes](slurm-qos-group-cap-regression-diagnosis.notes.md). |
| Production multi-tenant Slurm cluster | An owner decision after that session removed the service pre-flight refusal of a requested replica set against the recorded cap and made the scheduler refusal the reported condition. The code change was not part of the recorded session. | Generalized per privacy policy. See [notes](slurm-qos-group-cap-regression-diagnosis.notes.md). |
| Production multi-tenant Slurm cluster | A model-replica job pended at `QOSGrpNodeLimit` for hours beside nodes the account already used; a node pin changed the reason to `Resources`, partition-priority preemption requeued lower-tier jobs, and the job started in about a minute. | Cluster-specific identifiers, node names, and job numbers are withheld; see the notes file. |

## References

- [sacctmgr(1) — manage associations, accounts, and QOS](https://slurm.schedmd.com/sacctmgr.html)
- [Slurm account and partition discovery](slurm-account-partition-discovery.md) — the discovery commands that answer account, partition, and QOS questions.
- [Serving-pool replica outage diagnosis](serving-pool-replica-outage-diagnosis.md) — the branch where replicas die instead of staying pending.
- [Slurm walltime expiry outage diagnosis](slurm-walltime-expiry-outage-diagnosis.md) — the branch where a job disappears at its time limit.
- [Privacy-safe source evidence](slurm-qos-group-cap-regression-diagnosis.notes.md)
