---
name: python-module-decomposition-and-refactor-patterns
description: >-
  Use when decomposing oversized Python modules, classes, or functions; preserving
  imports, patch targets, state ownership, and typed signatures while extracting
  collaborators; breaking circular imports; planning line and complexity budgets;
  or auditing a refactor whose estimates, exception contracts, shared state, or
  test wiring may be stale.
category: architecture
date: 2026-07-26
version: "2.0.0"
user-invocable: false
verification: unverified
license: BSD-3-Clause
history: python-module-decomposition-and-refactor-patterns.history
tags:
  - python
  - refactoring
  - module-decomposition
  - collaborator-extraction
  - circular-imports
  - dependency-inversion
  - patch-routing
  - shared-state
  - signature-verification
  - complexity
---

# Python Module Decomposition and Refactor Patterns

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2026-07-26 |
| Objective | Split Python hotspots into focused units without changing their public, state, import, type, or test contracts |
| Outcome | A measure-first workflow covering functions, collaborators, compatibility façades, import cycles, patch routing, shared state, and verification |
| Evidence | Mixed: several patterns are CI- or locally verified; planning-only and salvaged cases remain unverified |

This is a contract-preservation exercise, not a line-moving exercise. The safe unit of work is one
cohesive slice whose callers, state, imports, exceptions, and test seams have been mapped. Detailed
case evidence is in the [notes](./python-module-decomposition-and-refactor-patterns.notes.md); the
complete superseded v1.16.0 is in the
[history](./python-module-decomposition-and-refactor-patterns.history).

## When to Use

Use this skill when one or more of these conditions hold:

- A module is over roughly 800–1000 lines, a class has several cohesive method clusters, or a
  function exceeds the repository's size or cyclomatic-complexity threshold.
- An extraction must preserve imports, console entry points, `patch.object` targets, module-local
  mocks, constants, or an existing façade.
- Startup fails with a partially initialized module, an eager `__init__.py` re-export, or a
  function-local import is masking a sibling cycle.
- A collaborator will own or mutate host state, especially caches, dictionaries, paths, flags, or
  values that tests reassign after construction.
- A plan proposes delegation stubs, tuple-returning helpers, provider dispatch, or exception
  wrapping without having read the exact signatures and call sites.
- A scanner must be narrowed from a repository-wide deny-list to a subdirectory allow-list, or a
  context-manager refactor left stale manual lifecycle accounting in a caller.
- A legacy fallback appears unused, a rewrite estimate is based on stale line numbers, or parallel
  implementation phases need a final compatibility and dead-code pass.

Do not use this workflow merely because a file is long. If its responsibilities are inseparable,
first improve local naming and tests. Do not add a Strategy or Protocol for a stable two-branch
boolean dispatch unless additional providers or substitution are real requirements.

## Verified Workflow

### Quick Reference

```bash
# Measure current physical spans and complexity; never trust issue line numbers.
wc -l <target.py>
rg -n '^(class |def |async def )|# noqa: C901' <target.py>

# Map public imports, calls, patches, state, and deferred imports.
rg -n 'from <module> import|import <module>|patch\(|patch\.object' <package> tests
rg -n 'self\.[A-Za-z_][A-Za-z0-9_]*' <target.py>
rg -n '^\s+(from|import) ' <target.py>

# Verify exact definitions before writing a stub or plan.
sed -n '<start>,<end>p' <target.py>
rg -n '<symbol>\(' <package> tests

# Verify the import graph and the narrowest relevant behavior first.
python -c 'import <package>; import <package>.<new_module>'
pytest -q <focused-tests>
ruff check <changed-python>
mypy <host.py> <collaborator.py>
pytest -q
```

Substitute the repository's own task runner and thresholds. Run the actual required gate after the
focused loop; a formatter or linter may mutate files on its first pass, so only a clean second pass
is final evidence.

### 1. Freeze the Current Contract

Before editing:

1. Read the complete target, its package initializer, entry-point declaration, direct callers,
   sibling imports, and relevant tests.
2. Record physical line spans with AST-aware or definition-aware measurement. Count decorators and
   docstrings if the repository's budget counts physical lines.
3. Inventory every moved symbol's import sites and patch strings. A patch follows the name lookup
   site, not the symbol's original definition.
4. For every candidate method, record exact positional and keyword-only parameters, defaults,
   return annotation, exceptions, and post-call values used by the parent.
5. Record all `self` fields read or written, including shared mutable objects and fields reassigned
   by fixtures after `__init__`.
6. Run the existing focused tests unchanged. They are characterization tests for compatibility.

An issue's line count, signature, or claimed root cause is a hypothesis. Read the current substrate
and revise the plan when evidence differs.

### 2. Choose the Smallest Cohesive Boundary

Prefer boundaries in this order:

1. A private helper for one pipeline step or a stable two-branch dispatch.
2. A leaf module for independent symbols or shutdown/lifecycle code.
3. A collaborator for a method cluster with one responsibility and clear state ownership.
4. A compatibility façade over several acyclic collaborators when callers cannot migrate at once.

Pick the first class slice by cohesion and low coupling, not by raw size or the scariest `C901`
method. Use the `self.<attribute>` inventory to find the cluster touching the fewest shared fields.
Keep methods used by multiple collaborator groups on the host unless a genuinely shared abstraction
is justified. A one-method collaborator is acceptable when it establishes a clean seam; a new
abstraction with no present consumer is not.

For a function extraction:

- Treat a loop body over roughly 40 lines as its own candidate.
- List every captured name as a parameter or an owned dependency.
- If the helper absorbs the only data-fetch call, return the fetched value needed downstream.
- Enumerate every value read after the helper call; tuple contracts must not drop flags used only
  on rare branches.
- Recompute the parent span arithmetically, including docstrings and delegation overhead.

### 3. Keep the Import Graph Directional

New leaf modules must not import their parent. Move neutral types/constants to a lower-level module,
or inject a narrow callable. Remove eager `__init__.py` re-exports when they make package import
execute CLI modules that import back into the package. If compatibility requires a public import,
re-export explicitly from the original façade after proving the resulting graph is acyclic.

For a family of modules, enforce:

- façade → collaborator edges only;
- no collaborator → façade back-edge;
- no sibling edge unless the dependency belongs in a lower-level shared module;
- `from __future__ import annotations` before all other imports when runtime annotation evaluation
  would otherwise create a cycle or PEP 604 types need deferred evaluation.

If a utility is already imported from the façade by another sibling, moving it into a collaborator
can create a cycle. Keep it at the stable layer or extract it to a true leaf; do not hide the cycle
with more function-local imports.

### 4. Preserve Compatibility and Patch Routing

Keep the original public symbol as a thin wrapper or re-export while callers migrate. For CLI
extraction, the original `main()` should delegate to the new implementation so tests patching names
in the original module still intercept them. When implicitly imported symbols are part of existing
tests, preserve them as explicit re-exports.

Thin host methods preserve `patch.object(host, "_method")`. When injecting a host method into a
collaborator, pass a lambda so lookup occurs at call time:

```python
self.worker = Worker(
    head_advanced=lambda before: self._head_advanced(before),
    state_dir=lambda: self.state_dir,
)
```

A bare bound method captures the pre-patch object, and a direct path value becomes stale when tests
or runtime code reassign the host field. Patch every module's local imported name separately after
a call chain is split. For a symbol patched many times across several destination modules, bucket
patches by test-class boundaries and trace delegation first; a patch already aimed at a downstream
module may not need to move.

### 5. Make State Ownership Explicit

Each mutable field needs one owner and a deliberate synchronization contract:

- Move the field with the responsible collaborator when no outside code uses it.
- Return a replacement and assign it in the host when the host remains authoritative.
- Share one mutable object when identity matters; update with `.clear()` and `.update()` instead of
  rebinding it.
- Use a zero-argument provider for host values that can change after collaborator construction.
- If compatibility attributes remain, propagate assignments explicitly and guard construction-time
  access; do not add a broad magical `__setattr__` unless the required compatibility surface is
  narrowly tested.

Update fixtures that seed a migrated cache through the old host attribute. Read method bodies, not
only names, before assigning ownership: a method named for arming, discovery, or fixing may call
across those boundaries.

### 6. Preserve Types, Parameters, Errors, and Authority

Copy signatures from source, including `/`, `*`, defaults, unions, and exact return types. A
keyword-only stub must also forward with `name=value`. AST checks for symbol presence do not catch a
fabricated parameter or incorrect return annotation, so type-check both the host and collaborators.
Conceptual mnemonics—such as slot workers usually accepting `acquired_slot` while their internal
substeps do not—guide investigation but never replace source reading.

Before consolidating provider branches, inspect the real return object and raised exceptions.
Normalize heterogeneous results only at a boundary that preserves information callers use. If the
wrapper absorbs `CalledProcessError`, every caller must check the returned `returncode`; document
which exceptions, such as `TimeoutExpired`, still propagate. Count all nested subprocess calls when
constructing mock `side_effect` lists.

For security-sensitive mutations, separate mechanical capability from approval authority. Keep one
exact mutation call site, prove authorization immediately before it, perform a fresh read-back, and
fail closed if state changes between proof and mutation. A façade should not broaden authority while
moving code.

### 7. Handle Adjacent Refactor Risks

- Replace repository-wide deny-lists with a positive `Path.is_relative_to(<root>)` allow-list when
  the scanner's contract is one subtree.
- After adopting a lifecycle context manager, search every caller for stale manual increment,
  decrement, acquire, or release logic.
- Before deleting a reference/fallback file, prove zero runtime imports, entry points, shell calls,
  tests that exercise it as production, and documentation references; delete stale back-references
  in the same change.
- When adding a module to an intentionally omitted package, update every coverage and smoke-test
  allowlist atomically and before creating the new module. Discover actual guard paths first.
- After parallel phases, remove duplicate helpers, temporary adapters, stale suppressions, and dead
  exports only after the combined suite characterizes the integrated behavior.

### 8. Verify in Layers

1. Import the package and each new module in a fresh interpreter.
2. Run unchanged characterization tests, then focused tests for the new boundary and negative paths.
3. Search for stale import paths, patch targets, moved attribute access, constants, deferred imports,
   old module names, and `# noqa: C901` annotations.
4. Type-check the façade and every collaborator; lint and format all changed files twice if hooks
   autofix.
5. Run structural guards for line budgets, import acyclicity, coverage allowlists, entry points, and
   privileged call-site count where applicable.
6. Run the full suite and repository-required checks. Report local, CI, and proposed-only evidence
   separately.

## Representative Patterns

### Compatibility Façade with a Typed Collaborator

```python
from collections.abc import Callable
from pathlib import Path

class Discovery:
    def __init__(self, state_dir: Callable[[], Path]) -> None:
        self._state_dir = state_dir

    def discover(self, *, limit: int) -> dict[str, str]:
        return _scan(self._state_dir(), limit=limit)

class Driver:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self._discovery = Discovery(lambda: self.state_dir)

    def _discover(self, *, limit: int) -> dict[str, str]:
        return self._discovery.discover(limit=limit)
```

### Pipeline Step with an Explicit Result Contract

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ReviewStep:
    verdict: str
    posted_ids: tuple[int, ...]
    reopened: bool
    should_stop: bool

def _process_review_iteration(*, review: str, prior_ids: set[int]) -> ReviewStep:
    """Perform one step; callers retain orchestration and loop ownership."""
    ...
```

### Leaf Extraction to Break a Cycle

```python
# shutdown.py imports neither runner.py nor package.__init__.
def request_shutdown(signum: int) -> None:
    ...

# runner.py imports the leaf directly.
from .shutdown import request_shutdown
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Move code first | Extracted methods before mapping callers, patches, state, and signatures | Tests patched stale lookup paths; caches and return contracts diverged | Freeze all observable contracts before editing |
| Bare bound-method injection | Passed `self._method` to a collaborator | Later `patch.object` replaced the host attribute but not the captured method | Inject `lambda: self._method(...)` when lookup must remain dynamic |
| State copied at construction | Passed `self.state_dir` or rebound a shared dict | Fixture reassignment and object identity no longer reached the collaborator | Use a provider or mutate the shared object in place |
| Signature by inference | Wrote stubs from method names or memory | Keyword-only parameters, real parameters, and return unions were fabricated or lost | Read every full `def` line and type-check host plus collaborators |
| Patch migration by range grep | Sampled a few patch sites and changed them by destination | Multi-class tests and existing downstream patches were misattributed | Bucket all sites by test class and trace lookup chains |
| Parent imports from collaborator | New module imported utilities from the façade | Created or hid a circular import | Keep dependencies in leaves and enforce a directional graph |
| Catch-all compatibility | Wrapped extraction in broad `except Exception` | Masked exhausted mocks and changed documented error behavior | Preserve narrow exception contracts and test negative paths |
| Size-only first slice | Chose the largest or highest-complexity method cluster | Maximized coupling and review risk | Choose the most cohesive, least state-coupled slice first |
| Trust issue estimates | Planned from stale LOC and symbol locations | Budgets and migration tables were wrong before implementation | Measure the current substrate and cite immutable evidence |
| Append-only shim | Added a delegate without replacing the old body | Duplicate definitions caused `F811` or left dead logic active | Replace the body and keep exactly one compatibility symbol |

## Results & Parameters

Use repository-specific limits, but make them explicit and machine-checkable:

| Parameter | Recommended starting point | Decision rule |
| --------- | -------------------------- | ------------- |
| Module review threshold | 800–1000 physical lines | Inspect for cohesive clusters; not an automatic extraction |
| Function review threshold | Repository limit, often 80–100 lines | Count decorators/docstrings according to the actual guard |
| Complexity threshold | Repository limit, commonly CC > 15 | Remove suppression only after the measured value passes |
| First PR | One cohesive slice | Prefer a single-state cluster; defer high-coupling C901 carriers |
| Compatibility | Thin façade/delegation wrapper | Retain until callers and patch sites are migrated |
| Import rule | Parent-to-leaf, no back-edge | Verify with fresh imports and an import-graph guard |
| Verification | Focused tests → types/lint → full gate | A local pass does not become CI-verified evidence |

Successful historical outcomes include module reductions of 1221→837, 1527→1105, 1488→142,
3338→2404, and 2404→1410 lines. Those measurements demonstrate the patterns, not universal size
targets. Planning-only façade budgets and salvaged closed-PR findings remain unverified until
implemented and run through their owning repository's gate.

## Verified On

| Project | Evidence | Status |
| ------- | -------- | ------ |
| ProjectScylla | PRs #1145, #1230, #1311, #1440, #1444–#1457, #1850 | Merged/CI evidence summarized in notes |
| ProjectHephaestus | PRs #308, #674, #714, #745, #1292, #1320 | Mixed verified-local and verified-ci; see notes |
| ProjectHermes | PR #522 context-manager counter repair | Verified by project tests |
| ProjectOdyssey | PR #5457 substrate-read estimate and implementation | CI green |
| ProjectHephaestus | Issues #1179, #1180, #1196, #1289 and closed PRs #2396, #2400, #2418 | Planning, local, partial, or unverified as labeled in notes |
| HomericIntelligence ecosystem | Five-hotspot façade/authority design | Unverified; reviewed design only |

See the [case index](./python-module-decomposition-and-refactor-patterns.notes.md#case-index) for
per-case provenance and verification boundaries.
