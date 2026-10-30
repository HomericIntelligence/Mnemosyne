---
name: agents-pr-review-forked-terminal-verdict-supersession
license: BSD-3-Clause
description: "Supersede a pull request whose review history forked under near-simultaneous terminal verdicts from two publishers. Use when an exchange/ledger-based review shows two terminal verdicts posted seconds apart, so label and merge delivery cannot bind one history."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: execution-observed
tags:
  - pr-review
  - review-exchange
  - ledger-fork
  - publisher-race
  - supersession
  - terminal-verdict
  - coordination
  - execution-observed
---

# Forked Terminal Verdicts: Supersede, Never Arbitrate

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-30 |
| **Objective** | Recover cleanly when two publishers post terminal review verdicts on the same pull-request head seconds apart, forking the review history and making label/merge delivery ambiguous. |
| **Outcome** | SUCCESS — PR superseded at the same branch and head, one fresh reviewer round by a single designated session, merged with exclusive GO label. The superseded lane published nothing further. |

## When to Use

- Your review protocol is ledger- or exchange-based (rounds, carriers, author-responses) with a single expected publisher per round.
- Two publishers both publish a terminal verdict (GO, or any verdict that ends the round) against the same PR head within seconds — the ledger now contains two divergent "round 1 terminal" histories.
- Downstream delivery (label swap, auto-merge arm, finalization) depends on binding to ONE complete history and can no longer determine which history is canonical.
- Prevention already failed: lanes had "donot double-drive" rules, but both publishers prepared and published against the same open window.

## Verified Workflow

### Quick Reference

```bash
# Step 1 — DETECT the fork: two terminal carriers at near-identical timestamps,
# each cryptographically/structurally valid on its own, claimed terminal on the
# same exchange id and head.
# Step 2 — STAND DOWN every non-designated publisher for that PR immediately:
# no further carriers, no labels, no merges, no "clarifying" edits.
# Step 3 — DESIGNATED OWNER (coordinator/session owner) closes the forked PR
# UNMERGED with a plain-language reason and points to the replacement PR.
# Step 4 — REPLACEMENT PR on the SAME branch and SAME head (no rebase churn).
# Step 5 — exactly ONE fresh reviewer round by ONE designated session on the
# replacement PR; nobody else reviews, labels, or merges it.
# Step 6 — label + automerge only from the replacement PR's single delivered
# history. The superseded lane does read-only residue verification and cleanup
# of its own artifacts (worktrees, branches) — it publishes nothing.
```

### Detailed Steps

1. **Detect the fork.** Compare published terminal carriers' timestamps and binding proofs. If both parse/verify cleanly and both claim terminal state on the same exchange at the same head, picking a winner by timestamp or trust ranking is NOT safe: each publisher's subsequent author-response/round logic can follow a different history, compounding the fork.
2. **Stand down non-designated publishers.** Any lane that had a prepared round for that PR discards it. Do not publish "my round was first" evidence on the PR; that adds a third lineage.
3. **One designated owner supersedes.** The coordinator (or explicit owner) closes the forked PR unmerged, stating the first cause plainly in the closing comment (forked review history; two terminal verdicts published ~simultaneously) and naming the replacement PR. This creates an auditable single narrative.
4. **Open the replacement on the same branch and head.** The code artifacts are sound; only the review history is contaminated. Opening PR2 at the identical head avoids rebase churn and keeps CI binding trivial. Include the same body and a one-line supersession pointer.
5. **One fresh round, one publisher.** The designated reviewer session runs round 1 on PR2 fresh (new exchange id, exact-head binding). The closing comment on PR1 should also instruct the review loop not to review/label/merge PR2 — that single round belongs to the designated session. Everyone else stays hands-off until it lands.
6. **Deliver through PR2 only.** Label swap, auto-merge, and merge evidence all flow from PR2's single complete history. After merge, a verification pass confirms: merge commit ancestor of main; exactly one state label; residue checks (for subtractive PRs) as applicable.
7. **Superseded lane finishes as read-only.** It verifies the landed result (post-merge residue greps, file-byte comparisons where promised), cleans its own worktrees/branches, reports, and stops. It must not interact with either PR further.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treat one of the two terminal GOs as authoritative | Continue rounds or label delivery against "the first" GO | Both carriers verify cleanly; downstream tooling sees two valid competing histories and every later round risks splitting again | A fork in a ledger protocol is structural, not a question of which publisher was right; supersede the PR |
| Let both publishers "converge" by exchanging author-responses on the forked PR | Trying to reconcile the two histories in place | Each new carrier relies on its own history's acceptance set; adds a third divergent lineage instead of merging the two | Stand down non-designated publishers immediately; only the designated owner supersedes |
| Re-create the superseded PR at a NEW head to "disambiguate" | Rebase or push an extra commit to make PR2 distinct | The problem is the review history, not the code; unnecessary churn breaks the head-binding CI/verdict artifacts for zero benefit | Supersede at the SAME branch and head; only the reviewer round restarts |

## Results & Parameters

A choreography-PR carrying a small subtractive change reached terminal GO from two publishers one second apart. Coordinate-heal sequence above executed verbatim: forked PR closed unmerged at the old head with first-cause note; replacement PR on the same branch/head; exactly one designated fresh round; exclusive GO label; merged minutes later with merge commit ancestor-verified; superseded lane performed read-only residue verification and cleanup only.

Verification: the label readback showed exactly one state label (exclusive GO); merge commit was an ancestor of main within minutes of merge; the forked PR's review/label/merge state remained exactly as the designated owner set it (untouched by other lanes). No test suite regression — the change was additive-only-to-deletion-safe by construction.

## Verified On

A multi-lane autonomous pull-request wave on a repository with a ledger-based review-exchange protocol (rounds bound to exact heads, exclusive state label, squash auto-merge). Two independently-acting publisher lanes raced a terminal verdict inside one open window; the supersession flow above restored single-history delivery with full audit trace.
