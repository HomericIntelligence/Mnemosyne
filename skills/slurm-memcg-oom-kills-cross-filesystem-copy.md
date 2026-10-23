---
name: slurm-memcg-oom-kills-cross-filesystem-copy
license: BSD-3-Clause
description: "Attribute an unexpected SIGKILL (exit code 137) of a small copy process during a large cross-filesystem transfer. Use when: (1) bash reports `Killed   mv <src> <dst>` or `cp  <src> <dst>` and the source and destination are on different filesystems, (2) the shell runs under a scheduler or container memory limit (for example Slurm with `ConstrainRAMSpace=yes`), (3) the destination is a network or shared filesystem, (4) the killed process uses little memory but the file is large, or (5) you must select between a memory-cgroup OOM kill, a security endpoint agent, and an external killer before you change anything."
category: debugging
date: 2026-10-23
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - slurm
  - cgroup
  - memcg
  - oom
  - sigkill
  - exit-137
  - mv
  - cross-filesystem
  - network-filesystem
  - lustre
  - memory-events
  - tmpdir
  - installer
---

# Slurm memcg OOM Kills a Cross-Filesystem Copy

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Identify the sender of a SIGKILL that stops `mv` or `cp` during a large cross-filesystem transfer, then select the fix. |
| **Outcome** | Successful locally. The signature (external SIGKILL of one small process), the active job memory limit, and the transfer shape identify the memory-cgroup OOM killer as the first suspect. The local verification executed the full diagnostic command set on the affected cluster type. The final counter check on the incident host was available as a procedure; the notes record which confirmations were pending. |

## When to Use

- Bash reports `line N: <pid> Killed   mv <src> <dst>` (or `cp`), the step exits with code 137, and a strace of the parent shows `WIFSIGNALED` with `WTERMSIG = 9` for the child.
- The transfer crosses filesystems: for example, an installer extracts an archive on local disk and moves a large binary into a home directory on a network filesystem. A cross-filesystem `mv` copies the data; a same-filesystem `mv` only renames the entry.
- The shell runs in a scheduler job (Slurm) or a container that has a cgroup memory limit, and the killed process is much smaller than the transferred file.
- `dmesg` access is denied on the shared host and you need a userspace confirmation.
- You must select between a memory-cgroup OOM kill, a security endpoint agent that kills writes of new executables, and an external killer.

## Verified Workflow

### Quick Reference

```bash
# 1. Show the active memory limit for this shell or job.
cat /proc/self/cgroup
cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current     # cgroup v2
scontrol show config | grep -i ConstrainRAMSpace                # Slurm applies the job limit
scontrol show job "$SLURM_JOB_ID" | grep -iE 'mem'              # the job limit value

# 2. Compare oom_kill counters before and after one retry.
grep -E 'oom|oom_kill' /sys/fs/cgroup/memory.events

# 3. Kernel and accounting evidence, when the host permits it.
dmesg -T | grep -iE 'oom|killed process'    # access is often denied on shared hosts
journalctl -k | grep -i oom
sacct -j "$SLURM_JOB_ID" --format=JobID,State,ExitCode,MaxRSS,ReqMem
```

### Suggested Approach

Decide from the counters, not from the exit code:

- `oom_kill` increases by one for each killed retry: the memory-cgroup OOM killer is the sender. Change the transfer shape or the limit (see fixes).
- No counter increase and no kernel record: direct the investigation to a security endpoint agent or an external killer. Do not claim OOM, and do not raise the limit without a new diagnosis.
- Exit code 137 alone is not proof of OOM. A signal handler can produce the same code. See [ci-failure-triage-and-diagnosis](ci-failure-triage-and-diagnosis.md).

Why the small process dies: a copy charges its page cache and dirty pages to the memory cgroup of the job. Near the limit, the kernel frequently kills the process that generates the charge, not the largest process. A large file that goes to a slow network filesystem accumulates charge quickly, while `mv` itself stays small. Compute nodes without swap are more sensitive.

Select one fix:

1. Remove the copy. Put the extraction directory on the same filesystem as the destination so that `mv` becomes a rename and moves no data:

   ```bash
   TMPDIR="$HOME/.tmp" bash install.sh    # $HOME/.tmp and the install directory on the same filesystem
   ```

2. Give the charge room. Increase the job memory limit (for example `--mem=`), or run the installer in a shell that has no limit.

When a step is unavailable: `dmesg` denied is normal on shared hosts; `memory.events` is the userspace substitute. If `memory.events` is not readable either, use `sacct` after the job ends and the job's own output. A scheduler can also kill a step when the step exceeds its limit; the scheduler's own log then records the event even when the kernel log is not readable.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Strace of the parent shell only | The trace ends at `clone` and `wait4` for the killed child | Without `-f`, the child's syscalls are invisible | The parent's `wait4` result still proves the kill came from outside: `WIFSIGNALED`, `WTERMSIG = 9` |
| `dmesg` for the OOM record | `read kernel buffer failed: Operation not permitted` | Shared clusters restrict the kernel buffer | Use `memory.events`, `journalctl -k`, and `sacct` |
| Classification from the exit code alone | 137 can also come from a signal handler or a security agent | No counter or log check was attached | Attach `memory.events` before and after one retry before any memory change |

## Results & Parameters

### Configuration

```bash
# Same-filesystem layout: the move is a rename, no data crosses a filesystem boundary.
mkdir -p "$HOME/.tmp"
TMPDIR="$HOME/.tmp" bash install.sh

# Alternative: a larger job limit for one install step.
salloc --mem=16G bash install.sh    # example value; size the request to the transfer plus the job
```

### Expected Output

- With the same-filesystem layout, the move is a rename: it finishes without data I/O, `oom_kill` does not increase, and the install completes.
- On the OOM path, one retry increases `oom_kill` by one, and the kernel or scheduler log names the killed process and the cgroup.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared Slurm cluster, cgroup v2, home on a network filesystem | Installer `mv` of a large binary received external SIGKILL; job limit 8 GiB with `ConstrainRAMSpace=yes` | [notes](slurm-memcg-oom-kills-cross-filesystem-copy.notes.md); the incident-host counter check was pending at publication |

## References

- [The Linux cgroup v2 memory controller and memory.events](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [ci-failure-triage-and-diagnosis](ci-failure-triage-and-diagnosis.md) — exit code 137 is not decisive
- [concurrency-and-process-reliability-patterns](concurrency-and-process-reliability-patterns.md) — bounded-memory reproduction with `ulimit -v`
- [debugging-wsl-host-hang-oom-forensic-diagnosis](debugging-wsl-host-hang-oom-forensic-diagnosis.md) — whole-host memory exhaustion, the contrast case
- [slurm-walltime-expiry-outage-diagnosis](slurm-walltime-expiry-outage-diagnosis.md) — scheduler kill signatures in accounting
