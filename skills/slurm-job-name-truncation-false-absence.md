---
name: slurm-job-name-truncation-false-absence
description: "Verify scheduler job lifecycle claims by exact job identifier, not by name-pattern grep over fixed-width listings. Use when a listing shows no matching rows and a rollout, incident, or cleanup decision depends on whether a job still runs."
category: debugging
date: 2026-10-22
version: "1.0.0"
user-invocable: false
tags:
  - slurm
  - scheduler
  - observability
  - truncation
  - false-negative
  - incident-response
---

# Slurm Job-Name Truncation False Absence

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Prevent false lifecycle conclusions (job ended, recycled, replaced) that name-pattern searches over fixed-width scheduler listings produce. |
| **Outcome** | Successful. An exact-identifier query reversed a wrong "job is gone" conclusion that a truncated fixed-width listing had produced during a production rollout. |

## When to Use

- A command such as `squeue`, `sacct`, `kubectl get jobs`, `qstat`, or `ps` lists jobs, and a name pattern selects the rows of interest.
- The listing format caps a column width, for example `squeue -o "%.24j"`, a default column layout, or terminal-width truncation.
- Deployed job names are longer than the visible column portion, or several jobs share a prefix longer than that portion.
- The reader plans to act on the job's absence: declare a recycle, close an incident thread, or launch a replacement.

## Verified Workflow

### Quick Reference

```bash
# Lifecycle question for a known job: query by exact identifier.
squeue -j 1234567 --noheader -o "%i %j %T %M %R"
sacct  -j 1234567 --format=JobID,JobName%40,State,ExitCode,Elapsed

# Discovery of candidates: full-width names, then an exact token match.
squeue --noheader -o "%i %j %T" | awk '$2 == "exact-job-name"'
```

Never treat zero rows from a name-pattern `grep` over a fixed-width listing
as proof that a job ended.

### Suggested Approach

A fixed-width field cuts names without a marker. A `grep` token that starts
after the cut cannot match, so the job looks absent while it runs. The same
surface has a second failure branch: a prefix pattern can match jobs from
several generations at once, and a stale match then misidentifies which job
is alive. Both branches resolve with one rule: existence and state come from
exact-identifier queries; name patterns only discover candidates.

1. Record the job identifier at submission time and propagate it through
   runbooks, status records, and handoffs.
2. For a lifecycle claim, query `squeue -j <id>` for the active set and
   `sacct -j <id>` for recent completions. One of the two answers the claim.
3. Use name patterns only to find candidate identifiers, and confirm each
   candidate by identifier before use.
4. Request a full-width name field (`%j` with no width cap, or a cap longer
   than the longest deployed name) for any discovery listing.
5. Correct any lifecycle statement already published from listing evidence,
   and cite the by-identifier probe in the correction.

When the scheduler's own tools are unavailable, delay the lifecycle claim
instead of deriving it from a listing fragment.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Fixed-width name grep as an existence test | Ran `squeue -o "%.24j ..."` and filtered the job column with a role pattern to locate a production job during a rollout. | The format truncated the job's name before the pattern token, so zero rows appeared and the job read as ended; the job was `RUNNING` the whole time. | Row absence in a truncated listing proves nothing. Verify lifecycle claims by exact job identifier, and record the truncation width next to any listing-based observation. |

## Results & Parameters

### Configuration

| Question | Reliable probe | Not evidence |
| --------- | ---------------- | --------------- |
| State of a known job | `squeue -j <id>`, then `sacct -j <id>` | Zero rows from a name grep over a truncated listing |
| Candidate discovery | Full-width `%j` listing plus an exact-token match | Partial-pattern matches on width-capped fields |

### Expected Output

- An exact-identifier query returns the job row with state, elapsed time,
  and node list, or a completion record with an exit code.
- A name grep over the truncated listing can return zero rows in both
  cases; that output carries no lifecycle information.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A production model-serving rollout on a Slurm cluster | Lifecycle check for a long-named production job during a client cutover | A running job read as gone through a truncated fixed-width listing; the by-identifier query reversed the conclusion — [notes](../skills/slurm-job-name-truncation-false-absence.notes.md) |

## References

- [Reconcile Before Retry After Mutation Status Loss](reconcile-before-retry-mutation-status-loss.md) — the complementary rule for operations whose terminal status was not observed.
- [Slurm Wrap Shell Contract](slurm-wrap-shell-contract.md) — an adjacent Slurm operational contract.
