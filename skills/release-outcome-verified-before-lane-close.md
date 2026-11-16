---
name: release-outcome-verified-before-lane-close
description: "Verify that a milestone or release outcome shipped before you close a lane that pursued it. Use when a lane resumes after days, a directive says the release is live, a milestone closed or was created retroactively, or you must decide the remaining delta of a promotion, integration, or review lane."
category: ci-cd
date: 2026-11-08
version: "1.0.0"
user-invocable: false
verification: verified-live
license: BSD-3-Clause
tags: [release, milestone, lane-closure, zero-delta, tag-ancestry, branch-model, retroactive-milestone, live-forge]
---

# Release Outcome Verified Before Lane Close

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-08 |
| **Objective** | Decide the true remaining delta of a lane that pursued a release, from live forge state rather than from issue-tracker counts. |
| **Outcome** | Operational. A review lane closed with a zero delta after a live audit showed the release shipped, the milestone closed, and every artifact it reviewed merged. The audit also showed that milestone counts and a symmetric ahead/behind pair prove neither the release nor a branch lag. |

A milestone with zero open issues is not a shipped release. A closed milestone
is not always the lane's target release, because a retroactive sweep can create
and close milestone records for older releases. A tag need not exist on the
development branch, and a promoted branch need not contain it either.

The rule: **verify the release object, the tag ancestry, and the branch model
before you state a delta or close the lane.**

## When to Use

- A lane resumes after an interruption of days, and other lanes continued the work.
- A directive states that the release is live, or that its milestone is closed.
- A milestone appears closed with zero open items, and you must confirm which release it records.
- Milestones exist for releases that are older than their creation date.
- You must state what remains for a promotion, integration, or review lane.
- An ahead/behind count between a development branch and a deployed branch is symmetric.

## Verified Workflow

### Quick Reference

```bash
# 1. Release objects, newest first. A tag name can differ from the release title.
gh release list -R <user>/<repo> --limit 10

# 2. Milestone state, creation time, and open count.
gh api graphql -f query='query { repository(owner:"<o>", name:"<r>") {
  milestones(first: 20, states:[OPEN,CLOSED]) { nodes {
    number title state createdAt closedAt issues(states: OPEN) { totalCount } } } } }'

# 3. Bind each tag to a commit and test where it lives.
git fetch origin --tags --prune
git rev-parse <tag>^{commit}
git merge-base --is-ancestor <tag-commit> origin/<dev-branch> && echo in-dev || echo not-in-dev
git merge-base --is-ancestor <tag-commit> origin/<deployed-branch>

# 4. Read the branch model before you report a lag.
git log --format='%h %p | %s' origin/<dev>..origin/<deployed> | head
```

### Suggested Approach

1. **Read the release record, not the milestone count.** The release list gives the
   published objects, their tags, and their dates. A release title can name a tag that
   differs from the release name, because a hotfix adds a suffix.
2. **Classify the closed milestone.** Compare its creation time with its close time. A
   milestone that was created after the release it records is a retroactive record. It
   confirms history, and it is not the lane's live target.
3. **Bind the tag to a commit, then test ancestry.** A tag can point to a promotion
   merge on the deployed branch. Such a tag is absent from the development branch by
   design. Test both branches and record which one holds the tag commit.
4. **Establish the branch model before you report a lag.** When both branches report the
   same non-zero ahead count, read the deployed-branch-only commits. If they are all
   merges of the development branch, the deployed branch is a merge-down target. It is
   not behind, and it needs no catch-up action from you.
5. **Compute the lane delta from its own artifacts.** For each artifact that the lane
   claimed, read its terminal state. For review lanes, also search the open artifacts for
   reviews that this lane authored. A merged artifact and an absent open review is zero
   delta.
6. **Do the remaining closure only.** Post the terminal record, close the objective with
   the audit evidence, and stop. Do not repeat merged work, and do not claim another
   lane's live release.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | ---------------- |
| Read the milestone count | Treated a milestone with zero open issues as proof that the release shipped | The count proves only that every tracked item closed. The release object and the tag ancestry were separate facts | Verify the release object and the tag commit before you state the outcome |
| Trust the milestone identity | Matched the release to a milestone title without a creation-time check | Retroactive milestones for older releases exist and are already closed, so a title match can select history instead of the live target | Compare the milestone creation time with its close time and with the release date |
| Require tag presence on the development branch | Expected the release tag to be an ancestor of the development branch | The tag pointed to a promotion merge on the deployed branch, so it is absent from development by design | Test tag ancestry on both branches and record which holds it |
| Report the deployed branch as behind | Saw an equal non-zero ahead/behind pair and read it as a lag in both directions | The deployed-branch-only commits were all merges of the development branch, so the branch is a merge-down target | Read the branch-only commits before you report a lag |

## Results & Parameters

### Configuration

```yaml
release_verification:
  release_object: gh release list --limit 10
  tag_binding: git rev-parse <tag>^{commit}
  ancestry_tests: [development branch, deployed branch]
  milestone_check: [state, created_at, closed_at, open_count]
  retroactive_record: created_at after the release date
branch_model_check:
  signal: both ahead counts equal and non-zero
  action: read the deployed-branch-only commits
  merge_down: every such commit is a merge of the development branch
lane_delta:
  - each claimed artifact terminal state
  - reviews authored by this lane on open artifacts
  - cleanup: owned branches only
closure:
  - post one terminal record
  - close the objective with audit evidence
  - stop
```

### Expected Output

- One release name, its tag, its commit, and the branch that holds the tag commit.
- A milestone classification: live target, or retroactive record.
- A branch model: promotion source, or merge-down target.
- A lane delta that names each artifact state, or states zero.
- A terminal record and a closed objective.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| private monorepo under many-lane release promotion | Review lane closed after a release shipped through other lanes | General pattern only. Do not record internal identifiers. See [notes](release-outcome-verified-before-lane-close.notes.md). |

## References

- [Merged-Delivery Resume Audit](merged-delivery-resume-audit.md)
- [Check If Already Shipped Before Planning](planning-check-already-shipped-before-planning.md)
- [GitHub Milestone, gh CLI, and Release Sweep](github-milestone-gh-cli-release-sweep.md)
- [PR Review: Two-Dot and Three-Dot Diffs](pr-review-two-dot-vs-three-dot-diff.md)