---
name: release-validation-running-source-mismatch
description: "Detection of release-validation evidence that describes a different source than the running lane. Use when a lane was hot-swapped, promoted, or redeployed and validation reports tag or release checks."
category: ci-cd
date: 2026-11-24
version: "1.0.0"
user-invocable: false
tags: [release-validation, hot-swap, source-sha, evidence-interpretation]
---

# Release Validation Describes Its Own Subject

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Decide whether release-validation output describes the content that the lane runs. |
| **Outcome** | Operational |

## When to Use

Use this skill when one or more of these conditions apply:

- A lane was hot-swapped, promoted, or redeployed, and you must confirm the running content.
- Deployment validation reports overall ready with version-tag and release checks in pass.
- The newest tag is older than the change under test, or no tag exists for the new content.
- Validation output names a tag or release while lane status names a source commit.

## Verified Workflow

### Quick Reference

```bash
# Read what the lane runs, then what validation checked.
<lane status> --json                  # generation "<job>:<color>:<source_sha>:<stamp>"
git ls-remote --tags <remote>         # newest tag and its peeled commit
<validation deployment> <lane> --json # read the version-tag "observed" text
```

Rule: validation that names tag X is evidence about X. A pass does not prove that the
lane runs X.

### Suggested Approach

1. List remote tags. Record the newest tag and its peeled commit.
2. Read lane status JSON. Record `source_sha` from `generation`. Record the `source_sha`
   field when it is present.
3. Run deployment validation JSON. Read the `observed` text of the tag and release
   checks, not only their status.
4. Compare the running source with the tag commit. Also compare it with the expected
   candidate commit.
5. When a hot-swap record exists, read `release-runs/<run>/hot-swap.json`. A pass
   requires outcome `stopped`.
6. Report the comparison. When the values differ, state that the lane runs untagged or
   older content. Do not cite tag or release passes as proof of the running content.
7. Continue behavior validation against the running source. The tag comparison is not a
   blocker for that work.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Treated overall "ready" as proof of the running content. | "Ready" aggregates checks that can pass against an older tag. | Compare the running `source_sha` with the tag commit. |
| 2 | Assumed a tag exists because the lane was hot-swapped. | A hot swap deploys a prepared tree. Tagging is a separate publication step. | List remote tags first. Absence of a tag is a finding. |
| 3 | Cited a release-check pass as proof of current publication. | The check observed the previous release. | Read the `observed` text, not only the status. |

## Results & Parameters

### Configuration

```yaml
lane_status:
  generation: "<scheduler-job>:<color>:<source_sha>:<publish-stamp>"
  source_sha: "<commit the lane runs>"
deployment_validation:
  counts: {pass: 5, fail: 0, pending: 5}
  tag_check_observed: "annotated tag <tag>"
  release_check_observed: "release for <tag> is published"
hot_swap_record:
  path: "release-runs/<run>/hot-swap.json"
  passing_outcome: "stopped"
```

### Expected Output

- One statement of the running source.
- One statement of the tag or release that validation observed.
- A mismatch finding when the two statements differ.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Serving fleet | Production lane after a hot swap, November 2026 | The lane ran a source commit with no tag. Validation observed the prior annotated tag. See [notes](release-validation-running-source-mismatch.notes.md). |

## References

- [Live publish target guard](immutable-release-publish-target-live-candidate.md)
- [Deployed-version runbooks](deployed-version-runbook-goal-feasibility.md)
- [ASD-STE100](../docs/asd-ste100.md)