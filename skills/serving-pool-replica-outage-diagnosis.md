---
name: serving-pool-replica-outage-diagnosis
license: BSD-3-Clause
description: "Classify the simultaneous loss of every replica of one model-serving pool as an engine crash, a scheduler reclamation, or a hardware event before incident response, and audit the recovery placement. Use when: (1) two or more replicas of one pool fail within minutes of each other, (2) the same exception or termination signature appears in more than one replica log, (3) replacement jobs start and then vanish before they register, (4) you are about to attribute the outage to node hardware, or (5) new replicas start, run for seconds to minutes, and end FAILED before they register, on every submission."
category: debugging
date: 2026-10-26
version: "1.1.0"
user-invocable: false
tags: [serving, outage-diagnosis, replica, poison-request, preemption, slurm, sacct, recovery-placement, gateway-registration, startup-failure, container-mount, engine-arguments, failure-breaker]
---

# Serving-Pool Simultaneous Replica Outage Diagnosis

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Classify a whole-pool replica loss from scheduler accounting and replica log tails before you report a cause, and verify that recovery jobs run on the placement that can keep the floor. |
| **Outcome** | Operational. A two-replica production pool loss was classified as one engine crash caused by one poison request class retried against the surviving replica, not as node failure. A two-hour recovery gap was attributed to replacement jobs running on the preemptible tier; protected-tier submission restored capacity in minutes. |

## When to Use

- Two or more replicas of one serving pool fail within minutes of each other.
- The same exception, traceback, or termination banner appears in more than one replica log.
- Replacement jobs show submission activity, but the pool does not return to registered and healthy.
- Final accounting for a replacement job shows no start time and no node list, yet job log files exist for it.
- You are about to attribute the event to node hardware, or to open a hardware ticket.
- New replicas reach RUNNING, then end FAILED within seconds to about fifteen minutes, with no registration, and every resubmission ends the same way.

## Verified Workflow

### Quick Reference

```bash
# Accounting for every dead job comes before any node or hardware hypothesis.
sacct -j <job-id-1>[,<job-id-2>,...] \
  -o JobID,Partition,QOS,Account,State,ExitCode,Submit,Start,End,Elapsed,NodeList

# FAILED + nonzero exit + the identical traceback in each replica log
#   -> engine crash from one poison request class, retried across replicas.
# PREEMPTED, or a "CANCELLED ... DUE TO PREEMPTION" banner in the job log
#   -> scheduler reclamation of a preemptible placement. Not a defect.
# NODE_FAIL, or a node reason on the job
#   -> start hardware diagnosis.
# FAILED within minutes, never registered, same first error on each submission
#   -> deterministic startup failure: read the first error of the lowest-rank engine log.

# The launch spec of a job that still waits shows the rendered flags and mounts.
scontrol write batch_script <job-id> -
```

### Suggested Approach

1. Treat the simultaneous loss of one pool as one incident with one cause until the evidence disagrees. N independent hardware failures within minutes on one pool is the least likely explanation.
2. Pull scheduler accounting for every dead job first: state, exit code, partition, QoS, account, submit, start, end, elapsed, and node list. Do not open service logs before this step.
3. Engine-crash branch: compare the tails of every dead replica log. An identical application exception, minutes apart in each replica, means one poison request class: the first crash moves the traffic, and the retry kills the surviving replica. The correction is request validation or error containment in the engine, not node repair. Record the request class. Then identify sibling pools that load the same engine model code. The same request class is lethal to those pools even when they stayed up, because only traffic selection protected them.
4. Reclamation branch: a job on a preemptible partition or QoS that ends PREEMPTED, or whose log shows a preemption banner close to its start, was reclaimed by higher-priority work. That is the placement contract, not a defect. A requeued job resets its summary row: final accounting can show no start and no node list while the job log artifacts show several brief earlier runs. Read the job log files and the full step records, not only the final summary row.
5. Recovery-placement audit: compare the partition, QoS, and account of each replacement job with the placement that the pool's protected floor uses. Replacement jobs on the preemptible tier can start, be preempted repeatedly, and then sit pending for hours while status views show only that replacements were submitted. Resubmit the floor replicas to the protected placement. Do not resubmit to the same tier and wait again.
6. Recovery is registration, not submission. A large checkpoint can need tens of minutes of engine startup after the job state becomes RUNNING. Declare the pool recovered only when the replacements register with the gateway or control plane and answer health checks.
7. Startup-failure branch: use it when new replicas end FAILED before they register and every submission fails the same way. Read the first error in the lowest-rank engine log, not the supervisor summary. A line such as "rank 0 exited first with status 137" reports the kill of the other processes after the first failure; the cause is above it. Then classify the first error:
   - A container start failure that names a bind-mount source ("mount source ... No such file or directory"). It appears within seconds to minutes and repeats on every submission. Check each mount source of the launch spec on the compute-node view of the filesystem. A directory that a new root never created, or that an older release kept elsewhere, is the usual cause. Restore the files from the copy that the older release used, verify them by checksum, and check that the launch spec names the restored path.
   - An engine argument conflict: a `ValueError` or `NotImplementedError` from backend setup that names two flags, such as a cache data type that the chosen attention backend does not accept. The engine checks these flags after it verifies the checkpoint, so each trial costs minutes. A fix for one conflict can expose the next. Collect every constraint from the messages, write the table of allowed combinations, and choose one combination that has a measurement before you submit again. Do not change one flag per resubmission.
   - The same first error on every replica of the pool means configuration, not hardware. Stop the resubmission loop. The pool failure breaker can trip after a small number of identical failures and stop all relaunches, so reset it after the fix and not before.
8. Prove a startup fix with one replica: the job stays RUNNING past the earlier failure time, the replica registers with the gateway, and a real request returns a completion. Then scale the pool.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Attributed the outage to node hardware because every replica of the pool went down within two minutes. | Accounting showed FAILED with a nonzero exit, each replica log ended with the identical unhandled application exception minutes apart, and replacement jobs later started on the same class of hardware. | Classify from scheduler state and log tails first. Simultaneous loss of one pool is usually one software cause plus retries against the remaining replicas. |
| Attempt 2 | Read the final summary row of the replacement jobs, which showed no start time and an empty node list, as "the replacements never ran". | The job log files showed several brief earlier runs on real nodes, each ending with the preemption banner. The jobs had been preempted and requeued, which resets the summary row. | For a requeued job, final accounting hides earlier incarnations. Read the job log artifacts and step records before you conclude that a job never ran. |
| Attempt 3 | Treated "replacement jobs submitted two minutes after the crash" as recovery in progress and waited. | The replacements ran on the preemptible tier, were preempted three times within their first minutes, and then sat pending for about two hours. New jobs on the protected tier restored capacity in minutes. | Audit the recovery placement against the protected floor. Verify gateway registration and health before you declare recovery. |
| Attempt 4 | Changed one engine flag at a time and resubmitted after each failure. | The engine checks flag combinations after checkpoint verification. Three different conflicts appeared in turn, and each run cost four to thirteen minutes. | Read every constraint in the error text, tabulate the allowed combinations, and pick one measured combination before the next run. Check the rendered launch spec of a waiting job first. |

## Results & Parameters

### Configuration

```yaml
outage_diagnosis:
  accounting_fields: [JobID, Partition, QOS, Account, State, ExitCode, Submit, Start, End, Elapsed, NodeList]
  crash_signature: identical application traceback in two or more dead replica logs, minutes apart
  reclamation_signature: [PREEMPTED state, preemption banner in job log, start-to-cancel in seconds-to-minutes]
  hardware_signature: [NODE_FAIL state, node Reason set, different failure modes per replica]
  startup_failure:
    signature: [FAILED within seconds to ~15 minutes, no registration, same first error on each submission]
    read: first error in the lowest-rank engine log, not the supervisor kill summary
    container_mount: mount source path must exist on the compute node view; restore from the older release copy and verify checksums
    engine_arguments: collect all flag constraints, choose one measured combination, one trial per combination
    breaker: reset after the fix; proof is registration plus one real completion
  recovery_audit:
    compare: [replacement partition, qos, account]
    against: protected floor placement
    complete_when: gateway registration plus health endpoint, not job submission or RUNNING state
```

### Expected Output

- One classification for each dead job: engine crash, scheduler reclamation, or hardware, each with its accounting and log evidence.
- The poison request class, when one exists, and the sibling pools that load the same engine model code and share the exposure.
- A recovery-placement verdict: replacement tier compared with the protected floor, plus the correction when they disagree.
- A recovery declaration bound to gateway registration and health answers, not to job submission.
- For a startup failure: the first error, its class (missing mount source or engine argument conflict), the allowed flag combinations, and the single replica that proves the fix.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production GPU model-serving fleet on a Slurm-style scheduler | Two-replica pool loss within two minutes; identical unhandled application exception in each replica log; three preempted replacement runs; a recovery gap of about two hours closed in minutes by protected-tier submission | Generalized coordinates. See [notes](serving-pool-replica-outage-diagnosis.notes.md). |

## References

- [Slurm walltime expiry outage diagnosis](slurm-walltime-expiry-outage-diagnosis.md): the single-job disappearance branch, planned drain versus crash.
- [Serving-lane zero-floor demotion](serving-lane-zero-floor-demotion.md): replica floor and ceiling policy that defines the protected placement.
- [serving-pool-replica-outage-diagnosis.notes.md](serving-pool-replica-outage-diagnosis.notes.md): privacy-safe source evidence.
