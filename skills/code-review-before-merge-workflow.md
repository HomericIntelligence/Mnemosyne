---
name: code-review-before-merge-workflow
license: BSD-3-Clause
description: "Review completed implementation work for correctness, regressions, maintainability, security, and test quality before merge. Use when: (1) a substantial change or complex fix is complete, (2) a branch is about to merge, (3) the author claims readiness and the claim needs independent technical review"
category: tooling
date: 2026-07-16
version: "1.1.0"
user-invocable: false
tags: [code-review, workflow, evidence, merge-gate]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/code-review-before-merge-workflow.history"
history-cleanup-date: "2026-09-20"
---

# Code Review Before Merge

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-16 |
| **Objective** | Standard workflow for reviewing completed implementation work before merge |
| **Outcome** | Operational — migrated from the Athena `code-review` skill into standard knowledge |

## When to Use

- After a substantial change or complex fix, before merge.
- When an author (human or agent) claims work is ready — review technical evidence, not the author's confidence.
- When review feedback needs an independent recheck after fixes.

## Verified Workflow

### Quick Reference — resolve the review diff against the true base

```bash
# Discover the remote tracked by the current branch (fall back to origin)
branch=$(git branch --show-current)
remote=$(git config --get "branch.${branch}.remote" || echo origin)

# Resolve the remote's default branch unambiguously
default=$(git ls-remote --symref "$remote" HEAD | awk '/^ref:/ {sub("refs/heads/", "", $2); print $2}')

# Fetch that exact base and diff from the merge-base
git fetch "$remote" "$default"
base=$(git merge-base HEAD "${remote}/${default}")
git diff "${base}...HEAD" --stat
git diff "${base}...HEAD"
```

If the base is unclear, inspect branch tracking and the requested review scope. Continue
reviewing independently understood changes; report the diff coverage limit until the base
is resolved.

### Detailed Steps

1. Read the target repository's `AGENTS.md`, the requirements, and relevant plans or issues.
2. Keep the target repository as the current working directory and produce the merge-base diff (quick reference above).
3. Consider an independent reviewer for complex or high-risk changes when delegation is available and authorized. Otherwise review sequentially.
4. Inspect correctness, requirement alignment, security boundaries, error handling, public API compatibility, tests, documentation, and unnecessary complexity. Use the relevant design philosophies to guide judgment about simplicity, boundaries, and observable behavior. Flag tests that pin prose or flaky implementation detail, and artifacts that create ongoing manual synchronization without a demonstrated product consumer.
5. Use relevant existing validation evidence and run affected checks when inputs changed or confidence is insufficient. Observe actual repository requirements and report coverage limits honestly.
6. Rank findings as critical, important, or suggestion. Include a path and line, impact, evidence, and concrete remediation for each finding.
7. Verify reviewer claims before changing code. Push back with evidence when a finding is incorrect.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Diff against local main | Reviewing `git diff main...HEAD` without fetching | Stale local base hides or fabricates changes | Prefer a verified merge-base; disclose stale remote evidence when a fetch is unavailable |
| Trusting author confidence | Accepting "it works" from the implementer | Confidence is not evidence | Rank findings from source and applicable observed validation evidence |

## Results & Parameters

### Expected Output

A review report containing:

- Scope and diff reviewed
- Strengths
- Critical findings
- Important findings
- Suggestions
- Verification commands and results
- Verdict: ready, ready after listed fixes, or not ready

Publish review comments or change GitHub state only within the task’s authorization.
Use existing authorization without asking again for the same action. If publication is
not authorized, deliver the review locally and continue other requested work.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | Shipped as the `code-review` plugin skill; exercised across HomericIntelligence repositories | Migrated 2026-07-16 |

## References

- Athena development policy: `docs/policies/development.md` in HomericIntelligence/Athena
- Related: [verification-evidence-audit.md](verification-evidence-audit.md), [finish-branch-delivery-workflow.md](finish-branch-delivery-workflow.md)
