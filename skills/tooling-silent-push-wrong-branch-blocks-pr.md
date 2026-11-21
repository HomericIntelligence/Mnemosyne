---
name: tooling-silent-push-wrong-branch-blocks-pr
description: "Use when your fix push succeeds but the target PR's head branch or merge state does not advance — the working tree pushed a sibling branch or a detached head instead of the PR's headRefName. Verify PR head OID after any push."
category: tooling
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags: [git, push, branch, pr-target, pr-head-oid, headrefname, ci-queue, blocked-pr, merge-queue, wrong-branch, dispatch]
---

# Tooling: Silently Push to the Wrong Branch, and the PR Goes Nowhere

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Stop burning time proving a PR should have moved when the local "pass" push silently landed on a sister branch. Bind the working tree to the PR's actual headRefName before any push, and confirm the remote side afterwards. |
| **Outcome** | Operational. The class of waste (local proof repeated, wrong branch ref quoted, CI rollup read against a stale head) is named here with a one-line verification rule. |

## When to Use

- You push a fix to close a red PR and the PR's `headRefOid` does not become your commit, or its `mergeStateStatus` stays `BLOCKED` after a correct change.
- You observe a green push with a short SHA that your PR does not carry.
- You find later that the same change exists on a sister branch or in another worktree's HEAD, while the intended PR still runs on the pre-fix base.
- The checkout's HEAD is detached, `branch --show-current` prints nothing, or one local branch name equals the PR's `headRefName` but the working tree is on another.

## Verified Workflow

### Quick Reference

```bash
# 0) Before the push: bind
gb=$(gh pr view <PR> -R <org>/<repo> --json headRefName --jq .headRefName)
git branch --show-current   # MUST equal "$gb"
# 1) Push only when bound; do not push from ambiguous detached HEADs
git push -u origin HEAD:"$gb"
# 2) After the push: verify the PR head advanced
gh pr view <PR> -R <org>/<repo> --json headRefOid,mergeStateStatus
```

### Suggested Approach

1. Read the PR's authoritative head before writing:
   `gh pr view <PR> --json headRefName,headRefOid,headRefName,mergeStateStatus,labels`. The PR's
   `headRefName` is the only ref the merge queue admits for that PR. Any other branch you push to
   (a sister branch you branched from, a detached HEAD, or a different PR's head) is a successful
   remote operation that cannot unblock the original PR.
2. Before `git commit`, run `git branch --show-current` and compare it with the bound `headRefName`.
   If it differs, check out `headRefName` (creating it at the expected SHA only if the forge
   has that branch as the PR's head source) or push with an explicit `git push -u origin HEAD:$gb`.
   Avoid pushing by bare `origin HEAD` when the tree may be detached.
3. After the push, query the same remote PR immediately and read `headRefOid`. It must equal
   the SHA you produced, or the PR still tracks the previous SHA. If it matches an older SHA
   (or an unrelated one), treat the mismatch as a data problem to investigate, not as a reason
   to revert the commit; compare remote refs before any destructive action.
   `git ls-remote origin <headRefName>` gives the authoritative ref comparison from your side.
4. If `mergeStateStatus` stays `BLOCKED`, read the current check rollup for the **present**
   `headRefOid` — not the PR's last-known one — and classify the failing gate before re-running
   the pipeline. Stale check-runs on superseded SHAs are common; the latest run's verdict is
   kept with the OID where it ran.
5. When multiple agents work against the same PR, coordinate one writer; see
   [Peer Rewrote the PR Head](./peer-rewrote-pr-head-orphaned-push.md) — that entry covers the
   concurrent-race case; this one covers silent branch mismatch.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Cherry-pick & push from a fresh worktree on a previously touched sister branch | Implemented a long-line lint fix for a PR on branch `fix/X` using `.worktrees/coverage-y` that had been reused shortly before. `git push -u origin fix/X` succeeded; PR head never moved. | The worktree carried a detached remnant; `git branch --show-current` printed the sister branch name (`test/coverage-…`) and the push silently advanced `test/coverage-…`, not `fix/X`. | Always check `git branch --show-current` before the push; refuse to push when the live branch is not the PR's `headRefName`. |
| Poll the PR's `--json mergeStateStatus` to confirm the fix landed | Reported `BLOCKED` and re-read check-runs on the stale head once per minute for several minutes. | The rollup remained stale until the actual `headRefOid` moved; the rollup is per OID, not per PR. | Poll the PR's `headRefOid` after the push; only then re-evaluate the blockers. |
| Push explicitly to `HEAD` without a refspec | Assumed `origin HEAD` tracks the branch borrowed name from the open PR. | The checkout was detached; `origin` accepted an unrelated destination; the PR's branch held stale commits. | Never rely on `origin HEAD`; bind the ref by name, then push `HEAD:<headRefName>`. |

## Results & Parameters

- Verified: a single `gh pr view ... --json headRefOid` before and after the push correctly
  identifies a blocked PR caused by branch mismatch against this signature (push succeeds, PR
  blocked; SHA differs before/after the PR's head changes).
- Default action after any such push signature: bind the worktree to the correct
  `headRefName`, then rebase your change onto the head and push as one `HEAD:<headRefName>`.
- The same signature also appears from concurrent-writer races; cite the companion entry before
  blaming the CI.
