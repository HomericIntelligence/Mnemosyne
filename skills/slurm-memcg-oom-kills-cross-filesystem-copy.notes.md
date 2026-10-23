# Notes: slurm-memcg-oom-kills-cross-filesystem-copy

## Evidence

The source session investigated an installer that failed at the same step on each
run: the last step moved a large binary from a temporary directory into a tool
directory below a home directory. Bash reported the death of the move process:

```text
main: line 307: <pid> Killed    mv "$tmp_dir/package/bin/$binary_name" "$INSTALL_DIR/$installed_binary"
```

The shell exited with code 137 (128 + 9). A strace of the parent shell showed the
child result `WIFSIGNALED(s) && WTERMSIG(s) == SIGKILL`, and the kernel siginfo
(`si_code=CLD_KILLED`) for the same process. SIGKILL arrived from outside the
child; the child did not fail on its own. Session coordinates are removed here.

### Environment facts (recorded on the same cluster type)

| Fact | Observed value | Decision value |
| ------ | --------- | --------- |
| Scheduler enforcement | `ConstrainRAMSpace=yes`, `ConstrainCores=no` | The job memory limit is active |
| Job allocation | `cpu=4, mem=8G, node=1` | A small job limit for the transfer shape |
| Cgroup shape | `slurmstepd.scope/job_<id>/step_batch/user`, `memory.max = 8589934592` | A per-job memory cgroup (v2) |
| Filesystems | temporary directory on local disk; home on a network filesystem (89 percent full, large free space) | The move is a real copy of the full file |
| Swap | none | The node has no write-off valve for charge peaks |
| Kernel buffer | `dmesg: read kernel buffer failed: Operation not permitted` | Userspace checks are required |
| Cluster history | `slurmstepd.scope` `memory.events` showed `oom` > 0 and `oom_kill` > 0 in aggregate | Such kills occur on these nodes |

### Verification status at publication

- Executed locally: the parent-trace attribution, `proc/self/cgroup`,
  `memory.max`, `memory.current`, and `memory.events` reads, Slurm configuration
  and job queries, and `sacct` command selection.
- Executed on the incident host from the strace: paths, exit status, and signal
  evidence only.
- Pending on the incident host: the `oom_kill` counter before-versus-after check
  during one retry. The same-filesystem `TMPDIR` workaround and a larger
  `--mem` request were selected as fixes but were not yet re-executed in the
  incident when this entry was published. Re-check the counters during the next
  retry and record the result.

### Why the copy dies and a rename does not

1. `mv` between filesystems reads the source and writes the destination; the
   written pages stay dirty in page cache until the network filesystem confirms
   the write.
2. The memory controller of the job charges these pages to the job cgroup. With
   an 8 GiB limit and other charge in the same job, the kernel OOM killer fires
   inside the job cgroup and frequently selects the process that generates the
   charge.
3. A same-filesystem `mv` is one `rename(2)`. It moves directory entries, not
   data, so it adds no charge.

### Commands recorded for the incident host

```bash
grep -E 'oom|oom_kill' /sys/fs/cgroup/memory.events
# retry the failing step, then:
grep -E 'oom|oom_kill' /sys/fs/cgroup/memory.events   # +1 per killed retry confirms memcg OOM
sacct -j "$SLURM_JOB_ID" --format=JobID,State,ExitCode,MaxRSS,ReqMem
```

If the counter does not move on the incident host, stop the memory work and
direct the investigation to a security endpoint agent that kills writes of new
executables, or to an external killer.
