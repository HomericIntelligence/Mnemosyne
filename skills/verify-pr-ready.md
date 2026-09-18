---
name: verify-pr-ready
license: BSD-3-Clause
description: Check merge readiness against live repository policy when checks, reviews, conflicts, or branch freshness are uncertain.
category: ci-cd
date: 2025-12-30
version: "1.1.0"
user-invocable: false
history: verify-pr-ready.history
---
# Verify PR Ready for Merge

## Overview

| Date | Objective | Outcome |
| --- | --- | --- |
| 2025-12-30 | Check merge requirements | Identify actual blockers without adding freshness or approval requirements |

## When to Use

- Before a manual merge or an authorized auto-merge request.
- When a PR is behind its target branch, blocked, or waiting for checks.
- When deciding which validation evidence still applies.
- When publishing a PR before validation is complete.

## Verified Workflow

### 1. Bind the PR and its requirements

Record the repository, PR number, target branch, and head commit. Read the current
repository instructions, applicable rulesets, branch protection, and required workflow
policy. These sources determine required checks, approvals, signatures, thread
resolution, and merge method. Do not infer policy from an old lesson or a status label.

Require human approval only when an applicable rule or action requires it. An agent
review does not replace a required forge approval. Conversely, a review workflow does
not create an extra human approval requirement.

### 2. Classify integration state

| State | Action |
| --- | --- |
| Behind the target, with no actual conflict or missing dependency | Continue when repository policy permits it. Do not rebase only for freshness. |
| Actual merge conflict | Resolve the conflict in an isolated worktree. Use the repository-supported integration method. Review and validate affected content. |
| Necessary dependency exists only on the target | Confirm that the task needs it, then integrate it with a supported method. Do not duplicate the missing implementation. |
| Mergeability is pending or unknown | Read the state again with a bounded wait. If it remains unknown, report the uncertainty and withhold merge. Do not infer a conflict. |
| Policy requires current integration with the target | Satisfy that requirement through the supported update method or merge queue. The policy does not itself prescribe a rebase. |

Use a rebase for an actual conflict, a necessary dependency, or an explicit request.
A cleanup request is separate and does not imply a rebase request.

### 3. Select validation and retain honest evidence

Prefer checks for the affected surface. Run broader checks when repository policy,
shared dependencies, or the change's risk requires them. Do not add tests that only
freeze documentation wording.

Reuse prior evidence only when its relevant source inputs, command, dependencies,
configuration, and environment remain applicable. Record the original tested commit,
command, result, and reason for reuse. A historical run is not a new current-head run.
If relevant inputs changed or applicability is uncertain, run the affected check again.

Required CI must satisfy the repository's current-head or merge-queue contract. Local
results and reused evidence do not replace those required checks. Review must cover
the exact candidate head before merge. Target movement alone does not change that
head, but can require a new integration check under repository policy.

### 4. Separate publication from merge

Publish a PR early when the task authorizes it, including while validation is pending.
State pending checks and evidence limits accurately. Publication is not a merge-readiness
claim. Before merge, require all applicable checks, exact-head review, required approvals,
thread resolution, and other repository gates. Do not bypass a failed gate.

### Quick Reference

These commands read state. Replace the placeholders with the bound target.

```bash
gh pr view <pr> --repo OWNER/REPO --json state,baseRefName,headRefOid,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
gh api repos/OWNER/REPO/rules/branches/main
gh api repos/OWNER/REPO/branches/main/protection
gh pr checks <pr> --repo OWNER/REPO --required
gh pr view <pr> --repo OWNER/REPO --json reviews
```

Use the actual target branch in both policy queries. Inspect both policy layers when
available. A missing branch-protection record does not mean that rulesets are absent.
An access error is not evidence that there are no requirements.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Prior checklist | Treated every branch behind main as a merge blocker | Added a freshness rule without checking repository policy | Classify actual conflicts, dependencies, and live policy first |
| Prior error handling | Recommended rebase when a mergeability query failed | A query failure or pending computation does not prove a conflict | Report the query error or recheck pending state with a bound |

## Results & Parameters

- Ready: the bound candidate satisfies all applicable merge gates.
- Blocked: name the actual missing gate, conflict, or dependency.
- Unknown: name missing policy access or pending mergeability; do not report ready.
- Pending validation: ordinary PR publication can proceed; merge cannot proceed until required gates pass.
- Reused evidence: retain its original revision and the applicability explanation.

## Evidence Boundary

The prior entry recorded a ProjectOdyssey merge-validation workflow. That record and
the complete prior text remain in [history](verify-pr-ready.history). The current policy
correction does not add operational verification or certify technical-English conformance.

## References

- [Ruleset review counts](github-ruleset-review-count-governance.md)
- [Required status checks](github-ruleset-required-status-checks-management.md)
- [GitHub CLI PR view](https://cli.github.com/manual/gh_pr_view)
