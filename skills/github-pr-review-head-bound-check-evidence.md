---
name: github-pr-review-head-bound-check-evidence
license: BSD-3-Clause
description: "Use when a review or promotion must bind CI evidence to a selected commit, or a branch moves during qualification."
category: ci-cd
date: 2026-08-02
version: "1.1.0"
user-invocable: false
verification: evidence-bound-review
tags: [ci, review, commit-sha, immutable-evidence, qualification]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/github-pr-review-head-bound-check-evidence.history"
history-cleanup-date: "2026-09-20"
---

# Bind Check Evidence to the Selected Commit

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2026-09-18 |
| Objective | Reuse applicable evidence without accepting results for a different source. |
| Outcome | Distinguish candidate identity, workflow identity, and current branch identity. |

## When to Use

- A review needs proof that required checks passed for a specified commit.
- A branch advances while qualification runs against an immutable source input.
- A manual workflow tests a source commit different from its workflow commit.
- A promotion would repeat a completed qualification without a changed requirement.

## Verified Workflow

### Quick Reference

Bind evidence to the selected commit and execution contract. A branch move alone does not invalidate that evidence.

### Procedure

1. Record the repository, selected source SHA, and applicable required checks.
2. Read provider records for the specified run and attempt. Treat comments and status summaries as discovery links.
3. For ordinary commit checks, verify the provider's source binding against the reviewed commit.
4. For a manual workflow, distinguish the workflow commit from the tested source input.
5. Verify the tested source through the trusted workflow's existing source record. The run's head SHA alone can identify workflow code.
6. Verify the required jobs, their terminal results, trusted publisher, and applicable artifact identities.
7. Require nonempty execution where the contract requires tests. Preparation or collection failure is not successful qualification.
8. Retain successful evidence when only the branch tip advances. Failed evidence remains diagnostic evidence for the same candidate.
9. If the selected candidate changes, obtain applicable evidence for the new candidate.
10. If coverage or execution requirements change, compare compatibility and repeat only the affected validation.
11. Record the workflow revision for traceability. Do not invalidate a run solely because an unrelated workflow revision exists.
12. Before promotion, verify that the authorized source is the qualified candidate. A newer PR head requires its own evidence.
13. Refresh observations of mutable production state at the operation boundary. Source tests do not prove current target health.

Use provider issues for requirements, PR reviews for source review, and Actions records for execution results. Link these records instead of copying their authority into handoff files. A comment can identify a run; it cannot prove that run passed.

Immediately before review publication or a readiness conclusion, read the PR identity, open state, base SHA, head SHA, and effective gate policy again. Reconcile each change with the selected candidate and evidence before proceeding.

Repository policy determines whether prior execution can satisfy a delivery gate. Change that policy through review before removing a required execution.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trust a green summary | Accepted a rollup without source identity. | The summary could include another commit. | Inspect the provider's immutable binding. |
| Invalidate on branch movement | Called a pinned run stale after the branch advanced. | The tested source had not changed. | Compare selected commits, not branch tips. |
| Use workflow head as tested source | Assumed a manual run tested its workflow revision. | The workflow selected another source SHA. | Verify both identities separately. |

## Results & Parameters

Record selected source SHA, workflow revision, run ID, attempt, required job results, publisher, and existing artifact references.

Report one result: applicable successful evidence, applicable failed evidence, or missing/incompatible evidence. Report the exact changed input when a rerun is necessary.

## Verified On

A qualification session exposed an incorrect stale-evidence claim after branch movement. The operator confirmed that the candidate was an immutable source input. This supports the identity rule; it does not prove deployment success or a measured reduction in duration.

## References

- [Check runs API](https://docs.github.com/rest/checks/runs)
- [Workflow runs API](https://docs.github.com/rest/actions/workflow-runs)
