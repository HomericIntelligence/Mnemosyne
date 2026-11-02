---
name: pr-review-behind-base-merge-result-verification
description: "Verify the merge result of a pull request that is behind its target before a terminal verdict. Use when the branch delta passes on its own base, the target advanced past the branch base, or the review must bind integrated behavior such as strict configuration loading, registries, or test inventories."
category: tooling
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [pr-review, merge-result, stale-branch, base-drift, worktree, strict-loader, registry, terminal-verdict]
---

# PR Review Behind Base: Verify the Merge Result

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Bind the integrated behavior of a pull request that is behind its target: verify a real merge result before a terminal verdict. |
| **Outcome** | Successful. Branch-internal verification passed while the merged tree failed a strict contract. Merge-result verification found the defects, and a later review confirmed a clean merge result for a pass verdict. |

## When to Use

- A pull request is behind its target branch, and the review must publish a terminal verdict, such as an approve, gate, or merge decision.
- The branch delta is internally consistent: its code, tests, and documentation agree at the branch base.
- The target advanced past the branch base with changes that touch the same surface: removed or renamed fields, moved modules, changed registries, or changed inventories.
- The behavior under review is computed, not stored: a loader, a registry, or an inventory check derives it from the merged tree.

Do not use this skill to classify the scope of a behind-base branch. Use the
contribution-scope rule in the references for that decision. Do not use it to
select a diff lens; use the two-dot and three-dot rule.

## Verified Workflow

### Quick Reference

```bash
# 1. Bind both revisions and the true diff lens.
git rev-parse <target-oid> <head-oid>
git merge-base <target-oid> <head-oid>     # MB: what the branch really builds on
git diff "$MB...<head-oid>" --stat         # branch contribution

# 2. Read the target advance for interactions with the branch surface.
git log --oneline "$MB..<target-oid>"
git diff "$MB..<target-oid>" --stat -- <branch-paths>

# 3. Materialize the merge result in an isolated worktree.
git worktree add --detach <merge-path> <target-oid>
git -C <merge-path> merge --no-ff --no-edit <head-oid>

# 4. Verify the merged tree, then discard the worktree.
git -C <merge-path> status --short         # conflicts are findings
# run the focused contract checks against <merge-path>
git worktree remove <merge-path>
```

### Suggested Approach

1. **Bind the revisions.** Record the exact target commit and head commit. A
   branch behind its target can still hold a green branch-internal state. The
   behind count alone does not predict behavior.
2. **Read the target advance before the merge.** The range from the merge base
   to the target tells you which interactions to verify: fields that the target
   removed, modules that it moved, registries and inventories that it changed.
3. **Materialize the real merge result.** Merge the bound head into the bound
   target in a detached, isolated worktree. Keep the shared checkout clean. A
   conflict is a finding with a location, not a reason to stop the review.
4. **Verify merged artifacts, not branch artifacts.** Run the checks that
   compute behavior from the merged tree: import and load the merged
   configuration code, enumerate the merged registries and inventories, and run
   the focused tests that cover the changed surface. Reading the same files at
   both endpoints does not execute the merged code.
5. **Give the verdict from both lenses.** Branch-internal evidence plus a
   failing merged tree is a fail verdict. Cite the merged artifact and the
   failing line. A clean merge result with branch-internal evidence supports
   the pass verdict. Record both lenses in the review.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Verify the branch delta only | Checked the branch code, tests, and documentation against the branch base, and issued a pass verdict | The target had removed a configuration field that the branch still passed. The strict loader rejected the merged configuration, and the failure appeared only in the merged tree | Branch-internal consistency does not exercise composed behavior. Verify the merge result before a terminal verdict |
| Read both endpoint trees to predict integration | Compared the branch files and the target files at the two endpoints | Tree comparison does not run the merged code. The loader failure needed execution to appear | Run the focused checks against the merged tree |
| Compare the branch inventory against the branch registry | Checked the new test module against the registry as it exists on the branch | The target advanced the inventory contract, so the merged tree held a module that no merged registry row covered | Enumerate registries and inventories from the merged tree |

## Results & Parameters

### Configuration

```yaml
merge_materialization:
  worktree: detached and isolated     # never the shared checkout
  direction: merge the head into the bound target with --no-ff
  lifetime: disposable                # remove after the verdict; it holds no unique state
verify_against_merged_tree:
  - strict configuration loaders     # loaders that reject unknown fields
  - module, command, and tier registries
  - test inventories
  - imports and entry points of merged code
  - focused tests that cover the changed surface
verdict_rule: branch-internal evidence and merge-result evidence must both support the verdict
```

### Expected Output

- The merge either completes or names the conflicting paths.
- Each focused check passes on the merged tree, or the failure names the merged artifact.
- The review cites the merge-base diff for the contribution and the merged-tree checks for integration.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| private repository | Terminal reviews of behind-base pull requests | General pattern only. Do not record internal identifiers. See [notes](pr-review-behind-base-merge-result-verification.notes.md). |

## References

- [PR Review Behind Its Base: Contribution and Scope](pr-review-behind-base-contribution-scope.md)
- [PR Review: Two-Dot and Three-Dot Diffs](pr-review-two-dot-vs-three-dot-diff.md)
- [Verify PR Ready for Merge](verify-pr-ready.md)
- [CI Merge-Preview Script Count Drift](ci-merge-preview-script-count-drift.md)
