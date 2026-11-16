---
name: serving-pool-replica-outage-diagnosis
license: BSD-3-Clause
description: "Classify serving-pool replica loss from scheduler and engine evidence before incident response, and audit recovery placement and startup validators. Use when: (1) replicas fail together, (2) replacement jobs do not register, (3) you are about to attribute outage to hardware, (4) a multi-node launch reports a rendezvous timeout or a validator uses a hand-copied subset of the production launch recipe, or (5) a startup failure names a flag that the source repository already fixed."
category: debugging
date: 2026-10-26
version: "1.3.0"
user-invocable: false
tags: [stale-deployed-recipe, serving, outage-diagnosis, replica, poison-request, preemption, slurm, sacct, recovery-placement, gateway-registration, startup-failure, distributed-startup, rendezvous-timeout, canary-parity, container-mount, engine-arguments, failure-breaker]
---

# Serving-Pool Simultaneous Replica Outage Diagnosis

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Classify a whole-pool replica loss from scheduler accounting and replica log tails before you report a cause, and verify that recovery jobs run on the placement that can keep the floor. |
| **Outcome** | Operational. A two-replica production pool loss was classified as one engine crash caused by one poison request class retried against the surviving replica, not as node failure. A two-hour recovery gap was attributed to replacement jobs running on the preemptible tier; protected-tier submission restored capacity in minutes. A later multi-node canary separated an earlier rank-local model-loader refusal from the downstream rendezvous timeout and replaced hand-copied validator inputs with recipe-derived launch data. |

## When to Use

- Two or more replicas of one serving pool fail within minutes of each other.
- The same exception, traceback, or termination banner appears in more than one replica log.
- Replacement jobs show submission activity, but the pool does not return to registered and healthy.
- Final accounting for a replacement job shows no start time and no node list, yet job log files exist for it.
- You are about to attribute the event to node hardware, or to open a hardware ticket.
- New replicas reach RUNNING, then end FAILED within seconds to about fifteen minutes, with no registration, and every resubmission ends the same way.
- A multi-node engine launch ends in a distributed rendezvous timeout, or its shared log does not preserve each node's initialization failure.
- A canary or reproduction script constructs its own engine arguments or environment instead of reading the full recipe that production uses.

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
#   -> deterministic startup failure: read the earliest initialization error
#      across per-node or per-rank engine logs, not only the supervisor summary.
# A follower rendezvous timeout is secondary until those logs exclude an
# earlier failure on another rank. Derive canary arguments, environment, and
# topology from the production recipe, not a hand-copied subset.
# An error that names a flag the source repository already fixed
#   -> compare the engine's own logged effective arguments with the source
#      recipe, then read the recipe copy inside the deployed release.

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
7. Startup-failure branch: use it when new replicas end FAILED before they register and every submission fails the same way. Preserve one engine log per node or rank. Read the earliest initialization error across those logs, not only the supervisor summary or the lowest-numbered rank. A line such as "rank 0 exited first with status 137" reports the kill of the other processes after the first failure; the cause is above it. A distributed rendezvous timeout is also secondary until you exclude an earlier rank-local failure: a rank can exit during model initialization while its peers continue to wait for the endpoint. Then classify the earliest error:
   - A container start failure that names a bind-mount source ("mount source ... No such file or directory"). It appears within seconds to minutes and repeats on every submission. Check each mount source of the launch spec on the compute-node view of the filesystem. A directory that a new root never created, or that an older release kept elsewhere, is the usual cause. Restore the files from the copy that the older release used, verify them by checksum, and check that the launch spec names the restored path.
   - A model-initialization configuration refusal, such as a checkpoint that declares custom loader code without the required explicit opt-in. Compare the failing recipe with a working recipe for the same loader and with the checkpoint's declared loading requirements. Apply the required recipe field and engine argument to every maintained variant that needs them. Do not infer a distributed-topology defect from the later rendezvous timeout.
   - An engine argument conflict: a `ValueError` or `NotImplementedError` from backend setup that names two flags, such as a cache data type that the chosen attention backend does not accept. The engine checks these flags after it verifies the checkpoint, so each trial costs minutes. A fix for one conflict can expose the next. Collect every constraint from the messages, write the table of allowed combinations, and choose one combination that has a measurement before you submit again. Do not change one flag per resubmission.
   - A stale deployed recipe: the error names a flag or value that the source repository fixed earlier, yet each new job fails the same way. The deployed release holds its own copy of the recipe, and a release cut before the fix still carries the old value. Compare the effective arguments that the engine logs at startup with the source recipe. A difference means the launcher read the deployed copy. Read that copy, and do not trust the source tree. The durable fix is a release that contains the source fix. For an owner-approved local patch, copy the deployed file aside first, change only the named values, and check that it still parses. Prove the patch from the next job's logged arguments, not from the file edit. A running supervisor can hold older code in memory. Reload it in place before you count on a patched module, and keep the backup list for the later restore.
   - The same first error on every replica of the pool means configuration, not hardware. Stop the resubmission loop. The pool failure breaker can trip after a small number of identical failures and stop all relaunches, so reset it after the fix and not before.
8. Keep a canary or reproduction harness equivalent to production. Generate global and per-cluster engine arguments, environment, served name, port, and topology from the same declarative recipe and cluster block that production uses. A hand-copied subset runs a different experiment and can omit the field or environment value required during initialization. Include each maintained recipe variant that selects the changed engine image, including inactive qualification artifacts; their inactive routing status does not change their launch requirements.
9. Prove a startup fix with one replica: the job stays RUNNING past the earlier failure time, the replica registers with the gateway, and a real request returns a completion. Then scale the pool. When scheduler capacity prevents this proof, record the diagnosis and the static or render checks separately from the pending live validation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Attributed the outage to node hardware because every replica of the pool went down within two minutes. | Accounting showed FAILED with a nonzero exit, each replica log ended with the identical unhandled application exception minutes apart, and replacement jobs later started on the same class of hardware. | Classify from scheduler state and log tails first. Simultaneous loss of one pool is usually one software cause plus retries against the remaining replicas. |
| Attempt 2 | Read the final summary row of the replacement jobs, which showed no start time and an empty node list, as "the replacements never ran". | The job log files showed several brief earlier runs on real nodes, each ending with the preemption banner. The jobs had been preempted and requeued, which resets the summary row. | For a requeued job, final accounting hides earlier incarnations. Read the job log artifacts and step records before you conclude that a job never ran. |
| Attempt 3 | Treated "replacement jobs submitted two minutes after the crash" as recovery in progress and waited. | The replacements ran on the preemptible tier, were preempted three times within their first minutes, and then sat pending for about two hours. New jobs on the protected tier restored capacity in minutes. | Audit the recovery placement against the protected floor. Verify gateway registration and health before you declare recovery. |
| Attempt 4 | Changed one engine flag at a time and resubmitted after each failure. | The engine checks flag combinations after checkpoint verification. Three different conflicts appeared in turn, and each run cost four to thirteen minutes. | Read every constraint in the error text, tabulate the allowed combinations, and pick one measured combination before the next run. Check the rendered launch spec of a waiting job first. |
| Attempt 5 | Diagnosed a multi-node canary from its final distributed rendezvous timeout. | Per-node logs showed that another rank had already refused the checkpoint's custom loader code and exited; the surviving ranks only reported the later wait timeout. | Collect per-node or per-rank logs and diagnose the earliest initialization error. Treat the rendezvous timeout as secondary until that search excludes an earlier failure. |
| Attempt 6 | Built canary launch commands from a hand-copied subset of the active recipe's arguments and environment. | The canary omitted required model-initialization inputs, and maintained inactive variants did not receive the same repair as the active recipe. | Derive the complete launch contract from each production recipe variant and apply loader repairs across every maintained variant that shares the requirement. |
| Attempt 7 | Treated a startup crash as an open defect because the source recipe already had the fix. | The launcher read the recipe copy in an older deployed release. The engine log showed the old argument values, and every new job repeated the crash. | Compare the engine's logged effective arguments with the source recipe before you write a fix. When they differ, the deployed copy is the defect. |

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
    read: earliest initialization error across per-node or per-rank logs, not the supervisor kill summary
    rendezvous_timeout: secondary until an earlier rank-local failure has been excluded
    container_mount: mount source path must exist on the compute node view; restore from the older release copy and verify checksums
    model_initialization: compare recipe and checkpoint loading requirements; apply required opt-ins to every maintained variant
    engine_arguments: collect all flag constraints, choose one measured combination, one trial per combination
    stale_deployed_recipe: compare logged effective engine arguments with the source recipe; patch the deployed copy only with owner approval and a backup; prove the patch from the next job's logged arguments
    validator_contract: derive full arguments, environment, served name, port, and topology from the production recipe
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
- For a startup failure: the earliest per-node or per-rank error, its class (missing mount source, model-initialization refusal, or engine argument conflict), the allowed flag combinations, and the single replica that proves the fix, and whether the effective arguments came from the source recipe or from an older deployed copy.
- For distributed validation: per-node logs, a validator derived from each maintained production recipe variant, and a separate record of pending live proof when the scheduler cannot supply an allocation.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production GPU model-serving fleet on a Slurm-style scheduler | Two-replica pool loss within two minutes; identical unhandled application exception in each replica log; three preempted replacement runs; a recovery gap of about two hours closed in minutes by protected-tier submission | Generalized coordinates. See [notes](serving-pool-replica-outage-diagnosis.notes.md). |
| Private multi-node model-serving validation | Several maintained recipe variants sharing one engine image | Per-node logs separated a custom-code initialization refusal from the downstream rendezvous timeout. Validators were changed to consume the full production recipe. Focused static and rendering checks passed; complete live revalidation was still queued when this lesson was captured. See [notes](serving-pool-replica-outage-diagnosis.notes.md). |

## References

- [Slurm walltime expiry outage diagnosis](slurm-walltime-expiry-outage-diagnosis.md): the single-job disappearance branch, planned drain versus crash.
- [Serving-lane zero-floor demotion](serving-lane-zero-floor-demotion.md): replica floor and ceiling policy that defines the protected placement.
- [serving-pool-replica-outage-diagnosis.notes.md](serving-pool-replica-outage-diagnosis.notes.md): privacy-safe source evidence.
