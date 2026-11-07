---
name: inference-gateway-backlog-low-engine-load-diagnosis
license: BSD-3-Clause
description: "Find why an LLM inference gateway rejects or queues requests while dashboards show low engine load. Use when: (1) clients get 429, 408, or 503 from the router, (2) engine load or capacity panels look low or empty, or (3) per-user throughput looks unfair."
category: debugging
date: 2026-11-04
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [inference, gateway, router, admission, queue, "429", "503", dashboard, stale-telemetry, dead-workers, fair-share, gpu-utilization, read-only]
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

### Suggested Approach

- **Stale data.** If the status record is older than its limit, find the reconcile or upload step that stopped. Read the first failing line, not the last. A validation gate that rejects the public projection stops status, autoscale, and metric refresh together. A blocked network path to the ingest service makes uploads time out while the gateway still serves.
- **Dead registrations.** Dead workers inflate the registered count, hide real load behind `-1` metrics, and produce `no_available_workers` or upstream 500 responses when the router picks them. The fix owner is the component that deregisters on job end. Check why health eviction did not remove them.
- **Real saturation.** Compare running requests per replica with the learned knee (the router metric for requests per replica at best throughput). If replicas run at the knee with 100% GPU use, the backlog is a true capacity shortage. Count the replicas that wait in the scheduler queue. Low KV-cache use does not show idle compute.
- **Admission limits.** A 429 that returns in microseconds is an admission rejection, not engine work. Read the queue limit for the request class. A low class limit (for example, the bulk class) rejects work while other classes and the partition have free slots. Models without their own partition share one default partition, so one heavy user can fill it.
- **Per-user fairness.** Check that policy keys match the live pool names. A policy for a pool with zero replicas does not apply to live traffic. Check that the allocator status lists the live models, and that the runtime policy file matches the deployed configuration.
- **Log volume.** Count lines by pattern before you read them. Per-request INFO lines for a polled route and repeated reconcile or deadline lines can make up most of a multi-gigabyte log. Record the dominant pattern and fix it separately.
- If you cannot read a protected route or metric, state the gap and use the open metrics port or the log counters instead. Do not search for credentials.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the load panels | Treated low engine load and low capacity on the dashboard as the cause of the backlog. | The state files had stopped refreshing, 20 of 31 workers reported `-1`, and uploads timed out. | Check data age and worker validity before you read load. |
| Read the first 429 reason | Assumed that a global concurrency cap caused the rejects. | The global cap was far above the load. The class queue limit and real saturation caused them. | Read per-class and per-partition outcome counters. |
| SSH to a compute node | Opened a shell on the node to read GPU state. | Key-based access was refused. | Use the scheduler's overlap exec inside the job allocation. |
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

## References

- [Supervised restart stale worker state guard](supervised-restart-stale-worker-state-guard.md)
- [Inference360 dynamic serving capacity](inference360-dynamic-serving-capacity.md)
