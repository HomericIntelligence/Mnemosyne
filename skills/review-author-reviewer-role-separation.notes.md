# Notes: review-author-reviewer-role-separation

Supporting evidence for the main skill. Generalized from one live session. Identifiers are omitted under the privacy rules.

## Observed sequence

1. A fresh-context reviewer found issues in a PR. The author had already answered them in a PR comment.
2. The reviewer wrote the author response and then published the verdict. A permission classifier flagged the action as self-approval.
3. The workflow changed. The reviewer returned a blocked result "needs author response". A fixer agent fixed the findings and published the author response. A new fresh-context reviewer reviewed the new head and delivered the verdict.
4. A later rebase and a base-branch merge each moved a PR head. Each move invalidated the earlier GO and cancelled auto-merge pinned to the old head. A re-review of the new head restored the gate.
5. One clean source review was refused at delivery. Causes seen: a linked-issue digest that drifted after a later issue comment, and an older unfinished exchange that made the reviewer-state history a forked chain. The owner gave explicit authority. The terminal state was rendered with the exchange reducer, published directly, and the readback was verified.
6. A chained publish command reused a stale payload file from a shared temporary directory. It published a stale duplicate review twice. The reviews could not be deleted.
7. A plain rebase of a branch with merge commits dropped the changes made inside the merges. The net diff was rebuilt as clean commits. Decision-record numbers collided with the base branch and were renumbered with all references. In one case the base already held the change, so the branch was not pushed and the owner was told to close the PR as superseded.

## Guard pattern for chained publish commands

- Create a new empty directory for each run.
- Run from the repository directory.
- Use `set -e` or an explicit `&&` chain so that a failed head or repository check stops the chain.
- Read the live head again immediately before each write.

## Addendum: dispatch block and inline-degradation recovery (2026-11-01)

Observed sequence, generalized from one session:

1. A background reviewer sub-agent returned a dispatch-time admission timeout
   before its first tool call. The footprint was zero.
2. The author session read the athena review skill and ran the review
   protocol itself, including the delivery helper. This prepared a terminal
   carrier for the change that the author wrote. The carrier was not an
   independent verdict.
3. A second dispatch started after the author had moved on, used a fresh
   context, and delivered a terminal GO with explicit independence wording.
   That delivery was the valid merge gate. The author's prepared carrier was
   a candidate that the helper refused to publish because a terminal carrier
   from another exchange already existed at the exact head.
4. The merge proceeded through the independent carrier. The author did not
   publish a second terminal state.

Recovery rules that this sequence supports:

- Treat an inline review by the author as author evidence. Label it as such.
  Do not use it as the merge gate.
- Bound re-dispatch attempts before you escalate. Re-dispatch in background
  mode so the author's remaining bookkeeping does not block.
- Give a fresh-context reviewer subagent explicit wording that its context is
  independent and that the platform permits it to deliver a GO.
- Classify any late delivery refusal as a sibling preemption before you
  treat it as a wedge. Audit the sibling carrier against your own prepared
  digests.
