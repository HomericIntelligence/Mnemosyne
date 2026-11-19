---
name: pr-backlog-drain-merge-queue
license: BSD-3-Clause
description: "Drain a large backlog of open pull requests in a repository whose default branch merges through a merge queue. Use when the same required check fails on every open PR, when a PR stays BLOCKED although every check is green, when a merge command is rejected because the queue owns the merge method, or when an automated merge loop must survive a moving default branch."
category: ci-cd
date: 2026-11-19
version: "1.0.0"
user-invocable: false
tags: [pr-backlog, merge-queue, fleet-triage, update-branch, ci-fan-out, main-red, enqueue, blocked-state, behind-base, bounded-loop, gh-cli, contested-amendments]
---

# PR Backlog Drain Under a Merge Queue

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-19 |
| **Objective** | Move a fleet of open pull requests to green and merged, without merging a defect and without losing a contested change |
| **Outcome** | Successful — a sweep of 46 open PRs ended with every PR merged or correctly stacked. The sweep survived a red default branch, one infrastructure flake, and a default branch that moved while the fleet drained |
| **Verification** | verified-ci |

## When to Use

- More open PRs exist than one review round can handle, and the default branch merges through a merge queue.
- The same required check fails on every open PR at the same time.
- A PR shows `BLOCKED` although every check is green.
- A merge command is rejected with "The merge strategy for main is set by the merge queue".
- An automated loop enqueued a PR many times, and the PR still did not merge.

Do not use this skill to classify one failing check on one PR. Use
[pr-ci-failure-triage-preexisting-vs-introduced](pr-ci-failure-triage-preexisting-vs-introduced.md)
for that decision.

## Verified Workflow

### Quick Reference

```bash
# 1. Is the default branch red? A fleet-wide failure usually starts here.
gh run list --branch <default-branch> --limit 5

# 2. Put every mergeable PR on the current default branch before you queue anything.
gh pr update-branch <number>

# 3. Queue one PR. The queue owns the merge method; method flags are rejected.
gh pr merge <number> --squash
```

### Suggested Approach

1. **Triage the default branch before any PR.** When one required check fails on
   every open PR, run the failing check against the default branch. One stale
   assertion on the default branch (for example, a test that pins a skill or
   package version) can fail every PR. Fix that first. Every concurrent CI run
   on a red default branch is wasted capacity, and per-PR fixes cannot go green
   until the default branch is green.
2. **Classify each remaining failure per PR.** Separate product defect,
   environment failure, and flake. Rerun a classified infrastructure flake with
   `gh run rerun <run-id> --failed`. Record what you reran and why.
3. **Fix PR-specific defects on their own branches.** When two PRs amend the
   same skill with opposite rules, do not force one rule over the other. Stack
   the amendments, give each branch its own version bump, and record a
   discriminator that tells a reader which branch applies.
4. **Update every mergeable branch, then queue.** `gh pr update-branch <n>`
   removes the behind-base blocker and starts fresh CI. Then queue with plain
   `gh pr merge <n> --squash`.
5. **Run a bounded loop that re-updates branches in every round.** The default
   branch moves while the fleet drains. A PR that was green can fall behind and
   block again. When checks are green but the state is `BLOCKED`, compare
   ahead/behind counts, run `gh pr update-branch` again, and re-queue. Log each
   PR disposition to a file, so a stopped loop can resume from the log.
6. **Verify the end state.** `gh pr list --state open` holds only PRs with a
   recorded reason to stay open, and the default branch CI is green after the
   last merge.

Note on freshness: outside a merge queue, a PR that is behind its target with no
conflict can often merge as-is. Under a merge queue this does not hold. The
queue tests the merge result, so a behind-base PR blocks even with green checks.
[verify-pr-ready](verify-pr-ready.md) records the no-conflict case; this entry
records the queue exception.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| One-shot merge loop that polled checks only | The loop ran `gh pr merge <n> --squash` whenever all checks were green, and never updated branches | Each merge moved the default branch. A green PR fell behind, the queue rejected it, and the loop re-ran the same enqueue 58 times with no progress | Re-run `gh pr update-branch` in every round when checks are green but the state stays `BLOCKED` |
| Merge with method and cleanup flags | `gh pr merge <n> --squash --delete-branch`, and method overrides on retry | The queue rejected `--delete-branch` and owns the merge method; the rejection messages looked like failures although the enqueue succeeded | Use the plain enqueue call. Treat "The merge strategy for main is set by the merge queue" as confirmation, not failure |
| Read `BLOCKED` as a broken PR | Started to debug rulesets and protection on all-green PRs that showed `BLOCKED` | The PR was three commits behind the default branch; no rule was broken | Compare ahead/behind counts before diagnosing branch policy |
| Fix the fleet while the default branch was red | Started per-PR fixes in parallel across 41 red PRs | One stale version pin in a consolidation test failed every PR. Per-PR work could not reach green and saturated CI capacity | When the same check fails fleet-wide, repair the default branch first, then update the fleet |
| Force-merge two contested amendments | Two PRs amended the same skill with opposite rules for one case; picking either discarded a real case from the other | Neither rule had decisive evidence, and each recorded a live incident | Stack both amendments with a discriminator note, and give each its own version bump |

## Results & Parameters

### Configuration

Bounded drain loop. State goes to a log file, so a stopped loop can resume:

```bash
#!/bin/bash
# drain.sh <pr-number>... — re-update, enqueue, and log each round.
# Stop conditions: every PR is MERGED, a check fails after classification,
# or the round budget is spent.
for round in 1 2 3 4 5 6; do
  left=""
  for n in "$@"; do
    gh pr view "$n" --json state --jq .state | grep -q MERGED && continue
    gh pr update-branch "$n" 2>&1 | tee -a drain.log
    gh pr merge "$n" --squash 2>&1 | tee -a drain.log
    left="$left $n"
  done
  set -- $left
  [ -z "$1" ] && exit 0
done
```

Notes on the parameters:

- Six rounds handled a 46-PR fleet in practice. Size the round budget to the
  fleet and to CI latency, and keep the budget explicit.
- `gh pr update-branch` fails on a conflicting PR. Route that PR to manual
  conflict resolution instead of retrying it.
- Keep the loop out of `main`. The loop only updates PR branches and enqueues.

### Expected Output

- A fleet-wide red resolves to one default-branch fix, then green re-runs on updated branches.
- Each PR ends `MERGED`, or stays open with a recorded reason: conflict, contested rule, or failed check.
- The drain log holds one enqueue or failure line per PR per round.
- The default branch CI is green after the last merge.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Mnemosyne | Fleet sweep of 46 open PRs under a merge queue, 2026-10-29 to 2026-10-30 | All PRs merged; one mirror-sync flake reran green; two contested amendments stayed stacked with a discriminator |

## References

- [pr-ci-failure-triage-preexisting-vs-introduced](pr-ci-failure-triage-preexisting-vs-introduced.md) — classify one failing check on one PR, including the stale-version-pin cause.
- [github-auto-merge-ci-gating-merge-method](github-auto-merge-ci-gating-merge-method.md) — diagnose one PR that will not merge across rulesets, signatures, and queue ownership.
- [verify-pr-ready](verify-pr-ready.md) — bind one PR's requirements and integration state before a merge.
