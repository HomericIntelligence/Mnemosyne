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

## Duplicate and adjacent-rule evidence

- A sibling "stop on already merged" rule decides the zero-write stop. That rule applies when
  every closeout step is complete. It does not decide what to do when a named closeout step
  is unfinished. This entry adds that decision branch.
- A "check already shipped" rule for planning asks whether a behavior exists on the default
  branch before someone plans an implementation.
- A merge-readiness rule checks checks, approvals, and conflicts for an open pull request.
- A label-gate rule explains that a re-run replays the old label payload. It does not cover
  the post-merge steps.

## Verification of this entry

- Frontmatter and section validation passed on the delivery revision.
- The main file is below the 30,000-byte editorial guideline.
- Duplicate search covered the corpus selector output and the nearest entries by intent.