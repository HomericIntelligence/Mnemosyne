---
name: lease-clock-starts-at-work-start
license: BSD-3-Clause
description: "Start a time-limited grant, lease, or duration when the work really begins, not when the request is admitted. Use when: (1) a service grants a lease or authority with a duration and the work first waits in a batch-scheduler queue, (2) every grant expired with no proof, nonce, or command recorded while the job was still queued, (3) a deregister of a registration that never started leaves it draining forever, or (4) an operator asks why a queued registration shows no worker state."
category: architecture
date: 2026-11-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [lease, expiry, authority-clock, batch-scheduler, queue-wait, pending-state, deregister, walltime, grant]
---

# Lease Clock Starts At Work Start

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Make a time-limited authority last for the work, not for the wait before the work. |
| **Outcome** | Operational. A pending state with no clock, a clock that starts at the first proof from the running worker, and a direct end for a registration that never started. |

## When to Use

- A service admits a request and starts a lease or duration at once, but the work waits in a scheduler queue first.
- All grants end as expired, with no nonce, no proof, and no command recorded, while the job is still queued.
- A deregister request on a registration with no running worker leaves it in a draining state, and a new register by the same owner is refused.
- An operator needs to know why a registration is quiet, and the service has no authority over the scheduler.

## Verified Workflow

### Quick Reference

```text
Admitted, no worker yet:  state = pending, NO clock.
First proof from worker:  start lease and requested duration now (scheduler allocation start).
Deregister while pending: end it directly. No worker exists to drain it.
Queue wait:               do not add a new timer; the existing duration already bounds the wait.
Status:                   show the scheduler's own job state and reason, read with the user's access.
```

### Suggested Approach

1. Find where the clock starts. If it starts at admission, compare it with the time the work can first run. When a queue sits between them, the lease can expire before the first proof.
2. Add a pending state. In this state the record holds the requested duration but no start time and no expiry.
3. Start the clock at the first proof from the running worker. Use the scheduler allocation start as the time base. This matches scheduler walltime semantics, where queue time never counts.
4. Do not add a separate queue-wait timer. A bound already exists, because the scheduler job has its own limits. A second arbitrary timer can expire valid work again.
5. Give a never-started registration a direct end on deregister. The drain path waits for a worker to acknowledge, and no worker exists. Without a direct end, the record stays in draining state and blocks a new register by the same owner.
6. Keep the service free of scheduler authority. Let the client status command read the job state and reason with the user's own scheduler access, and print them next to the service state.
7. Test the behavior: a grant that stays pending longer than its duration is still valid at first proof; the lease and expiry start from that proof; a deregister in pending state ends the record at once.

If the first proof is not available, keep the pending state and report the scheduler state. Do not guess a start time.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Start the lease at admission | Set expiry to admission time plus the requested duration. | The job waited in the queue longer than the duration. Every grant expired with zero proofs. | The clock must count run time, not wait time. |
| Add a queue-wait timeout | Considered a second timer for the pending state. | The duration already bounds the wait. A second value is arbitrary and can expire valid work. | Reuse the existing bound. |
| Drain on deregister while pending | Sent a drain request for a record with no worker. | No worker could acknowledge it, so the record stayed draining and blocked a new register. | End a never-started record directly. |

## Results & Parameters

```yaml
pending_state:
  lease_start: null
  expiry: null
first_proof:
  lease_start: scheduler_allocation_start
  expiry: lease_start + requested_duration
deregister_while_pending: end_directly
```

Failure signature that exposes the defect: grants all lost, with no nonces, no proofs, and no commands recorded.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private service (identifiers withheld) | A lease service in front of a batch scheduler | The fix was designed from a live failure where all grants expired in the queue. |

## References

- Related: `slurm-walltime-expiry-outage-diagnosis`
- Related: `slurm-queued-srun-timeout-false-failure`
