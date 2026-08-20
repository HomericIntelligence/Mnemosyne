---
name: refactor-extraction-plan-unverified-assumptions
description: "Review plans that extract a function cluster into a sibling module while re-exporting old paths. Use to challenge patch-path claims, line anchors, frozen invariants, cycle/import assumptions, unmerged dependency APIs, and promoted-helper verification."
category: architecture
date: 2026-07-04
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: unverified
history: refactor-extraction-plan-unverified-assumptions.history
tags:
  - refactoring
  - extraction
  - re-export
  - mock-patch-path
  - unmerged-dependency
  - circular-import
  - planning
  - verification
---

# Refactor Extraction Plan: Unverified Assumptions

## Overview

A verbatim cluster move can preserve import compatibility while silently breaking runtime lookup,
mock patch seams, import topology, frozen inventory checks, or test applicability. Convert every
plan claim into a repository query or execution probe, and distinguish landed facts from APIs
borrowed from unmerged dependencies or epic prose.

This is planning guidance only. The source issue #1360 and #1814 plans were revised but not
implemented, so `verification` remains `unverified`. Case evidence is indexed in
[refactor-extraction-plan-unverified-assumptions.notes.md](refactor-extraction-plan-unverified-assumptions.notes.md),
and the complete prior version is in
[refactor-extraction-plan-unverified-assumptions.history](refactor-extraction-plan-unverified-assumptions.history).

## When to Use

- Moving a coherent private-function cluster from a large module into a sibling module.
- Preserving the old path with explicit `name as name` re-exports.
- Claiming existing `patch("old.module._fn")` tests will keep intercepting calls.
- Citing line numbers for later steps after an earlier large deletion or insertion.
- Updating a frozen count, allowlist, coverage inventory, or magic-number invariant.
- Claiming no circular import or unused import based only on reading.
- Planning against a dependency issue whose types, constructors, routes, or fakes have not landed.
- Promoting an instance helper for reuse and deciding whether it should be pure.
- Citing boundary or parity tests as evidence for a symbol they may not exercise.

## Verified Workflow

The heading satisfies the corpus schema; the workflow itself is a proposed review procedure, not
an executed implementation.

### 1. Bind the plan to stable symbols

Record the base SHA. Replace sequential line ranges with function/class names, headings, or exact
configuration keys. After each structural edit, rediscover later anchors from the current tree.

```bash
git rev-parse HEAD
rg -n '^def (_one|_two)|^class Target|FROZEN_COUNT' src tests
```

Line numbers are useful review coordinates at one commit, not durable edit instructions.

### 2. Inventory every consumer and patch seam

Search the whole repository for definitions, imports, qualified calls, from-import bindings,
patches, monkeypatches, and string references:

```bash
rg -n '(_one|_two)|old\.module|patch\(|monkeypatch' .
```

An old-module re-export preserves callers that perform lookup through `old.module` at call time. It
does not redirect a name already bound by `from old.module import _one`, and it does not make a
canonical implementation call look up the shim's attribute.

Classify each caller:

| Call context | Patch target after move |
| --- | --- |
| Code still calls through the old module namespace | Old shim path can remain valid |
| Canonical moved code calls its sibling directly | Patch canonical module path |
| Another module imported the symbol by name | Patch where that consumer bound the name |

### 3. Inspect frozen invariants rather than incrementing blindly

Find every count, list, exclusion, and explanatory comment. Read the assertion: a literal length,
set equality, membership rule, and generated inventory require different updates. Recompute from
the authoritative source and update all coupled consumers in one change.

### 4. Prove import and lint claims by execution

```bash
python -c 'import package.old_module; import package.new_module'
python -c 'from package.old_module import _one; from package.new_module import _one as canonical; assert _one is canonical'
ruff check path/to/old_module.py path/to/new_module.py
```

Inspect both directions of the proposed import graph. Let the interpreter and linter determine
cycles and unused imports; comments are not evidence.

### 5. Gate unmerged dependencies with a compatibility probe

List every assumed symbol with its source issue: base classes, result types, route constants,
budget keys, context methods, constructors, and test fakes. Make implementation step one read the
landed modules and pin their exact signatures before writing extraction code.

```bash
rg -n 'class (WorkItem|StageOutcome|AgentJob|Stage)|ROUTES|def (advance|retry|fail_back)' src
rg -n 'class (FakeGitHub|FakeWorkerPool)' tests
```

If a symbol is absent or differs, revise the plan. Do not implement an adapter around a fictional
interface merely to preserve the original prose.

### 6. Prefer a pure promoted helper

A shared policy helper should compute a value; callers retain I/O, logging, and durable writes:

```python
def plan_verdict(*, is_go: bool) -> tuple[str, list[str]]:
    target = "state:plan-go" if is_go else "state:plan-no-go"
    siblings = [label for label in STATE_LABELS if label != target]
    return target, siblings
```

Avoid passing executor callables into a shared vocabulary module. That expands dependencies and
creates two calling conventions. Preserve observable ordering—for example, durable mutation before
return—in the caller that owns the effect.

### 7. Verify the verification command

Open each cited test and prove it exercises the moved or promoted symbol. A boundary test is
applicable only if the changed module crosses that boundary. A shim-parity test for other symbols
can stay green while this extraction is broken.

When legacy tests fully mock the old method, they prove patchability, not its internal log text or
call order. Add focused behavior tests for the new pure helper and canonical implementation path.

### 8. Execute in reversible slices

Move one coherent cluster, add the explicit shim, retarget internal callers, repair patch seams,
then run focused and full checks. When scenario rows must exist for both legacy and new systems,
say `copy then adapt`; ambiguous “move/migrate” instructions contradict a legacy-stays-green rule.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Assume re-export preserves every patch | Imported-into and canonical lookups bypass the shim | Patch where the caller resolves the symbol |
| 2 | Use original line numbers throughout sequential edits | Earlier edits shift later targets | Use stable anchors and rediscover after each step |
| 3 | Increment a frozen count from a comment | Assertion may enforce a different invariant | Read and recompute the executable source |
| 4 | Assert no cycle or unused import by inspection | Indirect edges and re-exports are easy to miss | Import and lint the result |
| 5 | Present epic-prose APIs as landed facts | Dependency may ship different names or shapes | Label assumptions and run a post-merge compatibility probe |
| 6 | Assume sibling test fakes exist | Plan compounds interface and fixture assumptions | Search and create explicit local fakes if absent |
| 7 | Promote an impure helper taking executors | Shared policy module gains surprising dependencies | Return data; keep effects in callers |
| 8 | Cite a related boundary/parity test | It may not import or exercise the changed symbol | Trace the test to the exact symbol and behavior |

## Results & Parameters

- Bind every plan to an immutable base SHA.
- Search the whole repository, not only the source file and its nearest test.
- Preserve explicit `name as name` shims where backward compatibility is required.
- Require identity smoke tests for every re-exported symbol.
- Inventory every assumed dependency API and fake before implementation.
- Keep promoted policy helpers pure unless effect ownership is itself the shared contract.
- Run focused tests, import smoke tests, Ruff, type checking, and the full affected suite.

## Evidence Boundary

Issue #1360 and the issue #1814 NOGO/revision cycle produced review findings only. Some repository
reads confirmed current symbols and test behavior, but no extraction or helper promotion was
implemented or validated in CI. Do not upgrade this skill beyond `unverified` from those reads.
