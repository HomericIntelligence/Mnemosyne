---
name: dry-refactoring-workflow
description: "Use when duplicated or near-duplicated code, data, or control flow should be consolidated without changing behavior. Covers current-state discovery, exact-vs-intentional-variant classification, canonical placement, TDD, compatibility and patch-seam preservation, incremental migration, and anti-drift verification."
category: architecture
date: 2026-07-04
version: "2.0.0"
user-invocable: false
verification: mixed
history: dry-refactoring-workflow.history
tags: [dry, refactoring, duplication, tdd, canonical-source, behavior-preservation, patch-seams, intentional-variants, anti-drift]
---

# DRY Refactoring Workflow

Consolidate repeated behavior into one authority while preserving each consumer's contract.

## Overview

| Field | Value |
| ------- | ------- |
| **Objective** | Remove duplication without flattening intentional differences or breaking callers |
| **Outcome** | A reusable discovery, classification, TDD, migration, and verification workflow |
| **Verification** | Mixed: the core workflow has verified-CI and verified-local uses; label each cited case independently |
| **History** | [Version history and pre-compaction detail](./dry-refactoring-workflow.history) |
| **Notes** | [Session notes and case index](./dry-refactoring-workflow.notes.md) |

## When to Use

Use this workflow when:

- identical logic or data construction appears in multiple consumers;
- several implementations share a stable core but retain behavior-bearing variations;
- repeated setup, retry, resource-lifecycle, or drain-loop scaffolding surrounds distinct bodies;
- a helper, constant, parser, wrapper, or small module should become the canonical source;
- a duplication issue cites counts, paths, or code that may have changed since it was written; or
- a prior consolidation may already have resolved the issue and only verification remains.

Do not consolidate solely because code looks similar. Keep implementations separate when their contracts,
ownership, dependency direction, or expected evolution differ. Use a migration- or public-API-specific skill
when moving ownership or removing an external interface is the primary intent.

## Verified Workflow

### Quick Reference

```bash
# Re-ground the task on the current tree.
rg -n '<symbol-or-literal>' <source-roots> <test-roots> <docs-roots>
rg -n 'patch\(|patch\.object|monkeypatch' <test-roots>

# Compare candidate bodies and locate every consumer before editing.
git diff --no-index <candidate-a> <candidate-b>
rg -n '<old-symbol-or-module>' .

# Run the repository-native RED/GREEN and regression gates.
<test-command> <focused-test>
<test-command> <affected-suite>
<lint-command>
<typecheck-command>

# Re-run a self-falsifying search after migration.
rg -n '<old-duplicate-pattern>' <source-roots> <test-roots> <docs-roots>
```

Core loop: **discover → classify → protect behavior → extract → migrate incrementally → remove duplicates → verify**.

### 1. Re-ground the task

Read the issue, plan, and review, then verify every cited path, count, duplicate body, and test target against
the current revision. Search for the behavior or literal itself, not only the named file. Treat issue evidence
and approved-plan anchors as hypotheses when the tree has moved.

If the canonical implementation already exists and every intended consumer delegates to it, stop planning a
second refactor. Verify the current state and add an anti-drift guard only when it protects a durable product
contract.

### 2. Inventory consumers and classify candidates

Record each candidate's inputs, outputs, exceptions, logging, side effects, public exports, patch targets, and
layer ownership. Classify before choosing an abstraction:

| Classification | Action |
| --------------- | ------ |
| Exact behavior | Keep one implementation and migrate all consumers |
| Shared core plus intentional extras | Extract only the core; compose or parameterize explicit variations |
| Shared scaffold around different bodies | Extract the scaffold with a callback, generator, or context manager |
| Superficial similarity | Leave separate and document the behavior-bearing difference |

Prefer the narrowest abstraction that removes the demonstrated duplication. Do not parameterize unrelated
differences merely to force code through one helper.

### 3. Choose the canonical home

Prefer an existing shared module that already owns the concept and is reachable by every consumer without
reversing dependency direction. If a new module is necessary, make it a focused leaf with minimal imports.
Avoid base classes or mixins unless the consumers already share that abstraction.

Keep compatibility wrappers or re-exports when a local name is public, patched by tests, or used as an
integration seam. A re-export preserves imports but does not redirect a moved function's internal global
lookups; repoint patches to the module where the reading function is defined after the move.

### 4. Protect behavior before implementation

For a behavior change or newly exposed contract, write the smallest failing test first and confirm it fails for
the intended reason. Cover variations discovered during classification, especially error text, ordering,
output formatting, cleanup, and side effects.

For a pure relocation or an already-landed consolidation, rely on existing behavioral tests when they cover the
contract. Do not invent a RED phase or freeze prose and implementation layout. Add a structural guard only when
the structure itself is a durable public or anti-drift invariant.

### 5. Extract and migrate incrementally

Create the canonical helper with explicit inputs and a result that preserves existing behavior. Migrate one
consumer at a time and run its focused tests before continuing. Keep local wrappers where they preserve names,
error messages, logging, or patch seams. Delete the duplicate only after every consumer and reference has moved.

After editing, re-derive imports, exports, allowlists, coverage configuration, docs, and test paths from the new
tree. Do not trust a plan's cleanup list to be exhaustive.

### 6. Verify the canonical source

Run focused tests, affected suites, the full repository gate, lint, and type checks required by the project.
Re-run the discovery queries and require results that falsify incomplete work: one canonical definition, no
forbidden duplicate bodies, no orphan references, and only documented intentional variants.

Report exact commands and results. A missing test path, empty selection, partial suite, or pending CI is not a
passing full verification.

### High-value examples

1. **Overlapping immutable collections:** extract a shared core and let each public collection compose its own
   extras. Preserve names and types; assert the core is included rather than flattening distinct contracts.
2. **Patched or public methods:** keep a one-line wrapper that delegates to the canonical free function. If the
   reading function moves modules, repoint patch sites to its new defining module and assert the mock fires.
3. **Repeated resource scaffolding:** extract acquisition and release into a context manager, but keep each
   caller's early-return decision and behavior-bearing `finally` side effects at the call site.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trust stale issue evidence | Used cited counts, paths, and “identical” claims without re-reading the tree | Prior changes had moved or differentiated the candidates | Re-grep and diff the current revision before scoping |
| Flatten near-duplicates | Merged shared and variant behavior into one value or function | Call-site-specific output, ordering, or semantics changed | Extract only the stable core and keep explicit extras |
| Delete compatibility seams | Removed a patched method, public export, or script entry point after extracting its body | Imports, mocks, or external callers still depended on the old name | Keep a thin wrapper or re-export until the compatibility contract can change |
| Patch the old module after moving the reader | Preserved an old re-export and assumed internal mocks still intercepted calls | Function globals resolve in the defining module, so the mock never fired | Repoint each patch to the post-move reader and assert it was called |
| Add the abstraction before a failing test | Copied behavior into the helper, then wrote a test and called it RED | The test passed immediately and proved no missing behavior | Observe a genuine failure first, or report a pure refactor as GREEN-first |
| Verify only the new helper | Ran focused tests without consumer, full-suite, or orphan-reference checks | Integration contracts and stale copies remained untested | Run consumer suites, repository gates, and self-falsifying searches |

## Results & Parameters

### Completion criteria

- Exactly one canonical implementation exists for the shared behavior.
- Intentional variants remain explicit and tested.
- Public names, patch seams, output, errors, cleanup, and side effects are preserved or deliberately changed.
- Focused and full repository-native checks pass with non-empty test selection.
- Searches find no forbidden duplicate bodies or orphan references.
- Verification claims identify the revision, commands, and actual result.

### Decision record

```yaml
candidates: <current paths or symbols>
classification: <exact | shared-core | shared-scaffold | intentional-variant>
canonical_home: <existing module or justified leaf module>
preserved_contracts: <exports, patches, output, errors, ordering, side effects>
focused_gate: <command>
full_gate: <command>
post_refactor_search: <command and expected count>
```

## Verified On

| Project | Context | Verification |
| ------- | ------- | ------------ |
| ProjectHephaestus | [Issue #739](https://github.com/HomericIntelligence/ProjectHephaestus/issues/739), private-helper extraction | verified-ci |
| ProjectHermes | [PR #652](https://github.com/HomericIntelligence/ProjectHermes/pull/652), current-state discovery before helper consolidation | verified-ci |
| ProjectHephaestus | [Issue #1437](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1437), repeated resource lifecycle extraction | verified-local |

## References

- [Version history and pre-compaction evidence](./dry-refactoring-workflow.history)
- [Session notes and case index](./dry-refactoring-workflow.notes.md)
- [Verify issue premises before planning](./planning-verify-issue-premise-before-implementing.md)
- [Cross-repository migration inventory](./architecture-cross-repo-migration-verify-issue-inventory.md)
