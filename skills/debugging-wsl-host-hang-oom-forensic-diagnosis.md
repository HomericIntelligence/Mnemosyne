---
name: debugging-wsl-host-hang-oom-forensic-diagnosis
description: "Forensic, after-the-fact diagnosis of a WSL2 host that hung/froze under heavy load.
  Use when: (1) a WSL2 host froze or became unresponsive during a heavy multi-agent build/swarm and
  you must prove what happened post-mortem, (2) you suspect a swap-death OOM but the kernel did not
  surgically kill one process (the whole VM hung), (3) you need to distinguish swap-death-by-overcommit
  from a clean single-process OOM, (4) `dmesg` is empty (WSL2 without root) and you need the real
  kernel evidence, (5) you must quantify the concurrent load (agent sessions, pixi solves, C++ builds)
  that caused host resource exhaustion. For the FIX once diagnosed, see
  concurrency-and-process-reliability-patterns (asyncio.Semaphore agent cap, ulimit -v, -j2 builds)."
category: debugging
date: 2026-06-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [wsl, wsl2, oom, swap, host-hang, forensics, syslog, multi-agent, resource-exhaustion, post-mortem]
---

# Debugging a WSL Host Hang: OOM / Swap-Death Forensic Diagnosis

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-29 |
| **Objective** | Forensically diagnose, after the fact, why a WSL2 host (`hostname` = `hermes`, 16 GB RAM / 8 cores) hung/froze during a heavy multi-agent build sweep, and prove the root cause from kernel + `/proc` evidence rather than guesswork. |
| **Outcome** | Root cause pinpointed: concurrent pixi SAT-solves + C++ builds across ~16 unthrottled agent sessions drove RAM → swap → disk-I/O thrash (swap-death-by-overcommit), distinct from a clean single-process OOM. |

## When to Use

- A WSL2 host **froze / hung / became unresponsive** under load (multi-agent swarm, parallel builds) and you need a post-mortem, not a live repro.
- You suspect OOM but `dmesg | grep -i oom` is **empty** (WSL2 without root surfaces nothing).
- You need to **distinguish swap-death-by-overcommit** (whole VM hangs) from a **single-process OOM** (kernel kills one PID surgically, VM stays alive).
- You need to **quantify** the concurrent load — agent sessions, pixi solves, C++ build parallelism — that exceeded the host's real RAM ceiling.
- You need to **rule out red herrings**: tmpfs `/tmp`, disk-space exhaustion, and `max_workers=N` mis-read as an agent concurrency cap.

This skill is the **diagnosis** counterpart. For the **prevention/fix** once you know the cause (asyncio.Semaphore agent cap, `ulimit -v` wrapper, `-j2` builds), see `concurrency-and-process-reliability-patterns`.

## Verified Workflow

### Quick Reference

```bash
# 1. Host identity + real ceiling (WSL2 with no memory= cap defaults to ~50% of Windows RAM)
hostname; cat /etc/wsl.conf
free -h; nproc; grep -E "MemTotal|SwapTotal|CommitLimit|Committed_AS" /proc/meminfo
cat /mnt/c/Users/*/.wslconfig; cat /proc/sys/vm/swappiness /proc/sys/vm/overcommit_memory

# 2. Smoking-gun kernel evidence (dmesg is empty without root under WSL → use syslog + journalctl)
grep -iE "Free swap = 0kB|memory pressure|Time jumped backwards|oom|killed process" /var/log/syslog | tail -30
journalctl -k | grep -iE "Free swap = 0kB|Time jumped backwards|oom" | tail -30
grep -E "pgmajfault|pswpin|pswpout" /proc/vmstat

# 3. Count the concurrent load
ls ~/.claude/worktrees/ | wc -l                 # actual simultaneous agent sessions
du -sh ~/.cache/rattler 2>/dev/null             # pixi SAT-solve cache (~0.5–1 GB per in-memory solve)
grep -rn "j\$(nproc)\|nproc" scripts/           # C++ builds claiming ALL cores

# 4. Rule out red herrings
df /tmp; stat -f -c '%T' /tmp                    # disk vs tmpfs; prove disk free space
# read the tooling: is max_workers bounding THREADS in one process, or agent/process SPAWNS?
```

### Detailed Steps

1. **Identify the host & its real ceiling first.** Run `hostname` — confirm whether "the X box hung"
   means the *host* or a *service* of the same name (here `hostname` is literally `hermes`; check
   `/etc/wsl.conf`). Then `free -h`, `nproc`, and
   `grep -E "MemTotal|SwapTotal|CommitLimit|Committed_AS" /proc/meminfo`. Read
   `/mnt/c/Users/*/.wslconfig`: **no `memory=` cap means WSL2 defaults to ~50% of Windows RAM**, so a
   VM reporting 16 GB implies a ~32 GB Windows host. Note `cat /proc/sys/vm/swappiness` (60 =
   aggressive swap) and `/proc/sys/vm/overcommit_memory`.

2. **Pull the smoking-gun kernel evidence.** `dmesg` is often empty without root under WSL, so use
   **`/var/log/syslog`** and `journalctl -k`. The signature of a swap-death freeze:
   - `kernel: Free swap = 0kB` — swap fully exhausted (**the killer line**).
   - `systemd-journald: Under memory pressure, flushing caches`.
   - `/proc/vmstat` **`pgmajfault`** in the thousands (major page faults = swap I/O stalls).
   - **`Time jumped backwards, rotating`** repeated many times in journalctl = scheduler starvation /
     the kernel timer not being serviced under extreme contention — a tell-tale of a **full hang**,
     not a clean OOM.
   - journal file **"corrupted or uncleanly shut down"** = the abrupt freeze.

3. **Count the concurrent load that caused it.** `ls ~/.claude/worktrees/` (or the orchestrator's
   worktree/clone dir) to count simultaneous agent sessions; `du -sh` them. Find the heavy ops:
   pixi solves (`~/.cache/rattler` size — was 12 GB here; each `pixi install` SAT-solves in-memory
   ~0.5–1 GB) and C++ builds (`grep -rn "j\$(nproc)\|nproc" scripts/` — each build claims ALL cores).
   Multiply: **N agents × (~0.7 GB solve + ~2.5 GB build) vs RAM** → the overcommit factor.

4. **Rule out red herrings.** Confirm `/tmp` is **disk, not tmpfs** (`df /tmp`,
   `stat -f -c '%T' /tmp`) — if disk, clones/builds didn't eat RAM and `df` free space proves disk
   wasn't the constraint. Check any `max_workers=N` in the tooling: a **`ThreadPoolExecutor`
   `max_workers` inside ONE Python process does NOT cap concurrent agent SESSIONS** — it's a red
   herring for host exhaustion. Verify by reading the code: is it bounding threads, or process/agent
   spawns?

5. **Conclude the contention vector.** Primary: **RAM → swap → disk-I/O thrash**. Secondary: **CPU
   oversubscription** (runnable-queue depth ≫ cores). The **`Time jumped backwards` + `Free swap = 0kB`
   combo is definitive for swap-death-by-overcommit**, distinct from a single-process OOM (which the
   kernel kills surgically without freezing the VM).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | --------------- | ------------ | ------------ |
| 1 | `dmesg | grep -i oom` to find the OOM kill | Empty — WSL2 without root surfaces nothing in `dmesg` | Use `/var/log/syslog` + `journalctl -k` for kernel OOM/swap evidence under WSL |
| 2 | Assumed `/tmp` was tmpfs (RAM-backed) and blamed clones for eating RAM | `df /tmp` / `stat -f` showed it on `/dev/sdd` ext with 466 GB free — disk-backed | Disk was never the constraint; the RAM pressure was pixi solves + C++ builds, not scratch files |
| 3 | Treated hephaestus `max_workers=3` as the agent concurrency cap | It only bounds an in-process `ThreadPoolExecutor`, NOT the ~16 concurrent Claude agent sessions | Read the code: `max_workers` caps threads in one process; the real agent fan-out was unthrottled |
| 4 | Estimated "5–6 concurrent agents" from memory | Actual forensics (`~/.claude/worktrees/`) showed ~16 directories | Always **count** the worktrees/clones; never estimate the fan-out |
| 5 | Grepped the failed CI/run log with a narrow pattern | Returned nothing — the OOM left zero-byte / buffered logs (writer reaped pre-flush) | Rely on kernel syslog + `/proc` (vmstat, meminfo), not app logs, for OOM post-mortems |

## Results & Parameters

Copy-paste diagnostic block (the exact commands that pinpointed this incident):

```bash
hostname; cat /etc/wsl.conf
free -h; nproc; grep -E "MemTotal|SwapTotal|CommitLimit|Committed_AS" /proc/meminfo
cat /mnt/c/Users/*/.wslconfig; cat /proc/sys/vm/swappiness /proc/sys/vm/overcommit_memory
grep -iE "Free swap = 0kB|memory pressure|Time jumped backwards|oom|killed process" /var/log/syslog | tail -30
grep -E "pgmajfault|pswpin|pswpout" /proc/vmstat
ls ~/.claude/worktrees/ | wc -l; du -sh ~/.cache/rattler 2>/dev/null
df /tmp; stat -f -c '%T' /tmp
```

Incident parameters observed:

| Parameter | Value |
| ----------- | ------- |
| Host | `hostname` = `hermes`, WSL2, 16 GB VM RAM / 8 cores (~32 GB Windows host implied by no `memory=` cap) |
| Swap state at freeze | `Free swap = 0kB` (fully exhausted) |
| Major page faults | `pgmajfault` in the thousands (swap I/O stalls) |
| Scheduler signature | repeated `Time jumped backwards, rotating` (full-hang tell, not clean OOM) |
| Concurrent agents | ~16 (counted from `~/.claude/worktrees/`, not estimated) |
| pixi SAT-solve cache | `~/.cache/rattler` ≈ 12 GB; ~0.5–1 GB in-memory per solve |
| C++ build parallelism | `-j$(nproc)` — each build claimed all 8 cores |
| `/tmp` backing | disk (`/dev/sdd` ext), 466 GB free — NOT tmpfs, ruled out as RAM/disk constraint |
| Root cause | swap-death-by-overcommit: N agents × (~0.7 GB solve + ~2.5 GB build) ≫ RAM |

For the **fix** once diagnosed, see `concurrency-and-process-reliability-patterns`
(asyncio.Semaphore agent cap, `ulimit -v` wrapper, `-j2` builds).

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| HomericIntelligence / `hermes` WSL2 host | Real host-hang incident during a heavy multi-agent build sweep, 2026-06-29 | verified-local: live forensic diagnosis performed against the actual frozen-host evidence — `Free swap = 0kB` + thousands of `pgmajfault` + repeated `Time jumped backwards` in syslog/journalctl pinpointed swap-death-by-overcommit; ~16 agents counted from `~/.claude/worktrees/`; `/tmp` proven disk-backed (466 GB free) and `max_workers=3` proven to be an in-process thread cap, both ruled out as red herrings |

## References

- [concurrency-and-process-reliability-patterns](concurrency-and-process-reliability-patterns.md) — the prevention/fix counterpart: asyncio.Semaphore agent cap, `ulimit -v` wrapper, `-j2` builds, Pattern 10 (Multi-Agent Host Exhaustion on WSL)
- [ci-failure-triage-and-diagnosis](ci-failure-triage-and-diagnosis.md) — CI-side OOM vs JIT-crash classification and core-dump capture (different surface: CI runners, not the WSL host)
