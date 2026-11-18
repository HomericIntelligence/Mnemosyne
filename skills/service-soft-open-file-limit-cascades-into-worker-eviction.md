---
name: service-soft-open-file-limit-cascades-into-worker-eviction
license: BSD-3-Clause
description: "Find and fix a long-running network service whose soft open-file limit is too low. Use when: (1) health probes of backend workers fail with a connect or DNS error that says 'Too many open files', (2) a router reports 'all workers unavailable' or a circuit breaker opens while the workers run, (3) healthy capacity swings up and down within minutes while load is flat, (4) a supervisor cancels or evicts replicas that serve traffic, or (5) a service started from a scheduler batch script shows a soft limit of 1024."
category: debugging
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags: ["file-descriptors", "ulimit", "prlimit", "health-check", "circuit-breaker", "scheduler", "gateway"]
---

# Soft Open-File Limit Cascades Into Worker Eviction

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Trace queue-full, worker-unavailable, and eviction symptoms to descriptor exhaustion, and fix it without a restart. |
| **Outcome** | Operational. After the soft limit was raised, healthy capacity stayed flat and the queue drained in the minutes that followed. |

## When to Use

- A router log shows health-probe failures such as `dns error ... Too many open files` (errno 24), not a refused or timed-out connection.
- Clients get 'all workers unavailable' or 'queue is full' while the backend engines are up and mostly idle.
- Healthy-worker capacity falls to near zero and recovers within minutes, and the queue fills each time it falls.
- A watchdog cancels replicas after a router drops them, and the cancelled replicas were serving.
- The service was started by a scheduler batch script, not by an interactive shell.

## Verified Workflow

### Quick Reference

```bash
pid=<router-or-proxy-pid>
grep 'open files' /proc/$pid/limits   # soft vs hard
ls /proc/$pid/fd | wc -l              # descriptors now open
prlimit --pid $pid --nofile=<hard>:<hard>   # raise a running process, no restart
```

In the service start script, before any child starts: `ulimit -Sn "$(ulimit -Hn)"`.

### Suggested Approach

1. **Confirm the cause.** Search the router log for `Too many open files`. Read the soft limit and the open count of the router, the front door, and the proxy. A count at the soft limit confirms it. Healthy capacity is a gauge that the router derives from health probes, so a swing in capacity with flat load points at probe failures first, not at the engines.
2. **Find where the limit dropped.** An interactive shell can show a high limit (for example 131072) while the same service shows a soft limit of 1024. Walk the parent chain with `/proc/<pid>/limits`. In the verified case the scheduler's step daemon had a high limit and the batch script below it had 1024. Every child inherits the lower value.
3. **Raise the running process first.** `prlimit` with soft not above hard works for a process of the same user and takes effect at once. Raise to the hard limit. A smaller step (double the soft limit) only buys time, because a process that was starved for descriptors uses more once it can.
4. **Fix the start path.** Raise the soft limit to the hard limit at the top of the start script, so every child inherits it. A container started by a scheduler step can start with its own soft limit, so also raise it in the shell inside the container, before the service starts. Make the raise non-fatal, and log the resulting limit.
5. **Check for `select()` first.** A soft limit above 1023 breaks code that uses `select()` on descriptor numbers above 1023. Search for `select.select`, `select.poll`, explicit `SelectSelector`, and descriptor-range loops. `selectors.DefaultSelector()` is `epoll` on Linux and has no such limit. Event-loop servers and Rust async runtimes use `epoll`.
6. **Repair the follow-on damage.** A watchdog that cancels a replica because the router dropped its worker acts on the router's view. Probe the replica engine directly before a cancel, and treat a probe timeout as unknown, not dead. A readiness count that subtracts queued jobs from a total can show zero while replicas serve. Count running and registered replicas directly.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Raise queue sizes after the 'queue is full' reports | The queue filled because healthy capacity collapsed, so a larger queue only delayed the rejections | Read the capacity gauge and the router log before sizing queues. |
| 2 | Run the test file for the changed script with stop-at-first-failure | It stopped at one failure and hid the others | Run the whole affected test file without stop-at-first-failure. |
| 3 | Prefix the container command with the limit raise | A test that read the first word of the command as the interpreter now read the prefix | When a prefix changes a command, update tests that parse the command, and keep the contract they check. |

## Results & Parameters

### Configuration

```bash
# top of the service start script (non-fatal, logged)
ulimit -Sn "$(ulimit -Hn)" 2>/dev/null || echo "could not raise the open-file limit" >&2
echo "open-file limit $(ulimit -Sn)/$(ulimit -Hn)" >&2

# inside a container started by a scheduler step
bash -c 'ulimit -Sn "$(ulimit -Hn)" 2>/dev/null; exec <service command>'
```

### Expected Output

- `grep 'open files' /proc/<pid>/limits` shows the soft limit equal to the hard limit.
- The open-descriptor count rises above the old limit and stays well under the new one. In the verified case it went from 1024 of 1024 to about 1600 and then settled.
- Health probes stop failing, healthy capacity stays flat, and the queue drains.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal inference gateway run as a scheduler job | Queue-full and worker-unavailable errors under a batch surge | A router at 1024 of 1024 descriptors failed its health probes. A watchdog then cancelled replicas that served. |

## References

- [shared-fs-hang-diagnosis-from-allocation](shared-fs-hang-diagnosis-from-allocation.md)
- [inference-gateway-backlog-low-engine-load-diagnosis](inference-gateway-backlog-low-engine-load-diagnosis.md)
