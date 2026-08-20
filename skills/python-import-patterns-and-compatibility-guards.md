---
name: python-import-patterns-and-compatibility-guards
description: >-
  Preserve Python importability and public API contracts across cycles, lazy exports,
  interpreter versions, and operating systems. Use when deferring an import, enforcing an
  acyclic runtime graph, widening a PEP 562 surface, or aligning exports with compatibility
  documentation and boundary tests.
category: architecture
date: 2026-08-08
version: "3.0.0"
user-invocable: false
verification: unverified
license: BSD-3-Clause
history: python-import-patterns-and-compatibility-guards.history
tags: [import-strategy, circular-dependency, lazy-loading, sdk-surface, version-guard, cross-platform, pep-562, compatibility, runtime-import-graph, ast]
---

# Python Import Patterns and Compatibility Guards

**Supporting cases:** [notes](./python-import-patterns-and-compatibility-guards.notes.md)

**Superseded content:** [history](./python-import-patterns-and-compatibility-guards.history)

## Overview

Import fixes have different strengths. A function-local import changes initialization order;
it does not remove the runtime dependency. A lazy export preserves a public facade without an
eager import. A version or OS guard preserves importability on a declared matrix. Structural
acyclicity requires a complete runtime dependency graph and a design change at the cycle.

The top-level verification remains `unverified` because the complete AST graph workflow and
neutral-leaf extraction are reviewed planning guidance. Individual compatibility, export, and
deprecation cases retain their `verified-local` or `verified-ci` status in the notes/history.

## When to Use

- Python fails during partial initialization, or a local import is proposed as a cycle fix.
- A package facade exposes symbols lazily through `__getattr__`, `_LAZY_EXPORTS`, or `__all__`.
- A sibling PR makes a strict public-surface test stale or causes an add/add export conflict.
- The lowest interpreter lacks a newer stdlib module such as `tomllib`.
- Windows lacks a POSIX-only module, or `zoneinfo` lacks timezone data.
- A public symbol is added and package exports, `dir()`, patch identity, and API docs must agree.
- An architecture requirement says the runtime module graph must be acyclic, including hidden
  function-local and lazy-map edges.

## Verified Workflow

1. **Identify the required contract.** Decide whether you need only import-time success,
   stable public identity, cross-matrix compatibility, or structural acyclicity.
2. **Inventory every surface.** Inspect module imports at all AST depths, package `__all__`,
   `TYPE_CHECKING`, `__getattr__`, lazy maps, facade re-exports, compatibility tables, patch
   paths, and the existing surface tests.
3. **Choose the narrow mechanism.** Use a local import for initialization deferral; a guarded
   import for platform/version availability; lazy resolution for optional public imports; or
   a neutral leaf/dependency inversion when the graph edge itself must disappear.
4. **Preserve identity and signatures.** A facade export should be the same object as the
   defining module's export. Keep adapter lookup sites patchable and avoid compatibility
   wrappers that subtly change defaults, annotations, or exception behavior.
5. **Update all declared surfaces together.** Align `__all__`, lazy maps, `TYPE_CHECKING`,
   `__dir__`, public documentation, and boundary tests in one change.
6. **Run matrix-appropriate checks.** Import on the minimum Python and Windows/POSIX targets,
   then run the whole live-tree validation module when its tests scan real files. A single
   isolated test can be a false negative if fixtures or module ordering populate state.
7. **For graph enforcement, test the detector.** Include synthetic cycles through top-level,
   local, `from package import child`, annotated/assigned lazy maps, and negated
   `TYPE_CHECKING` forms; include acyclic and type-only controls.

### Compatibility patterns

```python
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

try:
    import fcntl
except ModuleNotFoundError:  # POSIX-only
    fcntl = None  # type: ignore[assignment]
```

Declare matching conditional dependencies, for example `tomli; python_version < '3.11'`
and `tzdata; platform_system == 'Windows'`. Catch only the expected import error; do not hide
arbitrary exceptions raised during module initialization.

### Lazy public surfaces

Keep these sets synchronized:

- `TYPE_CHECKING` imports for static tools without eager runtime imports.
- `__all__` as the declared public surface.
- A name-to-module lazy map used by module-level `__getattr__`.
- Any eager-preload exclusion list used to protect phase entry points.
- `__dir__`, returning `sorted(set(globals()) | set(__all__) | set(lazy_map))`.
- Compatibility/API tables and their membership guards.

A deprecation warning at the PEP 562 boundary belongs in `__getattr__` and uses
`stacklevel=2`. Because the resolved name is commonly cached in module globals, a regression
test must remove that cached name before asserting a second access. Keep an existing call-time
warning if it covers a distinct direct-import path.

When a strict equality surface test fails after a sibling PR, prove the symbol landed on the
base branch before editing. If the production surface is legitimate, update or replace the
stale literal with the narrow intended invariant. Do not delete the peer export to satisfy an
old test.

### Runtime graph enforcement

Build the graph from package modules and record runtime edges from:

- `import` and `from ... import ...` at every AST depth;
- resolvable child modules in `from package import child`;
- assigned or annotated lazy-export maps;
- facade relationships intentionally normalized by policy.

Exclude imports proven type-only by positive `if TYPE_CHECKING:` branches and include runtime
imports in negated forms. Resolve relative imports against the importing module. Detect strongly
connected components with a deterministic algorithm such as Tarjan; report the full cycle and
edge origins.

Break a real cycle by extracting only shared low-level behavior into a dependency-neutral leaf,
inverting the collaborator, or passing a true call-level argument. Preserve the original public
facade with explicit re-exports and identity tests. Clear `sys.modules` or isolate subprocesses
when comparing before/after import order so cached modules do not mask regressions.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Claim a function-local import removes a cycle | Claim a function-local import removes a cycle | The runtime edge still exists | Describe it as deferral or redesign the seam |
| Guard only top-level AST imports | Guard only top-level AST imports | Local imports and lazy maps hide cycles | Traverse all depths and declared lazy edges |
| Catch broad `Exception` around an import | Catch broad `Exception` around an import | It masks defects inside the module | Catch the precise availability exception |
| Eagerly re-export a heavy or cyclic module | Eagerly re-export a heavy or cyclic module | Package import cost/cycles return | Use the established lazy facade and pin identity |
| Hardcode an exact `__all__` set | Hardcode an exact `__all__` set | Legitimate sibling exports create merge-skew failures | Assert the intended subset or a bidirectional documented contract |
| Guess an API-table “since” version from the latest tag | Guess an API-table “since” version from the latest tag | The symbol may belong to a different release cycle | Use same-cycle siblings or labeled git archaeology |
| Test a live-tree scanner in isolation | Test a live-tree scanner in isolation | Shared fixtures/import state can hide the defect | Run the full validation module or a fresh process |
| Implement `__dir__` from lazy names alone | Implement `__dir__` from lazy names alone | Custom `__dir__` replaces the default and hides globals | Union globals, `__all__`, and lazy names |

## Results & Parameters

| Parameter | Rule |
| --- | --- |
| Local import | Defers lookup only; graph edge remains |
| Version guard | Match the minimum supported interpreter and conditional dependency |
| OS guard | Catch the exact missing-module condition; test on the affected OS |
| Public export | Same object identity and signature through the facade |
| Lazy surface | Synchronize `TYPE_CHECKING`, `__all__`, lazy map, `__dir__`, docs, tests |
| `__dir__` | Sorted union of globals, declared exports, and lazy names |
| Graph scope | Runtime imports at every AST depth plus resolvable lazy edges |
| Type-only imports | Exclude only when control flow proves they do not run |
| Cycle report | Deterministic SCC members and edge origins |
| Verification | Full live-tree validation plus matrix/import-order coverage |

The result should import on every declared platform, preserve the public facade, and describe
honestly whether the structural graph is actually acyclic. Project-specific commands, PRs, and
verification boundaries are indexed in the notes.
