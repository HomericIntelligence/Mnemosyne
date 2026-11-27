---
name: supervisor-restart-trigger-vanished-worker
description: "Make a supervisor relaunch a worker when its scheduler job vanishes, not only when its heartbeat goes stale, and recover the claims that a dead worker leaves. Use when a supervised batch worker is cancelled or its allocation ends and queued requests wait for minutes, or when you review a supervisor whose only restart trigger is heartbeat age."
category: architecture
date: 2026-11-27
version: "1.0.0"
user-invocable: false
tags:
  - supervision
  - heartbeat
  - restart-trigger
  - scheduler-job
  - stale-claim
  - worker
  - liveness
---

# Supervisor Restart Trigger Must Cover A Vanished Worker

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-27 |
| **Objective** | Make the restart decision of a worker supervisor correct for every way a worker can die, and leave no request stuck on a claim of a dead worker. |
| **Outcome** | Diagnosed. A worker that a person cancelled was not relaunched until its heartbeat aged out (about ten minutes). Its claim stayed held. The fix is not yet verified in a live run. |

## When to Use

- A supervisor relaunches a worker only when a heartbeat is older than a limit, or only when the scheduler job is not live.
- A worker job was cancelled, preempted, or ended with its allocation, and queued requests stay pending for a full staleness window or longer.
- After a restart, a request still shows a claim from a worker that no longer exists, and no later worker takes it.
- You review a new supervisor loop, a keeper, or a watchdog that reads a heartbeat file.

## Verified Workflow

### Quick Reference

```text
Restart when ANY of these is true (each is a separate signal):
  1. no scheduler job exists for the worker          -> relaunch now
  2. the job exists but is not in a running state    -> relaunch now
  3. the job runs but the heartbeat is older than N  -> cancel it, then relaunch
A fresh heartbeat does not prove that the job lives. A live job does not
prove that the worker makes progress. Use both signals.

On every start, release claims whose recorded owner job no longer exists.
```

### Suggested Approach

1. **List the ways a worker ends.** Normal exit, crash, manual cancel, preemption, allocation end, node loss. For each one, write the heartbeat age that the supervisor sees at the next pass. A cancel leaves a fresh heartbeat. A hang leaves a live job with a stale heartbeat. A heartbeat-only trigger misses the first case for the whole staleness window.
2. **Read job state first, heartbeat second.** Job state answers "does it exist". Heartbeat age answers "does it progress". Check the job state before you trust the heartbeat, and require a heartbeat that is newer than the start of the current job.
3. **Keep one worker at a time.** Before a relaunch, look for a live job with the same name. Use a name check or an exclusive create, not a file lock on shared storage.
4. **Back off on repeated failed starts.** Count a start as failed when the job vanishes with no fresh heartbeat. Double the wait up to a cap. A relaunch loop must not become a submit storm.
5. **Reclaim orphaned claims at worker start.** A claim records its owner job. At start, release each claim whose owner job no longer exists, using an atomic replace or a generation check. Reclaim by owner state, not by file age alone, so a slow live worker keeps its claim. Reclaim the matching owner record too, or the next request for the same target stays blocked.
6. **Test the death shapes through the supervisor path.** Cancel the job: the next pass submits one new job. Stale heartbeat with a live job: cancel and relaunch. Fresh heartbeat with a live job: do nothing. Two quick passes: one job only. Dead owner claim: a new worker completes the request.

If you cannot change the supervisor now, document the window (the staleness limit) as the expected recovery time, and give operators the exact manual relaunch step.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Heartbeat age as the only trigger | The supervisor relaunched only after the heartbeat passed the staleness limit | A cancelled job leaves a fresh heartbeat, so the worker stayed down for the whole window | Add a job-state trigger. Heartbeat age catches hangs, not exits. |
| Job state as the only trigger | The supervisor relaunched only when the job was not live | A live but hung worker was never replaced | Keep the heartbeat trigger for hangs. Use both signals. |
| Trusting the new worker to finish old claims | A new worker started with the old claim files in place | The claim named a dead owner, so the request stayed held | Reclaim claims by owner job state at start. |
| Counting every missing job as one failure | The supervisor treated a clean end like a failed start | Back-off grew when it should not, or never grew when starts failed in a loop | Count a failed start only when the job is gone and no fresh heartbeat exists. |

## Results & Parameters

### Configuration

```yaml
supervisor:
  relaunch_when:
    - job_absent
    - job_not_running
    - heartbeat_older_than: staleness_limit   # also cancel the old job first
  heartbeat_must_be_newer_than: current_job_start
  single_worker: job_name_check
  failed_start_backoff: double_up_to_cap
worker_start:
  release_claims_where: owner_job_absent
  write_method: atomic_replace_or_generation_check
```

### Expected Output

- After a cancel, the next supervisor pass submits one new job. No wait for the staleness limit.
- A queued request that held a dead owner claim completes on the new worker.
- A live worker with a fresh heartbeat is never touched.
- Logs name the reason of each relaunch: absent, not running, or stale.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A batch worker that a keeper supervises as a scheduler job on a shared cluster | A person cancelled the worker. The next pass did not relaunch it until the heartbeat aged out. The old claim stayed held. | The behavior came from reading the keeper rules and one live observation. The fix is not yet verified live. |

## References

- [Give every service one supervision owner](service-supervision-ownership-parity.md) — ownership exists; this entry covers the trigger that owner uses
- [Supervised restart stale worker-state guard](supervised-restart-stale-worker-state-guard.md) — restart succeeds only if leftover state does not poison it
- [Prove liveness before you report an outage](prove-long-running-process-liveness.md)
- [Move a control plane out of an allocation: inventory first](control-plane-allocation-move-inventory.md)
