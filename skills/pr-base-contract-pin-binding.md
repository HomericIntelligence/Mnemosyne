---
name: pr-base-contract-pin-binding
description: "Open a pull request against the base branch that the consuming contract pins, not the repository default branch. Use when a delivery crosses repository boundaries and the consumer pins the producer's integration branch to an exact commit, when the default branch has diverged far from the pinned branch, or when a fresh pull request shows a far larger diff than the intended change."
category: tooling
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [pull-request, base-branch, contract-pin, cross-repository, divergent-base, wrong-base-diff, retarget, preflight]
---

# Bind the Pull-Request Base to the Contract-Pinned Branch

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Open every cross-repository pull request on the base branch the consumer's contract pins, so the presented change equals the intended change. |
| **Outcome** | Operational. A pull request first opened on the producer's default branch presented the whole divergence between the default branch and the pinned integration branch (about 880 files, +157k lines) instead of the intended change (15 files, +1323/-98). Retargeting to the pinned base returned the diff to the intended change, and the review proceeded on the presented change set. |

## When to Use

- A delivery crosses repository boundaries, and a consumer repository's contract pins the producer's integration branch to an exact commit.
- The producer repository keeps a default branch and a separate pinned integration branch (for example a production branch), and the default branch can run far ahead of the pinned branch.
- A new pull request shows a file count or a line count far above the intended change set.
- The lane plan names a base branch from habit or from repository default settings rather than from the consuming contract.

## Verified Workflow

### Quick Reference

Bind the base before the first push:

```bash
# 1. Read the pinned base from the consuming contract.
grep -rn "<producer-repo-name>" <consumer-contract-path>

# 2. Verify the pinned branch state before opening the pull request.
git fetch origin --quiet
git rev-parse origin/<pinned-branch>        # compare with the contract-pinned commit

# 3. Preview the pull-request diff against the pinned base.
git diff --stat origin/<pinned-branch>...<delivery-branch> | tail -1
# A file count far above the intended change set == wrong base. Stop here.

# 4. Open on the pinned base explicitly. Never inherit the repository default.
gh pr create --base <pinned-branch> --head <delivery-branch> ...
```

### Suggested Approach

1. Read the base gate from the consuming contract, not from repository defaults. The pinned record (branch name plus exact commit) outranks the producer repository's default-branch signal. When the plan does not name the base gate, the plan is incomplete: find the pin first.
2. Verify the pinned branch against the contract before opening. Fetch and compare the branch tip with the contract-pinned commit. A tip that differs from the pin is new evidence for the contract owner, not permission to pick a different base.
3. Preview the pull-request diff against the pinned base and compare the file count and line totals with the intended change set. A preview far above the intended size is a wrong-base or contaminated-history signal. Stop before the open; a pull request that presents divergence noise costs a review binding, CI runs, and reviewer attention on a change nobody intends.
4. Open the pull request with the pinned base named explicitly. The repository default applies only to pull requests that represent no pinned consumer.
5. If the pull request is already open on the wrong base, retarget it to the pinned base and re-verify the preview: the file set must return to the intended change set before the review continues. Record the retarget in the pull request so the review ledger stays honest.
6. When the change genuinely needs content that only the default branch carries, do not widen the base. Escalate the pin move to the contract owner, or deliver against the pinned base and hold content that waits for the pin.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Open on the default branch by habit | A cross-repository delivery opened its pull request on the producer's default branch because the default is the usual base and no base gate ran in the lane | The consumer's contract pinned the producer's integration branch to an exact commit; the default branch had run far ahead of the pinned branch, so the pull-request preview showed about 880 files and +157k lines instead of the intended 15 files and +1323/-98 | The pinned record outranks the repository default; preview the pull-request diff against the pinned base, and treat a far-larger file count as a wrong-base signal before the open |

## Results & Parameters

### Configuration

| Parameter | Value | Meaning |
| --------- | ----- | ------- |
| pinned base | branch name and exact commit from the consuming contract | the only binding base reference |
| check points | before the first push, and before the pull-request open | the two moments a wrong base is still free |
| preview gauge | intended change-set file count and line totals | a preview far above them is a wrong base, not more context |
| wrong-base recovery | retarget to the pinned base, then re-verify the preview | keep the review on the intended change |
| pin drift | branch tip differs from the contract-pinned commit | evidence for the contract owner, not a base choice |

### Expected Output

- The pull-request file list and line totals equal the intended change set.
- The base branch equals the consumer-pinned integration branch, verified against the pinned commit.
- The review proceeds on the intended change; no retarget event marks the exchange.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Cross-repository automation delivery between a shared producer and a contract-pinning consumer | The contract pinned an exact commit on the producer's integration branch; the initial pull request on the default branch showed about 880 files and +157k lines against the intended 15 files and +1323/-98; the retarget to the pinned base recovered the intended diff | [notes](pr-base-contract-pin-binding.notes.md) |

## References

- [stale-base-upstream-landing-recheck.md](stale-base-upstream-landing-recheck.md) — the sibling guard for the other stale-base failure mode: upstream landed the same scope during a lane. This entry covers base selection to a pinned integration branch, not scope overlap.
- [automation-multi-repo-pr-sweep-rebase-resolve.md](automation-multi-repo-pr-sweep-rebase-resolve.md) — the multi-repository sweep this base guard runs inside.
- [verify-commit-landed-before-opening-pr.md](verify-commit-landed-before-opening-pr.md) — the content-side preflight that runs beside the base check.
