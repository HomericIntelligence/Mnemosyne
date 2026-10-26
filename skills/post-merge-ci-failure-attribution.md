---
name: post-merge-ci-failure-attribution
description: "Attribute default-branch check failures at a merge commit before treating them as caused by that merge. Use when a merged pull request shows red checks on the default branch at its merge commit, when an aggregate gate fails while it names an unrelated upstream job as the cause, or when a completion report must decide between a delivered and a blocked disposition after the merge."
category: ci-cd
date: 2026-10-26
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags:
  - post-merge
  - merge-commit
  - check-runs
  - preexisting
  - attribution
  - cascade-gate
  - parent-commit
  - job-set-diff
  - disposition
  - default-branch
---

# Post-Merge CI Failure Attribution

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Decide whether default-branch check failures at a merge commit were caused by that merge or already existed on the parent, before a lane changes its final disposition or starts out-of-scope repair work. |
| **Outcome** | Successful — one resumed lane showed red checks at its merge commit; a parent-commit job-set comparison proved the identical failing set pre-dated the merge, the current default-branch head was green, and the delivered disposition stood with zero mutations. |

A merge commit inherits the health of its parent. A fast-moving default branch can be broken by
unrelated merges at the moment a change lands. Red checks at the merge commit are a trigger for
attribution, not evidence of cause. The correct comparison is the merge commit against its own
parent on the default branch, not against an old pull-request run or against the current head.

This skill complements pre-merge pull-request check triage: that workflow applies while a branch
can still be fixed, rebased, or rerun. After a squash or merge commit lands, those levers are gone;
the question that remains is attribution and disposition, not repair of the branch.

## When to Use

- The pull request merged, and the default-branch run at the merge commit shows failures.
- A completion report must choose between a delivered and a blocked disposition.
- An aggregate or required gate fails, and its message names a different upstream job as the cause.
- The branch is deleted or superseded, so pull-request-side reruns are no longer possible.
- Several unrelated merges landed in the same window, so other lanes can own the breakage.
- A plan or governing instruction limits scope, so repairing the default branch is out of scope.

## Verified Workflow

### Quick Reference

```bash
# Latest conclusion per job name at the merge commit
gh api "repos/OWNER/REPO/commits/MERGE_SHA/check-runs?per_page=100" \
  --jq '[.check_runs[] | {name, conclusion, started_at}]
        | group_by(.name) | map(max_by(.started_at))
        | map(select(.conclusion == "failure")) | .[].name' | sort > /tmp/merge-failing.txt

# The same set at the parent commit on the default branch
gh api "repos/OWNER/REPO/commits/PARENT_SHA/check-runs?per_page=100" \
  --jq '[.check_runs[] | {name, conclusion, started_at}]
        | group_by(.name) | map(max_by(.started_at))
        | map(select(.conclusion == "failure")) | .[].name' | sort > /tmp/parent-failing.txt

diff /tmp/parent-failing.txt /tmp/merge-failing.txt

# Confirm the merge is an ancestor of the current default-branch head
gh api repos/OWNER/REPO/compare/MERGE_SHA...main --jq '.status'
```

An empty diff of the failing job-name sets means the failures pre-date the merge: classify them
pre-existing. `compare` reporting the head ahead of the merge commit confirms ancestry.

### Suggested Approach

1. **Bind observations to exact commits.** Use the merge commit SHA, its parent SHA on the default
   branch, and the current head SHA. A squash merge makes the first parent the correct comparison
   base.
2. **Dedupe by job name first.** Each commit can carry several attempts of each check. Keep the
   latest attempt per name before any comparison.
3. **Compare failing job-name sets between merge commit and parent.** The same failing set at both
   commits is pre-existing breakage: everything except the merged change is controlled. Do not
   compare against the current head for this step; newer unrelated merges change the set.
4. **Read cascade messages before counting gates.** An aggregate or required gate that fails with a
   message such as "required job did not succeed: \<job\>" reports the named upstream job as the
   cause. Judge the named job, not the gate. When the same named job fails at the parent, the gate
   failure is also inherited.
5. **When job-name sets differ, compare failing node identities in the logs.** Shard planners can
   give one flaky test a different shard number in each run, so the shard-name set moves while the
   root stays the same. Fetch failed-node lines per job and compare the test identifiers.
6. **Corroborate with the current head and later history.** Ancestry of the merge under a green
   current head, plus later unrelated commits that repair the same failing signatures, confirms the
   breakage was foreign-owned and already absorbed.
7. **Resolve by classification:**
   - Pre-existing: the delivered disposition stands. Record the attribution evidence in the report.
     Do not repair the default branch from a narrow-scoped lane, do not rerun full suites for
     attribution, and do not report blocked.
   - Introduced or uncertain after the node-identity comparison: report the delta with its evidence
     and escalate to the process that owns the default branch. A merged change that breaks the
     default branch needs a reviewed fix or revert decision, not a silent pass.

If the check-runs API is unavailable, report the attribution limit and keep the disposition
provisional. Do not claim pre-existing on the color of one rollup.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | --------------- | -------------- | ---------------- |
| Single-rollup judgment | Reading the red rollup at the merge commit as evidence the merge broke the branch | A squash or merge commit inherits the parent state; unrelated merges can break the same jobs earlier | Attribution needs the parent-commit comparison; one commit proves nothing |
| Shard-name diff | Treating a different failing shard number as a different failure | The planner can give one flaky node a different shard each run | Compare job names first, then failing node identities in logs |
| Blanket rerun | Re-running the full suite at the merge commit to reach green | Pre-existing failures repeat; the rerun spends CI capacity and cannot change attribution | Reruns do not attribute; the parent diff does |
| In-lane main repair | Fixing the broken default branch from the same narrow-scoped lane | The scope rules forbid adopting adjacent work; the repair belongs to the owning process | Report the classification; escalate introduced breakage; stay in scope |

## Results & Parameters

Classification outcomes:

| Evidence | Classification | Action |
| -------- | -------------- | ------ |
| Failing job-name sets identical at merge commit and parent | Pre-existing | Keep delivered disposition; record evidence |
| Aggregate gate fails at both commits naming the same upstream job | Pre-existing cascade | Judge the named job, not the gate |
| Merge is an ancestor of a green current head; later unrelated commits fixed the same signatures | Corroborated foreign breakage | Note as confirmation, not as the primary proof |
| Job-name sets differ; the same test identifiers fail in the logs of both | Same flaky root | Pre-existing or flaky; not introduced |
| Job-name sets differ; new failing identifiers exist only after the merge | Possibly introduced | Report the delta and escalate to the owner of the default branch |

Evidence to record in the completion report: merge commit SHA, parent SHA, the two deduped failing
job-name sets or their diff, each cascade message read, ancestry status, and the current head state.

## Evidence Boundary

The decision method was exercised on one active default branch with a sharded matrix and an
aggregate required gate: the merge commit and its parent carried the identical failing job set,
the gate message named an unrelated upstream job at both commits, ancestry held under a green
current head, and later unrelated commits repaired the same signatures. Commit topology, planner
behavior, and gate wording are repository-specific; re-read the live runs before each use.
Supporting session detail is in
[post-merge-ci-failure-attribution.notes.md](post-merge-ci-failure-attribution.notes.md).
