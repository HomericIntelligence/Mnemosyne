---
name: finish-branch-delivery-workflow
license: BSD-3-Clause
description: "Complete feature-branch delivery with relevant verification, repository-specific commit hygiene, and the user's existing PR or merge authorization."
category: tooling
date: 2026-07-16
version: "1.1.0"
user-invocable: false
tags: [git, branch, delivery, pull-request, dco]
---

# Finish a Development Branch

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-16 |
| **Objective** | Standard workflow for finishing a feature branch: validate, verify commit hygiene, and deliver with explicit authority |
| **Outcome** | Operational — migrated from the Athena `finish-branch` skill into standard knowledge |

## When to Use

- A branch needs verification, a pull request, or a clear account of remaining delivery work.

## Verified Workflow

### Detailed Steps

1. Read the target repository's `AGENTS.md` and development policy.
2. Use repository-local delivery tools where available. Resolve Hephaestus only if a needed helper depends on it; unavailable optional tooling need not block other delivery work.
3. Discover the default branch and repository-defined validation commands from the target's task runner, manifests, and required workflow. Do not substitute Hephaestus-specific commands.
4. Select checks for the changed behavior and applicable repository gates. Report results and unresolved coverage; continue correcting in-scope failures.
5. Review `git log <base>..HEAD` and both the merge-base and current-base diffs.
6. Check commit signing, DCO trailers, and message format where the target repository requires them. Correct applicable violations as part of delivery.
7. Complete the delivery the user requested without asking them to select it again. If delivery scope is genuinely unclear, preserve the branch while resolving that decision.
8. For authorized PR delivery, push the feature branch and link an existing tracking issue when appropriate. Merge or enable auto-merge when the user's authorization covers it; otherwise leave the PR ready for review.
9. Treat cleanup as a separate scope decision. When already authorized, inspect current worktree state and use the applicable cleanup workflow without requesting the same permission again. Preserve active or uncommitted work.

### Merge-method helper

Use the resolved Hephaestus checkout's current merge-method helper when the target repository does not provide its own. Never use an unrelated executable from `PATH` or guess an organization-wide merge method.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Direct merge to default | Merging locally to the protected default branch | Bypasses required checks and review | Always deliver through a PR against the protected branch |
| Cleanup as side effect | Removing worktrees while finishing the branch | Deleted work the user had not authorized losing | Inspect cleanup scope and preserve active work; request approval only when existing authority does not cover deletion |

## Results & Parameters

### Never

- Merge directly to the protected default branch.
- Skip hooks, fabricate successful checks, or force-push without explicit authority.
- Delete a branch or worktree without the required confirmation.
- Claim completion while CI is absent, stale, skipped incorrectly, or failing.

### Expected Output

Exact validation commands and results, commit-hygiene status, and the user's chosen delivery action (PR created/updated, branch preserved, or cleanup audit requested).

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | Shipped as the `finish-branch` plugin skill; exercised across HomericIntelligence repositories | Migrated 2026-07-16 |

## References

- Athena dependency-resolution contract: `docs/dependency-resolution.md` in HomericIntelligence/Athena
- Related: [verification-evidence-audit.md](verification-evidence-audit.md), [code-review-before-merge-workflow.md](code-review-before-merge-workflow.md)
- Adapted from [obra/superpowers](https://github.com/obra/superpowers) under the MIT License. Copyright (c) 2025 Jesse Vincent.
