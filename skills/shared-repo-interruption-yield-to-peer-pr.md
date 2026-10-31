---
name: shared-repo-interruption-yield-to-peer-pr
license: BSD-3-Clause
description: "Inventory what parallel agent sessions delivered before redoing interrupted prepared work in a shared Git repository. Use when a session resumes after a crash, restart, or idle gap and finds its worktrees removed, staged work gone, or the default branch advanced by peers, and must decide between re-doing its plan and yielding to a peer pull request that already covers the intent. Also use when a resume directive carries a live implementation mandate (an approved plan or terminal plan-state label) for an issue that reference-only merges may have fully delivered while leaving it open. Also use mid-ceremony, when a delivery duty that must publish one canonical change finds a same-intent lane it did not create — with timestamps inside its own inspection window but no pushed branch or open pull request — and must resolve whether the sibling is live before it decides between publication and a stand-down report."
category: tooling
date: 2026-10-14
version: "1.3.0"
user-invocable: false
verification: verified-live
tags: [parallel-sessions, multi-agent, shared-repository, interruption-recovery, worktree, duplicate-work, yield, salvage, git, automation-loop, session-recovery, patch-preservation, already-delivered, ancestor-verification, in-flight-lane, liveness-probe]
---

# Inventory and Yield Interrupted Work When Parallel Sessions Share a Repository

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-14 |
| **Objective** | After an interruption in a repository that parallel agent sessions share, decide between resuming and yielding — without losing prepared work and without duplicating a peer's delivered pull request. |
| **Outcome** | Operational. One prepared-but-uncommitted feature removal was yielded to a peer session's broader open pull request after inventory showed the peer had delivered the same intent on the advanced default branch. The orphaned branch was deleted safely, prepared publication text was annotated against misposting, and dependent work was deferred once instead of rebased twice. A later case yielded a durable-learning publication to a live sibling lane: the sibling commit landed inside the discovery window, its committed diff covered the intent's decision branches, and the sibling pull request was reported as the ceremony outcome with zero local writes. |
| **Verification** | verified-live: every probe and disposition below ran on a live shared repository, and the operator confirmed each destructive step. See [notes](shared-repo-interruption-yield-to-peer-pr.notes.md). |

## When to Use

- An agent session resumes after a crash, a harness restart, or an idle gap and finds a prepared worktree removed, staged-but-uncommitted work gone, or the shared default branch advanced by peers.
- More than one agent session or automation loop works in the same repository at the same time.
- You hold a prepared plan (patch, staged tree, branch, drafted comments) whose intent a peer might have delivered while you were down.
- A restart directive assigns you to *drive* a named peer pull request (review it, keep its checks green, merge it) that was created while you were down.
- A resume directive carries a live implementation mandate for a named *issue* — an approved plan, a terminal plan-state label — whose full scope parallel merges may have delivered while you were down. Reference-only merges (`Refs`, not a closing keyword) leave the issue open by design, so an open issue carrying an approval label is not proof of remaining work.
- You must choose between re-creating, rebasing, deferring, or abandoning prepared work.
- A delivery duty that must publish one canonical change (for example a durable-learning
  ceremony) finds a same-intent lane it did not create — recent timestamps but no pushed
  branch and no open pull request — and must decide whether the sibling is live before it
  publishes its own variant.

## Verified Workflow

### Quick Reference

Rebuild ground truth with read-only probes before any write:

```bash
git worktree list                                 # who is checked out where
git branch --list '<pattern>' -vv                 # tips and tracking state
git log origin/<default> --oneline -6             # what merged while you were down
git ls-tree -r origin/<default> --name-only | grep -c <feature-marker>
gh pr list --state open --limit 30 --json number,headRefName,title
git reflog show --date=iso <peer-branch> | head -5    # commits inside your window = live lane
git ls-remote --heads origin <peer-branch>            # publication state of a foreign lane
git stash list                                    # peer preservation entries
```

Rule: **deliver first, redo never.** If an open peer pull request or a recently merged default-branch commit already covers your intent, yield the track. Resume only the parts of your plan that nobody delivered.

### Suggested Approach

1. Probe before you plan. Treat every summary of pre-interruption state as stale — the shared repository moved while you were down. Run the Quick Reference probes and record branch tips before you touch anything.
2. Classify the intent as landed, in flight, or free. Landed: the feature marker appears or disappears on the default branch, or a merge commit names it. In flight: the open pull-request list contains the intent by title or branch, or a peer worktree contains the signature file (in this campaign, a new seam module found in a peer's integration worktree). Free: no peer artifact matches.

   When the assigned vehicle is a named pull request rather than an unknown peer, fetch its exact state first:

   ```bash
   gh pr view <N> --json state,mergedAt,mergeCommit,labels,reviewDecision
   gh issue view <M> --json state,stateReason        # the issue the pull request closes
   ```

   A `MERGED` state with the closing issue `CLOSED`/completed is terminal: the drive is already done. Verify the pinned values on the default branch, report, and stop. Do not start review rounds on a merged head, and do not push your own variant branch.

   When the mandate names an *issue* rather than a pull request, complete delivery can leave the issue open — every merged pull request referenced it instead of closing it. The terminal test is delivered-state on the current default branch, never forge surface signals (an open issue, an approval label, a passed ownership gate):

   ```bash
   # Every pull request that references the issue, all states, not only open:
   gh pr list --state all --search "<issue-number> in:body,title" \
     --json number,state,mergedAt,mergeCommit
   # Ancestor-bind each merged pull request to the current default branch:
   git merge-base --is-ancestor <merge-commit> origin/<default> && echo ancestor
   ```

   Then enumerate the issue's acceptance checklist and verify each item against `origin/<default>` (the removed content grep, the contract documents, the cross-issue record edits the plan required, the test-tier registration), and run the guarding tests once inside your own isolated worktree. If every criterion passes and no scope remains, the drive is terminal even though the issue is open: report already-delivered with the criteria reads, the ancestor binds, and the test result, then stop. Do not open a token pull request to force the closing keyword, and do not manufacture a failing test to satisfy a test-first delivery protocol — both fabricate work. Escalate closure to the coordinating authority, file follow-up issues for residuals that other lanes own instead of folding them in as drive-by fixes, and clean up only your own artifacts. If only some criteria pass, the delivery is partial: apply the keep-open bookkeeping and escalation of the mid-drive peer-completion audit, not this terminal branch.

   When parallel work has advanced the default branch far past your base, a whole-tree `git diff` of your branch becomes noise — unrelated changes dominate it. Classify coverage by value identity on the paths your intent pins, not by tree equality:

   ```bash
   git show origin/<default>:<pinned-path> | grep -B2 -A2 '<pinned-marker>'
   git show --stat <merge-commit>                     # scope of the landed change
   ```

   Trees may differ (a peer's merged change can touch more files than yours — broader tests, adjacent contexts); the pinned values must match.

   An in-flight lane can also exist before any pull request. A canonical-content duty (for example a durable-learning ceremony that must publish one canonical change) can discover a foreign branch or worktree on a matching slug whose mtimes fall inside its own inspection window, with a ` M` status line but an empty `git diff` (the status line is stat-level evidence — the writer committed between the two reads), and with no pushed branch or open pull request yet. Resolve liveness from the branch reflog, the remote branch list, and a second pull-request read minutes later — never from status lines or mtimes alone. A commit landing inside your window, a push, and then a pull request minutes after mark a live publication. Do not start a competing lane against it: verify coverage on the sibling's committed diff (`git show <their-commit> -- <paths>`) against each decision branch of your own evidence. When the coverage holds, report the sibling's pull request as the outcome of your duty and stop with zero writes. A mandate that nominally demands your own worktree, signed commit, and pull request is satisfied by a verified sibling publication of the same intent: the invariant is exactly one canonical change per intent, not one branch per writer. When the sibling content misses a decision branch that your evidence supports, wait for its publication, then prepare a follow-up amendment instead of racing.
3. Decide per artifact, not per plan:
   - Peer delivered the intent (merged, or an open pull request whose tree contains the signature change): yield. Do not create a competing pull request — it forces duplicate review and rebase churn on both sides. Search peer trees by content (`grep -rl <signature> <peer-worktrees>`), not by pull-request titles alone.
   - Peer work is adjacent and unmerged: defer your rebase until it merges. Queued branches that target code a large peer change rewrites would need two rebases; wait and rebase once. Some queued items may be obsolete after the peer lands — re-check applicability then, not now.
   - Parts of your plan are uncovered (policy text, issue bookkeeping, follow-up comments): keep exactly those parts. They become your new, smaller plan.
4. Dispose safely:
   - Delete an orphaned branch only with the safe form `git branch -d`, and only after you confirm its tip is an ancestor of the default branch (nothing unique is lost).
   - Remove only generated content (test caches, build outputs) from dead worktree paths. Never delete peer stashes, peer worktrees, or saved patches. A stash labeled as preserved is a peer's recovery source; a disconnected peer session may still rely on it.
   - Annotate prepared publication text immediately. A drafted pull-request body or issue comment that names a vehicle that no longer exists must carry a superseded marker at the top, so it cannot be posted verbatim by a later session.
   - Keep a committed local branch whose tip is not an ancestor of the default branch as a local backup when a peer landed equivalent values through different commits. `git branch -d` correctly refuses such a branch because its commits are unique, even though its content is redundant. Do not push it and do not force-delete it while redundancy matters; record its tip once.
5. Keep a source-of-truth patch outside the worktree. Save `git diff` output (including untracked files copied separately) under a build directory before an interruption can strike. Staged-but-uncommitted content dies with a force-removed worktree index; its blobs linger in the object database and `git fsck --unreachable` plus known-marker `git cat-file` scans can recover them, but that is a last resort when no patch exists.
6. Serialize heavyweight validation on a contended shared host. A commit-gate or test suite that dies mid-run with zero FAILED lines and exit evidence of a signal was killed by resource contention, not by a failing test. Do not debug the suite; rerun it alone. Queue your own commits strictly one at a time on such hosts.

Define completion by evidence: branch tips recorded, the peer artifact that covers the intent named, each disposed artifact listed with its safe-disposal proof, and the remaining re-scoped plan stated.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Resuming from pre-interruption memory | Planned to re-apply the prepared patch as-is after the restart | The peer session had merged adjacent work, advanced the default branch, staged the shared worktree, and then removed it; the prepared plan no longer matched reality | Probe the live repository first; state summaries decay within hours on an active shared repository |
| Verifying before every heavyweight commit | Ran a full fast-selection suite as a separate pre-commit verification while peer hook suites ran concurrently | The suite was killed mid-run with zero FAILED lines by host contention, burning ~10 minutes with no result | On a shared host, serialize heavyweight suites; a silent mid-run kill is a contention symptom, not a test failure |
| Counting on staged content surviving cleanup | Relied on the worktree index and working tree to hold the prepared change | A force-removed worktree destroyed both; only blobs in the object database and an independently saved patch survived | Keep a source-of-truth patch outside the worktree; treat the index as volatile |
| Verifying peer parity with a whole-tree diff | Diffed a stale local branch against the advanced default branch to check whether a merged peer change carried the same pinned values | Weeks of unrelated parallel merges dominated the diff; equivalence was unreadable | Compare pinned values at their paths (`git show origin/<default>:<path> \| grep`) and scope the landed change with `git show --stat <merge-commit>`; do not compare trees |
| Starting to drive a named pull request without fetching its state | Prepared review rounds against the assigned pull request on the restart directive alone | The pull request had merged during the gap; the linked issue was already closed with a completed reason | Fetch the exact state of a named pull request and its closing issue first; a terminal state reduces the drive to verification and a report |
| Adopting a foreign lane's modified-but-diff-empty worktree | Prepared to commit, push, and publish a same-intent branch whose files showed ` M` with recent mtimes and no open pull request | The status line was stat-level evidence only; the owning session committed during the inspection window, pushed, and opened its pull request minutes later | Resolve liveness from the branch reflog and the remote branch list, not from status or mtimes; verify coverage on the sibling's committed diff; report the sibling's pull request as the duty's outcome |

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
- A live in-flight same-intent lane yielded after reflog and remote proof: its committed diff
  checked for decision-branch coverage, its pull request reported as the duty's outcome, and
  zero writes from the yielding session.
- A fully delivered issue reported terminal with acceptance-criteria, ancestor-bind, and guarding-test evidence; closure escalated to the coordinating authority; zero token or empty pull requests opened.
- Orphaned branches deleted only via the safe form with ancestor proof.
- Prepared publication text carries a superseded marker where its vehicle changed.
- Dependent queued work deferred with an explicit re-entry trigger (peer merge), not silently rebased.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Hephaestus | Session-restart recovery with a parallel session's open integration pull request covering the prepared removal | [notes.md](../skills/shared-repo-interruption-yield-to-peer-pr.notes.md) |
| Shared multi-wave configuration repository | Restart directive assigned driving a named sibling pull request that had merged during the gap; pinned values verified on the default branch and the local variant retained unpushed as a backup | [notes.md](../skills/shared-repo-interruption-yield-to-peer-pr.notes.md) |
| Shared mono-repository under a many-lane single-issue worker wave | Resume-after-kill directive carried an approved plan and terminal plan-state label for an issue that two reference-only merges had fully delivered days earlier, with the default branch since migrated further; every acceptance criterion verified on the current tip, both merge commits ancestor-bound, guarding tests green in an isolated worktree; the drive ended as an already-delivered report with closure escalated and one follow-up issue filed | [notes.md](../skills/shared-repo-interruption-yield-to-peer-pr.notes.md) |

## References

- [Interrupted implementation-lane recovery](hephaestus-interrupted-implementation-lane-recovery.md) — resume a single interrupted automation-loop lane
- [Relaunch salvage for an interrupted automation loop](interrupted-automation-loop-relaunch-salvage.md) — preserve in-flight worker output across loop restarts
- [Recover stashed work after a concurrent branch reset](tooling-git-recover-stashed-work-after-concurrent-branch-reset.md) — restore work a concurrent process stashed away
- [Shared-host test environment pinning](testing-shared-host-env-pinning-and-baseline.md) — attribute and isolate environment failures on the same class of host
- [Sandbox tool availability invocation probe](sandbox-tool-availability-invocation-probe.md) — probe execution capability by invocation on each interface before you declare interrupted work blocked
