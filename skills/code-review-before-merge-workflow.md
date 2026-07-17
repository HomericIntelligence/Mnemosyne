---
name: code-review-before-merge-workflow
description: "Review completed implementation work for correctness, regressions, maintainability, security, and test quality before merge. Use when: (1) a substantial change or complex fix is complete, (2) a branch is about to merge, (3) the author claims readiness and the claim needs independent technical review"
category: tooling
date: 2026-07-16
version: "1.0.0"
user-invocable: false
tags: [code-review, workflow, evidence, merge-gate]
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

Stop if the remote or default branch cannot be resolved unambiguously.

### Detailed Steps

1. Read the target repository's `AGENTS.md`, the requirements, and relevant plans or issues.
2. Keep the target repository as the current working directory and produce the merge-base diff (quick reference above).
3. Delegate to one independent reviewer when the host supports subagents; do not prescribe a vendor model. If delegation is unavailable, review sequentially in the current agent.
4. Inspect correctness, requirement alignment, security boundaries, error handling, public API compatibility, tests, documentation, and unnecessary complexity. Apply KISS, YAGNI, TDD, DRY, SOLID, modularity, least-astonishment, durable-artifact, and behavior-test rules. Flag tests that pin prose or flaky implementation detail, and artifacts that create ongoing manual synchronization without a demonstrated product consumer.
5. Run the repository-defined focused tests and quality gates. Never invent successful output.
6. Rank findings as critical, important, or suggestion. Include a path and line, impact, evidence, and concrete remediation for each finding.
7. Verify reviewer claims before changing code. Push back with evidence when a finding is incorrect.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Diff against local main | Reviewing `git diff main...HEAD` without fetching | Stale local base hides or fabricates changes | Always fetch the remote default branch and diff from the merge-base |
| Trusting author confidence | Accepting "it works" from the implementer | Confidence is not evidence | Review runs the gates itself and ranks findings from observed behavior |

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

Do not post review comments or mutate GitHub state unless the user explicitly requests it.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | Shipped as the `code-review` plugin skill; exercised across HomericIntelligence repositories | Migrated 2026-07-16 |

## References

- Athena development policy: `docs/policies/development.md` in HomericIntelligence/Athena
- Related: [verification-evidence-audit.md](verification-evidence-audit.md), [finish-branch-delivery-workflow.md](finish-branch-delivery-workflow.md)
