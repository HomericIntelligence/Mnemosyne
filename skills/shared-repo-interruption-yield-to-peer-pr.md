---
name: shared-repo-interruption-yield-to-peer-pr
license: BSD-3-Clause
description: "Inventory what parallel agent sessions delivered before redoing interrupted prepared work in a shared Git repository. Use when a session resumes after a crash, restart, or idle gap and finds its worktrees removed, staged work gone, or the default branch advanced by peers, and must decide between re-doing its plan and yielding to a peer pull request that already covers the intent."
category: tooling
date: 2026-10-14
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [parallel-sessions, multi-agent, shared-repository, interruption-recovery, worktree, duplicate-work, yield, salvage, git, automation-loop, session-recovery, patch-preservation]
---

# Inventory and Yield Interrupted Work When Parallel Sessions Share a Repository

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-14 |
| **Objective** | After an interruption in a repository that parallel agent sessions share, decide between resuming and yielding — without losing prepared work and without duplicating a peer's delivered pull request. |
| **Outcome** | Operational. One prepared-but-uncommitted feature removal was yielded to a peer session's broader open pull request after inventory showed the peer had delivered the same intent on the advanced default branch. The orphaned branch was deleted safely, prepared publication text was annotated against misposting, and dependent work was deferred once instead of rebased twice. |
| **Verification** | verified-live: every probe and disposition below ran on a live shared repository, and the operator confirmed each destructive step. See [notes](shared-repo-interruption-yield-to-peer-pr.notes.md). |

## When to Use

- An agent session resumes after a crash, a harness restart, or an idle gap and finds a prepared worktree removed, staged-but-uncommitted work gone, or the shared default branch advanced by peers.
- More than one agent session or automation loop works in the same repository at the same time.
- You hold a prepared plan (patch, staged tree, branch, drafted comments) whose intent a peer might have delivered while you were down.
- You must choose between re-creating, rebasing, deferring, or abandoning prepared work.

## Verified Workflow

### Quick Reference

Rebuild ground truth with read-only probes before any write:

```bash
git worktree list                                 # who is checked out where
git branch --list '<pattern>' -vv                 # tips and tracking state
git log origin/<default> --oneline -6             # what merged while you were down
git ls-tree -r origin/<default> --name-only | grep -c <feature-marker>
gh pr list --state open --limit 30 --json number,headRefName,title
git stash list                                    # peer preservation entries
```

Rule: **deliver first, redo never.** If an open peer pull request or a recently merged default-branch commit already covers your intent, yield the track. Resume only the parts of your plan that nobody delivered.

### Suggested Approach

1. Probe before you plan. Treat every summary of pre-interruption state as stale — the shared repository moved while you were down. Run the Quick Reference probes and record branch tips before you touch anything.
2. Classify the intent as landed, in flight, or free. Landed: the feature marker appears or disappears on the default branch, or a merge commit names it. In flight: the open pull-request list contains the intent by title or branch, or a peer worktree contains the signature file (in this campaign, a new seam module found in a peer's integration worktree). Free: no peer artifact matches.
3. Decide per artifact, not per plan:
   - Peer delivered the intent (merged, or an open pull request whose tree contains the signature change): yield. Do not create a competing pull request — it forces duplicate review and rebase churn on both sides. Search peer trees by content (`grep -rl <signature> <peer-worktrees>`), not by pull-request titles alone.
   - Peer work is adjacent and unmerged: defer your rebase until it merges. Queued branches that target code a large peer change rewrites would need two rebases; wait and rebase once. Some queued items may be obsolete after the peer lands — re-check applicability then, not now.
   - Parts of your plan are uncovered (policy text, issue bookkeeping, follow-up comments): keep exactly those parts. They become your new, smaller plan.
4. Dispose safely:
   - Delete an orphaned branch only with the safe form `git branch -d`, and only after you confirm its tip is an ancestor of the default branch (nothing unique is lost).
   - Remove only generated content (test caches, build outputs) from dead worktree paths. Never delete peer stashes, peer worktrees, or saved patches. A stash labeled as preserved is a peer's recovery source; a disconnected peer session may still rely on it.
   - Annotate prepared publication text immediately. A drafted pull-request body or issue comment that names a vehicle that no longer exists must carry a superseded marker at the top, so it cannot be posted verbatim by a later session.
5. Keep a source-of-truth patch outside the worktree. Save `git diff` output (including untracked files copied separately) under a build directory before an interruption can strike. Staged-but-uncommitted content dies with a force-removed worktree index; its blobs linger in the object database and `git fsck --unreachable` plus known-marker `git cat-file` scans can recover them, but that is a last resort when no patch exists.
6. Serialize heavyweight validation on a contended shared host. A commit-gate or test suite that dies mid-run with zero FAILED lines and exit evidence of a signal was killed by resource contention, not by a failing test. Do not debug the suite; rerun it alone. Queue your own commits strictly one at a time on such hosts.

Define completion by evidence: branch tips recorded, the peer artifact that covers the intent named, each disposed artifact listed with its safe-disposal proof, and the remaining re-scoped plan stated.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Resuming from pre-interruption memory | Planned to re-apply the prepared patch as-is after the restart | The peer session had merged adjacent work, advanced the default branch, staged the shared worktree, and then removed it; the prepared plan no longer matched reality | Probe the live repository first; state summaries decay within hours on an active shared repository |
| Verifying before every heavyweight commit | Ran a full fast-selection suite as a separate pre-commit verification while peer hook suites ran concurrently | The suite was killed mid-run with zero FAILED lines by host contention, burning ~10 minutes with no result | On a shared host, serialize heavyweight suites; a silent mid-run kill is a contention symptom, not a test failure |
| Counting on staged content surviving cleanup | Relied on the worktree index and working tree to hold the prepared change | A force-removed worktree destroyed both; only blobs in the object database and an independently saved patch survived | Keep a source-of-truth patch outside the worktree; treat the index as volatile |

## Results & Parameters

### Configuration

The inventory probe set that decides resume versus yield:

```bash
# 1. Did the intent land on the default branch?
git fetch origin <default> --quiet
git log origin/<default> --oneline -6
git ls-tree -r origin/<default> --name-only | grep -c <feature-marker>

# 2. Is the intent in flight?
gh pr list --repo <org>/<repo> --state open --limit 30 \
  --json number,headRefName,title \
  --jq '.[]|"\(.number) [\(.headRefName)] \(.title)"'
grep -rl <signature-string> <peer-worktree-root> 2>/dev/null | head -3

# 3. What of mine survived?
git branch --list '<my-branches>' -vv
git stash list
ls <build-dir>/*.diff <build-dir>/*.patch 2>/dev/null
```

### Expected Output

- No competing pull request opened for an intent a peer already covers.
- Orphaned branches deleted only via the safe form with ancestor proof.
- Prepared publication text carries a superseded marker where its vehicle changed.
- Dependent queued work deferred with an explicit re-entry trigger (peer merge), not silently rebased.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Hephaestus | Session-restart recovery with a parallel session's open integration pull request covering the prepared removal | [notes.md](../skills/shared-repo-interruption-yield-to-peer-pr.notes.md) |

## References

- [Interrupted implementation-lane recovery](hephaestus-interrupted-implementation-lane-recovery.md) — resume a single interrupted automation-loop lane
- [Relaunch salvage for an interrupted automation loop](interrupted-automation-loop-relaunch-salvage.md) — preserve in-flight worker output across loop restarts
- [Recover stashed work after a concurrent branch reset](tooling-git-recover-stashed-work-after-concurrent-branch-reset.md) — restore work a concurrent process stashed away
- [Shared-host test environment pinning](testing-shared-host-env-pinning-and-baseline.md) — attribute and isolate environment failures on the same class of host
