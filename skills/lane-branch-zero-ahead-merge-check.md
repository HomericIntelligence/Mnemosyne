---
name: lane-branch-zero-ahead-merge-check
description: "Classify a leftover automation-generated implementation branch that is zero commits ahead of the default branch before re-implementing. Use when queue-start or salvage discovery must decide reuse, re-implementation, or cleanup."
category: tooling
date: 2026-10-25
version: "1.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags: [lane-recovery, branch-audit, already-merged, zero-ahead, reimplementation-avoidance, adoption]
---

# Lane Branch Zero-Ahead Merge State Check

**Supporting cases:** [notes](./lane-branch-zero-ahead-merge-check.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Classify a leftover automation-generated implementation branch (`0` commits ahead of the default branch) before deciding to re-implement, reuse, or clean up |
| **Outcome** | Successful — a merge-state check identified an already-merged pull request and prevented a duplicate implementation of a finished issue |
| **Verification** | verified-local |

## When to Use

- A reconcile or adoption phase finds a leftover lane branch for a backlog issue (for
  example an `auto-impl` branch left by an earlier run or another session), and no open
  pull request references the issue.
- `git rev-list --count origin/<default>..<branch-head>` returns `0`, and you must decide
  what that means before new implementation starts.
- Several lanes or sessions share the branch namespace of one repository, so a previous
  owner may have completed and merged the work.
- The alternative is a full re-implementation that costs hours; a merge-state query costs
  seconds.

## Core Rule

Zero commits ahead has two readings. Do not distinguish them by commit count alone:

1. **Empty lane** — the earlier run never landed work (timeout, intake failure, or a
   worktree removed before commit).
2. **Post-merge lane** — the work already merged. After a merge, the branch head is an
   ancestor of the default branch, so the ahead count is exactly `0`.

A stale reading in either direction is expensive: re-implementing a merged issue wastes a
full implementation and creates a conflicting second pull request; discarding an
already-delivered branch as "empty" hides that the issue is delivered.

## Verified Workflow

### Quick Reference

```bash
# 1. Pull-request state for the issue, all states (open, closed, merged)
gh pr list --repo <owner>/<repo> --state all \
  --search "<issue-number> in:body,title" \
  --json number,state,mergedAt,mergeCommit,headRefName

# 2. Ancestry: is the lane head reachable from the default branch?
git merge-base --is-ancestor <branch-head> origin/<default-branch> \
  && echo "present-on-default" || echo "not-present"

# 3. Only when no merge evidence exists, look for unpublished work
git rev-list --count origin/<default-branch>..<branch-head>
git diff --stat origin/<default-branch> <branch-head>
```

### Suggested Approach

Classify against the queried evidence, not the branch name or the ahead count:

| Evidence | Classification | Action |
| --------- | --------------- | ------- |
| A merged pull request names the issue and its merge commit is reachable from the default branch | already delivered | Audit the merged content against the delivery contract (required files, required tests at the current default branch). Mark delivered. Keep the branch until an owner approves cleanup. |
| The lane head is an ancestor of the default branch and the diff of the branch against it is empty or is only reverse drift | empty lane | Safe to re-use or clean up per owner policy. |
| Unpublished commits exist ahead of the default branch | salvage candidate | Use the interrupted-lane recovery entry; do not re-implement over the commits. |

When the classification is "already delivered", audit the delivered change before
accepting it. A short audit is cheap and verifies the merge the count could not prove:

1. Read the canonical delivery contract (issue plan or specification).
2. Check that each required artifact exists on the current default branch.
3. Run the behavior tests the contract names, at the current default branch, in a
   disposable worktree.
4. Record the verdict with the exact queries and results.

If a step is unavailable (no live query, no test runner), state the limit and prefer the
least destructive decision: keep the branch and classify by the remaining evidence.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Commit-count verdict | Classified a leftover lane branch as "nothing salvageable" because `--count` returned `0` | The reason was wrong although the conclusion happened to be right: the work had merged the previous day, and `0` came from post-merge ancestry | Zero ahead is never self-classifying; add the pull-request state and ancestry checks before any re-implement or discard decision |

## Results & Parameters

### Configuration

```yaml
default_branch: <default-branch>
lane_branch: <automation-generated-branch-name>
issue: <issue-number>
queries:
  - pull-request-state-all-search-body-and-title
  - merge-base-ancestry-against-default
  - rev-list-count-and-diff-stat-only-when-unclassified
audit_when_delivered:
  - required-artifacts-present-on-default
  - contract-named-behavior-tests-at-current-default
```

### Expected Output

- One of three classifications with its evidence: already delivered, empty lane, or
  salvage candidate.
- For already delivered: an audit verdict and, when the audit passes, the issue marked
  delivered without new implementation.
- No duplicate second pull request for a merged issue.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An orchestrated multi-lane issue-backlog wave (identifiers withheld under the privacy policy) | Queue-start reconcile classified a leftover implementation branch as already merged and an audit confirmed the merge; the issue needed no new implementation | See [notes](./lane-branch-zero-ahead-merge-check.notes.md) |

## References

- [Interrupted automation implementation lane recovery](hephaestus-interrupted-implementation-lane-recovery.md) — pre-pull-request lanes; use when unpublished work exists
- [Interrupted automation loop relaunch salvage](interrupted-automation-loop-relaunch-salvage.md) — reuse decisions for relaunch artifacts
- [Git branch state triage and recovery](git-branch-state-triage-and-recovery.md) — general branch-state inspection
