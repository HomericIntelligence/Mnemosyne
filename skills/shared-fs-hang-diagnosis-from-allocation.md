---
name: shared-fs-hang-diagnosis-from-allocation
license: BSD-3-Clause
description: "Find the first cause when a scheduler-managed network service accepts TCP connections but never answers, and node access is denied. Use when: (1) every HTTP request hangs while the port is open and a published status record still says UP, (2) you cannot SSH to the node, (3) service logs show repeated health-probe timeouts or the supervisor and monitor logs stopped, or (4) component logs report that a bound root changed its mode or identity."
category: debugging
date: 2026-10-24
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [hang, shared-filesystem, flock, fuse, virtiofs, slurm, srun-overlap, request-wait-answer, accept-queue, proc, outage-diagnosis, root-identity-drift]
---

# Shared-Filesystem Hang Diagnosis From Inside The Allocation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Decide, with evidence taken before any restart, why a service that accepts connections gives no reply. Rule causes in or out in a fixed order. |
| **Outcome** | Operational. A live outage was narrowed to threads that wait on a pending shared-filesystem request. A second stall had a different cause: a bound root changed its mode. |
| **Verification** | verified-live on a production-like cluster. Names, paths, job numbers and counts are generalized. A kernel stack for the blocked thread was not readable, so the exact lock file was inferred and not proved. |

## When to Use

- Connections to the service port succeed, but every request (including health and metrics) times out.
- A published status or discovery record still reports the service as up. That record does not test the live path.
- Node access is denied (SSH), but you can read the service logs and you own the scheduler job.
- Service logs repeat "health probe failed: read timeout" and the supervisor, monitor or fleet-report log stops or shows "read operation timed out".
- A component log says a bound root "changed during root resolution" with a different mode, owner or inode.

## Verified Workflow

### Quick Reference

```bash
# Read-only probe inside the running allocation. Use a script file, not a long -c string.
# Give it up to 150 s. One attempt returned in seconds, an earlier one hung for 60 s.
srun --jobid=<job> --overlap --ntasks=1 -N1 -c1 --mem=0 --time=3 bash probe.sh > out.txt 2>&1

# probe.sh: what to collect
ss -tnl 'sport = :<port>'                      # listen row: Recv-Q = accept backlog now, Send-Q = backlog limit
ss -tan '( sport = :<port> )' | awk 'NR>1{c[$1]++}END{for(k in c)print k,c[k]}'
free -g | head -2; ulimit -n
ps -eo pid,ppid,etimes,nlwp,rss,stat,wchan:22,args --sort=-rss | head -15
for t in /proc/<pid>/task/*; do echo "$(cat $t/comm) $(cat $t/wchan)"; done | sort | uniq -c
ls -l /proc/<pid>/fd | awk '{print $NF}' | grep -E 'lock|\.lck'   # open lock files on shared storage
```

### Suggested Approach

1. **Save evidence first.** Copy the tail of every component log, the status records, and the scheduler job and node records to a directory outside the service tree. Do this before any restart. A restart destroys live process state.
2. **Confirm the live path is dead.** Probe with a short timeout. Do not trust the published record or the status command that reads it.
3. **Collect a process snapshot from inside the allocation** (Quick Reference). An `srun --overlap` step runs in the job's own resources, so it needs no node login. Write output to a file. If the step hangs, wait longer and retry once before you decide it is unavailable.
4. **Rule causes out in this order, and name the evidence for each:**

   | Cause | Evidence that rules it out |
   | --- | --- |
   | Accept-queue backlog | Listen row has `Recv-Q` near 0, far below `Send-Q`. |
   | File-descriptor exhaustion | Largest per-process fd count is far below `ulimit -n`. |
   | Memory or cgroup limit | `used` is small in `free -g`; the largest RSS is a small part of the reservation. Scheduler `MaxRSS` close to `AveRSS` shows no steep growth. |
   | Neighbour job interference | Neighbour CPU and memory do not touch the allocation; the service processes are idle, not CPU-bound. |

5. **Read the kernel wait channel of every thread.** `wchan = request_wait_answer` means the thread waits for a reply to a pending FUSE or virtiofs request. A blocking `flock`, or any call on a stuck shared-storage path, shows this state. Threads in `futex_wait` or `ep_poll` are idle or waiting for the blocked thread. A blocked event loop makes every request hang while the port stays open.
6. **Find the blocking call in the code.** List open file descriptors of the blocked process that point to lock files on shared storage. Search the source for `fcntl.flock` with `LOCK_EX` or `LOCK_SH` and no `LOCK_NB`. A repository rule that "shared storage takes no file lock" does not prove that every call site follows it. Report the lock as inferred if the thread stack is not readable.
7. **Fix the cause class, not only the process.** Replace a blocking lock wait with a bounded loop on `LOCK_NB` that raises a typed timeout and fails closed. Restart only to restore service.

### Branch: stall with a healthy front

If the front answers (a protected endpoint returns 401 quickly, a health route returns 200) but the supervisor and monitor stop, the cause is not a hang.

1. Decode the mode in the log message as octal. For example `17901` is `0o42755` and `16877` is `0o40755`. The difference is the setgid bit.
2. Run `stat` on the named root. Compare its mode and ctime with the first error. Look for new entries that appeared at the same second. A one-shot command from another lane can create entries and clear the bit.
3. A guard that compares live identity with the identity captured at start fails closed for ever when the root changes. Restoring the captured mode is a small, reversible repair. A restart only captures the new mode.
4. Prove recovery by the error count, not the log tail. Log lines may have no timestamps. Count the matching lines, wait one interval, and count again. Also confirm that the heartbeat file advances.

### Branch: restart choices

- A graceful blue/green reload can refuse to run when the running job predates its protocol marker. The refusal sends no signal. The tool then names a full stop and start.
- Wait until the old job has left the scheduler queue before you start the new one. A stale record for a job that is still completing can block the start.
- If the start command times out while it waits for the activation receipt, do not run it again. Inspect the scheduler job and the published record first.
- An environment variable that selects a deployment context can conflict with the explicit flag and give a generic error. Unset the variable for the command.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Node login | SSH to the gateway node | Public-key login denied for the job user | Use a read-only scheduler step inside the allocation. |
| First overlap step | `srun --overlap` with a 60 s limit and default resources | The step hung and was killed | Add `-c1 --mem=0 --time=3`, use a script file, allow 150 s, and retry once. |
| Kernel stack | Read `/proc/<pid>/task/<tid>/stack` and `syscall` | Permission denied for an unprivileged user | Use `wchan` and the open-fd list, and label the blocked file as inferred. |
| Lock table | Read `/proc/locks` on the node | No row for the lock file | Lock state on a shared mount may live on the host. An empty table does not clear a lock. |
| Status record | Trust the published status that said UP | The record is not written from the live path | Probe the live port. |
| Free memory | Treat low `free` as a leak | Almost all of it was page cache | Compare `used` with `buff/cache`, then use scheduler `MaxRSS`. |

## Results & Parameters

### Expected Output

- A hung event loop shows one or two threads at `request_wait_answer` and all others idle. The listen `Recv-Q` is near 0.
- A mode drift shows a repeating "mode expected X observed Y" line and a heartbeat file that stops. It ends when the mode matches again.

### Notes

- Keep the probe read-only. Do not signal, ptrace, or attach a debugger to a production process unless you have separate authority.
- Report each ruled-out cause with its evidence, and report the lock as inferred when the stack is unavailable.
