---
name: github-pr-review-head-bound-check-evidence
license: BSD-3-Clause
description: "Use when: (1) a GitHub pull-request review needs to determine whether required checks passed on the exact reviewed commit, (2) a status rollup looks green but does not identify the commit for each result, or (3) a review must fail closed rather than infer merge readiness from mutable CI metadata."
category: ci-cd
date: 2026-08-02
version: "1.0.0"
user-invocable: false
verification: evidence-bound-review
tags: [github, pull-request, ci, check-runs, commit-sha, immutable-evidence, review]
---

# GitHub PR Review Check Evidence Bound to the Head Commit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-02 |
| **Objective** | Prevent a pull-request review from treating mutable or unbound CI summaries as proof that the reviewed commit passed its required checks. |
| **Outcome** | A strict review of an otherwise healthy pull request remained conditional because its successful rollup could not be tied to the exact reviewed commit. |
| **Verification** | Evidence-bound review: canonical PR identity, base/head OIDs, scope, linked requirement, path manifest, and collector output were bound before inspection. |

## When to Use

- A GitHub pull-request reviewer needs a merge-readiness decision for one immutable head commit.
- `statusCheckRollup` or `gh pr checks` reports a result but does not provide a per-check commit SHA.
- A force-push, rerun, merge preview, or queued run could make a branch-level status summary stale or ambiguous.
- A review system can query the commit check-runs endpoint or an equivalent authenticated capability that returns each result's exact commit binding.

## Verified Workflow

### Quick Reference

```text
1. Retain the open PR's canonical repository, number, base OID, and head OID.
2. Query check evidence through a capability scoped to the retained head OID.
3. Accept a check only when its returned commit/SHA equals that head OID.
4. Require every effective gate to have one complete, current, head-bound result.
5. Mark absent, stale, mixed-head, malformed, or unbound results as a coverage gap.
```

### Detailed Steps

1. Resolve the pull request once and retain its canonical repository, open state, base OID, head OID, and required-gate policy. Re-fetch this identity immediately before any review publication or merge-readiness conclusion.
2. Treat `statusCheckRollup`, branch status, workflow names, and `gh pr checks` output as discovery hints only. They may summarize runs from another commit or omit the identity needed to bind a result to the reviewed source.
3. Use an authenticated provider capability equivalent to `GET /repos/<owner>/<repo>/commits/<head-oid>/check-runs`. Retain each result's check name, conclusion, status, details URL, completion metadata, and returned head binding.
4. Reject the entire check-evidence set when any consumed record is missing a commit binding, names a different commit, is incomplete, is stale after re-fetch, or cannot be reconciled with the repository's effective required gates. Do not substitute a successful rollup or a similarly named workflow.
5. Keep the source and check bindings separate: a local diff proves source identity, while provider evidence proves that the provider evaluated that identity. Both are required for a merge-ready decision.
6. A clean source review with unbound CI remains conditional, not green. Preserve the coverage gap and request or implement a safe head-bound evidence capability rather than weakening the review policy.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust a successful status rollup | Used a pull request's visible CI summary as success evidence | The summary did not identify the commit associated with every check and can include stale or superseded runs | A green rollup is not immutable check evidence. |
| Use `gh pr checks` as a binding source | Treated branch-oriented CLI check output as proof for the reviewed commit | Its result shape does not provide a per-check reviewed-head binding | Use it only to discover checks; query a head-scoped provider capability for evidence. |
| Infer freshness from a matching branch name | Assumed a check on the PR branch applied to the retained head | A branch can move after force-pushes, reruns, or merge-queue activity | Bind to commit OIDs, never branch names. |

## Results & Parameters

### Required Evidence Record

```yaml
reviewed_head_oid: <immutable-pull-request-head-oid>
effective_required_gates:
  - <required-check-name>
checks:
  - name: <check-name>
    commit_oid: <provider-returned-commit-oid>
    status: COMPLETED
    conclusion: SUCCESS
    details_url: <provider-url>
```

### Decision Rules

- Accept a check only when `commit_oid == reviewed_head_oid` and its final status satisfies the required-gate policy.
- Record a coverage gap when any effective gate lacks a complete matching record.
- Recollect and compare the complete evidence set if the PR head, scope, linked requirements, or changed-path manifest changes.
- Never convert an unbound or partial CI result into a merge-ready claim.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | PR review #67 | The collector retained the exact PR head while intentionally reporting a coverage gap for visible, but unbound, successful checks. |

## References

- [GitHub check-runs API](https://docs.github.com/rest/checks/runs)
- [Athena issue #68](https://github.com/HomericIntelligence/Athena/issues/68)
