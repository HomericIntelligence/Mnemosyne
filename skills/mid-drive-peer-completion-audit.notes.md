# Notes — mid-drive-peer-completion-audit

Evidence for `mid-drive-peer-completion-audit.md`. Generalized per the privacy
rules; repository identity, issue numbers, and internal identifiers are
withheld.

## Measured pass (2026-10-25)

Environment: a large shared monorepo under a many-lane release wave; a
coordinator directive issued a serial three-issue implementation queue with
pipeline state taken from a snapshot about one hour old. Queue rule per
issue: verify state, adopt any existing PR instead of re-implementing, run
the review exchange to a terminal verdict, swap the issue state label to the
terminal rank, arm merge, and drive checks green.

### Item 1 — peer finished the round under one actor

The driver's round-1 reviewer returned NO-GO with two inline findings. During
the driver's idle gap, a different lane performed the author-response, the
round-2 review, the terminal GO, and the merge — all under one GitHub actor,
and it skipped the issue-label swap. The driver audited the merged result
against its own head (same diff, one repair commit added), verified forge
coherence (review carrier bound to the exact GO head, merge commit on the
default branch), executed the missing issue-label swap, and recorded the
reviewer-independence gap in its report. Zero work redone.

### Item 2 — driver verdicts withheld on an immutable artifact

The driver's own round-1 reviewer completed a NO-GO assessment with two minor
findings but could not publish: a peer session had run its complete exchange
(NO-GO, then GO, then merge) on the same PR minutes earlier. The two heads
differed by one renumber-only commit; content equality was verified file by
file. The peer had again skipped the issue-label swap; the driver completed it
post-merge. Pre-merge checks at the reviewed head were green; post-merge
failures on the default branch were classified unrelated by comparing the
identical failure pattern on the adjacent commits before and after the merge.

### Item 3 — partial scope by plan decision table; two reviewers raced

Queue-start discovery found a prior session's PR, adopted after verifying it
matched the approved plan (attribution fix plus a surfaced exit-code contract,
with new tests). The environment blocked the plan's diagnostic probe (no
container runtime option, no read access to the weights directory), so the
plan's decision table selected the row that ships failure-attribution only
and keeps the crash fix open. The PR used a `Refs` body keyword per the plan.
Two background review processes then raced the PR — one attributable to a
prior lane, one to the current drive. A third session delivered terminal GO
and merged while both reviewers still ran. Both orphan reviewers were left
alive: they read from their own snapshot directories, and the exact-head
publication guard withholds delivery on a merged artifact. The driver posted
the lane-record comment on the still-open issue (decision-table row, shipped
scope, remaining scope), retained the plan-state label, escalated the
disposition, and removed the adopted worktree plus branch after binding the
merge commit and confirming no reviewer read from it.

### Cleanup evidence pattern

- Squash merge ⇒ lane-branch commits are not ancestors of the default branch;
  `git branch -d` refuses correctly, and deletion is justified only by the
  bound merge commit and the PR `MERGED` state.
- Pre-merge checks at the reviewed head were green on all three items; the
  default branch carried pre-existing cross-lane failures, classified with
  adjacent-commit comparisons rather than assumed.

### Delivered-evidence reproduction method (v1.1.0 added case)

A separate review session audited a delivered terminal carrier on a merged
artifact. Its anchor manifest published SHA-256 digests for two diff lenses.
A `git diff` over the same ranges with default flags produced different
digests from the published values; the identical ranges under the publisher's
documented serialization flags (a full-index diff format) matched both
digests exactly.

- Decision rule: before you report a digest or manifest mismatch as tamper
  evidence, find the flags the publisher documents for the record type and
  rerun with those flags. A difference under different flags is a flags
  mismatch, not a content mismatch.
- This changes a decision: without the clause, an honest audit can misreport
  a healthy delivered record as corrupted and can drive a wrong void/repair
  or an escalation of a false finding.

## Provenance

- Delivery base: `8cdb8d577bc7e984bfcd295b855a91e77cc5a65d` (main, refresh
  verified at write time).
- Duplicate checks at write time (bound corpus, 857 retrievable mains):
  - `shared-repo-interruption-yield-to-peer-pr` — resume-after-interruption
    yield for prepared-but-undelivered work. Distinct: this skill covers an
    active drive whose own artifacts move under it.
  - `hephaestus-interrupted-implementation-lane-recovery` — salvage before
    first publication. Distinct trigger.
  - `parallel-agent-swarm-dispatch-patterns` — dispatch-time `Refs`/ `Closes`
    keyword rule. This skill supplies the post-merge issue-side bookkeeping
    that the keyword rule does not cover.
  - `github-pr-review-record-void-repair` — post-publication carrier repair;
    different boundary (already-published records).
  - Keyword sweeps performed for: lane adoption/salvage/handoff, refs-vs-
    closes/partial scope/decision table, review race/duplicate reviewer,
    multi-lane coordination. No additional intent match found.
- Open PRs at write time: 15 enumerated in the delivery repository. Two are
  adjacent and pending: one adds a queue-start leftover-branch classification
  (zero-ahead merge-state check — pre-drive, not mid-drive), one amends the
  resume-yield entry for a different case. None conflicts with this entry.
