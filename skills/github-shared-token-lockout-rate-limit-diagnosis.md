---
name: github-shared-token-lockout-rate-limit-diagnosis
description: "Tell hourly quota exhaustion apart from a concurrency lockout on one GitHub account, attribute the burn to bursts or steady load, reduce duplicate reads, and use the REST budget as a GraphQL-exhausted fallback. Use when an automation job reports an API rate-limit error while the reported quota still shows a large remaining budget."
category: debugging
date: 2026-10-12
version: "1.1.0"
user-invocable: false
tags:
  - github-api
  - rate-limit
  - concurrency
  - automation
  - diagnosis
  - credentials
  - caching
---

# GitHub Shared-Token Lockout Rate-Limit Diagnosis

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-10-12 |
| **Objective** | Choose the correct recovery when several automation jobs share one GitHub account and the jobs report rate-limit errors. |
| **Outcome** | Operational. The operator restored the job by serializing the account instead of waiting for the hourly reset. |

## When to Use

Use this skill when:

- A GitHub command fails with an API rate-limit message.
- The failure text does not contain a usable reset time.
- A budget read still reports a large remaining quota.
- More than one automation job, loop, or agent uses one account token.
- Required writes (issue or pull-request creation) must proceed while GraphQL is exhausted.
- Repeated reads look wasteful, and a per-minute budget attribution is needed before a rate change.

Do not use this skill to repair detection code inside a tool. Use it to choose the operator
recovery. For tool code, see
[github-api-secondary-rate-limit-backoff](github-api-secondary-rate-limit-backoff.md).

## Verified Workflow

### Quick Reference

Compare one budget read with one live call that uses the same credential:

```bash
# 1. Read the remaining budget.
gh api rate_limit --jq '.resources.graphql | "\(.remaining)/\(.limit)"'

# 2. Make one live call.
gh issue view <number> --repo <owner>/<repo> --json number,state
```

| Budget read | Live call | Classification | Recovery |
| ----------- | --------- | -------------- | -------- |
| Near zero | Fails | Hourly quota exhaustion | Wait for the reported reset. |
| Large | Fails | Concurrency or abuse lockout | Serialize the account. See the steps below. |
| Large | Succeeds | Transient error | Retry with backoff. |

For hourly exhaustion, also measure the burn shape before you change any rate. Two budget reads a
few minutes apart give points per minute:

```bash
# 3. Two samples, same resource object, a few minutes apart.
gh api rate_limit --jq '.resources.graphql | .remaining'
```

| Burn shape | Meaning | Action |
| ---------- | ------- | ------ |
| Quiet-window spend far below the cap, yet exhaustion recurs | Correlated bursts: parallel worker fan-out, or deferred jobs resuming together after a reset | Stagger restarts after a reset; cap per-job fan-out; isolate budgets per job. |
| Quiet-window spend near the cap | Duplicated reads dominate | Deduplicate or cache repeated reads. |

### Suggested Approach

1. Classify before you act. Run both commands. A rate-limit message alone does not name the limit
   class, and a missing reset value is a common sign of a lockout.
2. For a lockout, reduce the number of processes that use the account. Stop the sibling jobs
   first. Send a termination signal that lets each job record its state, and write down the exact
   command that restarts it.
3. Give the job that must run its own credential, if the host stores more than one account.
4. Lower the request rate of the surviving job. A lower rate before a lockout helps. The same
   lower rate during a lockout does not restore access.
5. Confirm recovery with one live call before you restart the job.
6. Keep the tool-side repair separate. A tool that misreads the message, or that backs off for a
   whole window, still needs its own code fix.

A lockout clears when request pressure stops. Repeated retries keep the pressure, so a retry loop
can prolong the lockout for every job that shares the account.

### Reduce, isolate, and fall back

For hourly exhaustion, not only lockouts:

1. Attribute the burn before a rate change. Two budget reads minutes apart separate quiet spend
   from bursts. A fleet that waits out a reset and then resumes every job in the same second
   re-exhausts the fresh budget at once; stagger restarts past the reset.
2. Deduplicate or cache reads that repeat within a short window (issue labels, PR head/base,
   review threads, discovery scans). A read-through local cache with a fixed TTL removes them.
   ETag conditional requests help only REST callers; GraphQL has no 304 mechanism, so a TTL cache
   is the only local reduction for GraphQL reads.
3. Isolate budgets per job at the account level when possible: a separate token per job gives each
   job its own hourly budget and ends cross-job attribution noise.
4. Use the REST budget as a GraphQL-exhausted fallback for required writes. The REST primary rate
   limit is a separate bucket from the GraphQL budget; `gh api` REST paths continue to work when
   GraphQL calls are rejected:

   ```bash
   gh api repos/<owner>/<repo>/issues -X POST -F title=... -F body=@body.md
   gh api repos/<owner>/<repo>/pulls  -X POST -F title=... -F head=<branch> -F base=<base> -F body=@body.md
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | --------------- |
| Retry after the reported reset | A driver waited for the reset that the tool reported, then started again. | The hourly quota never ran out. The wait used an hour, and the next attempt failed in seconds. | A reset wait helps only hourly exhaustion. |
| Fewer workers and a lower client rate | The job was restarted with fewer workers and a lower client request rate. | The account was already locked out. Every call still failed. | Throttling prevents a lockout. It does not clear one. |
| Trust the message text | The recovery was chosen from the message alone. | The message names a rate limit but not the class, and it carried no usable reset value. | Classify from a budget read plus a live call. |
| Treat steady-state spend as the problem | Rates and caps were tuned from one quiet-window reading, but exhaustion kept recurring at bursts. | Quiet-window spend was far below the cap; correlated bursts from parallel workers and post-reset resume storms were the cause. | Attribute burn with two budget reads before a rate change. |
| Restart everything at the reset | Deferred jobs resumed together at the reset second. | The fresh budget was spent to zero again within minutes. | Stagger restarts past the reset; isolate budgets per job where possible. |

## Results & Parameters

### Configuration

```yaml
concurrency:
  jobs_per_account: 1
  client_rate_per_second: 5
  cooldown_after_lockout_seconds: 600
```

### Expected Output

- One budget read and one live call per diagnosis.
- A classification that names the limit class and the evidence for it.
- A restart record for each job that the operator stopped.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Private automation host | Operator session with several jobs on one account | See [notes](github-shared-token-lockout-rate-limit-diagnosis.notes.md). |

## References

- [GitHub rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [github-api-secondary-rate-limit-backoff](github-api-secondary-rate-limit-backoff.md)