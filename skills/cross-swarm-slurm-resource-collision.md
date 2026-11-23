---
name: cross-swarm-slurm-resource-collision
license: BSD-3-Clause
description: "Detect and resolve two independent coordinator sessions submitting real jobs against the same shared, scarce scheduler resource (a Slurm QOS or node cap) for the same backlog intent. Use when a swarm's jobs stay queued longer than a known third-party occupant explains, when a peer session reaches out claiming the same intent, or before trusting an assumed capacity limit instead of the scheduler's own live accounting."
category: tooling
date: 2026-11-23
version: "1.0.0"
user-invocable: false
tags: [slurm, qos, gres, node-cap, cross-session, peer-collision, swarm, myrmidon, scarce-resource, scheduler-accounting, job-ownership-verification, yield-to-peer]
---

# Cross-Swarm Slurm/Scheduler Resource Collision

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-23 |
| **Objective** | Stop two independent coordinator sessions from unknowingly splitting the same scarce scheduler capacity while each benchmarks the same backlog intent, and resolve the collision without touching a true third party's job. |
| **Outcome** | Operational. A coordinator assumed its only queue contention was one named third-party job and planned around a documented node-count limit. A peer session reached out mid-run naming matching job output paths and slugs for the identical intent. The live scheduler accounting showed a group cap far smaller than the documented limit, shared cluster-wide, with the peer's own queued jobs as the second, previously-invisible occupant. One session yielded ownership, the other cancelled only the job it could independently verify was its own, and both continued without further contention. |

## When to Use

- A swarm or coordinator session submits jobs against a shared Slurm QOS or node-count cap for a specific GitHub issue or backlog intent, and jobs queue longer than a single known third-party occupant explains.
- A peer session (a different coordinator, possibly started independently by the same or a different user) sends a cross-session message naming job IDs, output paths, or a slug that overlaps your own in-flight work.
- You are about to plan scheduling around a documented or assumed per-account capacity limit (a number from project memory, a README, or an earlier session) rather than the scheduler's own live group accounting.
- A security or safety classifier flags a job-cancellation action generically, and the acting agent's only evidence that the job is its own is its own prior self-report.

Do not use this entry for collisions inside one coordinator's own swarm (one coordinator's agents stepping on each other's files or worktrees) — that is ordinary dispatch-ownership work. Use it when the colliding party is a **separate, independently started session** that neither delegated to nor was delegated by the current coordinator.

## Verified Workflow

### Quick Reference

```bash
# Get the scheduler's own live view of the shared cap — never trust a documented number alone.
scontrol show node=<node> | grep -o 'AllocTRES=[^ ]*'
sacctmgr show qos <qos> format=Name,GrpTRES,GrpNodes
squeue --qos=<qos> -o "%i %u %j %T %r"            # every job and user currently on the cap, not just yours

# Verify a job is YOURS before cancelling it, on independent scheduler evidence —
# never on a peer's or your own agent's self-report alone.
sacct -j <job-id> --format=JobID,JobName,User,State -P

# Only cancel after the User= field matches your own submitting account.
scancel <job-id>
```

### Suggested Approach

1. **Do not assume the documented or remembered capacity limit is the one actually enforced.** A project's own memory or README can state a per-account node limit that differs from the live QOS group cap — the two can describe different scopes (per-account vs. cluster-wide-shared) and only the scheduler's own `sacctmgr`/`scontrol` output is authoritative for what is actually blocking your jobs right now.
2. **When queued jobs stay pending longer than one known occupant explains, re-derive the full occupant list from the scheduler, not from memory.** `squeue --qos=<qos>` lists every user and job currently charged against the cap. A second, previously-unconsidered occupant — including a peer session's own jobs for the same intent — is a common and easy-to-miss explanation for slower-than-expected throughput.
3. **Treat an unsolicited peer message naming matching job IDs, output paths, or a slug as strong evidence of true overlap, not just a title match.** Apply the same yield-to-peer principle used for shared Git-repository collisions here, generalized to a shared scheduler resource: exactly one session should own the intent going forward, decided by who started first or whose evidence is more complete, not by which session happened to notice the collision first.
4. **Resolve ownership explicitly over the cross-session channel, then have only the non-owning session act.** State plainly which session keeps the intent and which stands down. The standing-down session cancels its own queued/pending work for that intent; the owning session's jobs are untouched.
5. **Before cancelling anything, verify job ownership independently via the scheduler's own accounting (`sacct ... User=`), even when a safety classifier flags the cancel action generically and even when the acting agent is confident the jobs are its own.** A generic "interference with workloads" classifier warning on a cancel command is not evidence of a real violation by itself, and is not evidence of a real violation's absence either — resolve it with the scheduler's own ownership record, never with either party's self-report alone.
6. **After resolving, let the previously-blocked slot absorb the freed capacity without resubmitting duplicate work.** Confirm via the scheduler that the cancelled job is gone and the queue advances, rather than assuming the cancellation succeeded from the command's exit code alone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Planning queue timing around a remembered per-account node limit | Assumed the only contention was one named third-party job within a documented node-count budget | The live QOS group cap was much smaller and shared cluster-wide; a second session's own queued jobs for the identical intent were invisible until the scheduler's own accounting was checked | Re-derive the live cap and occupant list from the scheduler before reasoning about queue delays; a documented limit can describe a different scope than what is actually enforced |
| Treating a peer's cross-session claim of ownership as settled by title alone | Compared only the stated intent/title between sessions | Titles alone do not prove the same underlying scheduler resources are involved | Require concrete overlapping identifiers (job IDs, output paths, slugs) before conceding or asserting ownership |
| Refusing to verify a cancel target because a generic safety classifier already flagged the action | Treated the classifier warning as either proof of a violation or as something to route around without checking | The classifier's warning is a blanket caution on any cancellation command, not evidence either way | Resolve the classifier's concern with independent scheduler evidence (`sacct` ownership field) rather than trusting self-report in either direction |

## Results & Parameters

### Configuration

```bash
# The three checks that settle a suspected cross-swarm scheduler collision, in order:
sacctmgr show qos <qos> format=Name,GrpTRES,GrpNodes      # 1. the real cap, not the remembered one
squeue --qos=<qos> -o "%i %u %j %T %r"                    # 2. every current occupant, not just the known one
sacct -j <job-id> --format=JobID,JobName,User,State -P    # 3. independent ownership proof before any cancel
```

### Expected Output

- The live scheduler cap and occupant list, not a remembered or documented number, drives the collision diagnosis.
- Exactly one session continues the intent; the other stands down and cancels only jobs it independently verified as its own.
- No third party's running job is touched.
- Freed capacity is absorbed by the continuing session's existing queued work, with no duplicate resubmission.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Multi-coordinator benchmark swarm on a shared GPU cluster | Two independently started coordinator sessions each ran a real-job Slurm benchmark sweep for the same backlog issue under the same QOS; a documented per-account node limit understated the actual shared cap, and the peer's own jobs were the second, previously-invisible occupant | — |

## References

- [Inventory and yield interrupted work when parallel sessions share a repository](shared-repo-interruption-yield-to-peer-pr.md) — the same yield-to-peer decision for Git/pull-request collisions; this entry generalizes it to a shared external scheduler resource
- [Slurm QOS group-cap regression diagnosis](slurm-qos-group-cap-regression-diagnosis.md) — classify pending jobs under a QOS group-limit reason as a lowered cap versus legitimate saturation; use alongside this entry once the occupant list is known
