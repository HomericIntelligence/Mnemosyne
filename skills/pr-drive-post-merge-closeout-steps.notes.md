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

## Case record: pre-merge link state (amendment 1.1.0)

A drive brief carried a template that told the lane to use `Closes #N`. The issue's
approved plan, and a newer recorded decision on that issue, required `Refs #N` instead:
two acceptance criteria needed operator logs and a deploy that ran after the merge. The
drive PR used `Refs` and stated the reason in its body.

The PR body also explained the decision in prose and wrote the closing keyword inside a
code span. The author then checked the body text with an anchored `grep` for a closing
line. The grep found that sentence and suggested a closing link. The forge reported
`closingIssuesReferences.totalCount = 0` for the PR. GitHub does not link a keyword that
sits inside a code span, so the issue stayed open as the plan required.

Measurements (generalized):

- Body text with one standalone closing line: anchored `grep` count `1`.
- Body text with only a backticked mention: anchored `grep` count `0`, grep status `1`.
- The API check on the PR with the backticked mention: `totalCount` `0`.

A superseded review finding, withdrawn under a later authority reframe, had suggested
"other invocations are unsupported" as a closure branch for a related help-text defect.
The owner decision that resolved the issue instead required the behavior. The lesson:
cite the authority record, not the withdrawn finding.

## Duplicate and adjacent-rule evidence

- A sibling "stop on already merged" rule decides the zero-write stop. That rule applies when
  every closeout step is complete. It does not decide what to do when a named closeout step
  is unfinished. This entry adds that decision branch.
- A "check already shipped" rule for planning asks whether a behavior exists on the default
  branch before someone plans an implementation.
- A merge-readiness rule checks checks, approvals, and conflicts for an open pull request.
- A label-gate rule explains that a re-run replays the old label payload. It does not cover
  the post-merge steps.
- A review-admission rule is gated on a standalone closing line and an
  orphan check. It does not decide when a plan requires a deliberate non-closing link.
- A batch-shipping rule and an epic-sequencing rule check the PR body bytes for a policy
  gate. They treat the body as the policy input, not as proof of the forge link state.
- A resume rule uses the linked-issue API after a merge. This entry now owns the same
  check before submission, so the decision has one owner.

## Verification of this entry

- Frontmatter and section validation passed on the delivery revision.
- The main file is below the 30,000-byte editorial guideline.
- Duplicate search covered the corpus selector output and the nearest entries by intent.