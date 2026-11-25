---
name: identify-before-cancelling-scheduler-steps
license: BSD-3-Clause
description: "Attribute each apparently orphaned scheduler step or process to its owner before you cancel it, and prove the data path after the cleanup. Use when old-looking steps in a shared allocation block a new launch (for example accelerator memory that stays in use), or when a front-door health check stays green after a cleanup."
category: debugging
date: 2026-11-25
version: "1.0.0"
user-invocable: false
tags:
- scheduler
- slurm
- cleanup
- orphan-process
- cancel
- health-check
- data-path
- outage-detection
---

# Skill: identify-before-cancelling-scheduler-steps

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Do not cancel a live component of a service while you clean up apparent leftovers, and detect the damage fast when it happens |
| **Outcome** | Operational. One cleanup cancelled the router of a running service. The front door stayed healthy, so the outage stayed unseen for hours. |

## When to Use

- A new launch fails because an older process holds a scarce resource (accelerator memory, a port), and the same allocation lists old-looking steps or processes.
- You are about to cancel steps, kill processes, or delete job records because they look stale, orphaned, or "left over".
- Several steps have the same generic name (for example the name of a shell), so the name does not show which component owns them.
- A cleanup is done and the service front door or proxy still reports healthy.
- A supervisor log repeats one recovery warning (for example "hand off to a fresh generation") with no new progress.

## Verified Workflow

### Quick Reference

```bash
# 1. List every step with start time, node, name, and requested CPUs.
squeue -s -h -j <job> -o "%i %j %N %S %C"
# 2. Attribute each candidate before you cancel it.
scontrol show step <job>.<step>                 # command, nodes, resources
nvidia-smi --query-compute-apps=pid,used_memory --format=csv   # on the node
cat /proc/<pid>/cgroup                          # which step owns the holder pid
# 3. Cancel only the steps that own a proven stale holder. Then probe the data path.
```

### Suggested Approach

1. **Attribute before you cancel.** A step is an orphan only when its parent unit (the step or job that launched it) is gone. A step that started at the same moment as a service component, with a generic name, is probably part of that component. Age and name alone do not prove a leftover.
2. **Find the proven holder.** For a blocked resource, list the process ids that hold it. Map each pid to its step through the process cgroup. Cancel only the steps whose cgroup holds a stale pid, and only after you confirm that the launching unit has ended.
3. **Prefer the narrowest cancel.** Cancel one attributed step. Do not cancel by name pattern, by age, or by "all steps except the ones I know".
4. **Probe the data path after the cleanup.** A front door can stay healthy while the router behind it is dead. Check, in this order: the listener port of each component on its node, the router readiness endpoint with its worker count, and one real request. The check passes only when the worker count equals the expected count.
5. **Read the recovery loop.** If a supervisor repeats one recovery warning, recovery has failed. Read the first distinct error before the repeats. A recovery path can be blocked by an unrelated identity check.
6. **Restore through the owner's path.** If a component died, restart it with the supported restart verb. Do not start it by hand, because a hand start skips the records that the restart verb writes.

### Decision table

| Evidence | Action |
| ---------- | -------- |
| Step started with the service start, generic name, parent alive | Treat as a component. Do not cancel. |
| Step owns a pid that holds the blocked resource, and its launching unit has ended | Orphan. Cancel that one step. |
| Step is old, but nothing proves who owns it | Leave it. Find the owner first. |
| Front door healthy, router port closed or worker count low | Outage. The cleanup or another change broke a component. |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Cancel by age and name | Cancelled several old steps with a generic name, because a launch failed on a busy accelerator. | One step was the router of the running service, started with it. The router died and every replica failed to register. | Attribute each step first. Generic names and age do not show ownership. |
| Front-door health as proof | Treated a healthy proxy response after the cleanup as proof that the service worked. | The proxy ran in a different process from the dead router, so it stayed healthy for hours. | Probe the router listener, worker count, and a real request. |
| Wait for the supervisor | Assumed the supervisor would restart the killed component. | The restart path was blocked by an identity check, and the supervisor repeated one warning hundreds of times. | A repeated recovery warning means recovery has failed. Read the first distinct error. |

## Results & Parameters

### Configuration

```bash
# Data-path probe after any cleanup (replace the placeholders).
curl -s http://<router-host>:<router-port>/readiness      # status and healthy worker count
ss -ltn | grep ":<router-port> "                          # listener on the node
```

### Expected Output

- Each component listener port is open on its node.
- The router readiness reports `ready` and `healthy_workers` equal to `total_workers`, with the expected models listed.
- One real request returns a normal response.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared GPU cluster, one service allocation | A cleanup of steps that looked like leftovers of replica jobs cancelled the router of the live gateway | Replicas stayed up but unrouted until the next restart. |

## References

- [prove-long-running-process-liveness](prove-long-running-process-liveness.md)
- [serving-pool-replica-outage-diagnosis](serving-pool-replica-outage-diagnosis.md)
- [backup-before-state-mutation](backup-before-state-mutation.md)
