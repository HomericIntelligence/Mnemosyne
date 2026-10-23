# Notes: Cgroup Page-Cache Growth Diagnosis

Supporting evidence for
[cgroup-page-cache-growth-diagnosis](cgroup-page-cache-growth-diagnosis.md).
All identifiers are generalized. The source session used a shared batch-scheduled
cluster with cgroup v2.

## Demonstrated diagnostic chain

1. A Grafana dashboard definition contained a memory-breakdown panel with a series
   labeled `File cache`. The panel query selected a `memory_file_bytes` column from a
   one-minute job rollup table, beside `memory_anon_bytes`, `memory_sock_bytes`, and
   `memory_slab_bytes`.
2. The job monitor read each of these columns out of the job allocation cgroup:
   `memory_file_bytes` came from `memory.stat` field `file`, `memory_anon_bytes` from
   `anon`, `memory_sock_bytes` from `sock`, and slab from `slab` (with a fallback that
   sums `slab_reclaimable` and `slab_unreclaimable`). The same sample recorded
   `memory.current`, `memory.max`, and the `oom` and `oom_kill` events.
3. The monitor located the allocation cgroup by walking up from the process cgroup of
   a job process until the directory named after the job identifier.
4. The job template set a scheduler memory directive (`--mem`) for the service
   allocation, with a comment that the bound is deliberate instead of the full-node
   default. The same allocation rolled up as an `allocation memory max` dashboard
   series. The bound is therefore visible to operators and was part of the answer.
5. A repository search for `memory.reclaim` and `drop_caches` found no writer in the
   service. The reduction path is kernel-managed; no service configuration applies.

## Growth drivers identified on the node

- Seven long-lived components of the job (front, proxy, router, fair-share, monitor,
  supervisor, batch runner) each appended to their own log file under a shared logs
  directory. Log writes are the dominant monotonic driver of the file charge for this
  job shape.
- The same dashboard exposed the correlate signals that separate benign growth from
  pressure: OOM event series, socket memory series, and an open-descriptor series. The
  service-health runbook already keyed on them.

## cgroup v2 semantics used in the answer

- First-toucher charging: a page of page cache is charged to the cgroup of the process
  that touched the file first. Files shared between jobs stay charged to the first
  reader for the life of the page.
- Reclaim order: the kernel reclaims clean page-cache pages before it touches
  anonymous memory. Dirty pages (log writes) become reclaimable after writeback.
  Writeback alone does not remove the charge; the page stays cached.
- Cgroup removal: deleting a cgroup moves its page-cache charges to the parent. A
  restart alone moves the charge. Deletion or truncation of the files plus pressure
  (or `memory.reclaim`) actually frees the pages.
- Targeted relief: `echo <bytes> > memory.reclaim` on the job cgroup asks the kernel to
  reclaim only from that job. The kernel can reclaim less than requested.

## Binding limits

- Evidence came from one cluster with cgroup v2, dashboard rollups at one-minute
  granularity, and a scheduler with per-job memory bounds. Numeric sizes are not part
  of the lesson; they are site operational detail.
- On cgroup v1 the same reasoning applies with different file names (`memory.stat`
  `cache`, `memory.limit_in_bytes`, `memory.force_empty`). Verify the local cgroup
  version before you reuse the paths.
