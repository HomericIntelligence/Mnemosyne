---
name: lane-branch-zero-ahead-merge-check
description: "Classify a leftover automation-generated implementation branch that is zero commits ahead of the default branch, or an apparently unowned issue with no open pull request, before re-implementing. Use when queue-start, salvage, or issue-pickup ownership gates must decide reuse, claim, stop, re-implementation, or cleanup; state labels and open-pull-request searches alone miss merged or in-flight lanes."
category: tooling
date: 2026-10-25
version: "1.2.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags: [lane-recovery, branch-audit, already-merged, zero-ahead, reimplementation-avoidance, adoption, ownership-gate, timeline-recency, label-lag, follow-up-lane, active-lane, tip-recency]
---

# Lane Branch Zero-Ahead Merge State Check

**Supporting cases:** [notes](./lane-branch-zero-ahead-merge-check.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Classify a leftover or freshly armed lane branch (`0` commits ahead of the default branch) or an apparently unowned issue before deciding to re-implement, reuse, claim, defer, stop, or clean up |
| **Outcome** | Successful — a merge-state check prevented a duplicate implementation of a finished issue; a timeline-recency gate stopped an issue-pickup worker from claiming an issue a lane had merged inside the window; a tip-recency check keeps an armed active lane from being mistaken for an empty one |
| **Verification** | verified-local |

## When to Use

- A reconcile or adoption phase finds a leftover lane branch for a backlog issue (for
  example an `auto-impl` branch left by an earlier run or another session), and no open
  pull request references the issue.
- An ownership gate for a new run finds zero-ahead lane stubs and must decide whether
  they are leftovers or an active lane arming before its first publication write.
- `git rev-list --count origin/<default>..<branch-head>` returns `0`, and you must decide
  what that means before new implementation starts.
- An issue-pickup or ownership gate finds no open pull request, no assignee, and no
  leftover branch, and must decide whether the issue is free to claim.
- The issue state labels look ready for a worker (for example a plan-approved label), but
  several lanes or sessions share the repository. A label records the last label event,
  not the current delivery state; it can stay set after another lane merges the fix.
- Several lanes or sessions share the branch namespace of one repository, so a previous
  owner may have completed and merged the work.
- The alternative is a full re-implementation that costs hours; a merge-state query costs
  seconds.

## Core Rule

Zero commits ahead has three readings. Do not distinguish them by commit count alone:

1. **Empty lane** — the earlier run never landed work (timeout, intake failure, or a
   worktree removed before commit).
2. **Post-merge lane** — the work already merged. After a merge, the branch head is an
   ancestor of the default branch, so the ahead count is exactly `0`.
3. **Arming lane** — an active lane whose stub the automation (re)created or reset
   against the current default branch shortly before the check. No work is pushed yet,
   but a pull request can appear hours later with no further warning.

The recency discriminator separates reading 3 from readings 1 and 2. A zero-ahead tip is
a default-branch commit, so the tip commit's timestamp tells when the ref was armed:
a stub whose tip commit is only minutes or a few hours old was armed against a default
branch that already contained that commit — the lane is preparing now. A stub whose tip
commit is days or weeks old was armed long ago and is a leftover. Compare the tip
timestamp with the gate's activity window, and treat a fresh stub with no pull request
as possibly active, not as free.

A stale reading in any direction is expensive: re-implementing a merged issue wastes a
full implementation and creates a conflicting second pull request; discarding an
already-delivered branch as "empty" hides that the issue is delivered; and treating an
arming lane as empty lets two workers implement the same issue at the same time.

The same blind spots apply when there is no branch at all:

1. **Open-state search scope** — a `--state open` pull-request search answers only "work
   in review now". It cannot see work that merged inside the recency window.
2. **Label lag** — a ready-to-implement state label (for example a plan-approved label)
   records the last label mutation, not the delivery state. Another lane can merge the
   requested fix while the label stays set. Labels are never ownership evidence on their
   own.

Classify by forge activity inside the gate's recency window (for example 48 hours), not
by label text or by an open-only search.

## Verified Workflow

### Quick Reference

```bash
# 1. Pull-request state for the issue, all states (open, closed, merged)
gh pr list --repo <owner>/<repo> --state all \
  --search "<issue-number> in:body,title" \
  --json number,state,mergedAt,mergeCommit,headRefName

# 2. Issue timeline inside the recency window: cross-references and commits
#    (required when step 1 is empty and no leftover branch exists)
gh api repos/<owner>/<repo>/issues/<issue-number>/timeline --paginate \
  --jq '.[] | select(.created_at >= "<window-start>") |
    {event, created_at, source: (.source.issue.number // null), commit: (.commit_id // null)}'

# 3. Ancestry: is the lane head reachable from the default branch?
git merge-base --is-ancestor <branch-head> origin/<default-branch> \
  && echo "present-on-default" || echo "not-present"

# 2b. Tip recency: when was the stub armed? A zero-ahead tip is a default-branch
# commit, so a fresh tip timestamp means an armed-now lane, not an old leftover.
git log -1 --format=%cI <branch-head>

# 4. Only when no merge evidence exists, look for unpublished work
git rev-list --count origin/<default-branch>..<branch-head>
git diff --stat origin/<default-branch> <branch-head>
```

### Suggested Approach

Classify against the queried evidence, not the branch name or the ahead count:

| Evidence | Classification | Action |
| --------- | --------------- | ------- |
| A merged pull request names the issue and its merge commit is reachable from the default branch | already delivered | Audit the merged content against the delivery contract (required files, required tests at the current default branch). Mark delivered. Keep the branch until an owner approves cleanup. |
| A pull request merged inside the recency window and names the issue (any branch name), whether or not the issue auto-closed | owned / already delivered | Stop. Do not claim the issue, change labels, comment, or create a branch. Report the merge evidence. When your orders require it, audit the merged content first. |
| A timeline `referenced` event (a commit on the default branch) or a `cross-referenced` event from another open issue on the same feature lands inside the window | in-flight lane | Stop. Do not claim. Report the event evidence. A follow-up issue means the lane continues. |
| The lane head is an ancestor of the default branch and the diff of the branch against it is empty or is only reverse drift | empty lane | Safe to re-use or clean up per owner policy. |
| No pull request names the issue, but the stub tip commit is fresh (armed inside the activity window) | possibly-active lane | Do not treat the issue as free. Defer new implementation or schedule a probe re-run before the first publication write; if a peer pull request opens in between, yield to it (see the interruption-yield entry below). |
| Unpublished commits exist ahead of the default branch | salvage candidate | Use the interrupted-lane recovery entry; do not re-implement over the commits. |
| No pull request in any state, no timeline activity inside the window, and ready-looking labels are the only signal | free to claim | Proceed under the gate's remaining checks. The labels are not part of the decision. |

Gate evidence decays while a run works. Even after a clean ownership gate, re-run the
same read-only probes before the first publication write (push, branch work, or PR),
and after every interruption: a probe set that cost seconds prevents a duplicate
implementation that cost hours.

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
| Open-search and label verdict | Classified an issue as unowned because the open-pull-request search was empty, no assignee was set, and a plan-approved label pointed at implementation | Another lane had merged the requested fix hours earlier; the merge, the issue-named lane branch, and a follow-up issue on the same feature were visible only in the issue timeline and in a state-all pull-request search | An open-state search and state labels are not ownership evidence; add the timeline check (`cross-referenced` and `referenced` events inside the window) before claiming an issue |
| Scaffolding verdict | An ownership gate classified fresh zero-ahead lane stubs as harmless repo-wide scaffolding because many issues carried identical empty stubs | The stubs were armed against the current default branch one to two hours before the gate; the lane automation opened a complete peer pull request for the same issue hours later, mid-run | A fresh tip timestamp on a zero-ahead stub is an arming signal, not a leftover; re-run the read-only probes before the first publication write and after every interruption |

## Results & Parameters

### Configuration

```yaml
default_branch: <default-branch>
lane_branch: <automation-generated-branch-name>
issue: <issue-number>
recency_window: <gate-policy-window, for example 48h>
queries:
  - pull-request-state-all-search-body-and-title
  - issue-timeline-events-inside-recency-window
  - merge-base-ancestry-against-default
  - tip-commit-timestamp-against-activity-window
  - rev-list-count-and-diff-stat-only-when-unclassified
audit_when_delivered:
  - required-artifacts-present-on-default
  - contract-named-behavior-tests-at-current-default
```

### Expected Output

- One of seven classifications with its evidence: already delivered, owned by a merged
  lane inside the window, in-flight lane, possibly-active lane, empty lane, salvage candidate, or free to
  claim.
- For already delivered: an audit verdict and, when the audit passes, the issue marked
  delivered without new implementation.
- For owned or in-flight: an immediate stop with no label change, no comment, no new
  branch, and no worktree; the report quotes the timeline or merge evidence.
- No duplicate second pull request for a merged issue.
- For possibly-active (fresh tip timestamp): no new implementation starts; a probe re-run is
  scheduled before the first publication write.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An orchestrated multi-lane issue-backlog wave (identifiers withheld under the privacy policy) | Queue-start reconcile classified a leftover implementation branch as already merged and an audit confirmed the merge; the issue needed no new implementation | See [notes](./lane-branch-zero-ahead-merge-check.notes.md) |
| An orchestrated single-issue worker fleet (identifiers withheld under the privacy policy) | Issue-pickup ownership gate: empty open-pull-request search and a plan-approved label gave a false unowned reading; the issue timeline showed a merged lane and a follow-up issue inside the window, and the worker stopped with no mutation | See [notes](./lane-branch-zero-ahead-merge-check.notes.md) |
| An orchestrated multi-lane issue-backlog wave (identifiers withheld under the privacy policy) | Ownership-gate stubs armed one to two hours before the gate delivered a complete peer pull request mid-run; a forced post-interruption probe refresh caught it, and the worker yielded and cleaned up its unpushed lane | See [notes](./lane-branch-zero-ahead-merge-check.notes.md) |

## References

- [Interrupted automation implementation lane recovery](hephaestus-interrupted-implementation-lane-recovery.md) — pre-pull-request lanes; use when unpublished work exists
- [Interrupted automation loop relaunch salvage](interrupted-automation-loop-relaunch-salvage.md) — reuse decisions for relaunch artifacts
- [Inventory and yield interrupted work when parallel sessions share a repository](shared-repo-interruption-yield-to-peer-pr.md) — the yield disposition when a peer pull request covers the intent
- [Git branch state triage and recovery](git-branch-state-triage-and-recovery.md) — general branch-state inspection
- [Planning: check if already shipped before writing a plan](planning-check-already-shipped-before-planning.md) — plan-time code-state check for issues that describe a past snapshot
