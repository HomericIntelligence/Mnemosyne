---
name: slurm-job-content-attribution
license: BSD-3-Clause
description: "Identify what a live Slurm job executes, for your own allocations and for jobs owned by other accounts. Use when: (1) srun --overlap is refused for a job you must inspect, (2) an --overlap shell lists every process on the node and you must attribute processes to one allocation, (3) you must learn the purpose of a foreign-owned job without read access to its logs, (4) a queue column such as QOS is read as a node name or a location, or (5) the submit command is a generated wrapper script whose content does not itself describe the workload."
category: tooling
date: 2026-10-22
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - slurm
  - scontrol
  - srun
  - overlap
  - cgroup
  - job-inspection
  - shared-filesystem
  - scheduler-metadata
  - process-attribution
  - qos
---

# Slurm Running-Job Content Attribution

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Identify what a live (pending or running) Slurm job executes — submit command, working directory, log targets, and live process tree — when you cannot create a step inside the allocation, or when a shared node hides which processes belong to the job. |
| **Outcome** | Successful. Every observed running job on a shared cluster was identified from scheduler metadata, a readability-gated shared-filesystem log, or cgroup attribution. No identification required credential escalation. |
| **Verification** | verified-local on a shared cluster with foreign-owned batch jobs, shared compute nodes, and cgroup v2 visibility. |

## When to Use

- You must explain what a live Slurm job (yours or another account's) is doing, beyond its name and elapsed time.
- `srun --overlap --jobid=<id>` fails with `Unable to create step for job <id>: Access/permission denied` because the job is not yours.
- An `--overlap` shell inside your own job lists every process on the node (the whole host `/proc`), so process-to-job ownership is ambiguous on a shared node.
- A job's home or log directories are unreadable from your identity, so the workload must come from scheduler metadata and any readable shared paths.
- The submit `Command` is a generated wrapper (for example one `job.sbatch` name that several jobs of a campaign share), so the path name carries no signal and the workload definition sits in the scripts that the wrapper exports and invokes.
- A queue column that holds a QOS class is being read as a node name or a location.

Do not use this entry for these intents:

- Classify a terminal (completed, failed, timed-out) foreign job without log access, or gate an artifact pin on scheduler evidence: see `slurm-foreign-job-artifact-gate`.
- Map jobs to accounts, partitions, or QOS entries, or enumerate what a user may submit to: use the cluster account-and-partition discovery guidance.
- Keep a server (for example tmux) alive across client attach and detach steps inside an allocation: see `slurm-step-lifetime-server-ownership`.

## Verified Workflow

### Quick Reference

Work through the levels in order. Stop at the first level that answers the question.

```bash
# 1. Identity bundle — readable for ANY live job. No step access is required.
scontrol show job <id> | tr ' ' '\n' \
  | grep -E '^(JobName|UserId|Command|WorkDir|StdOut|StdErr|NodeList)'

# 1b. Wrapper recursion — open the submit script when its name carries no signal.
sed -n '1,80p' <command-path>            # resource requests, export lines, exec step
ls -l "$(dirname <stdout-path>)"         # side logs the payload redirects to

# 2. Readability gate — check paths BEFORE you promise log evidence.
ls -l <stdout-path> <workdir>; id

# 3. Own job only: attribute node processes to the allocation through cgroups.
srun --overlap --jobid=<id> --cpu-bind=no bash -c \
  'for p in /proc/[0-9]*/cgroup; do grep -qs "job_<id>" "$p" \
   && { pid=${p%/cgroup}; pid=${pid#/proc/}; \
        tr "\0" " " < "/proc/$pid/cmdline"; echo "   [pid $pid]"; }; done'

# 4. Column disambiguation: QOS is a scheduler class, not a node or a location.
squeue -j <id> -o '%.10i %.30j %.12P %.14q %.20N %.10T'
sacctmgr show qos <name>
```

### Suggested Approach

1. Start with `scontrol show job`. The controller makes the identity bundle readable cluster-wide: submit `Command`, `WorkDir`, `StdOut`/`StdErr` targets, `NodeList`, and `UserId`. A descriptive job name plus its command path frequently classifies a coordinator job completely (for example a CPU job that drives remote accelerator replicas through a proxy).
2. Open the submit script when its name carries no signal. Generated campaigns give many jobs the same wrapper path (for example `job.sbatch`) with the same `job-<id>.out` log pattern. The wrapper shows `#SBATCH` resource requests and the `export` lines that set the workload parameters; the real workload definition sits in the payload script that the wrapper invokes (for example through `srun ... bash payload.sh`), including any fallback order for launch options. Follow the chain one level at a time and record each log destination that the scripts redirect to: a payload can send the live progress output to a side file in the output directory, so an almost-empty `StdOut` can hide an active job whose side log shows real progress.
3. Gate log evidence on path readability before you promise it. Test `StdOut`/`StdErr`, each discovered side log, and `WorkDir` with `ls`. Log directories on a shared filesystem are frequently group- or world-readable even for foreign accounts. When they are, a `tail` of `StdOut` or of a side log usually names the driver, its workers or replicas, and its progress — one screen that describes the live workload. Observe the same `0700`/`0750` boundary rules as the foreign-observation contract: do not use elevated rights to read a denied path.
4. For your own jobs (where the controller lets you create a step), `srun --overlap` reaches the node but exposes the whole host process table. Attribute processes by scanning `/proc/*/cgroup` for the string `job_<job-id>`, which is present in cgroup v1 and v2 paths (for example `.../uid_<uid>/job_<id>/...`). Processes found under your job belong to the allocation; all other processes are node noise: other tenants, system daemons, and your own different jobs on the same node.
5. Read the step list. An allocation's `slurmstepd: [<id>.extern]` daemon persists for the job lifetime; payload steps appear as `[<id>.<n>]`. An interactive `bash` allocation that shows only `.extern` is an idle reservation, not an active workload.
6. Verify ambiguous column values before you narrate. `%q` (QOS) is a quality-of-service class, `%N` is the node list, `%P` is the partition. Resolve an unknown class name with `sacctmgr show qos <name>`; resolve account, partition, and submission-rights questions with the account-and-partition discovery guidance.
7. Report per job: the command source (scheduler metadata, log tail, or cgroup attribution), the evidence level that was available, and each stated limit. When no log is readable and no step is possible, give the metadata-only conclusion and name the limit. Do not guess a purpose that the evidence does not show.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | `srun --overlap --jobid=<id>` into a foreign-owned job to run `ps` on its node. | `Unable to create step for job <id>: Access/permission denied`. Steps require job ownership (or operator rights). | Scheduler metadata (`scontrol show job`) is the first-class source for jobs you do not own; it needs no step access. |
| Attempt 2 | `ps -eo pid,cmd` and `ps -u <user>` inside an `--overlap` shell on a shared node. | The shell sees the entire host `/proc`. User-level filtering still mixes several allocations and tenants. | Attribute with `/proc/*/cgroup` matching `job_<id>`; user filters do not separate jobs on a shared node. |
| Attempt 3 | Answered "which job runs here" from a QOS column value read as a location. | QOS is a service class, not a node. The reading misinformed the answer for two jobs that both used the class. | Resolve ambiguous values with `sacctmgr show qos` and read `%N` for placement before you report. |

## Results & Parameters

### Configuration

Fleet-wide scan format (job id, name, node list, state, age, user, partition, QOS):

```bash
squeue -t RUNNING -o '%.10i %.30j %.22N %.12T %.12M %.10u %.12P %.14q'
```

Per-job field allowlist for `scontrol show job` output:

```text
JobName, UserId, Command, WorkDir, StdOut, StdErr, NodeList
```

Cgroup attribution one-liner: see Quick Reference item 3; interpolate the numeric job id in the `grep` pattern.

### Expected Output

- Per job: owner, submit command, working directory, log path with its readability result, and node list.
- For your own allocations: the command lines of the processes that belong to the job, with `slurmstepd: [<id>.<step>]` markers, and an explicit `no active workload` result when only `.extern` remains.
- For a foreign job with a readable log: a short workload summary from the log tail.
- For a foreign job without a readable log: a metadata-only summary with the access limit stated.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared Slurm cluster | Live job-content inventory across foreign-owned batch coordinators, shared interactive nodes, and idle placeholder allocations | See [notes](slurm-job-content-attribution.notes.md). |

## References

- [Slurm Foreign-Job Observer and Produced-Artifact Pin Gate](slurm-foreign-job-artifact-gate.md)
- [Slurm Step-Lifetime Server Ownership](slurm-step-lifetime-server-ownership.md)
