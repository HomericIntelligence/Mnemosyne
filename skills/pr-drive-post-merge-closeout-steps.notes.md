# Notes: pr-drive-post-merge-closeout-steps

Supporting evidence for the main skill. Generalized; no repository, forge, or session
identifiers.

## Case record

A coordinator task instructed one full pull request drive: read the current state, classify
the failure, rebase if needed, deliver a verdict at the exact head, merge, then confirm the
merge, post one summary comment, and record a lesson.

The first binding read, before any content work, showed the target was already `MERGED`. A
previous session had merged it. All required checks had passed at the merged head. The
merge commit was recorded, and the linked issue was `CLOSED` with reason `COMPLETED`.

The review-state label at the merged head recorded the delivered verdict. The full state
read, the checks list, the merge record, and the issue record all agreed.

The drive therefore had no delivery work. It did have closeout work: the comment history
held no merge summary, and no lesson record existed. The correct response was to post the
one missing summary comment, then run the lesson workflow separately, with an isolated
worktree and a duplicate search.

## Case record, second: a fix prepared after the merge

The first case bound a drive that met the merge at its first read. The second case met the
merge in the middle of review work. A full review of a long-lived pull request found three
defects and delivered signed commits that fixed two of them. The owner then rebased the
branch, applied the gating label, and merged. While the review answered the last open
thread, a forge read showed `state: MERGED` and a deleted source branch.

Evidence that the merged tree held the fixes:

- The last two review findings were verified by content, not by an ancestry test. The
  squash merge puts the source commits outside the default branch.
- A whole-tree search over the changed paths returned zero hits for the removed artifact.
  The same search showed the build-reading names that the fix introduced.
- The one finding that did not reach the merge was a comment-only correction. The review had
  committed it locally after the merge. The source branch no longer existed, so a push had
  no ref. The local commit was kept, and the reply named it as local work outside the merge.

Attribution of the default-branch red came from the failing set, not from the merge color.
A required aggregate gate failed at the merge commit. About 28 of 32 shards failed. Most
failures were one signature: a directory created at the runner umask reaches a mode check.
Other failures were in files the merged change never touched. None of the failing signatures
was in a file the merge changed.

## Duplicate and adjacent-rule evidence

- A sibling "stop on already merged" rule decides the zero-write stop. That rule applies when
  every closeout step is complete. It does not decide what to do when a named closeout step
  is unfinished. This entry adds that decision branch.
- A "check already shipped" rule for planning asks whether a behavior exists on the default
  branch before someone plans an implementation.
- A merge-readiness rule checks checks, approvals, and conflicts for an open pull request.
- A label-gate rule explains that a re-run replays the old label payload. It does not cover
  the post-merge steps.
- A branch-state recovery entry owns the merged-before-local-work proof: stop before a
  rebase, and compare content when commits were rewritten. This entry owns the different
  decision: a change prepared after the merge. It records where the change stands and
  reports local work as local.
- A post-merge failure-attribution entry owns the parent-commit comparison for a red default
  branch. This entry only records the classification in a closeout report.

## Verification of this entry

- Frontmatter and section validation passed on the delivery revision.
- The main file is below the 30,000-byte editorial guideline.
- Duplicate search covered the corpus selector output and the nearest entries by intent.
- The second case applied the content-equivalence test to two fixes and caught one absent
  change. It checked the changed paths at the merge commit and the default branch, and found
  a comment-only correction that the merge did not include. The check compares documents byte
  for byte, so a comment change cannot hide a missing code change.
