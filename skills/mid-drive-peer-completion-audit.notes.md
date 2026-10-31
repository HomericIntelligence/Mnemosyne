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

## Zero-delta takeover of a delivered rebase task (v1.2.0 case, 2026-10-31)

Environment: the same shared monorepo under many-lane operation. A directive
assigned one open-PR task: rebase the branch onto the default branch and
resolve each conflict. The directive asserted that the PR was conflicting
against the default branch and could not merge.

### Live read at pickup

- The forge reported the PR mergeable and clean, not conflicting.
- `git merge-base <default> <head>` equaled the default-branch head; the
  branch held only the two reviewed commits. The directive premise was
  already false at pickup.
- PR timeline: approval label at about 03:53 UTC; two head force-pushes at
  about 09:11 and 09:22; a handover comment at about 09:39, about 17 minutes
  before pickup. The shared forge actor made all posts, so worker identity
  comes from the name prefix in the comment, not from the actor field.

### Handover audit

The peer's handover comment named the old head (the approval head), the new
head, one resolved conflict (a modify/delete on a documentation page the
default branch had deleted; the PR-side section was not relocated — a
documented, deliberate content drop), two branch-caused check repairs (a new
test module missing from the tier partition, and a typed fake for a static
type gate), local validation results, and the final check status.
Independent verification agreed at every point: all checks green at the new
head, the approval label retained, mergeable and clean state, auto-merge not
armed, and the added commit signed and signed-off.

### Disposition

The delta was empty: every contract step, including the report, was already
delivered. The pickup did not re-run the rebase, did not push, and did not
post a duplicate comment. It reported the takeover (old head, new head,
evidence, label coverage) and stopped. A second rebase would have produced a
third head, invalidated the peer's green checks, and duplicated the report.
The approval label binds to the exact old head; the record states that it
does not cover the new head even while the label stays on the PR.

## Provenance (v1.2.0)

- Delivery base: `188d710bc0b0bc1ba873402133fea0d79c61a300` (main). The parked
  checkout was on a merged feature branch, so the delivery worktree bound
  directly to the fetched default head.
- Duplicate checks at write time: the four then-open PRs in the delivery
  repository changed no byte of this entry. A bound-corpus sweep (mid-drive,
  peer, stale, premise, lane, claim) found no same-intent entry: the
  stale-premise family splits into `stale-plan-already-resolved` (defect
  premise on captured artifacts) and this entry (peer-completion takeover),
  and no current entry carries the zero-delta branch or the rebase-shape
  probes (merge-base equality, force-push timeline).

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
