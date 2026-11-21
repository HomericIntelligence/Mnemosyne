---
name: immutable-release-publish-target-live-candidate
license: BSD-3-Clause
description: "Stop an immutable release publish (a tag or a published release) from landing on a commit that is not the commit that runs live. Use when: (1) a release verb takes its tag target from a promotion pull request's merge commit and not from the candidate you pass, (2) a release path runs from a commit before the promotion merges (a pipe-clean, a rehearsal, a main-branch commit), or (3) the only comparison of tag target and live release is a check after the publish."
category: ci-cd
date: 2026-11-18
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [release, immutable-tag, publish-target, promotion, merge-commit, guard, pipe-clean, hot-swap]
---

# Immutable Publish Target Must Equal the Live Candidate

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Make sure that the one step that creates an immutable object (a tag or a published release) names the commit that the lane serves. |
| **Outcome** | Operational. A release path was run at a main-branch commit before its promotion merged. The publish verb would have tagged the merge commit of the older promotion pull request, a commit without the fixes and not live. A guard in the step script stopped it, with nothing created. The release was made after a second promotion produced a merge commit that carried the fixes. |

A release driver passes a candidate commit to every step. That does not mean that every verb uses it. A publish verb can ignore the candidate and read the merge commit of the promotion pull request. When the candidate and that merge commit differ, the tag points at the wrong commit. A tag is immutable, so the error cannot be repaired. A check that runs after the publish only reports it.

## When to Use

- A release verb creates a tag or a published release, and its inputs include both a candidate revision and a promotion pull request number.
- The verb documentation says that the revision input is unused, or you do not know where the target comes from.
- You run the release path before the promotion merges, for a pipe-clean or a rehearsal, or after a first promotion that you then replaced.
- The only comparison of tag target and live release is a verification step that runs after the publish.

## Verified Workflow

### Quick Reference

```text
Before the first call that creates an immutable object:
  target = the commit that the verb will tag   (read the verb: PR merge commit? candidate? HEAD?)
  live   = the commit of the release that the lane serves
  require target == live; otherwise stop, with nothing created
```

```bash
# Guard at the top of the publish step script (the PR number and candidate come from the step inputs).
PRM=$(gh pr view "$PROMOTION_PR" --json mergeCommit --jq '.mergeCommit.oid // "none"' 2>/dev/null || echo unknown)
[ "$PRM" = "$CANDIDATE" ] || { echo "STOP: the tag target would be $PRM, not the candidate $CANDIDATE" >&2; exit 1; }
```

### Suggested Approach

1. Read how the publish verb chooses its target. A verb that reads the merge commit of a pull request tags that commit and ignores the revision argument.
2. Compare that target with the commit of the live release before the first create call. A dry-run mode that creates a draft already creates an object, so put the guard before the dry run.
3. Put the guard in the step's own script. A shell driver reads its file while it runs, so an edit of the driver during a run can corrupt that run. A step script is read again when the step starts, so an edit before that step takes effect.
4. For a candidate that is not the promotion merge commit, the publish step must not run. A main-branch commit and a merge ref cannot satisfy the guard. Run the steps before the publish for the pipe-clean. Make the release only after a promotion has merged with the fixes, and then take that merge commit as the candidate.
5. Keep the check after the publish (tag, target and asset against the live manifest). It is the second line and does not replace the guard.
6. After a stopped run, read the forge to confirm that no release and no tag ref exist.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Check after the publish | Relied on the verification step that compares the tag target with the live manifest. | It runs after the tag exists. A tag cannot be undone, so the check can only report the error. | Guard before the first create call. |
| Pass the candidate to the verb | Passed the candidate revision and expected the tag to follow it. | The verb documented the revision as unused and read the merge commit of the promotion pull request. | Read the verb code for the source of the target. |
| Reuse the first promotion number | Kept the number of the first promotion pull request after the candidate moved to a later commit. | The merged pull request still names its own merge commit, which lacked the later fixes. | The pull request number and the candidate must name the same promotion. |
| Edit the driver during a run | Added the guard to the long driver script while a run used it. | A shell reads a script as it runs, so the edit can corrupt the run. | Edit the step script that has not started, or wait for the run to end. |

## Results & Parameters

```yaml
publish_guard:
  placement: first lines of the publish step script, before any dry run that creates a draft
  compare: [merge commit of the promotion pull request, candidate commit that the lane serves]
  on_mismatch: exit non-zero; create no draft and no tag
  skip_when: the step only prints its command (a flag check)
  verify_after_stop: forge shows no release and no tag ref
pre_merge_candidates:
  allowed_steps: every step before the publish
  publish: refused until a promotion merge commit that carries the fixes is the candidate
```

### Expected Output

- A stopped publish that names both commits and says that nothing was created.
- After the correct promotion: the published release, its tag, the lane's live release and the production branch head all name the same commit.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Release run before a second promotion merged, 2026-11 | The guard stopped the tag step once with no object created. After the second promotion merged, the publish, the post check and an independent forge read agreed on one commit. |

## References

- [release-activation-with-live-old-release-outage](release-activation-with-live-old-release-outage.md): recovery when an activation leaves the lane ahead of the serving generation.
- [deployed-version-runbook-goal-feasibility](deployed-version-runbook-goal-feasibility.md): check that a terminal step can work on the deployed release.
- [release-tag-drift-recut-on-fixed-commit](release-tag-drift-recut-on-fixed-commit.md): re-cut a tag that drifted for a different reason (package publication).
