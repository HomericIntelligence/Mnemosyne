---
name: agents-pr-review-forked-terminal-verdict-supersession
license: BSD-3-Clause
description: "Deliver a valid review verdict on the same pull request when the review-exchange helper refuses it for bookkeeping reasons (forked chain, head move during delivery, edited carrier, authority record a shared login cannot give). Post a plain exact-head review and verify before auto-merge; do not open replacement PRs. Use when two terminal verdicts fork the history or a helper rejects a head-bound verdict."
category: tooling
date: 2026-10-30
version: "1.1.0"
user-invocable: false
verification: execution-observed
tags:
  - pr-review
  - review-exchange
  - ledger-fork
  - publisher-race
  - direct-verdict
  - no-replacement-pr
  - terminal-verdict
  - coordination
  - execution-observed
---

# Review Delivery Refused: Post Direct Exact-Head Verdict, Never Replace the PR

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-06 |
| **Objective** | Deliver a valid reviewer verdict bound to the exact head commit when an automated review-exchange helper refuses it because of bookkeeping state, without multiplying pull requests, reviews, or CI runs. |
| **Outcome** | The verdict is posted as a plain review on the same pull request; the coordinator verifies it and enables auto-merge. |

## When to Use

- A reviewer holds a valid verdict bound to the exact current head, but the exchange helper refuses to deliver it.
- The cause is bookkeeping state, not the code or the verdict: a forked exchange chain (two terminal verdicts posted seconds apart), a head move during delivery, an edited carrier review, or a required-authority record that a shared login cannot give.
- Label, auto-merge, or finalization steps cannot bind one history.
- The competing terminal GO contradicts your source evidence, because your review found a defect that the zero-finding GO missed.

## Repair the code before you deliver the verdict

A direct verdict carries the current code forward into the surviving history. It
does not change the code. Before step 3, decide whether that is safe:

| Your evidence about the code | Disposition |
| --- | --- |
| Sound. The fork is only a review-record problem. | Post the direct exact-head verdict. |
| Defective. You found a required defect that the competing GO missed. | Do NOT post a pass verdict. Repair the branch first. |

A pass verdict on code you know is wrong merges the defect behind a clean-looking
record. Repair the branch instead. The repair changes the head, which ends the
stale terminal exchange and lets one designated session start a fresh round at
the new head. A head change caused by new code is the one case where a new head
is correct: the problem is no longer only the review history.

Record the defect and its repair in the verdict's first cause, so the record
shows why the head moved.

### Why not a replacement pull request

[Pull request #3838](https://github.com/HomericIntelligence/Mnemosyne/pull/3838)
recorded the replacement-PR recovery: close the forked PR unmerged, then reopen
the same branch and head as a second PR and run one fresh round. The owner
rejected that recovery. It doubles PRs, reviews, and CI runs for a bookkeeping
failure, and the second PR carries the same code. The direct exact-head verdict
delivers the same single history without the extra PR.

## Verified Workflow

### Quick Reference

```bash
# 1. Reviewer: post the verdict as a plain review bound to the exact head.
gh api repos/<OWNER>/<REPO>/pulls/<PR>/reviews -X POST \
  -f commit_id=<EXACT_HEAD_SHA> -f event=COMMENT -f body="<verdict text>"
# 2. Coordinator, before enabling auto-merge, verify all three:
gh pr view <PR> --json headRefOid          # equals the review commit_id
git verify-commit <EXACT_HEAD_SHA>         # signature valid
gh api repos/<OWNER>/<REPO>/pulls/<PR>/reviews --jq '.[-1]|{commit_id,body}'   # verdict text
```

### Detailed Steps

1. **Confirm the fork, then stand down extra publishers.** Compare the published terminal carriers' timestamps and binding proofs. When both parse and verify cleanly and both claim terminal state at the same head, neither has precedence. Every lane except one designated reviewer stops publishing carriers, labels, and merges for that PR. Do not pick a winner by timestamp or trust ranking; each publisher's later round logic can follow a different history and compound the fork.
2. **Do not open a replacement PR.** A replacement PR doubles PRs, reviews, and CI runs. The owner rejected this recovery. The code is sound; only helper bookkeeping failed.
3. **Post the verdict directly.** The reviewer posts a plain review with `commit_id` set to the exact head. The verdict text stays the same as the refused verdict.
4. **Verify before arming.** The coordinator checks that the review `commit_id` equals the current head, that the head commit signature is valid, and that the verdict text is a pass verdict. Then enable auto-merge pinned to that head.
5. **Reuse the reviewer.** Use the same reviewer agent for the same issue across rounds. A new reviewer has no context and restarts findings.
6. **Treat a head move as stale.** A later head move makes the verdict stale. Re-review the exact new head. A test-only delta is a short re-review.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Replacement PR for a clean exchange | Close the PR and reopen the same branch to restart the exchange | Doubled PRs, reviews, and CI runs; the owner rejected it | Bookkeeping failure is not a reason to replace the PR; post a direct exact-head review |
| Treat one of two terminal verdicts as authoritative | Continue rounds or label delivery against the first verdict | Two valid competing histories; each later round can split again | Stand down extra publishers and deliver one direct verdict |
| Reconcile both histories with author responses | Exchange responses on the forked PR | Adds a third lineage | Do not reconcile in place |
| Arm auto-merge without checking | Trust the posted review | A head move or an unsigned head makes the verdict stale or invalid | Verify head, signature, and verdict text first |

| Supersede at the same head while the code is known defective | Posted a pass verdict for a fork where the competing GO had zero findings but the code carried a required defect | The single surviving history then reviews code already known to be wrong, and the defect merges with a clean-looking record | Decide code soundness before delivering a verdict. Repair first; a head change caused by new code is the correct way to restart the exchange |

## Results & Parameters

- Review state: `COMMENT`, with `commit_id` equal to the head at review time.
- Required checks before auto-merge: head match, valid signature, pass verdict text.
- A head change invalidates the verdict; a test-only delta needs only a short re-review.

A second, contrasting case bounded the direct-verdict rule: one lane published a
zero-finding terminal GO, and an independent reviewer published a NO-GO seconds
later after finding required defects in the same head. Because the evidence
showed the code was defective, the recovery repaired the code first, and the
head change started a fresh round. The competing GO was never treated as the
surviving history, so the defects did not merge behind a clean record.
