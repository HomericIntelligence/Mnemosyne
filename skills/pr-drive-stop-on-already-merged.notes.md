# Notes: pr-drive-stop-on-already-merged

Supporting evidence for the main skill. Generalized; no repository, forge, or
session identifiers.

## Case record

A coordinator task instructed one full pull request drive: review the request,
fix every required finding, get the review verdict at the exact head, then enable
auto-merge, and record a lesson after the merge.

The first binding read, before any review work, showed:

- the pull request state was `MERGED`, with a merge timestamp from the same day;
- the forge returned a merge commit object identifier;
- the request carried the review GO state label, so a verdict was already
  delivered at the merged head; and
- a local ancestry check proved the merge commit was an ancestor of the default
  branch, and the merge parent matched the recorded base commit of the task.

The drive therefore had no open artifact. The correct response was to stop with
zero forge writes: no reviewer round, no author response, no status comment, and
no auto-merge request. The remaining task step was the lesson record, then the
session close per the already-complete rule.

## Distinction from adjacent rules

- A "check already shipped" rule for planning work asks whether a behavior
  already exists on the default branch before someone plans an implementation.
  This lesson asks about the lifecycle state of the review artifact itself.
- A merge-readiness rule checks checks, approvals, and conflicts for an open
  pull request before a merge. This lesson runs earlier and handles the terminal
  case, where no merge action is possible.
- A stale-premise rule re-checks a defect on the current default branch before a
  fix. This lesson re-checks the delivery state of the assigned artifact before
  any review write.

## Delivery-worktree evidence

The knowledge checkout was on a non-default branch, and its freshness could not
be refreshed through the normal resolver. The remote was reachable through a
read-only probe. The delivery worktree was therefore created directly from the
live default-branch tip object identifier. A first attempt that used the stale
local revision as the start point failed, because the helper could not resolve
that revision on the remote.

## Verification of this entry

- Frontmatter and section validation passed on the delivery revision.
- The main file is below the 30,000-byte editorial guideline.
- Duplicate search covered the corpus selector output and the nearest entries by
  intent; none decides the terminal-merged case for a drive task.

## Re-bind after a wait

A CI-failure fix session classified 8 red checks on one promotion pull
request and found a second session driving the same artifact from the same
prompt. It stayed read-only and watched the default-branch tip and the
published-review count until both held unchanged for 25 minutes. That window
closed three times; on the third a push landed 1 minute later, and a fourth
push followed after a further 12-minute window.

On the final verification read the check rollup showed 161 successes and 0
failures, and the pull request carried the implementation-go label. Before
reporting the work done, a lifecycle re-read showed the pull request `MERGED`
17 minutes earlier, by the concurrent lane, and the run history showed green
against a head the waiting session never bound.

Disposition: the waiting session reported the delivered state instead of
claiming completion. The rule now requires the binding read again before any
work starts after a wait, and treats a post-wait green read as a possibly
stale signal until the lifecycle state confirms it.

## Readiness field on a terminal pull request

A rebase task instructed the session to read the lifecycle state and the merge
readiness at the start, and to stop only when the readiness value was ready. The
task also required a force-push and a status comment after the rebase.

The binding read showed the pull request `MERGED` and the readiness value
`UNKNOWN`. The readiness value did not match the stated stop condition, so a
literal reading of the task would have started a rebase. The merge commit was
already an ancestor of the default branch, and the local branch named for the
rebase held an old base commit that did not contain the pull request change.

Disposition: the session did not rebase, did not push, and did not comment. A
rebase would have dropped the change, because the default branch already had it.
The session restored the isolated checkout to the default-branch tip and deleted
its own unneeded local branch. It reported the merged state, the merge commit,
the ancestry proof, and the reason the readiness value did not apply.

General rule: the lifecycle state decides. A readiness field is a merge
computation for an open pull request. A terminal pull request can report a
non-ready or unknown readiness value at any time, and that value is not a signal
to start repair work.
