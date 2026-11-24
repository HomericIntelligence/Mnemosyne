---
name: slurm-requeue-preemptor-attribution
license: BSD-3-Clause
description: "Explain why running Slurm jobs went back to pending, and find which jobs preempted them. Use when: (1) running jobs of yours reappear as PENDING with Restarts or Requeue counts raised, (2) sacct and scontrol show no requeue reason, (3) you are tempted to say 'same partition tier cannot preempt, so the cause is unknown', or (4) other jobs started on your freed nodes within seconds."
category: tooling
date: 2026-11-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - slurm
  - preemption
  - requeue
  - scontrol
  - sacct
  - qos
  - partition-priority
  - incident-diagnosis
---

# Slurm Requeue: Attribute the Preemptor from Timing, Not from Config

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Explain why several running jobs of one account went back to PENDING, and name the jobs that caused it. |
| **Outcome** | Cause attributed from start times and node overlap. Config review alone gave a false "not possible". |
| **Verification** | verified-local on a shared cluster with `PreemptType=preempt/partition_prio` and `PreemptMode=REQUEUE`. The scheduler log was not readable, so the attribution is inferred, not logged. |

## When to Use

- Running jobs reappear as PENDING. `scontrol show job` shows `Requeue=1` and a raised `Restarts` count.
- `sacct` and `scontrol` give no reason for the requeue. Slurm stores no preemptor identity in job records.
- Jobs of other users or accounts started on the freed nodes within seconds of the requeue.

Do not use this entry to identify what a live job executes. Use `slurm-job-content-attribution` for that.

## Verified Workflow

### Quick Reference

```bash
# 1. Requeue time per victim (Submit resets to the requeue time).
sacct -X -j <ids> --format=JobID,State,Submit,Start,End,NodeList%25,QOS,Partition -P

# 2. Who runs on the victims' old nodes now, and since when.
squeue -w <old-nodelist> -o "%.10i %.9P %.20j %.10u %.2t %.10M %.20S %R"
scontrol show job <id> | grep -E "Partition=|QOS=|Account=|StartTime|SubmitTime|Command"

# 3. Preemption rules in force.
scontrol show config | grep -E "PreemptType|PreemptMode|PreemptExemptTime"
scontrol show partition | grep -E "PartitionName|PriorityTier"
sacctmgr -n -P show qos format=Name,Preempt,PreemptMode
```

1. Record the requeue time of each victim from step 1.
2. List the jobs now on the victims' old nodes. A job whose start time is within seconds of the requeue is a preemptor candidate. Use the node overlap as evidence. Do not rely on the job name alone.
3. Compare the QOS, account, and partition of each candidate with the victims. A different QOS or account that the cluster treats as higher priority is a strong signal. A script name that contains "preempt" is a hint only.
4. Read the preemption rules last. Use them to rank causes. Do not use them to reject a cause.
5. Report the attribution as inferred when the controller log is not readable. State that only an admin can confirm it in the controller log. Look for lines such as "preempted by".

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Config-first diagnosis | Reasoned from `PreemptType=preempt/partition_prio` that jobs in one partition tier cannot preempt each other, and called the cause unknown. | Config shows the allowed mechanism, not what happened. The reading ignored multi-partition submissions and QOS or account differences. The account owner named the new jobs as the preemptors, and the timing matched. | Attribute from start time and node overlap first. Use config only to rank causes. |
| Partition column as tier | Treated the `Partition` column of a running job as the tier it was scheduled under. | A job submitted to several partitions shows only the partition where it ran. | Ask for the submit line or the job's partition list in the controller log. |
| Reason lookup in accounting | Searched `sacct` for a preemption reason on the victim. | Accounting records have no reason or preemptor ID. | Use timing and node overlap, then ask an admin for the controller log. |

## Results & Parameters

- Requeue signal: `Requeue=1` and `Restarts` raised in `scontrol show job`.
- Attribution window: preemptor start within about 15 seconds of the victim requeue.
- Cluster used: `PreemptMode=REQUEUE`, `PreemptType=preempt/partition_prio`, `PreemptExemptTime=00:00:00`.
- Result: 3 jobs requeued, 4 foreign jobs started on 4 of the freed nodes, and 2 own pending jobs started at the same second.
- Limit: no controller log access, so the result is an inference.
