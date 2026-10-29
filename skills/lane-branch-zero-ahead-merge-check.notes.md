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

## Second case: armed stubs mistaken for scaffolding (generalized)

1. A single-issue worker ran its mandatory ownership gate before any write. The probes
   found no pull request in any state, no assignee, no in-progress label, and a
   completed plan round with a terminal approval. Four lane stubs for the same issue
   were `0` commits ahead of the default branch, and matching stub patterns existed
   for more than a hundred other issues — some sharing tip hashes across issues.
2. The gate classified the stubs as repo-wide empty scaffolding from content alone.
   What the classification missed: every stub tip was a default-branch commit created
   one to two hours before the gate, so the refs had been armed against the current
   default branch just before the check began.
3. The worker planned and started test-first implementation (a RED test file only,
   never committed or pushed).
4. A provider outage interrupted the run hours later. The resume directive forced a
   read-only forge refresh before any further write: the lane automation had pushed a
   complete implementation to one of the armed stubs and opened a peer pull request
   for the same issue minutes earlier (single commit, all checks green).
5. The worker yielded: it removed its own unpushed worktree and local branch (whose
   tip was the pre-drift default head — nothing unique was committed), touched no
   labels, comments, or the peer pull request, and reported an owned disposition.
6. Arm-to-PR gap in this case: about five to six hours. The only duplicated cost was
   one RED test file and the gate time.

## Why the discriminator works

- Lane automation arms a stub by pointing the branch at the current default-branch
  head before a worker starts. The branch therefore contains no lane work, but its
  tip commit is fresh. A leftover from days ago points at a stale default commit
  instead. `git log -1 --format=%cI <branch-head>` separates the two without guessing.
- Identical stub layouts across many issues (shared hashes, shared pattern) describe
  *how* the automation arms lanes, not *whether* this issue's lane is idle. Pattern
  breadth is not evidence of idleness.
- An ownership gate's evidence list often enumerates pull requests, labels, assignees,
  and comment activity. Ref freshness on issue-numbered lane branches belongs on the
  same list; without it, the arming window (here five to six hours) is invisible.
- The saving control was procedural: the resume forced a read-only refresh before the
  first publication write. The same refresh before any push, branch work, or PR
  catches the same class of race without an interruption.

## Evidence limits in the second case

- One observed case; the exact freshness threshold that marks a stub as armed is not
  verified. The observed tip age at gate time was one to two hours and the arm-to-PR
  gap was five to six hours on the same lane-automation generation.
- The worker's lost work was limited to an uncommitted test file; no claim is made
  about safety when unique commits exist (use the salvage-candidate row for that).
