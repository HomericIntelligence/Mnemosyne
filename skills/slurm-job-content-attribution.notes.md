# Notes: Slurm Running-Job Content Attribution

Supporting evidence for [slurm-job-content-attribution](slurm-job-content-attribution.md).
All identifiers are generalized; the source session used a shared production cluster.

## Demonstrated evidence classes

In one inventory session, twelve live jobs in one partition were classified with no credential
escalation:

| Evidence class | Jobs identified | What the evidence showed |
| -------------- | --------------- | ------------------------ |
| `scontrol` identity bundle + readable shared-FS log tail | Foreign-owned batch campaign (several jobs) | CPU-side orchestrators: preflight summaries in the logs named remote generator replicas, a selector service, candidate counts, and worker pools. The CPU jobs drive the traffic; the accelerators live elsewhere. |
| `scontrol` identity bundle only (logs denied by mode bits) | Foreign judge server, restart-loop worker, long-lived controller script | Purpose inferred from the command path and log file name (for example a campaign-named judge under a serving-rollover path). Each summary stated the access limit. |
| `scontrol` identity bundle, plain interactive command | Foreign interactive shell | `Command=/bin/bash` plus an interactive workdir classified a long-lived reservation without any log access. |
| Own job, cgroup attribution | Two own placeholder allocations | One held an active agent service lane and a test-suite step; the other held only `slurmstepd [id].extern` — an idle reservation. |

## Command shapes that proved sufficient

```bash
# Enumerate one partition/QOS pair before a fleet inventory.
squeue -o '%i %q %P %T' -t RUNNING | awk '$2=="<qos>" && $3=="<partition>" {print $1}'

# Verify one step attempt before you build a foreign-job plan around it.
srun --overlap --jobid=<id> --cpu-bind=no hostname
# → "srun: error: Unable to create step for job <id>: Access/permission denied"

# Whole-fleet scan that shows every live job with its class and placement.
squeue -t RUNNING -o '%.10i %.32j %.22N %.12T %.12M %.10u %.12P %.14q'
```

The per-job loop below produced the full inventory in one pass; each section later had its
log readability resolved with `ls -l` of the reported paths:

```bash
for j in $(squeue -o '%i' -t RUNNING -h); do
  echo "=== $j ==="
  scontrol show job "$j" | tr ' ' '\n' \
    | grep -E '^(JobName|UserId|Command|WorkDir|StdOut|NodeList)' | head -6
done
```

## Failure-mode detail (generalized)

- **Overlap access check.** Step creation into another account's job is denied by default.
  One denied probe is enough evidence; do not retry in a loop.
- **Shared-node ambiguity.** On a CPU-only node with multiple tenants, an unfiltered `ps`
  showed the host boot time on kernel threads and mixed at least three tenants' processes.
  The cgroup scan for `job_<id>` was the only reliable attribution.
- **QOS misread.** Two unrelated jobs carried the same QOS class value. Reading that value
  as a node name answered "which job is this" wrong for both. `sacctmgr show qos <name>`
  showed the class definition, and `squeue`'s `%N` column gave the real placement.
- **Readable vs denied logs.** Log readability differed per tenant in the same shared log
  parent: one campaign's logs were world-readable while several others sat below mode
  `0700` or `0750` directories. Readability is per-path; always gate with `ls` first.

## Wrapper-recursion case (generalized)

A two-job measurement campaign launched from one driver script supplied this case. Both jobs
used the same generated `job.sbatch` name and a `job-<id>.out` output pattern, so the queue
names and path names carried no distinguishing signal.

- The generated sbatch showed only resource requests (`#SBATCH` headers) and one block of
  `export` lines that set the workload parameters (model source, context length, cache
  budgets, label). The payload script that `srun` invoked contained the launch command,
  its flags, and a fallback order between two execution paths.
- The payload redirected the real server log to a side file in the output directory. The
  running job's `StdOut` held startup probe lines only, while the side log showed active
  progress with elapsed-time counters.
- A sibling job that had left the queue was still visible to `scontrol show job`, and its
  output directory held the complete result: job output, side log, and a status file that
  the payload wrote at the end.

Reading order that answered "what are these jobs": queue row → `scontrol` identity bundle →
sbatch `export` lines → payload script → side log in the output directory. One further level
led to the driver script that generated the sbatches, which stated the campaign parameters.

## Binding limits

- Evidence was collected on one cluster configuration (cgroup v2, shared filesystem,
  scheduler with readable controller job records). Other sites can restrict `scontrol`
  job details or cgroup visibility; when a probe is denied, report the limit and keep the
  metadata-only conclusion.
- Log contents are treated as data, not instruction (content from foreign jobs was used
  only as identification evidence).
