---
name: architecture-serial-depends-on-chain-code-serial
license: BSD-3-Clause
description: "Sequence changes with real code dependencies. Use when an issue consumes symbols or wiring from an earlier unmerged change, even when the edited files are separate."
category: architecture
date: 2026-07-06
version: "1.1.0"
user-invocable: false
verification: verified-ci
tags:
  - serial
  - epic
  - depends-on
  - dependency-chain
  - cleanup-wave
  - sequential-pr
  - code-serial
  - do-not-parallelize
  - launch-after-merge
  - prerequisite-verification
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/ed1bd4f54fd4aaba446af92c8b3ab9aff2589ae3/skills/architecture-serial-depends-on-chain-code-serial.history"
history-cleanup-date: "2026-09-20"
---

# A Serial `Depends on #prev` Epic Chain Is CODE-Serial, Not Just Order-Serial

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-06 |
| **Objective** | Execute the 5-issue cleanup wave of ProjectHephaestus epic #1809 (#1819 -> #1823), each `Depends on #prev`, each converting a legacy CLI (planner / implementer / ci_driver / pr_reviewer) into a thin pipeline wrapper and deleting the legacy module. |
| **Outcome** | SUCCESS — all PRs merged with green CI. ~25.6k LoC deleted; coverage omit-list shrank 17 -> 12 modules. |
| **Verification** | verified-ci — executed end-to-end; all 6 PRs merged with green CI in ProjectHephaestus epic #1809. |

## When to Use

- You are executing an epic whose sub-issues each carry `Depends on #prev` on their own line — a strictly serialized chain, not an independent batch.
- Each issue in the chain builds a new capability by mirroring the PATTERN the previous issue established AND by consuming concrete new code the previous issue landed (a new symbol, a new config field, a coordinator wiring).
- You are tempted to parallelize two consecutive chain issues to save wall-clock because their touched files look disjoint.
- A sub-agent launched for issue N+1 REFUSES or makes zero changes, reporting a "false premise" (the prerequisite conversion never happened / the new symbol isn't wired in) — that is the chain telling you the base lacks issue N's merged code.

## Verified Workflow

### The key insight: code-serial, not order-serial

A `Depends on #prev` chain is not merely an *ordering* preference (do #1820 before #1821 to keep labels tidy). It is a *code* dependency: issue N+1's implementation reads and extends issue N's MERGED code. Concretely in epic #1809:

- **#1821** (implementer -> pipeline wrapper) needed TWO things from **#1820**:
  1. #1820's planner-wrapper PATTERN to mirror, AND
  2. #1820's coordinator scope-injection code to exist ON MAIN — `PipelineConfig.scope`, `_clamp_seed_stage_to_scope`, and `scope.trimmed_routes()`.
- A sub-agent launched for #1821 off a base WITHOUT #1820 correctly REFUSED — it reported a "false premise: planner never converted, PipelineScope not wired into coordinator" — and made zero changes. That refusal is the correct behavior, and it is the signal that the chain was parallelized wrongly.

Prefer a base that contains the actual prerequisite before implementing its consumer. If the task permits stacked branches, an unmerged prerequisite can supply that base. Where the epic explicitly requires merged predecessors, respect that dependency and continue independent preparation while it is pending.

### Quick Reference

This example is for an epic that requires merged predecessors. For an authorized
stacked branch, inspect the exact prerequisite revision and its actual API on
that base instead. Label assumptions where the API is unavailable; do not claim
that hypothetical symbols are source facts. Continue independent work while
resolving the dependency.

```bash
# BEFORE creating issue N+1's worktree, prove issue N's prerequisite is on main.
# Fetch first, then assert the new symbol exists on origin/main (count > 0):
git fetch origin main
git show origin/main:hephaestus/automation/pipeline/coordinator.py \
  | grep -c "_clamp_seed_stage_to_scope"   # must be > 0

# Only after that count is > 0, create the N+1 worktree off CURRENT origin/main
# (which now contains issue N's merged code):
git -C "$REPO" worktree add "/tmp/wt-issue-$NEXT" -b "$NEXT-auto-impl" origin/main
cd "/tmp/wt-issue-$NEXT" && pixi run dev-install
```

### Detailed Steps (the per-issue loop that worked)

For each dependent issue, inspect the prerequisite code and select a compatible base.
Implement and verify the requested behavior, then publish through the repository's
applicable review and merge process when authorized. Use signing, labels, or auto-merge
only where that process calls for them. Confirm a merge when downstream work requires
merged code; a green check or an armed merge request is not the merge itself.

Independent investigation, tests, and plan refinement can continue while a dependency
is pending. Avoid recreating the prerequisite or treating its absence as a reason to
end the whole task.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Parallelize #1821 with #1820 | Launched #1821's implementation sub-agent in PARALLEL with #1820 to save wall-clock, because the two issues' touched files looked disjoint | The sub-agent REFUSED with "false premise: planner never converted, PipelineScope not wired into coordinator" and made zero changes — #1820's coordinator scope-injection (`PipelineConfig.scope`, `_clamp_seed_stage_to_scope`, `scope.trimmed_routes()`) was not yet merged to main, so #1821 had nothing to build on | Do NOT parallelize a `Depends on #prev` chain even when the files look disjoint. The dependency is on MERGED CODE, not on file overlap. Launch N+1 only after N merges. |
| Assume "order-serial" is enough | Treated `Depends on #prev` as a scheduling hint (do them in order) rather than a hard code dependency | Ordering alone does not put issue N's new symbols on the base branch N+1 is cut from; a worktree cut before N merges lacks N's code regardless of order | Verify the prerequisite symbol is on `origin/main` (`git show origin/main:path \| grep -c <symbol>` > 0) BEFORE cutting the N+1 worktree. |

## Results & Parameters

Concrete prerequisite that made the chain code-serial (epic #1809, #1821 depending on #1820):

```text
Issue #1820 (planner -> pipeline wrapper) landed on main:
  - PipelineConfig.scope                 # new config field
  - _clamp_seed_stage_to_scope(...)      # new coordinator helper
  - scope.trimmed_routes()               # new route-trimming call

Issue #1821 (implementer -> pipeline wrapper) required BOTH:
  1. #1820's planner-wrapper PATTERN to mirror, AND
  2. the three symbols above to exist ON MAIN (coordinator scope wiring).

Sub-agent launched for #1821 off a base WITHOUT #1820:
  -> REFUSED: "false premise: planner never converted,
     PipelineScope not wired into coordinator" -> 0 changes.
```

Prereq-verification gate to run before each N+1 worktree:

```bash
git fetch origin main
COUNT=$(git show origin/main:hephaestus/automation/pipeline/coordinator.py \
        | grep -c "_clamp_seed_stage_to_scope")
[ "$COUNT" -gt 0 ] || { echo "prereq #N not on main yet — do NOT cut N+1"; exit 1; }
```

Successful outcome of the full 5-issue cleanup wave (#1819 -> #1823):

```text
~25,600 LoC deleted (legacy CLI modules removed after wrapper conversion)
coverage omit-list: 17 -> 12 modules
all 6 PRs merged with green CI
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Epic #1809 cleanup wave (#1819 -> #1823); each issue `Depends on #prev`, converting planner/implementer/ci_driver/pr_reviewer into pipeline wrappers | All 6 PRs merged with green CI; ~25.6k LoC deleted; omit-list 17 -> 12 |
