# Notes: Lane Branch Zero-Ahead Merge State Check

Supporting evidence for `lane-branch-zero-ahead-merge-check`. All identifiers are
generalized under the privacy policy; the case facts below describe an anonymized case.

## Case timeline (generalized)

1. A reconcile phase for a backlog wave found a leftover automation-generated
   implementation branch for a backlog issue. The branch was `0` commits ahead of the
   default branch.
2. An initial summary classified the branch as "nothing salvageable" from the count
   alone.
3. A fresh adoption pass ran the pull-request state queries and found a merged pull
   request for the same issue, merged hours earlier, with its merge commit reachable
   from the default branch.
4. The audit confirmed delivery: every artifact the delivery contract required was
   present on the current default branch, and the contract-named behavior tests passed
   there (14 targeted selections, 0 failures).
5. No re-implementation happened. The queue advanced to the next issue.

## Why the two readings matter

- Post-merge, a feature branch head becomes an ancestor of the default branch (merge
  commit or squash result contains its content). `git rev-list --count
  origin/<default>..<branch>` is exactly `0` for both an empty lane and a delivered one.
- The cheap discriminators are `gh pr list --state all` on the issue number (body and
  title) and `git merge-base --is-ancestor`. Both complete in seconds.
- The expensive mistake is acting on the wrong reading: a duplicate implementation
  (hours of agent time, a conflicting second pull request) or a discard of delivered
  evidence.

## Audit pattern when classification is "already delivered"

1. Read the canonical contract (issue plan comment or specification).
2. Verify each required artifact on the current default branch by path presence and
   content spot-checks.
3. Run the contract's named behavior tests in a disposable worktree at the current
   default branch; record exact selections and counts.
4. Accept the delivery only when the audit passes; otherwise treat the merged change
   as an incomplete delivery and classify the remainder by the contract.

## Evidence limits in this case

- The audit ran locally against the current default branch read from the remote; the
  verification state is `verified-local`, not `verified-ci`.
- Review-decision and merge details live on the forge; the notes keep only the decision
  structure, not the identifiers.

## Case: issue-pickup ownership gate with no branch present (generalized)

1. A single-issue fleet worker received an issue whose only state label was a
   plan-approved ("implementer may proceed") label, with no assignee. The mandated
   open-pull-request search for the issue number returned an empty list.
2. The issue timeline inside the gate's 48-hour recency window showed:
   a `cross-referenced` event from a pull request whose lane branch was named for the
   issue, merged hours earlier; a `referenced` event for the resulting squash commit on
   the default branch; and a second `cross-referenced` event from a new follow-up issue
   that continued the same feature.
3. A state-all pull-request search confirmed the merged pull request and its merge time.
   The plan-approved label had stayed set through the merge — no automation had moved it.
4. Verdict: owned. The worker changed no labels, posted no comment, created no branch
   and no worktree, and reported the merge and timeline evidence.

Decision value this case adds:

- The ownership failure happened at issue pickup, before any lane branch existed, so the
  zero-ahead branch audit had nothing to inspect. The discriminators were the state-all
  pull-request search and the issue timeline events inside the recency window.
- The plan-approved label was the strongest-looking "free to claim" signal and it was
  wrong: label events and delivery events are not synchronized, so labels can lag a
  merge by hours.
- A `cross-referenced` event that originates from another issue (not a pull request)
  still counts as a continuing lane when it lands inside the window.

## Evidence limits in the ownership-gate case

- All verification was forge-side (timeline events, pull-request state); no local audit
  of the merged content ran because the gate outcome was stop, not adopt. Verification
  state is `verified-local`.
- Repository, issue, pull-request, and lane identifiers are withheld under the privacy
  policy; the notes keep only the decision structure.
