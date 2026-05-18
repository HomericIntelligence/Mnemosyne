---
name: tooling-gh-pr-merge-admin-parallel-base-branch-race
description: "gh pr merge --admin against the same base branch fails with 'GraphQL: Base branch was modified. Review and try the merge again. (mergePullRequest)' when run in parallel — even --admin merges hit this race. Use when: (1) bulk-merging many PRs after a CI gate fix lands on main, (2) batch-clearing a PR queue with admin override, (3) admin-overriding a blocking required check on multiple PRs simultaneously, (4) running parallel `gh pr merge --admin --squash --delete-branch` against the same base branch (typically main), (5) you see 'Base branch was modified' errors and assumed --admin would bypass the race (it does not — --admin bypasses branch protection rules, not the GitHub mergeability backend race), (6) a Myrmidon swarm or xargs -P pipeline is firing concurrent merges and most fail with mergePullRequest GraphQL errors, (7) deciding whether to parallelize PR merges across the same base branch — answer: don't, loop sequentially."
category: tooling
date: 2026-05-18
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - gh-cli
  - github
  - pr-merge
  - race-condition
  - parallel-execution
  - admin-merge
  - graphql
  - base-branch
  - mergePullRequest
  - bulk-merge
---

# gh pr merge --admin Parallel Base-Branch Race

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-05-18 |
| **Objective** | Bulk-merge 17 PRs against the same `main` base via `gh pr merge --admin --squash --delete-branch` in parallel (max 5 concurrent) |
| **Outcome** | 4/17 succeeded, 13/17 failed with `GraphQL: Base branch was modified. Review and try the merge again. (mergePullRequest)`. Sequential retry of the 13 failures: 13/13 succeeded. The `--admin` flag bypasses branch protection rules but does NOT bypass GitHub's backend mergeability race — each successful merge advances main's tip SHA, invalidating the in-flight base SHA cached for the other concurrent merge attempts. |

## When to Use

- (1) You have a backlog of N≤20 PRs all targeting the same base branch (usually `main`) ready to merge after a CI gate fix
- (2) You are tempted to parallelize with `xargs -P 5`, GNU parallel, a Myrmidon swarm, or background `&` jobs to "go faster"
- (3) You already tried parallel admin-merge and got widespread `Base branch was modified` failures and want to understand why
- (4) You are designing a bulk-merge automation script and need to know the safe concurrency model
- (5) You see the exact error string `GraphQL: Base branch was modified. Review and try the merge again. (mergePullRequest)` in `gh pr merge` stderr
- (6) You assumed `--admin` overrides everything — it doesn't; it overrides branch protection, not the GitHub merge backend's stale-base-SHA detection
- (7) A swarm coordinator is dispatching parallel merge tasks and you need to switch to a sequential drain pattern

## Verified Workflow

### Quick Reference — Sequential Loop (Recommended)

For N≤20 PRs against the same base branch, sequential is **fast enough** (a few seconds per merge) and avoids the race entirely:

```bash
# Sequential admin-merge — safe, no race
for pr in 1730 1731 1732 1733 1734 1735 1736 1737 1738 1739 1740 1741 1742 1743 1744 1745 1746; do
  gh pr merge "$pr" --admin --squash --delete-branch || echo "FAILED: $pr"
done
```

For N>20 against the same base, still loop sequentially — the GitHub merge endpoint is the bottleneck, not your shell.

### If You Must Parallelize

Only parallelize across **different base branches** (different repos, or different release branches in the same repo). Within one base branch, GitHub serializes merges anyway — parallelism only buys you retries.

### Recovery From a Parallel-Merge Failure Wave

```bash
# 1. Collect the failure list (PRs that returned 'Base branch was modified')
FAILED_PRS=(1733 1734 1736 1737 1738 1739 1740 1741 1742 1743 1744 1745 1746)

# 2. Sequential retry — no rebase needed, PRs are still mergeable, just stale
for pr in "${FAILED_PRS[@]}"; do
  gh pr merge "$pr" --admin --squash --delete-branch
done
```

Key insight: **no rebase is required**. The PR's own branch hasn't changed and the merge is still computable; the API just rejected it because the in-flight base SHA was stale. A second attempt picks up the new base SHA and succeeds.

### Detection Pattern

```bash
gh pr merge "$pr" --admin --squash --delete-branch 2>&1 | tee /tmp/merge-$pr.log
if grep -q "Base branch was modified" /tmp/merge-$pr.log; then
  echo "RACE: retry $pr sequentially after queue drains"
fi
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Parallel admin-merge wave (5-concurrent) | Dispatched 17 `gh pr merge --admin --squash --delete-branch` via background jobs limited to 5 concurrent against the same `main` base | 13/17 failed with `GraphQL: Base branch was modified. Review and try the merge again. (mergePullRequest)` — each successful merge advanced `main`'s tip SHA, invalidating the cached base SHA in every other in-flight merge request | The `--admin` flag bypasses branch protection (required checks, required reviews) but NOT the GitHub backend's mergeability race. Parallel admin-merge against one base branch is fundamentally racy above ~3-4 concurrent merges. |
| Assuming `--admin` bypasses all merge gates | Assumed admin override covered everything including stale base SHAs | `--admin` is a permissions override (skip branch protection), not a transactional/optimistic-concurrency override. The merge backend still computes mergeability against the parent SHA captured at request-start time | Read `--admin` as "bypass branch protection only" — it has nothing to do with concurrency safety. |
| Retrying parallel failures in another parallel batch | Re-firing the 13 failures with another `xargs -P` batch | Same race recurs — the second batch also fights itself for sequential SHA advances | Once you've hit the race, switch to a sequential drain. Don't re-parallelize the recovery. |
| Rebasing failed PRs before retry | Assumed "Base branch was modified" meant the PR was now stale and needed `git pull --rebase origin/main` before re-merging | Unnecessary — the PR was still mergeable; GitHub just needed a fresh base-SHA snapshot. The rebase wasted minutes and force-pushed branches that didn't need it | Distinguish "Base branch was modified" (in-flight SHA race, retry as-is) from "merge conflict" (real divergence, needs rebase). The first is transient; the second is real. |
| Using `--auto` to side-step the race | Tried `gh pr merge --auto --admin --squash` to let GitHub queue the merges | `--auto` only fires when required checks pass; for already-mergeable PRs it can still trigger immediate merges that race the same way. Also, `--auto` for `--admin` overrides has surprising semantics in some repo configs | If the PRs are already green and you want them merged now, sequential loop is simpler and more predictable than `--auto`. |

## Results & Parameters

### Exact Error String to Match

```text
GraphQL: Base branch was modified. Review and try the merge again. (mergePullRequest)
```

Match on `Base branch was modified` (case-sensitive) to disambiguate from other GraphQL errors like `Pull request is in clean status` (different transient issue, also retry-safe).

### Empirical Concurrency Threshold

| Concurrency (parallel merges, same base) | Observed success rate |
| ---------------------------------------- | --------------------- |
| 1 (sequential) | 100% (13/13 in retry) |
| 2-3 | ~80-90% (anecdotal, mostly safe) |
| 5 (this session) | ~24% (4/17) |
| >5 | Expected to degrade further (untested) |

**Recommendation:** Use concurrency = 1 against one base branch. Above ~3-4, race failures dominate.

### Copy-Paste Bulk-Merge Snippet (Final Recommended Form)

```bash
# Collect PRs to merge (example: all OPEN PRs with label 'ready-to-merge')
mapfile -t PRS < <(gh pr list --state open --label ready-to-merge --json number --jq '.[].number')

# Sequential drain — no race, full reliability
for pr in "${PRS[@]}"; do
  if ! gh pr merge "$pr" --admin --squash --delete-branch 2>/tmp/merge-err-$pr.log; then
    echo "FAILED $pr: $(cat /tmp/merge-err-$pr.log)"
  fi
done
```

### Decision Table

| Scenario | Recommended Pattern |
| -------- | ------------------- |
| N≤20 PRs, one base branch | Sequential loop, `--admin --squash --delete-branch` |
| N>20 PRs, one base branch | Sequential loop; consider `--auto` if CI is the gate |
| N PRs spread across different bases (or repos) | Parallelize **across** bases, sequential **within** each base |
| Recovery from a parallel-merge race wave | Sequential retry, no rebase |
| Real merge conflicts (not "Base branch was modified") | Rebase the PR, then retry |

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectMnemosyne | 2026-05-18 bulk-merge session: 17 skill PRs against `main`, 13/17 failed with `Base branch was modified` under 5-way parallel admin-merge; 13/13 succeeded on sequential retry | Direct observation in this session |
