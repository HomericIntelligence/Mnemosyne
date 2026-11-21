---
name: ci-failed-in-seconds-actions-budget-rerun-failed-jobs
description: "Use when required CI checks on a pull request fail within a few seconds, or the failure annotation says the job was not started because an Actions budget is preventing further use. These are not code defects. Re-run only the failed jobs, and separate them from real failures."
category: ci-cd
date: 2026-11-21
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [github-actions, ci-failure-triage, budget-limit, rerun-failed-jobs, auto-merge, stale-check-rows]
---

# CI Failed in Seconds: Actions Budget, Not Code

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-21 |
| **Objective** | Tell a budget-limit CI failure from a real defect, and clear it without code changes |
| **Outcome** | Several pull requests with 4 to 7 red checks merged after a re-run of only the failed jobs. A few had real defects mixed in. Those needed a code fix first |
| **Verification** | verified-local — one multi-day session with about a dozen pull requests. No hosted-runner billing data was inspected |

## When to Use

- A required check, often a gate or label gate, ends in 0 to 5 seconds with a failure.
- The check annotation says the job was not started because an Actions budget is preventing further use.
- A pull request has green approvals and an armed auto-merge, yet it stays blocked behind red checks.
- The failing rows may come from an older head. The newest runs may be green.

## Verified Workflow

### Quick Reference

```bash
# 1. Per failed check: duration and annotation.
gh api repos/OWNER/REPO/commits/<head-sha>/check-runs?per_page=100 \
  -q '.check_runs[]|select(.conclusion=="failure")|"\(.id) \(.name) \(.started_at) \(.completed_at)"'
gh api repos/OWNER/REPO/check-runs/<check-run-id>/annotations -q '.[].message'

# 2. Re-run only the failed jobs of a COMPLETED run.
gh run rerun <run-id> --failed
```

### Steps

1. Triage each failed check by duration and annotation. A job that ends in seconds with the budget
   message never ran your code. A job that ran for minutes failed on its own merits.
2. Check that the failed run belongs to the current head. The status rollup keeps rows from older
   heads, so a pull request can show a red gate while its newest gate run passed. Judge the latest
   run of each check name, not the aggregate.
3. Split the failures into two lists. Fix real failures first, with a signed commit if needed. A
   mixed pull request has both lists.
4. For the budget list, re-run only the failed jobs with `gh run rerun <run-id> --failed`. The run
   must be complete. If other jobs are still queued or running, wait for the run to finish.
5. Do not change code, rebase, relabel, or re-sign to clear a budget failure. A new head starts new
   runs that can fail the same way. It also voids approvals that are bound to the old head.
6. After the re-run, confirm that the new run passed on the same head. Armed auto-merge then
   completes the merge without more action.
7. On a repository you do not own, the re-run can need admin rights and the refusal says so. Ask a
   maintainer. Do not add empty commits to force a new run.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treat every red check as code | Started a fix for a gate that failed in two seconds | There was no code defect. The job never started | Read duration and annotation before you open the diff |
| Read the aggregate status | Saw red gate rows and assumed the head was broken | The rows came from older heads. The newest run passed | Look at the latest run of each check |
| Re-run one job of a running run | Asked for a single job re-run while other jobs were queued | The service refused with "cannot be rerun" | Wait for the whole run to complete, then re-run the failed jobs |
| Re-run on a foreign repository | Ran `gh run rerun --failed` on an upstream project | The service required admin rights | Ask a maintainer. Do not push noise commits |

## Results & Parameters

```text
Budget-limit signature:   conclusion = failure, duration <= 5 s, annotation names the Actions budget
Real-failure signature:   duration of minutes, failing test or lint output in the job log
Clear it:                 gh run rerun <run-id> --failed   (run complete; write access; admin on foreign repos)
Do not:                   change code, rebase, relabel, or re-sign to clear a budget failure
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A private multi-service repository | About a dozen pull requests over several days | Two pull requests had only budget failures. Two had real test failures plus budget failures. One foreign-repository re-run was refused for lack of admin rights |
