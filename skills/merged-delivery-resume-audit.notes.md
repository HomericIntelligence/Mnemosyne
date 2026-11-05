# merged-delivery-resume-audit — notes

## Source case (2026-11-02 to 2026-11-04)

### Environment

A shared monorepo under a many-lane release milestone. Several agents worked
the same repository. A delivery directive told one agent to drive one pull
request to `MERGED`. The agent session ended because the model provider was
unavailable. A later turn resumed the task with the same directive.

### Observed sequence

- Step 0 of the directive asked for a fresh read. The read showed
  `state: MERGED`, a merge time about two days before the resume turn, a
  merge commit, and a merged head.
- The check list still showed a set of old runs. One required documentation
  check was red on the run that started before the merge. The merge did not
  wait for that check.
- The linked issue was `CLOSED` with `stateReason: COMPLETED`, with a close
  time one second after the merge time.
- The record comment count for the driver prefix was zero. The post-merge
  record step had not run.
- The auditor posted one record comment. The comment named the merge commit,
  the merged head, the merged content, the closed issue, and the red check
  with its run. The auditor did not change the branch.

### Disposition

The delta was one missing record comment. The audit did not touch the
branch, the head, or the merge.

### Decision value

- The trigger is new: a resume or takeover turn that starts after the merge.
  The active-drive sibling entry starts before the merge.
- The check branch is new: a red check after a final merge is a history
  record. It is not a reason to change the branch.
- The delta test is new: test each contract step against its own evidence,
  including the record comment count.

## Privacy screen

The main entry and this notes file contain no personal data, internal paths,
hostnames, issue IDs, pull request numbers, or repository names. The evidence
uses general roles: "a pull request", "the linked issue", "a check".

## Provenance

- Disposition: `create`.
- Delivery base: the default branch of the knowledge repository, revision
  recorded in the pull request.
- Duplicate checks at write time:
  - `mid-drive-peer-completion-audit` (v1.3.0): peer completion while you
    actively drive. It contains a merged-artifact stop for a reviewer role.
    It does not contain the resume-turn trigger or the post-merge record
    delta test.
  - `shared-repo-interruption-yield-to-peer-pr`: yield after an interruption
    for prepared but undelivered work.
  - `merged-content-verify`: content ancestry and marker tests for merged
    work. It covers content, not the record bookkeeping steps.
  - `ci-cd-verify-merged-prs-end-to-end`: end-to-end composition of merged
    work. Different outcome.
  - `stale-plan-already-resolved`: stale premises on open artifacts. It does
    not cover a terminal merge state.
  - Open pull requests in the delivery repository at write time changed no
    byte of this new entry.