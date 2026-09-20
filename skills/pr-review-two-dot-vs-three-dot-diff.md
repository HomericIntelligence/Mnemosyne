---
name: pr-review-two-dot-vs-three-dot-diff
license: BSD-3-Clause
description: Select endpoint and merge-base diffs when reviewing a branch behind its target, investigating apparent deletions, or checking whether work already landed.
category: tooling
date: 2026-07-10
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: [pr-review, git-diff, two-dot, three-dot, merge-base, stale-branch, merge-readiness]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/e98a4da5d67f0766bc6b4bfaed1ab399fca90e9f/skills/pr-review-two-dot-vs-three-dot-diff.history"
history-cleanup-date: "2026-09-19"
---

# PR Review: Two-Dot and Three-Dot Diffs

## Overview

| Date | Objective | Outcome |
| --- | --- | --- |
| 2026-07-10 | Select the diff that answers the review question | Separate branch changes, endpoint differences, and integration results |

## When to Use

- A branch is behind its target and an endpoint diff shows unexpected deletions.
- A branch diff appears to repeat work that already landed through another PR.
- A reviewer needs to distinguish the branch contribution from integration state.

## Verified Workflow

### 1. Bind both revisions

Record the exact target and head commits. Use immutable commit identifiers for review.
An ahead or behind count describes ancestry. It does not prove a conflict or require a
rebase. Apply [readiness policy](verify-pr-ready.md) before changing the branch.

### 2. Select the question

| Question | Command | Limit |
| --- | --- | --- |
| How do the two endpoint trees differ? | `git diff BASE..HEAD` | Includes target-only changes in reverse. It does not predict a merge result. |
| What changed on the branch since the merge base? | `git diff BASE...HEAD` | Can include equivalent changes that landed separately on the target. Inspect that overlap. |
| Can the candidate integrate with the current target? | Inspect forge mergeability and required integration evidence | Neither diff alone proves the resulting tree or behavior. Unknown mergeability is not a conflict. |

A two-dot diff describes the patch that would turn the target tree into the branch tree.
Applying that patch directly can remove target-only work. A normal Git merge does not
simply apply that endpoint patch. Do not claim that endpoint deletions will occur in a
merge without evidence of the actual integration result.

### 3. Investigate overlap without rewriting history

Read the relevant files at both commits and examine the branch contribution. Inspect
linked merged PRs and patches when a squash merge changed commit identity. Commit
subjects and symbol searches are discovery aids, not proof of complete integration.

An empty diff for one file proves equality for that file only. Before declaring a PR
redundant, compare its complete intended change and requirements with the target.
Do not close a PR or discard work only because one file matches.

### 4. Keep review, integration, and cleanup separate

Review the exact head. Check integration against the current target as policy requires.
Rebase only for an actual conflict, a necessary dependency, or an explicit request.
If the head changes, review the resulting candidate. Reuse validation only under the
applicability rules in [verify-pr-ready](verify-pr-ready.md).

Cleanup does not require a rebase. Preserve uncertain work and use the authorized cleanup
workflow separately. Do not rewrite a branch merely to make the two diff views agree.

### Quick Reference

```bash
# Bind these values to the PR target and candidate before inspection.
git rev-parse origin/main
git rev-parse HEAD
git merge-base BASE HEAD
git diff BASE...HEAD
git diff BASE..HEAD
git show BASE:path/to/file
git show HEAD:path/to/file
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Endpoint diff as merge prediction | Interpreted target-only files absent from the branch as inevitable merge deletions | Tree comparison does not calculate integration | Inspect integration evidence separately |
| Endpoint diff as branch contribution | Reviewed a branch behind main through target-to-head differences | Target advances appeared as reverse changes and obscured the branch work | Use the merge-base diff for branch contribution |
| One-file redundancy check | Treated an empty file diff as proof that the whole PR had landed | The observation did not cover other files or requirements | Compare the complete intended change |

## Results & Parameters

- `BASE`: the recorded target commit for the selected comparison.
- `HEAD`: the exact candidate commit, not an unbound moving branch name.
- Two-dot: endpoint tree differences.
- Three-dot: merge-base-to-head differences.
- Integration readiness: current policy, mergeability, required checks, and exact-head review.

## Evidence Boundary

The `verified-local` metadata describes the retained historical diff observations.
The complete earlier text and case evidence remain in
[history](https://github.com/HomericIntelligence/Mnemosyne/blob/e98a4da5d67f0766bc6b4bfaed1ab399fca90e9f/skills/pr-review-two-dot-vs-three-dot-diff.history). Its old interpretation of an
endpoint diff as a merge prediction is superseded. This documentation correction does
not claim a new merge experiment or a new operational verification result.
