---
name: inference-gateway-backlog-low-engine-load-diagnosis
license: BSD-3-Clause
description: "Find why an LLM inference gateway rejects or queues requests while dashboards show low engine load. Use when: (1) clients get 429, 408, or 503 from the router, (2) engine load or capacity panels look low or empty, or (3) per-user throughput looks unfair, or (4) a latency-sensitive class is rejected while a bulk class holds nearly all slots."
category: debugging
date: 2026-11-04
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: [capacity-starvation, replica-launch-failure, queue-timeout, inference, gateway, router, admission, queue, "429", "503", dashboard, stale-telemetry, dead-workers, fair-share, gpu-utilization, read-only]
---

# Inference Gateway Backlog With Low Engine Load

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-04 |
| **Objective** | Decide whether a gateway backlog comes from real capacity shortage, an admission limit, stale or missing data, or a stalled control plane. |
| **Outcome** | Operational. The method separated four causes that look the same on a dashboard. |

## When to Use

- The router, proxy, or front door shows a backlog or many rejects, but engine load and capacity panels look low.
- Clients get 429 (queue full), 408 (queue timeout), or 503 (no available workers) in large numbers.
- 408 failures concentrate on one model, and the fleet record shows far fewer ready replicas than desired replicas.
- A status command reports the gateway as down while the health route answers.
- One user or one model seems to get less throughput than its configured share.

## Verified Workflow

### Quick Reference

Check these in order. Each check is read-only. Do not restart anything before you finish them, because a restart destroys evidence.

1. **Data age.** Read the age of every state file and telemetry upload that feeds the panels. Stale files and failed uploads show old values, not current load.
2. **Registered workers against the scheduler.** Compare the worker list that the router holds with the replicas that the job scheduler runs. A worker whose job ended, and that still reports health or load of `-1`, is a dead registration.
3. **Engine ground truth.** Run `nvidia-smi` inside a live replica allocation (`srun --jobid=<job> --overlap`). Utilization near 100% and high power draw means the engine is saturated, whatever the panel says.
4. **Router counters by outcome.** Group responses by status and error code. Read the per-partition and per-class admission counters.
5. **Control plane.** Read the supervisor or reconcile log for a repeating failure, and the age of its heartbeat.
6. **Desired against ready replicas.** Chart ready, allocated, and desired replicas per model over the failure window. Align each 408 spike with a drop in ready replicas.

### Suggested Approach

- **Stale data.** If the status record is older than its limit, find the reconcile or upload step that stopped. Read the first failing line, not the last. A validation gate that rejects the public projection stops status, autoscale, and metric refresh together. A blocked network path to the ingest service makes uploads time out while the gateway still serves.
- **Dead registrations.** Dead workers inflate the registered count, hide real load behind `-1` metrics, and produce `no_available_workers` or upstream 500 responses when the router picks them. The fix owner is the component that deregisters on job end. Check why health eviction did not remove them.
- **Real saturation.** Compare running requests per replica with the learned knee (the router metric for requests per replica at best throughput). If replicas run at the knee with 100% GPU use, the backlog is a true capacity shortage. Count the replicas that wait in the scheduler queue. Low KV-cache use does not show idle compute.
- **Capacity starvation from replicas that cannot start.** A 408 is a queue timeout, not an engine error: the request waited longer than the router queue limit for a slot. When ready replicas stay far below desired replicas, the router is healthy and the pool is short. Find out why replacements do not arrive:
  - Count scheduler job outcomes per day for the pool's replica jobs. A day with many FAILED jobs and no new RUNNING job dates the onset. The replicas that still serve are old jobs. Capacity falls each time one ends, and nothing replaces it.
  - Classify the first error of every failed job in bulk, with one search over the per-job rank logs. Do not read one log and generalize. A single repeated first error across all jobs and all pools is a launch-contract defect, not load or hardware. Continue with the startup-failure branch of [serving-pool replica outage diagnosis](serving-pool-replica-outage-diagnosis.md), for example a missing bind-mount source.
  - Read the autoscaler decisions. A hold reason such as a pending-replica limit means that replacements are submitted one at a time. Each deterministic failure then wastes one slot, and the loop never ends by itself.
  - Take the log path from the scheduler job record (`scontrol show job <id>`, the `StdOut` field), not from a filesystem search. A `find` over shared storage passes the tool timeout.
  - Name the heaviest users by their 408 count. A few clients can send most of the traffic, so they see most of the failures even when the cause is shared.
- **Router counter semantics.** Before you quote a failure rate from router counters, compare them with the front-door status-code table. In one case the admitted and interrupted rates were about equal while the success rate was far below the delivered rate of 200 responses. Streamed completions can be counted in other classes. The status-code table gave the usable rate.
- **Admission limits.** A 429 that returns in microseconds is an admission rejection, not engine work. Read the queue limit for the request class. A low class limit (for example, the bulk class) rejects work while other classes and the partition have free slots. Models without their own partition share one default partition, so one heavy user can fill it.
- **Per-tenant queue cap that protects no one.** When one user fills a shared queue and starves others, compare the per-tenant queued-request cap with the size of each queue it applies to: the global queue and every admission-partition queue. A cap stored as an absolute count that is larger than a queue is a no-op, so one tenant can take all of that queue. Do this check before you blame capacity or weights.
  - Store the cap as a percentage of the queue, with an upper bound of 75. Compute the absolute value at render or deploy time for each queue as `max(1, floor(percent * queue_size / 100))`. Never store the absolute count. Reject a percentage above the bound at validation. An unset value resolves to the bound, not to a fixed number.
  - Limit: if the router accepts only one global cap value, a partition queue smaller than that value stays fillable by one tenant. Read the router's own option list or source to see whether a per-partition cap exists. Do not invent a flag.
  - Roll the change out through the gateway's hot (blue/green) reload path, not a cold restart. A running gateway keeps the old value until the reload.
  - Example: a cap of 64 on a partition queue of 32 admits one tenant to 100% of that queue. At 75 percent it becomes 24 for that queue.
  - **When the router has no per-partition cap, enforce fairness at the proxy gate that you own.** Prove the gap first: one user sent almost all requests to one model, most of them got 429 queue-full or 503 capacity-exhausted, and other users were refused too. Then apply these rules. They were implemented and reviewed, but not yet checked under live load:
    - Give each user one FIFO inside the model's wait queue. Serve the user queues round-robin. Give each user a skip flag that is set when the user is new or when another user was admitted while it waited. A request from a flagged user goes first once, and the flag clears. At most one request jumps for each skip, so a lone flood still fills idle slots but cannot hold a new user out.
    - Cap one user at 75 percent of that model's limit (waiting plus in-flight). Apply the cap only to a request that must wait, and only while another user is active. A free slot is always used, and a lone user is never capped.
    - Key the count by user and model. A user at the cap on one model stays free on another model. A shared per-user counter would need atomic create or generation checks, not a file lock. A per-worker count (the cap divided by the worker count, at least 1) is approximate across workers and has no shared state.
    - Do not apply the cap or the jump to private or donated models, or to requests that the reservation router pins to them. Give these requests an exempt user key that does not count as another active user.
    - Refuse with a distinct 429 code and `Retry-After`, not the model-wide capacity code, so a capped user sees a different message from a saturated pool. Add the new counter to every place that merges worker telemetry, or it disappears with more than one worker.
- **Priority classes do not protect a class from a full shared queue.** Read in-flight and queue depth per class and partition. If the bulk class holds nearly all slots and its queue depth exceeds its own class limit, the class limits are soft shares of one queue. A request of any class is rejected when the queue is full, and priority only orders requests that are already waiting. Reservations and a smaller bulk queue limit helped only a little in a scaled test. A separate partition with its own concurrency and queue budget gave a hard guarantee. Bound the bulk class before the shared queue instead when the replicas cannot be split: a per-model in-flight limit at the proxy that answers 429 with a retry delay, plus a client window that backs off. Test the choice first with a real router and mock workers in a scaled partition, with a bulk load far above capacity and a light protected load, and compare the admitted fraction of the protected class.
- **Per-user fairness.** Check that policy keys match the live pool names. A policy for a pool with zero replicas does not apply to live traffic. Check that the allocator status lists the live models, and that the runtime policy file matches the deployed configuration.
- **Log volume.** Count lines by pattern before you read them. Per-request INFO lines for a polled route and repeated reconcile or deadline lines can make up most of a multi-gigabyte log. Record the dominant pattern and fix it separately.
- If you cannot read a protected route or metric, state the gap and use the open metrics port or the log counters instead. Do not search for credentials.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the load panels | Treated low engine load and low capacity on the dashboard as the cause of the backlog. | The state files had stopped refreshing, 20 of 31 workers reported `-1`, and uploads timed out. | Check data age and worker validity before you read load. |
| Read the first 429 reason | Assumed that a global concurrency cap caused the rejects. | The global cap was far above the load. The class queue limit and real saturation caused them. | Read per-class and per-partition outcome counters. |
| SSH to a compute node | Opened a shell on the node to read GPU state. | Key-based access was refused. | Use the scheduler's overlap exec inside the job allocation. |
| Read the router counters as the failure rate | Used the admit, interrupted, and success rates of the router to size the failures. | The counters disagreed with the delivered 200 responses, and the real failures were 408 timeouts from a queue that waited for missing replicas. | Use the status-code table for the rate. Use the replica fleet record to find the cause. |
| Raise capacity or weights for a starved tenant | Treated one tenant filling the shared queue as a shortage of capacity or a weight error. | The per-tenant cap was an absolute count larger than the queue, so it limited nothing. | Compare the cap with each queue size first. Store it as a percentage. |
| Cap one tenant at a percentage of the global queue | Expected the router cap to stop one user from filling a small per-model queue. | The cap came from the 2000-slot global queue, so it was far above the 80-slot model queue and never applied. | Compute the cap from the queue it protects. If the router cannot, enforce it at the proxy gate per model. |
| Send the protected class with a higher priority header | Expected the higher class to be admitted ahead of bulk. | Bulk filled the whole queue, and the new request was rejected as queue full, with the same result as the default class. | Priority orders waiters; it does not make room. Bound bulk first or give the class its own budget. |
| Count log lines in a huge file | Ran a full-file scan. | The command passed the tool timeout. | Take a bounded tail, or run the scan in the background. |

## Results & Parameters

### Configuration

```bash
# GPU ground truth inside a live replica allocation (read-only)
srun --jobid=<replica-job> --overlap -N1 -n1 \
  nvidia-smi --query-gpu=utilization.gpu,memory.used,power.draw --format=csv,noheader

# Router outcome counters (open metrics port; group by status and error code)
curl -s http://<router-host>:<metrics-port>/metrics | grep -E 'http_responses_total|admit_total|partition_(capacity|inflight|healthy_replicas|queue_size_limit)'

# Registered workers that the scheduler does not run
squeue -u <service-user> -h -t R -o "%j %N"   # compare node names with worker URLs
```

### Expected Output

- A named cause with its evidence: stale data, dead registrations, real saturation, an admission limit, or a stalled reconcile.
- A count of each reject type, and the share of workers with `-1` health.
- One tracked issue per distinct cause, with the data that proves it.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal multi-model inference gateway | Backlog with low panel load | The status record was 18 hours old after a validation gate rejected a new directory. 17 of 29 registered workers were dead. Live GPUs ran at 100% and 440 to 460 W. The bulk class queue limit and policy keys for pools with no replicas explained the rejects and the unfair shares. |
| An internal multi-model inference gateway | 408 queue timeouts for one model | Ready replicas fell from a few to none while desired replicas stayed high. Over many hours, every new replica job failed within minutes on one missing container bind-mount source, and the survivors were old jobs. |

## References

- [Supervised restart stale worker state guard](supervised-restart-stale-worker-state-guard.md)
- [Serving-pool replica outage diagnosis](serving-pool-replica-outage-diagnosis.md): classify replica launch failures after this entry shows that ready replicas are below desired replicas.
- [Inference360 dynamic serving capacity](inference360-dynamic-serving-capacity.md)
