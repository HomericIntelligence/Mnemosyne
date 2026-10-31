---
name: shared-checkout-unstable-ref-reads
license: BSD-3-Clause
description: "Verify live remote revision state through a forge API or an explicitly pinned SHA before a repair or write decision, because ambient refs in a shared or multi-lane Git environment can silently regress between two reads or differ across checkout lanes. Use when a fetch-by-branch-name result (such as FETCH_HEAD) is read again after any time gap, when two reads of the same ambient ref disagree, when a peer lane can fetch or merge in the same store between your reads, or when one checkout lane's remote-tracking ref lags behind a lane another process refreshes."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - git
  - shared-checkout
  - ambient-refs
  - verify-before-write
  - forge-api
---
# Skill: shared checkout unstable ref reads

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-30 |
| **Objective** | Prevent repair or write decisions from accepting stale readings of ambient Git refs (`FETCH_HEAD`, `origin/<branch>`) in shared, concurrently fetched environments |
| **Outcome** | A false "pull request content dropped" conclusion, minutes from an unneeded recovery push, was stopped by a forge API re-read; a stale `origin/main` in a second checkout lane was caught by SHA pinning before it became a stale delivery base |
| **Impact** | Prevents false remote-state conclusions, duplicate recovery writes, and branches based on silently outdated tips |

## When to Use

- You fetched a branch by name and read `FETCH_HEAD`, `origin/<branch>`, or another
  shared ref again after any pause; a peer lane may have fetched in between.
- Two reads of the same ambient ref disagree, or local Git evidence contradicts a
  recent forge read (`gh pr view --json headRefOid`, `gh pr diff`).
- Local evidence suggests remote content was lost, reverted, or replaced, and you are
  about to re-push, force-push, or open a repair: re-read the forge first.
- A resolver or automation selects one of several checkout lanes for the same
  repository; each lane that is a separate clone advances its remote-tracking refs
  only on its own fetches, so `origin/<branch>` can be days stale in an idle lane.

## Verified Workflow

1. Bind remote state through the forge, not the ambient ref:

   ```bash
   gh pr view <n> --repo <owner>/<repo> --json headRefOid,files   # binding read
   gh pr diff <n> --repo <owner>/<repo>                           # content read
   ```

2. When local Git evidence must be used, pin full SHAs in the same command block as
   the fetch and read only by SHA afterwards:

   ```bash
   git fetch origin <branch>
   HEAD_SHA=$(git rev-parse FETCH_HEAD)     # pin immediately; same command block
   git log --oneline <base>..${HEAD_SHA}
   git show ${HEAD_SHA}:<path>              # never re-read FETCH_HEAD after a gap
   ```

3. Treat an ambient-ref read as valid only within one uninterrupted command
   sequence. A resume, a response gap, or any peer activity invalidates the earlier
   read.
4. When local Git evidence and forge evidence disagree on remote state, the forge
   wins. Investigate the checkout (peer fetch lanes, separate clones, helper
   refreshes) instead of repairing the remote.
5. Before branching from `origin/<branch>`, fetch in that exact checkout lane, pin
   the resulting SHA, and compare it against the forge-known tip.

### Quick Reference

| Symptom | Cause | Action |
| --- | --- | --- |
| Second read of an ambient ref returns an older revision | A peer lane's fetch rewrote the shared ref, or an idle clone lane holds an older copy | Pin the SHA in the same command block as the fetch; fetch in the lane you branch from |
| `git diff <ambient-ref> origin/main` suddenly empty while the forge diff still shows the change | The ambient ref regressed to the checkout's for-merge upstream | Trust `gh pr diff`; investigate the checkout |
| Local "content lost" signal after a time gap | Stale ref, not lost content | Re-verify through the forge API before any repair write |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Read `git log --oneline FETCH_HEAD -- <path>`, `git show FETCH_HEAD:<path>`, and `git diff FETCH_HEAD origin/main` minutes after a branch fetch and an ancestor check that had bound the correct head, and nearly concluded that peer merges had silently dropped pending pull-request content | The shared checkout's FETCH_HEAD had been rewritten by peer fetch activity during the gap; the second read resolved an older entry version while the pull-request head still carried the full change (forge diff +107/+37, all checks green) | Ambient refs in a concurrently fetched checkout are mutable across lanes; re-verify remote content through the forge (`gh pr diff`, REST `pulls/<n>/files`) before any repair, and pin SHAs in the fetch command block when local evidence must be used |
| 2 | Created a worktree from `origin/main` in a resolver-selected dependency checkout after a different lane of the same environment had just reported a fresh refresh of main | That checkout lane was a separate clone whose remote-tracking refs moved only on its own fetches; its `origin/main` was days and dozens of merges stale, which silently produced a stale base | Fetch inside the checkout lane that supplies the base, pin the returned SHA, confirm it against the forge-known tip, and branch from the pinned SHA |

## Results & Parameters

| Parameter | Value | Notes |
| --- | --- | --- |
| Binding read for pull-request state | `gh pr view --json headRefOid,files`, `gh pr diff`, REST `pulls/<n>/files` | Computed by the forge from live head and base |
| Valid lifetime of a shared FETCH_HEAD read | One uninterrupted command block | Any gap admits a peer rewrite |
| Local fallback when API access is unavailable | `git fetch origin <branch> && SHA=$(git rev-parse FETCH_HEAD)`, then SHA-only reads | Extends to `git fetch origin <sha>` pinning |
| Base for a new branch in multi-checkout setups | Pinned SHA after a fetch in that same lane, compared against the forge-known tip | Do not assume another lane's refresh applies |
| Verification basis | `verified-live` | Stale-ref regression and stale-clone base observed in a production multi-lane knowledge-corpus environment |
