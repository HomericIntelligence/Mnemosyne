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
