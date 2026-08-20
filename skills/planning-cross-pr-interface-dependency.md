---
name: planning-cross-pr-interface-dependency
description: "Plan a capstone integration issue whose sibling interfaces are still unmerged. Use when new code depends on symbols described only in issue bodies, must preserve legacy dispatch, changes blocking or CLI semantics, or extracts from a coverage-omitted module. Separate verified facts from assumed contracts and make merged-base interface pinning the first implementation gate."
category: architecture
date: 2026-07-04
version: "2.0.0"
license: BSD-3-Clause
history: planning-cross-pr-interface-dependency.history
user-invocable: false
verification: unverified
tags: [planning, capstone, integration, serialized-epic, unmerged-siblings, interface-gate]
---

# Planning Cross-PR Interface Dependencies

## Overview

A capstone plan can coordinate against sibling issue contracts, but it cannot present unmerged
symbols as repository facts. Separate what was read from the current tree from what was transcribed
from issue bodies, and convert every assumed interface into a merged-base pinning gate before code.

The skill remains `unverified`: its source is a reviewed plan, not an implemented capstone. Detailed
review findings are indexed in
[`planning-cross-pr-interface-dependency.notes.md`](planning-cross-pr-interface-dependency.notes.md),
and the complete prior source is archived in
[`planning-cross-pr-interface-dependency.history`](planning-cross-pr-interface-dependency.history).

## When to Use

- A terminal/integration issue fans in several still-open sibling dependencies.
- Coordinators, queues, stages, routes, configs, or test fakes exist only in issue prose.
- A caller mentions a symbol but its real defining module has not been opened.
- A helper may move out of a coverage-omitted module with a frozen omit justification.
- New dispatch must preserve a legacy path or a blocking operation becomes non-blocking.
- A CLI flag’s precedence or meaning changes as part of integration.

## Verified Workflow

### 1. Inventory the dependency graph

Read the epic and every sibling issue/PR. Confirm each live merge state and record the declared
interface: symbol name, module, signature, fields, return/disposition, consumer, and source URL.
Issue-body text is the only available contract until code lands; label it assumed.

```bash
gh issue view <issue> --repo <owner>/<repo>
gh pr list --repo <owner>/<repo> --state all --search '<issue>'
```

Add a dependency note that the capstone branch is cut from a base containing the last sibling merge.
If the dependency sequence is not fully merged, implementation is blocked even when the plan is
complete.

### 2. Split verified facts from assumptions

Maintain two explicit tables:

```text
VERIFIED: fact | current file:line | command/read evidence | design consequence
ASSUMED: interface | issue/PR source | consumers | post-merge confirmation command
```

Only facts read from current source are verified. Grep every existing symbol to its definition; a
caller does not establish module ownership. Keep sibling signatures, fake shapes, state transitions,
and tick ordering assumed until their merged implementations can be read.

### 3. Make merged-base pinning Step 1

Before any integration code:

```bash
git fetch origin
git rebase origin/main
rg -n '<symbol-one>|<symbol-two>|<symbol-three>' <expected-package>
```

Read each definition and update imports, constructors, return types, route tables, tests, and the
plan if names or shapes drifted. Do not write adapters that preserve a stale issue-body guess. Record
the exact merged base used to discharge assumptions.

### 4. Ground designs in verified facts

Every design decision needs a current-tree premise. Examples of valid chains include:

- an existing helper sleeps the only coordinator thread → new budget gating is a non-blocking
  predicate;
- dispatch at the top of `main()` → the legacy runner path remains untouched;
- an existing `store_true` default is false → flag presence can take precedence over environment;
- a new module is absent from the coverage omit list → leave it included rather than adding an
  exemption.

Document semantic changes in CLI help, module documentation, and the mapping site. “No edit to the
omit list” is not proof; positively run the frozen-membership test and search the config.

### 5. Specify cross-sibling handoffs completely

For every disposition/state, map producer output to a concrete next action and owning stage. Import
sibling types; do not redefine near-copies in the capstone. Show concrete constructor calls for
downstream jobs/messages, preserve distinct counters/state fields with their increment/decrement
sites, and order imported types/stages before routing logic.

Every introduced predicate needs both branches wired. Every acceptance-criteria mechanism must have
zero remaining design choices: function, caller, state mutation, error route, and named tests.
Avoid fields whose only consumer is a future issue.

### 6. Protect shared entry points and extractions

Place the new dispatch before shared side-effecting calls so the new path does not clone, mutate, or
sleep twice. Add a negative assertion that the legacy/shared side effect is not invoked on the new
path.

Before extracting from a coverage-omitted module, read the omit-justification test. If moving the
helper would invalidate its anchor, plan either a coordinated justification update backed by actual
coverage or an inline-copy fallback; do not strand a frozen omit member.

### 7. Make evidence delivery executable

Each “evidence in PR” criterion needs a command, output path, and attachment/body step. Absence of a
change is not verification. Name focused tests for legacy byte-for-byte behavior, each handoff,
state mutation, both predicate branches, flag precedence, and coverage membership. Mark the plan and
all sibling contracts unverified until merged-base implementation and CI complete.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Issue-as-schema | Presented sibling prose as existing API | Symbols were not on disk | Label assumed and pin after merge |
| Caller ownership | Inferred module from a use site | Import home was wrong | Grep the definition |
| Late interface check | Began code before pinning names | Drift spread through integration | Pin merged interfaces as Step 1 |
| Double mutation | Dispatched after shared side effect | New path repeated clone/mutation | Branch before shared side effects |
| Orphan predicate | Added guard without both actions | One state had no transition | Wire both branches concretely |
| Collapsed state | Derived distinct field from another | Lost protocol semantics | Preserve each declared field and mutations |
| Hand-wavy mechanism | Named convergence without algorithm | Implementer retained design decisions | Specify callable, state, errors, tests |
| Negative coverage proof | Said omit list was untouched | Did not prove new module coverage | Run positive config and test assertions |
| Missing evidence step | Promised PR evidence only | No artifact was captured | Name command, output, attachment |
| False cycle guard | Used local import preemptively | No cycle was demonstrated | Prefer module import until cycle exists |

## Results & Parameters

```text
epic/capstone and ordered sibling issue/PR URLs
declared interface matrix and current merge states
verified-fact table with file:line evidence
assumed-contract table with merged-base grep commands
last dependency merge and capstone base SHA
disposition-to-action handoff table
state fields, mutation sites, concrete constructors, error routes
legacy-path, side-effect, flag, coverage, and handoff tests
evidence commands, artifact paths, and PR attachment steps
```

## Verified On

- ProjectHephaestus capstone plan and NOGO-to-revision cycle on 2026-07-04.
- No implementation or CI run was completed; verification remains `unverified`.
