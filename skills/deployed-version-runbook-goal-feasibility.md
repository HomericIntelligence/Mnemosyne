---
name: deployed-version-runbook-goal-feasibility
license: BSD-3-Clause
description: "Verify that operator directions keyed to a deployed version can reach their terminal goal on that deployed version before publication. Use when each step of a runbook was validated against a live deployment, when the deployed release is older than main, when an upgrade or promotion is in flight, or when the terminal step is a named operation (seal, activate, migrate, enroll) whose availability depends on the release."
category: documentation
date: 2026-10-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [runbook, operator-directions, deployed-version, goal-feasibility, version-drift, promotion-ordering, release-precondition, comet]
---

# Deployed-Version Runbook Goal Feasibility

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Prevent publication of version-keyed operator directions whose terminal goal the deployed release cannot execute. |
| **Outcome** | Successful — the published runbook received a same-day correction, the campaign order was reversed (promotion before any seal), and no seal was attempted on an incapable release. |

Step-level validation answers: "does each command work on this deployment".
Goal feasibility answers a different question: "can the deployed release
reach the end state of this runbook at all". A runbook can pass the first
check and fail the second. This occurs when the terminal operation is
version-gated. The failure invalidates the directions as a sequence. The
individually valid steps do not prevent this.

## When to Use

Use this skill when one of these conditions applies:

- You write or review directions that name a deployed version, tag, digest,
  or release as the target of execution.
- The terminal step is a named operation whose implementation changed
  between versions: seal, activate, migrate, enroll, promote, or similar.
- `main` already carries a fix or a feature that the deployed release does
  not. Code read on `main` is not evidence of the deployed behavior.
- A promotion or upgrade is in flight, and the order of other work depends
  on the capabilities of the current release.

## Verified Workflow

### Quick Reference

Do these checks before you publish version-keyed directions:

1. Identify the deployed version exactly: tag, digest, or commit. Terms
   such as "latest" or "the cluster" are not sufficient.
2. Read the terminal goal's code path at that ref, for example with
   `git show <tag>:<path>`, or in the source of the deployed artifact.
3. Follow that path to its exit conditions. Record each unavailable or
   placeholder implementation with its exact error text.
4. Publish only after this check. Annotate the directions with the verified
   ref. If the goal is not reachable, re-sequence the work first.

### Suggested Approach

- Validate the steps against the deployment. Validate the goal against the
  deployed ref. Both checks are necessary. Neither check implies the other.
- Search the goal path at the deployed ref for refusal classes. Typical
  signs: names that contain `Unavailable`, `NotImplemented` errors,
  placeholder implementations, and feature flags that default to off.
  Record the exact refusal string. It becomes the evidence in the
  correction and in the precondition issue.
- Compare with `main` only to find the carrying change: the commit or pull
  request that makes the goal reachable. Name that change as the
  precondition. Record its promotion vehicle and its check status.
- When the goal is not reachable: do not delete the validated steps. They
  become the post-promotion sequence. Change the order of the campaign.
  Correct the published directions. Keep the evidence links for both.
- When you cannot read the code of the deployed artifact, for example
  because of an access boundary, treat goal feasibility as unverified. Mark
  the directions as unverified. Do not imply capability.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Publish after step-level validation | Published a six-model seal runbook keyed to deployed tag v0.2.3. Each step was validated against the live service. | The terminal seal operation on v0.2.3 exits through a placeholder verifier that refuses the operation with a fixed error. Every seal the runbook directed was impossible on that release. The runbook needed a public correction. | Step-level validation on a live deployment does not show that the deployed release can reach the runbook's goal. Read the terminal code path at the deployed ref before publication. |

## Results & Parameters

### Configuration

Record these fields with the directions:

```text
deployed_ref: <exact tag or commit of the deployment>
goal_operation: <terminal command, for example checkpoint seal>
goal_path_at_ref: <source path that implements the terminal operation>
refusal_evidence: <verbatim error text the deployed ref produces>
carrying_change: <commit or PR that makes the goal reachable, with its
  promotion vehicle>
```

### Expected Output

- Each published direction names the ref against which it was verified.
- The work order names version deltas as hard preconditions, with evidence.
- Corrections name the refusal evidence and the carrying change.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet | K2-Horizon BF16 enablement campaign; issues #845, #2851, #2953; promotion PR #2951 | [notes.md](./deployed-version-runbook-goal-feasibility.notes.md) |

## References

- [pr-ci-failure-triage-preexisting-vs-introduced](pr-ci-failure-triage-preexisting-vs-introduced.md) — the same classify-before-action discipline applied to red checks; this skill applies it to version-keyed directions.
- [comet-live-readonly-release-status-probe](comet-live-readonly-release-status-probe.md) — read-only evidence capture on a live deployment, which a runbook review can reuse.
