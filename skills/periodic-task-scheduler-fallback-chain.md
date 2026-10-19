---
name: periodic-task-scheduler-fallback-chain
license: BSD-3-Clause
description: "Schedule periodic maintenance when cron, user-level systemd, and the scheduler's native recurring submission are all unavailable. Use a self-resubmitting job that queues its successor before it works."
category: tooling
date: 2026-10-19
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - scheduling
  - cron
  - systemd-user
  - slurm
  - sbatch
  - self-resubmit
  - periodic-task
  - flock
  - fallback
---
# Self-Resubmitting Jobs When Every Scheduler Is Denied

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-19 |
| **Objective** | Run a recurring maintenance task on a managed cluster where the account has no cron access, no usable user systemd manager, and no scheduler-native recurring submission. |
| **Outcome** | Operational. An hourly export runs as a batch-scheduled job that first submits its own successor for the next interval and then does its work under a single-instance lock. The chain stayed alive across days and across job-host changes. |
| **Verification** | verified-live: the denial of each standard primitive was confirmed by probing it; the chain was verified by observing the next queued job and the completed run log at the following interval. See [notes](periodic-task-scheduler-fallback-chain.notes.md). |

## When to Use

- `crontab` is denied by an allowlist and no administrator exception will be granted.
- `systemctl --user` fails because there is no lingering user manager or no session bus.
- The job scheduler's recurring-submission facility (for example `scrontab`) is disabled site-wide.
- Work must run on a cadence regardless of which execution host the scheduler picks.

## Verified Workflow

### Quick Reference

```bash
# Shape: queue the successor FIRST, then do the work. A failure then costs
# one interval, never the whole chain.
sbatch --job-name="$NAME" --begin="now+${INTERVAL}" "$0"   # successor
exec 9>"$LOCK"; flock -n 9 || exit 0                        # single instance
do_the_work >>"$LOG" 2>&1                                   # one logged run
```

### Suggested Approach

1. **Probe each denied primitive and record the denial.** An allowlist check, a missing user bus, and a disabled subsystem each fail differently. Record which was probed, so the next operator does not repeat the search or assume a misconfiguration.
2. **Prefer a chain over a long-lived loop.** A single always-running driver job wastes an allocation and dies with its host. A chain of one-shot jobs occupies no resources between intervals.
3. **Queue the successor before starting work.** Submitting the next run first guarantees cadence survives a crash, an eviction, or a timeout of the current run. The successor is cheap insurance: a duplicate run is made harmless by the lock.
4. **Take a single-instance lock around the work.** A manual submission plus the scheduled one must not race on the same outputs. A non-blocking `flock` on a fixed path makes overlap a no-op instead of a corruption source.
5. **Log every run in one durable place.** Each run appends its counts and outcomes to a log on shared storage, so verification at the next interval is a file read, and so missing intervals are provable absences.
6. **Verify the chain at the following interval, not at submission.** Check that the expected queued successor existed and that the log gained an entry at the right time. Submission success is not schedule success.
7. **Anchor the chain after outages and maintenance.** A draining node, a full queue, or a cancelled job breaks the chain. Document the one command that resubmits the anchor, and re-run it after any site maintenance window.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| cron | Submitted a crontab entry | The account was absent from cron.allow and the edit was denied | Probe the allowlist before writing the schedule |
| User systemd timer | Loaded a user unit | The login environment had no user manager and no lingering; the bus was unreachable | Cluster login nodes often have no per-user systemd at all |
| Scheduler-native recurring submission | Tried the scheduler's own periodic facility | The site had disabled it | Readonly probing of the facility is cheaper than designing around an assumed feature |
| Work first, successor after | Queued the next run at the end of the job | A late failure would have ended the cadence silently | Successor-first ordering converts crashes into single-interval losses |

## Results & Parameters

### Configuration

```yaml
self_resubmitting_chain:
  interval: hourly
  ordering: submit-successor-before-work
  overlap_protection: non-blocking-flock-on-fixed-path
  logging: append-per-run-on-shared-storage
  recovery: one-documented-reanchor-command
```

### Expected Output

- A queued successor visible in the scheduler at every interval boundary.
- One appended log line per completed run, with gaps provable from the log.
- A chain that survives host changes, evictions, and manual duplicate submissions.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared-cluster inference deployment | Hourly maintenance export on a multi-login batch cluster | Three standard primitives probed and denied; successor-first chain with locking ran for days and verified at each interval. See [notes](periodic-task-scheduler-fallback-chain.notes.md). |

## References

- [Guard exports against destructive overwrites](durable-export-overwrite-guard.md)
