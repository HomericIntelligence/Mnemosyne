---
name: promotion-scope-branch-config-diff
description: "Gate source-to-deployed promotion scope on a branch-to-branch diff of release-embedded configuration. Use when: (1) scoping a release or promotion from an issue tracker, (2) deployed-environment behavior is declared in repository configuration such as contexts, rosters, schedules, or policies, (3) a bootstrap or minimization change on the source branch can have removed deployed content without a tracking issue."
category: ci-cd
date: 2026-10-22
version: "1.0.0"
user-invocable: false
tags: [promotion, release-scope, branch-diff, configuration-completeness, issue-tracker, untracked-removal, regression]
---

# Promotion Scope: Diff Release-Embedded Configuration Between Branches

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Find promotion-blocking configuration deltas that have no tracking issue before a source branch is promoted to a deployed branch. |
| **Outcome** | Successful. One scan of several hundred open issues was complemented by one branch-to-branch configuration diff. The diff found an untracked removal of four deployed entries plus their routing, accounting, and capacity policy. The promotion would have shipped that removal with no warning. |

## When to Use

- Scoping a release or promotion campaign from an issue tracker, an epic, or
  a checklist of open issues.
- A branch-to-branch promotion where deployed-environment behavior is embedded
  in repository configuration: deployment contexts, model or service rosters,
  cluster profiles, allocation schedules, fair-share or routing policy.
- A bootstrap, minimization, or root-repair change touched the deployed
  configuration on the source branch and its commit message documents only the
  primary purpose.
- Any claim of the form "nothing but the tracked issues stands between source
  and production".

Do not use this skill to revalidate the configuration of a single branch, or to
review the mechanics of one pull request. For diff-endpoint selection during a
branch review, see
[pr-review-two-dot-vs-three-dot-diff](pr-review-two-dot-vs-three-dot-diff.md).

## Verified Workflow

### Quick Reference

```bash
git fetch origin <source-branch> <deployed-branch>
# 1. What the deployed environment would lose or gain at promotion:
git diff --stat origin/<deployed-branch> origin/<source-branch> -- <release-config-paths>
git diff        origin/<deployed-branch> origin/<source-branch> -- <release-config-paths>
# 2. Which source-branch change removed a known deployed marker:
git log -S'<deployed-marker>' --oneline origin/<source-branch> -- <path>
# 3. Marker can live outside the repo: query the live environment's declared
#    roster/state and diff it against the source-branch configuration too.
```

### Suggested Approach

1. Identify the release-embedded configuration paths. A path qualifies when
   its repository content becomes part of the deployed release or its rendered
   runtime (compiled-in data files, deployment contexts, policy files,
   scheduler profiles).
2. Run an endpoint diff from the deployed branch to the source branch over
   those paths. Removed entries in this direction are what the promotion
   deletes from production. An ahead/behind commit count does not answer this
   question: the source branch can contain every deployed commit and still
   declare less content.
3. Correlate each removal with the tracker. A removal is untracked when no open
   issue documents it and no commit message records it as intentional. Keyword
   search over issues ("removed", "restore", the entry name) proves the
   negative only after the diff defines what to search for.
4. For each untracked removal, use `git log -S` to find the removing change,
   read its message and review for intent, then file an issue that records: the
   removed content, the consequence at promotion, the required restoration, and
   derived-identity churn side effects (a roster edit can change computed
   release identities and every golden digest bound to them). Link the issue
   into the promotion epic.
5. Define the promotion scope as the union of tracked issues and untracked
   configuration deltas. Record the empty-diff case as evidence instead of
   assuming it.

If the deployed branch cannot be fetched, run the same comparison against the
last known deployed release tag or the live environment's declared state, and
record the weaker binding.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Accept the open-issue list as the complete promotion scope | Scoped a promotion from several hundred open issues filtered by acceptance requirements | A prior change had removed four deployed roster entries plus their routing, accounting, and capacity policy from the source branch; no issue tracked the removal | The tracker tracks tickets, not bytes. Completeness of a promotion scope comes from a content diff between what runs and what will run |
| Keyword search over issues for the missing entries | Searched issue bodies for "removed"/"restore" plus entry names | No issue existed; keyword absence cannot prove zero untracked change | Diff first, then search. The diff output is the exact search key set and the filing evidence |

## Results & Parameters

### Configuration

```yaml
inputs:
  source_branch: <branch-that-will-be-promoted>
  deployed_branch: <branch-that-runs-in-production>
  release_config_paths: [<deployment-contexts>, <cluster-profiles>, <policy-files>]
  live_state_probe: <optional-read-only-state-endpoint-or-status-file>
outputs:
  untracked_deltas: <list-of-removals-not-covered-by-an-issue>
  filed_issues: <one-issue-per-untracked-delta-or-a-recorded-empty-result>
```

### Expected Output

- A list of configuration removals from the deployed branch that the source
  branch would ship, each either covered by an existing issue or filed as a
  new issue linked to the promotion epic; or a recorded empty result.
- The removing commit for each untracked removal, with an intent statement.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal multi-model inference-serving platform | Promotion epic construction, several hundred open issues; diff of deployed vs source deployment contexts found an untracked four-entry roster removal | See [notes](promotion-scope-branch-config-diff.notes.md). |

## References

- [pr-review-two-dot-vs-three-dot-diff](pr-review-two-dot-vs-three-dot-diff.md) — diff-endpoint selection for branch review
- [audit-orphan-source-sweep-to-find-omissions](audit-orphan-source-sweep-to-find-omissions.md) — horizontal omission sweep for derived datasets
