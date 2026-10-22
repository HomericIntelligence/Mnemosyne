---
name: slurm-walltime-expiry-outage-diagnosis
license: BSD-3-Clause
description: "Classify the disappearance of a scheduler-managed service as a planned walltime drain or a crash before incident response. Use when: (1) a replica or worker goes down at a round clock time or near its start time plus the time limit, (2) scheduler accounting shows CANCELLED steps and a clean parent exit with no error reason, or (3) the service has a renewal mechanism that may have failed silently."
category: debugging
date: 2026-10-22
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [slurm, walltime, time-limit, outage-diagnosis, sigterm, drain, sacct, timezone-conversion, lease-renewal, recycling]
---

# Slurm Walltime Expiry Outage Diagnosis

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Decide whether a scheduler-managed service disappearance is the planned time-limit drain or a crash, before you report an outage or start crash forensics. |
| **Outcome** | Operational. A replica reported down at a round local clock time was a healthy job drained at its multi-day time limit: SIGTERM at the limit boundary, a graceful drain, and a clean exit. The renewal path had failed silently, so no replacement allocation existed. |
| **Verification** | verified-live from scheduler accounting, service logs, and status records during an incident review. Coordinates are generalized. See [notes](slurm-walltime-expiry-outage-diagnosis.notes.md). |

## When to Use

- A user reports that a scheduler-managed worker or replica went down at a specific wall-clock time.
- The down time is near the job's start time plus its time limit, or near a round clock boundary.
- Accounting shows the job COMPLETED or TIMEOUT, steps CANCELLED with a signal, and no error reason.
- You are about to search node, GPU, or service logs for a crash before you check scheduler accounting.
- A service that should renew its allocation stayed down after the event.

## Verified Workflow

### Quick Reference

```bash
# Compare elapsed time with the limit before any crash hypothesis.
sacct -j <job-id> --format=JobID,State,ExitCode,Reason,Start,End,Elapsed,Timelimit
# Walltime drain signature: Elapsed ~= Timelimit (within drain grace),
# parent COMPLETED/TIMEOUT with exit 0:0, steps CANCELLED by signal 15, Reason empty.

# Convert a reported local time with both DST variants before log correlation.
TZ=America/Los_Angeles date -d '2026-10-16 18:20' -u   # Pacific reports PDT (UTC-7) in October
```

### Suggested Approach

1. **Convert the reported time first.** Users report local times ("6:20 pm"). Scheduler records and logs use UTC or a site zone. When the zone arrives as an abbreviation (for example "PST" during daylight-saving months), compute both the standard and the daylight variant and search the union window. A one-hour error can place the event outside the evidence.
2. **Pull scheduler accounting before any log forensics.** Collect state, exit code, reason, start, end, elapsed, and time limit for the job and its steps.
3. **Compare elapsed with the limit.** Elapsed approximately equal to the limit (within the scheduler's drain grace) supports planned expiry. Elapsed far below the limit rules walltime out; continue crash diagnosis.
4. **Read the termination signal and exit state.** Steps CANCELLED with signal 15, an empty reason, and a parent that ends COMPLETED with exit code 0:0 form the scheduler's own graceful cutoff. A non-zero exit, an error reason, or an out-of-memory or hardware marker indicates a fault.
5. **Confirm the drain signature in the service log.** A planned drain shows a TERM-receipt line, graceful drain messages (stop new work, deregister or remove workers), and a clean final exit within the grace period. A crash shows traces or abrupt log truncation instead.
6. **Check the renewal mechanism after an expiry classification.** A persistent service should replace its allocation before the limit. Inspect pool, registry, or status records for a blocked renewal (for example, a recorded lease-refresh failure). A walltime kill of a long-lived service usually means the renewal path failed silently; that failure, not the drain, is the defect to fix next.
7. **Report the classification with its evidence.** Give elapsed versus limit, the signal and exit state, the drain or crash log signature, and the renewal-mechanism health with any follow-up defect.

If accounting is unavailable, classify from the service-log drain signature alone and mark the result provisional: only accounting binds the event to the limit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Log forensics first | Searched service and node logs for a crash signature before checking scheduler accounting | The logs held a clean SIGTERM drain with no error; the cause was visible only in accounting | Pull accounting first; it classifies terminal events directly |
| Single-offset timezone conversion | Mapped the reported local time onto UTC with one assumed DST offset | The assumed offset placed the event an hour away, and no evidence matched at that time | Compute both DST variants of a zone abbreviation and search the wider window |
| Operator-kill assumption | Read CANCELLED steps and the parent's clean exit as a manual kill by an operator | The steps ended by signal 15 with elapsed equal to the time limit, which is the scheduler's drain pattern, not human action | Let the elapsed-versus-limit comparison and the termination signal attribute the kill |

## Results & Parameters

### Configuration

```yaml
walltime_diagnosis:
  accounting_fields: [JobID, State, ExitCode, Reason, Start, End, Elapsed, Timelimit]
  drain_signal: 15                # SIGTERM recorded on the job steps
  match_grace_minutes: 30         # elapsed within this of the limit supports planned expiry
  tz_variants: [standard, daylight]  # evaluate both when the zone abbreviation is ambiguous
```

### Expected Output

- A classification line: planned walltime expiry or crash, with the measured elapsed and limit values.
- The terminating signal and exit state from accounting.
- The drain or crash log signature that corroborates the classification.
- A renewal-mechanism health statement, with the follow-up defect when renewal is blocked.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Project-neutral scheduler-backed serving pool | Incident review of a replica reported down at a round local clock time | Accounting showed elapsed equal to a multi-day limit, a SIGTERM drain, and a clean exit; status records showed a blocked lease refresh. See [notes](slurm-walltime-expiry-outage-diagnosis.notes.md). |

## References

- [Scheduler service replacement identity continuity](scheduler-service-replacement-identity-continuity.md)
- [Prove liveness before you report an outage](prove-long-running-process-liveness.md)
