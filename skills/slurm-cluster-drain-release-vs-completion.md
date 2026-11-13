---
name: slurm-cluster-drain-release-vs-completion
description: "Decide whether a cluster-wide node drain that removed serving capacity ended or was released, and when the capacity is truly back. Use when: (1) many unrelated jobs or serving replicas end within the same second or in tight bursts, (2) nodes show a planned state and then the planned count falls quickly, (3) nodes stay drained with a kill-task or epilog failure reason after the wave, or (4) a reporter says that the service is back and you must verify the claim."
category: debugging
date: 2026-11-13
version: "1.0.0"
user-invocable: false
tags: [slurm, drain, maintenance, reboot, preemption, node-state, outage-diagnosis, capacity, registration]
---

# Slurm Cluster Drain Release vs Completion

## Overview

| Field | Value |
| ------- | -------- |
| **Date** | 2026-11-13 |
| **Objective** | Classify a cluster-wide drain wave as a completed maintenance or a released drain, and separate restored capacity from restored service. |
| **Outcome** | Operational. A wave that removed most low-priority serving replicas was a released drain: the planned count fell to near zero while only a small number of nodes had a new boot time. The released nodes accepted the queued backlog within minutes, and the service still needed registration and health checks. |

## When to Use

- Many unrelated jobs or serving replicas end in the same second, or in a few tight bursts.
- Nodes show a planned state, then the planned count falls to near zero in minutes.
- Nodes stay drained with a kill-task, epilog, or process-kill failure reason after the wave.
- A person reports that "everything is back" and you must verify the claim from evidence.
- A serving pool lost most of its replicas and you must decide between a pool defect and a cluster event.

## Verified Workflow

### Quick Reference

```bash
# 1. Waves: job ends per minute. One second with many unrelated jobs is a scheduler action.
sacct -S <start> -E <end> -o End -X -a | grep -oE '^[0-9-]+T[0-9]{2}:[0-9]{2}' | sort | uniq -c

# 2. State mix before and after the wave.
sinfo -p <partition> -o "%.10T %.6D"

# 3. Reboot evidence: planned nodes against nodes with a new boot time.
scontrol show node -o | grep -c "PLANNED"
scontrol show node -o | grep -c "BootTime=$(date +%F)"

# 4. Nodes that stay out need an operator action.
sinfo -t drain,drain*,drng -o "%.30N %.10T %.50E"
```

### Suggested Approach

1. Count job ends per minute before you read any service log. A single second that holds many ends from unrelated users and job families is one scheduler-wide action. A pool defect does not remove other users' jobs.
2. Read the node state mix. A planned state that falls to near zero while idle and allocated counts rise is a released drain. The scheduler returned the nodes to service.
3. Compare the planned count with the count of nodes whose `BootTime` or `SlurmdStartTime` changed. Equal counts mean that reboots happened. A much lower changed count means that most nodes never rebooted, so the drain plan was released rather than completed.
4. List the nodes that stay out. A drained node with a kill-task or epilog failure does not return by itself. It needs an operator resume or reboot. Report the list and the reason, and do not wait for automatic recovery.
5. Treat a fast allocation jump as restored backlog, not as new demand. Released nodes accept the queue at once. Count the queued jobs before the wave and compare them with the jobs that start after it.
6. Declare service recovery from the service record. A replica is back when it registers and answers health checks. A job with a future start time, or a job in `RUNNING`, is not a recovered replica.
7. Keep the two outcomes separate in the report: node capacity, and service capacity. One can return in minutes while the other needs an engine start and a registration.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| Attempt 1 | Read the planned state as a completed reboot and reported that maintenance finished. | The planned count fell to near zero, but only a small fraction of the planned nodes had a new boot time. The rest were released without a reboot. | Compare the planned count with the changed boot-time count before you name the outcome. |
| Attempt 2 | Reported pool recovery from job state and from a start estimate. | The jobs were only queued. The start estimate moved by about a day, then the replicas got start times within two minutes, and engine start and registration still remained. | Recovery evidence is registration plus a health answer, not a job state or a start estimate. |
| Attempt 3 | Treated the mass job-end burst as a defect in one serving pool. | Unrelated users and job families ended at the same second, and node states changed across the cluster. | Check the cross-user distribution first. A shared second means a shared cause. |
| Attempt 4 | Counted every planned node as a reboot and waited for all of them. | A released plan returns nodes with their old boot time in minutes. Waiting on a reboot that will not happen delays the capacity report. | Separate the rebooted nodes from the released nodes, then report each count. |

## Results & Parameters

### Configuration

```yaml
drain_classification:
  wave_window: "1 to 2 minutes"
  wave_signal: "one second or minute holds most job ends across unrelated users"
  release_check: "planned count is much higher than the changed BootTime count"
  completion_check: "planned count is about equal to the changed BootTime count"
  blocked_nodes: "drained with a kill-task or epilog failure reason"
  recovery_evidence: "registry entry plus a health answer"
```

### Expected Output

Use this report shape:

- Wave: the seconds or minutes that hold most job ends, and the number of users and job families in each burst.
- State: the planned count before and after the wave, and the idle and allocated counts after it.
- Classification: `released` or `completed`, with the planned and changed boot-time counts.
- Blocked nodes: the drained nodes and their reason, if any remain.
- Service: the live replica count and the registration and health evidence.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Shared GPU cluster | Incident review of a cluster-wide drain wave on a multi-tenant Slurm cluster | [notes](slurm-cluster-drain-release-vs-completion.notes.md) |

## References

- [Serving-pool replica outage diagnosis](serving-pool-replica-outage-diagnosis.md)
- [Slurm walltime expiry outage diagnosis](slurm-walltime-expiry-outage-diagnosis.md)
- [Slurm QOS group-cap regression diagnosis](slurm-qos-group-cap-regression-diagnosis.md)
- [Slurm job name truncation false absence](slurm-job-name-truncation-false-absence.md)