---
name: prove-long-running-process-liveness
license: BSD-3-Clause
description: "Decide whether a long-running service component is alive before reporting an outage or running disruptive recovery. Use when a log, status file, or poll output stays quiet and you must tell a healthy change-driven process from a stalled one."
category: debugging
date: 2026-10-15
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [liveness, observability, outage-diagnosis, false-alarm, status-file, mtime, error-only-logging, recovery-gating, long-running-process, reconciler]
---

# Prove Liveness Before You Report an Outage

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-15 |
| **Objective** | Decide whether a long-running service component is alive before you report an outage, restart it, cancel its work, or open a page against it. |
| **Outcome** | Operational. A reconciler whose log had not changed for many hours was alive and completing a pass roughly every 30 seconds. The false outage claim was withdrawn before any disruptive action ran. |
| **Verification** | verified-live: each probe below ran against a live component, and the artifact comparison decided the case. See [notes](prove-long-running-process-liveness.notes.md). |

## When to Use

- A component writes only on error or state change, and its log has not changed for a long period.
- You are about to report an outage, restart a service, resize capacity, or cancel work because an output stream stayed quiet.
- A status view reports healthy results, but you cannot tell which process produced them or whether that process still runs.
- An earlier stall or outage claim came from an unchanged timestamp.

## Verified Workflow

### Quick Reference

```bash
# Silence is not evidence. Prove liveness with an artifact the process rewrites.
S=<state-file-the-process-rewrites-once-per-pass>
a=$(stat -c%Y "$S"); sleep 30; b=$(stat -c%Y "$S")
[ "$b" -gt "$a" ] && echo "alive: artifact advanced" || echo "no advance in the interval"
```

### Suggested Approach

1. **Decide whether the output is change-driven.** Many long-running reconcilers log only on error or state change. For those, a quiet log is the normal healthy condition, not a fault.
2. **Find one positive liveness signal.** Use an artifact that the process rewrites on every pass, such as a state file, a lease, a heartbeat record, or a per-pass status document.
3. **Observe that signal across two intervals.** Compare a modification time or a content digest before and after an interval longer than the expected pass period.
4. **Read content, not only the time.** A rewritten value proves the pass produced a new decision. That is stronger evidence than a touched file.
5. **Report the positive signal.** Give the artifact, the interval, and the expected pass period. Put the observed cadence next to the expected one.
6. **Judge a stall only after repeated misses.** A stall needs repeated missed intervals, not one quiet observation.

If no advancing artifact exists, add one before you rely on a log. If the process cannot report at all, use an external check such as a resource counter for the owning account or the process identifier.

Continue when the signal is unavailable. Report the limit. Do not substitute log silence for a signal you could not read.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Inferring an outage from an unchanged log | Reported a reconciler as stalled because its log timestamp stopped advancing | The component writes only on error, so a healthy process is silent while its state file advanced on every pass | Prove liveness with an advancing artifact before you claim a stall |
| Treating a long silence as a measured interval | Waited a fixed number of hours, then acted | The expected pass period was unknown, so the wait established nothing | Compare the observed cadence with the documented period |
| Restarting to test liveness | Restarted a quiet component to see whether it came back | The restart destroyed the evidence and put a healthy service at risk | Read an existing signal before you run a destructive probe |

## Results & Parameters

### Configuration

```yaml
liveness:
  signal: state-file-rewritten-once-per-pass
  observe_intervals: 2
  interval_s: 30
  expected_pass_period_s: 30
```

### Expected Output

- A liveness decision that names the signal it used.
- The observed cadence and the expected pass period, side by side.
- A separate statement for content, so a touched file is not read as a completed pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared inference service deployment | Live supervisor reconciliation after a workload change | The error-only log stayed unchanged for many hours while the state file advanced on every pass. See [notes](prove-long-running-process-liveness.notes.md). |

## References

- [Distinguish progress from termination for delegated work](swarm-agent-status-misread-as-premature-exit.md)