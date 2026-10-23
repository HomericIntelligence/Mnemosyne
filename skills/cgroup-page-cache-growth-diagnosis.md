---
name: cgroup-page-cache-growth-diagnosis
license: BSD-3-Clause
description: "Explain and bound a monotonically growing file-cache or page-cache memory metric for a long-lived job or service. Use when: (1) a dashboard shows file cache growing with uptime and an operator asks why it is so large, (2) you must state whether the growth has an upper bound and what makes it reduce, (3) you suspect an application cache leak but cannot find a cache configuration, or (4) you must decide between benign kernel behavior and internal growth that needs investigation."
category: debugging
date: 2026-10-23
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - cgroup
  - page-cache
  - file-cache
  - memory-accounting
  - monitoring
  - grafana
  - memory-leak
  - slurm
---

# Cgroup Page-Cache Growth Diagnosis

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Decide whether a growing file-cache metric for a job or service is a defect, and state its bound and its relief mechanism from the collector source of the metric. |
| **Outcome** | Successful. The metric was traced from the dashboard panel to the cgroup v2 `memory.stat` `file` counter of the job. The growth was reclaimable kernel page cache charged to the job, not an application cache. The bound and the reduction mechanism needed no application change. |
| **Verification** | verified-local on a shared batch-scheduled cluster with cgroup v2 and dashboard-backed job rollups. |

## When to Use

- A monitoring dashboard shows a memory series named `file cache` (or page cache) for a long-lived job or service. The series grows with uptime and does not come down on its own.
- A person asks why the cache is so large, whether it has an upper bound, and how it reduces.
- You suspect an application-managed cache, but a search for `filecache`, cache directories, or eviction settings finds no such component.
- You must decide whether the observation is benign or a case of internal growth that needs investigation.

Do not use this entry for these intents:

- Application-level caches that an application must evict itself, for example an in-process LRU or the prefix KV cache of an inference engine.
- GPU or accelerator memory growth.

## Verified Workflow

### Quick Reference

Trace the metric to its kernel source before you diagnose:

```bash
# 1. In the dashboard definition, find the series and its query column.
grep -n '"File cache"' <dashboard>.json
#    -> the panel query shows a rollup column, for example memory_file_bytes.

# 2. In the collector source, resolve that column to its kernel counter.
grep -rn 'memory_file_bytes' <collector-source>
#    -> typically: stat.get("file") from the job cgroup memory.stat (cgroup v2).

# 3. On the node, read the job cgroup directly. Get the path from /proc/<pid>/cgroup.
grep -E '^(file|anon|sock|slab) ' /sys/fs/cgroup/<job-cgroup>/memory.stat
cat /sys/fs/cgroup/<job-cgroup>/memory.current /sys/fs/cgroup/<job-cgroup>/memory.max
cat /sys/fs/cgroup/<job-cgroup>/memory.events
```

Decision rule: `file` is page cache that the kernel charged to the cgroup by first touch.
It is reclaimable. Only `memory.max` bounds it, as one component of `memory.current`.
It reduces when the kernel reclaims clean pages because anonymous memory or host pressure
needs the space.

### Suggested Approach

1. Identify what the series counts. A dashboard label is product vocabulary, not kernel
   semantics. Follow the chain: label -> query column -> collector field -> kernel
   counter. On cgroup v2 job rollups, a label of `file cache` or `page cache` maps to
   `memory.stat` `file` in almost all cases.
2. Explain the growth drivers. The kernel charges a cached page to the cgroup whose
   process touched the file first. A long-lived job that reads state, records, and model
   or configuration data accumulates charge. The dominant monotonic driver is the job's
   own log files: each appended byte passes through the page cache and stays charged to
   the job. The kernel keeps these pages while free memory exists. This growth is the
   use of spare memory, not a leak.
3. State the bound. There is no dedicated file-cache limit. `file` is one component of
   `memory.current`, and `memory.max` bounds the total. The job's scheduler memory
   request (for example the `--mem` directive of a batch allocation) usually sets this
   value. Report the actual value of `memory.max` to the requester.
4. State the relief mechanism. Clean page cache is the first reclaim victim when the
   allocation comes near `memory.max` or when the host has memory pressure. Dirty pages
   become reclaimable after writeback. Deletion or truncation of the charged files (log
   rotation with cleanup) frees the pages at the next eviction. A job restart starts a
   fresh cgroup; the old charges move to the parent cgroup and are reclaimed when the
   files are deleted or no longer referenced. To force reclaim without a restart on
   cgroup v2, write a byte count to `memory.reclaim` of the job cgroup. A node-wide
   `drop_caches` write is a blunt instrument that needs root; do not make it the
   routine answer.
5. Give the decision boundary. Treat the growth as benign when `oom` and `oom_kill` in
   `memory.events` stay at zero, anonymous RSS stays stable, and traffic or a deployment
   explains the log-write rate. Investigate when OOM events increase, when anonymous,
   socket, or slab memory grows with request pressure, or when the log-write rate grows
   without a traffic or deployment explanation.
6. Do not prescribe an application cache-eviction setting, a cache-size configuration, or
   a periodic restart as the fix for a cgroup `file` charge. None exists because no
   application cache is involved. Change an identified driver only when investigation
   shows one, for example an unjustified log verbosity.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Searched the service source for the application cache behind the metric: `filecache`, `file_cache`, cache-directory variables, and eviction settings. | No application cache existed for the series. The only matches were unrelated vendor patches. | A dashboard label that names a cache need not map to any application component. Resolve the series to its collector field and its kernel counter first. |
| Attempt 2 | Looked for the upper bound and eviction policy of the cache in the service configuration and job templates. | No bound or policy existed there. Nothing in the repository wrote a reclaim control. | For a cgroup `file` charge, the effective bound is the job cgroup `memory.max`, and the relief is kernel reclaim. The service configuration surface is the wrong place to look. |
| Attempt 3 | Classified the monotonic growth itself as a leak that needs a restart or a code fix. | The counter only records pages the kernel kept while memory was free. The series drops again when pressure arrives, so the growth has a benign kernel explanation. | Test the kernel-accounting hypothesis before the leak hypothesis. OOM counters and the anonymous-memory trend, not the file-cache trend, decide the verdict. |

## Results & Parameters

### Configuration

Cgroup v2 files of the job cgroup to read:

```text
memory.stat        # file, anon, sock, slab (or slab_reclaimable + slab_unreclaimable)
memory.current     # current total charge
memory.max         # the effective bound for the job
memory.events      # oom, oom_kill counters; the real pressure signal
memory.reclaim     # write-only: requested targeted reclaim in bytes
```

Counter meanings:

- `file`: page cache, charged to the first-toucher cgroup. Reclaimable.
- `anon`: process heap and stacks. Not reclaimable. The leak signal.
- `sock`: kernel memory for network sockets. Grows with request pressure.
- `slab`: kernel object memory, partly reclaimable.

### Expected Output

- A verdict in one line: benign page-cache charge, or internal growth, with the counter
  evidence for each verdict.
- The bound: the value of `memory.max` for the job, and the share of `memory.current`
  that `file` holds.
- The relief statement: automatic kernel reclaim, plus the concrete manual options
  (file deletion or rotation with cleanup, `memory.reclaim`, or a planned restart) and a
  condition for each.
- The watch items: `memory.events` OOM counters, the trend of `anon`, `sock`, and `slab`,
  and the log-write rate compared with traffic.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A batch-scheduled inference-serving control plane on a shared cluster | Operator question about a dashboard `File cache` series that grew on a long-lived gateway-role job | See [notes](cgroup-page-cache-growth-diagnosis.notes.md). |

## References

- [The kernel documentation: Control Group v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [slurm-job-content-attribution](slurm-job-content-attribution.md)
