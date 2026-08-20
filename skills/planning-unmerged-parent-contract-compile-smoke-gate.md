---
name: planning-unmerged-parent-contract-compile-smoke-gate
description: "Plan against an approved but unmerged parent without treating proposed APIs as landed facts. Use when a child imports not-yet-present symbols, a reviewer flags unread APIs, a validation-only task depends on a parent script, a dispatch table needs concrete callables, or numeric/file-line claims may have drifted. Gate implementation on parent presence, read every cited API, and make compile smoke the first post-merge check."
category: architecture
date: 2026-07-04
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: unverified
history: planning-unmerged-parent-contract-compile-smoke-gate.history
tags: [planning, unmerged-parent, prerequisite-gate, contract, compile-smoke, assumption-audit]
---

# Planning Against an Unmerged Parent

## Overview

An approved parent plan is a contract to coordinate against, not evidence that its code exists. A
child plan may use the proposed names and signatures, but must stop before implementation until the
parent lands, then compile against the actual merge before tests or dependent edits proceed.

This skill remains `unverified`: its rules were learned from plan reviews, but the compacted corpus
does not claim an end-to-end implementation result. Project cases are indexed in
[`planning-unmerged-parent-contract-compile-smoke-gate.notes.md`](planning-unmerged-parent-contract-compile-smoke-gate.notes.md),
and the complete prior source is archived in
[`planning-unmerged-parent-contract-compile-smoke-gate.history`](planning-unmerged-parent-contract-compile-smoke-gate.history).

## When to Use

- A child issue depends on an unmerged parent with an approved plan.
- Planned imports, types, fields, or helpers do not exist on the target branch.
- Review found an API citation that was inferred rather than read from source.
- A plan includes numeric counts, exact file lines, a route/op table, or a signature change.
- A validation-only child will run a parent-produced CLI, container command, or log parser.
- A randomized training criterion needs a stable threshold and honest fallback.

## Verified Workflow

### 1. Establish the dependency state

Verify both merge history and the concrete artifact the parent is expected to create:

```bash
git fetch origin
git log --oneline origin/main | grep '(#<parent>)'
test -d <path-created-by-parent>
gh pr list --state all --search '<parent>'
```

An empty PR search or absent path means the dependency is not implementation-ready. Put a literal
step zero in the child plan: stop if the required path/symbol is absent; do not write importing
tests or implementation until the parent has merged. A prose `Depends on #N` note is insufficient.

### 2. Separate contracts from facts

Transcribe approved parent names and signatures as the expected contract and identify their source.
List every external API not opened in the current tree under `Unverified API Assumptions`, with:

```text
assumption | expected signature/behavior | source to read | downstream plan locations
```

If review flags an API, read its declaration now and revise every affected step. Do not move the
verification later in the plan. Treat any cited-but-unread call shape, return type, default, flag,
log format, loader behavior, or container invocation as unverified.

### 3. Make the re-plan mechanical

Add an assumption mapping:

```text
Assumption | file/line to inspect after merge | plan sections to update | failure action
```

Immediately before publishing, re-run searches for every cited line and replace approximate line
numbers. Grep numeric claims from the current tree rather than copying issue prose. Check open work
for same-line edits so two planned PRs do not independently update one stale count or comment.

Before changing a per-example function signature, find all callers:

```bash
grep -rn 'function_name(' --include='*.mojo' .
```

Every cross-file hit changes the planned edit set. Never dismiss an unexpected caller as local.

### 4. Resolve every dispatch case

Every op, route, or dispatch table must map each enumerated case to a concrete named callable and a
freshly verified `file:line`. If no clean public seam exists, state that gap and select the smallest
explicit seam. Do not write “dispatch to module X.” A test double used by later tests must enumerate
its complete mutator surface rather than “etc.”

For worker callbacks whose result is observed through `future.result()`, plan capture of
`BaseException`, not merely `Exception`. Specify helper paths such as lock files. Derive symbol-set
invariants from the public export surface (for example `__all__`) and assert the set is nonempty so
the test cannot pass vacuously.

### 5. Compile first after the parent merges

Once the prerequisite exists, refresh the branch and run the repository’s strict compile command
before dependent tests or implementation:

```bash
git fetch origin
git rebase origin/main
pixi run mojo build --Werror <entrypoint>
```

Any failure means the approved contract drifted. Re-read merged source, update the assumption map,
and revise the child plan before proceeding. Also smoke-run the example’s own `main()` with minimal
inputs; an importing test does not exercise CLI parsing, loader defaults, or top-level wiring.

### 6. Harden validation-only plans

Read the actual entrypoint, flags, log records, data-loader defaults, container recipe, and artifact
rules. Preflight container invocation and dataset network access. If evidence lives under a
gitignored directory, name an allowed attachment route such as:

```bash
gh pr comment <pr> --body-file <evidence-file>
```

Require parsers to report and assert `parsed N > 0`; exit-zero with zero parsed samples is a loud
failure, not success. Set wall-clock budgets from measured data or label them estimates with a stop
condition.

For noisy loss series, retain the issue’s exact threshold and add diagnostics rather than weakening
it:

```text
hard floor:       loss[-1] < loss[0]
issue threshold: loss[-1] < 0.95 * loss[0]
trend diagnostic: fitted slope < 0
```

Mitigate instability with more samples, stronger signal, or warm-up. A fitted trend may explain a
noisy plateau but never replaces the issue-prescribed assertion.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Parent-as-code | Treated an approved plan as merged code | Names and signatures drifted | Hard prerequisite gate, then compile first |
| Deferred source read | Moved reviewer-flagged API checks later | Wrong assumptions contaminated the plan | Read source now and revise every dependent step |
| Approximate citations | Copied lines and counts from prose | Plan became stale and unverifiable | Re-grep immediately before publication |
| Module dispatch | Named a module but no callable | Cases had no concrete seam | Resolve every case or name the missing seam |
| Empty parser | Accepted a zero-record log | Format drift yielded meaningless success | Assert and print `parsed N > 0` |
| Weakened threshold | Lowered a flaky issue target | Changed the acceptance contract | Preserve it; improve data or hyperparameters |
| Import-only smoke | Compiled only an importing test | Missed top-level entrypoint failures | Smoke-run the example’s `main()` |

## Results & Parameters

```text
parent issue/PR and approved-plan URL
expected merge artifact and hard prerequisite command
expected imports, call signatures, return types, fields, and defaults
unverified API assumptions and their source locations
assumption-to-plan-section mapping
complete dispatch table and test-double surface
first post-merge compile command and entrypoint smoke command
numeric-count and caller-search commands
validation flags, log format, parsed-sample guard, artifact route, wall-clock budget
acceptance thresholds and non-weakening mitigations
```

## Verified On

- Review-derived planning cases through 2026-07-04.
- Verification remains `unverified`; compaction for issue #3335 does not upgrade the evidence.
