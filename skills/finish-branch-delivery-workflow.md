---
name: finish-branch-delivery-workflow
description: "Finish a development branch with repository-defined validation, signed DCO Conventional Commits, and explicit delivery choices. Use when: (1) implementation on a feature branch is complete, (2) a branch is ready for PR creation or preservation, (3) commit hygiene must be verified before delivery"
category: tooling
date: 2026-07-16
version: "1.0.0"
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

- Implementation on a branch is complete and verification has already passed (run the verification evidence audit first; do not proceed while relevant repository-defined checks fail).

## Verified Workflow

### Detailed Steps

1. Read the target repository's `AGENTS.md` and development policy.
2. Prepare Hephaestus at `$HOME/.agent_brain/automation` under Athena's canonical dependency-resolution contract. Report repository, SHA, and trust basis; any preparation or revalidation failure is blocking.
3. Discover the default branch and repository-defined validation commands from the target's task runner, manifests, and required workflow. Do not substitute Hephaestus-specific commands.
4. Run the relevant tests, validation, formatting, linting, and build/package checks. Report exact commands and results.
5. Review `git log <base>..HEAD` and both the merge-base and current-base diffs.
6. Verify every commit is cryptographically signed, has a DCO `Signed-off-by` trailer, and follows Conventional Commits. Fix violations before offering delivery.
7. Present three choices: create/update a pull request, preserve the branch and worktree, or request a separate read-only worktree-cleanup audit. Do not represent a cleanup request as removal authority.
8. For a PR, push only the feature branch and create a body containing `Closes #N` when a tracking issue exists. Do not enable auto-merge or merge without explicit user authority.
9. Never remove a worktree directly. Route each candidate through the worktree-cleanup audit, which requires a fresh audit and separate explicit approval for the exact path and audited HEAD.

### Merge-method helper

Use the resolved Hephaestus checkout's current merge-method helper when the target repository does not provide its own. Never use an unrelated executable from `PATH` or guess an organization-wide merge method.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Direct merge to default | Merging locally to the protected default branch | Bypasses required checks and review | Always deliver through a PR against the protected branch |
| Cleanup as side effect | Removing worktrees while finishing the branch | Deleted work the user had not authorized losing | Worktree removal always goes through a separate audited approval |

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
