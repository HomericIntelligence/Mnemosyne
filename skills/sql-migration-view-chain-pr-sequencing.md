---
name: sql-migration-view-chain-pr-sequencing
description: "Sequence parallel pull requests whose incremental migrations redefine the same SQL object so that migration-stem apply order equals the intended semantic layering. Use when several open PRs add CREATE OR REPLACE migrations on the same view or table and every merge-prefix must stay deploy-safe."
category: ci-cd
date: 2026-10-26
version: "1.0.0"
user-invocable: false
tags: [migrations, sql-view-chain, create-or-replace, apply-order, merge-order, regression-window, chain-guard, pr-sequencing, monorepo]
---

# SQL Migration View-Chain PR Sequencing

**Supporting details:** [notes](./sql-migration-view-chain-pr-sequencing.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Deliver several open PRs that each add one incremental migration redefining the same SQL object (one named view or table), without ever letting a deployable intermediate state silently lose rows, visibility, or earlier received behavior. |
| **Outcome** | Successful; verified-ci in the source case (all chained migrations landed in stem order, the highest stem is the final object definition on every database, and the chain holds under both empty-database install and upgrade paths). |

## When to Use

- Two or more open pull requests each add one new incremental migration whose SQL contains
  `CREATE OR REPLACE` (or another full-object redefinition) of the **same** named view or table.
- The deploy pipeline applies migrations in filename/stem order, so the **highest stem at apply
  time** wins on every database — independently of git merge order.
- Databases at different ages exist (fresh installs replay the whole chain; upgraded installs
  apply only the missing tail), so only the final stem's definition must produce the intended
  end state in both directions.
- You must decide per-PR renumbering, merge order, and whether arming auto-merge on every PR in
  the cluster is safe.

## Verified Workflow

### Quick Reference

1. Assign stems so stem order == semantic layering; the correct final definition owns the highest
   stem. Renumber BEFORE review lands, not after merges start.
2. Audit every merge-prefix; reorder merges or fold lost rows so no reachable prefix regresses.
3. Merge strictly low-stem to high-stem; disarm auto-merge on out-of-order PRs and re-verify arm
   state before each merge — other actors can arm them back.

### Decision Rules

1. **Stem order is the merge-order contract.** The deployer applies migrations in stem order on
   fresh installs and in the same order on upgrades. Git merge order only controls when a file
   appears, never the apply order. The object definition that must be the end state owns the
   highest stem; design every chain member to be self-contained-correct when applied in stem
   order from a fresh install and when applied as a tail over an existing database.
2. **Audit each merge-prefix for regressions.** Enumerate every reachable intermediate state
   (prefix of the chain that could exist on a deployable main between merges). A prefix is a
   regression when its highest applied redefinition drops rows, hides entities, or reverts
   behavior that an already-merged lower stem established. Fix by reordering merges so the
   regression-free chain lands first, or by folding the lost content into the intermediate
   migration. Never arm a merge whose landing creates a regression prefix while a fixing PR is
   still open.
3. **Fold upstream state into rebased members.** When an earlier member of the chain was extended
   by a fourth migration (for example, a static allowlist gained rows after the chain was
   authored), keep the later members' content consistent with that extension during rebase-on-
   conflict; a rebase that replays an out-of-date literal redefinition recreates a regression
   window under a different stem number.
4. **Number for the final deployer view, not the authoring timeline.** If branches were authored
   before their upstream neighbors existed, renumber the files and every in-repo reference
   (tests, docs, index lists) at delivery time, then treat the rebase as the single point of
   truth for semantics.
5. **Guards belong in the repo, not in runbook text.** Prefer tests that keep the chain honest
   automatically (see notes for the concrete patterns): an explicit enumeration of the
   defining-migration set so a new definer fails loudly; a monotonic static-prefix check where
   literals exist; and order-free ledger/receipt assertions. A compaction later replacing the
   per-migration lists with a directory-derived helper is fine — the semantic guards survive it.
6. **Foreign actors change nothing about the ordering contract.** A routine merge train,
   dependabot burst, or another session's PR can land a chain member early. Re-audit the result
   for compositional correctness; if the landed content matches the chain design, continue with
   the next stem. Only intervene (disarm, rebase, repair) when the landed state breaks a prefix
   invariant.

### Common Execution Traps

- `gh pr merge --auto` silently accepts arms on CONFLICTING or out-of-order PRs. Auto-merge fire
  order then depends on CI completion order, not on the chain. Disarm non-next members; re-check
  arm state right before each land, because other actors can re-arm.
- A mergeable/`MERGEABLE` report can disagree with a direct merge attempt after concurrent branch
  movement; trust the merge result and re-audit, not the flag.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Number migrations by branch/authoring order | Let each PR keep the stem it was created with during a multi-issue implementation wave | A branch authored last but merged through review first superseded an earlier semantic layer; upgrades run the stems in filename order regardless of review order | Renumber for the final deployer layering before merges begin; git order is irrelevant to the apply order |
| Arm auto-merge on the whole cluster | Armed `--auto --squash` on every chain PR for throughput | The fallbacks-view PR landed before the fleet-view PR and before the registry-projection PR it assumed; the fp8 rows briefly vanished from the deployed highest redefinition | Arm only the next member; audit prefixes before each merge; disarm and re-audit out-of-order arms |
| Rebase replaying the authored redefinition | Conflict-resolved a chain member by keeping its original literal view after an upstream fourteenth-row addition landed | The rebased intermediate stem would have dropped the added rows again whenever it was the highest applied stem | During each chain rebase, fold upstream extensions into the member's literals or reorder the merge |
| Insertion-order ledger assertion in receipt tests | Asserted `after == before + blocked` in the migration-ledger integrity test | Any new stem sorting after the blocked dependents broke the assertion even though the ledger was correct | Compare sets or sort the expected side (`sorted(before + blocked)`) so the guard is order-free for new stems |

## Results & Parameters

### Configuration

```yaml
chain_member:
  stem_assignment: semantic_layering_over_authoring_order
  final_object_definition: highest_stem
merge_protocol:
  order: lowest_stem_first
  auto_merge: arm_only_next_member
  before_each_merge:
    - verify_arm_state_unchanged
    - confirm_prefix_regression_free
    - confirm_current_head_vs_base
```

### Expected Output

- Migrations directory contains the chain in lexical order matching the intended layering.
- Every reachable merge-prefix applies cleanly from empty and from an upgraded template, and the
  object definition of the highest applied stem never drops content an earlier merged stem had.
- Enumeration-style guard fails loudly when a new definer of the shared object appears; DB-level
  tests validate only the final (highest-stem) definition's behavior.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A private service monorepo | Dashboard-telemetry delivery wave: 8 concurrent PRs, 4 of them redefining one shared reporting view with new incremental migrations; one member merged by a foreign actor mid-flight; dependabot and task waves moved main every ~20-60 minutes | All 8 merged in stem order after renumbering to 99-102, prefix regression audits, chain guards (defining-set enumeration, monotonic static prefix, history-seed check, order-free ledger assertion), and per-rebase composition of literals and docs; verified-ci |

## References

- [github-auto-merge-ci-gating-merge-method](github-auto-merge-ci-gating-merge-method.md) — layered merge-state diagnosis before arming or force-merging members
- [automation-multi-repo-pr-sweep-rebase-resolve](automation-multi-repo-pr-sweep-rebase-resolve.md) — merge-train cascade handling for sibling PRs touching shared files
- [rebase-stale-automation-pr-onto-refactored-main](rebase-stale-automation-pr-onto-refactored-main.md) — semantic conflict classes to preserve PR intent across upstream refactors
- [git-rebase-signing-ci](git-rebase-signing-ci.md) — keep every rebase signed and under lease; end-game window manufacturing on strict up-to-date repos
