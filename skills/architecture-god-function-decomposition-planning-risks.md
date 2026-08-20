---
name: architecture-god-function-decomposition-planning-risks
description: "Use when planning extraction of oversized functions or classes from issue-cited paths and counts. Re-measure the AST on disk; prove subtraction arithmetic and call-site wiring; enumerate every control-flow sentinel; preserve patch.object(instance, '_method') seams with thin delegates; select an internal helper versus injected collaborator from sibling self-call coupling; and prevent circular imports by relocating shared helpers to a cycle-free leaf and re-exporting them. Planning guidance remains unverified until implementation and tests run."
category: architecture
date: 2026-06-30
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
history: architecture-god-function-decomposition-planning-risks.history
verification: unverified
tags: [architecture, python, refactoring, god-function, god-class, extraction, planning, sentinel, delegation, circular-import, test-seams]
---

# Architecture: God-Function Decomposition — Planning Risks

## Overview

An extraction plan is only as sound as its current source measurements, control-flow contract, and
call-site wiring. Issue line numbers drift; helper prose omits returns; class collaborators introduce
cycles; and deleting a method can break extensive `patch.object(instance, "_method")` test seams.

This skill intentionally remains `unverified`: it records planning and review lessons, not a shipped
decomposition. Implementers must re-read the target and run the resulting tests. Detailed case
measurements are indexed in
[the notes](./architecture-god-function-decomposition-planning-risks.notes.md), and the exact
superseded content is in
[history](./architecture-god-function-decomposition-planning-risks.history).

## When to Use

- An issue cites function/class line numbers, method sizes, or paths for decomposition.
- A proposed extraction claims the source will fall below a line cap.
- A loop contains break/continue/retry/abort semantics that must cross a helper boundary.
- A helper is described or defined but the replacement block does not call it.
- A plan names a test file or fixture without opening it.
- A class extraction would move methods patched directly on existing instances.
- A candidate collaborator calls many sibling `self._...` helpers or mutable fields.
- A moved method uses a module-level helper defined in the god module.
- A reviewer flags guessed signatures, return types, file locations, or arithmetic.

## Verified Workflow

The workflow is proposed and unverified. Treat every step as a planning gate that implementation and
tests must confirm.

### Quick Reference

```bash
# Re-locate and measure definitions from the current tree.
rg -n '^\s*(async )?def <name>|^class <Name>' <source-root>
python - <<'PY'
import ast
from pathlib import Path
p = Path('<file.py>')
t = ast.parse(p.read_text())
for n in ast.walk(t):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        print(n.name, n.lineno, n.end_lineno, n.end_lineno - n.lineno + 1)
PY

# Find real callers, patch seams, sibling calls, and shared-helper imports.
rg -n '<method>\(' <source-root> tests/
rg -n 'patch\.object\([^,]+, ["'"']_<method>["'"']' tests/
rg -o 'self\._[A-Za-z0-9_]+' <candidate-range> | sort -u
rg -n '<module_helper>' <source-root> tests/

# Confirm planned test paths and read their fixture conventions.
test -f tests/path/test_target.py
sed -n '1,120p' tests/path/test_target.py
```

### 1. Reconstruct the current target

Fetch the current base, locate the symbol by name, and use AST `lineno`/`end_lineno` rather than
issue-cited coordinates. Count the full syntactic span: decorators, multiline signature, docstring,
and body. A policy that checks AST span cannot be satisfied by counting executable statements only.

Record each target's current span, direct callers, awaited/callback use, mutable fields, sibling
helper calls, tests, patch seams, and feature guards. If the issue's target moved or already shrank,
re-scope before writing extraction steps.

### 2. Prove the line-budget arithmetic

For each extraction, show:

```text
old AST span
- moved span
+ delegate/call-site span
+ retained signature/docstring/decorators
= predicted new AST span
```

Use exact current spans. If one helper cannot meet the cap, name all helpers and assign nonoverlapping
responsibility. After implementation, re-run the same AST measurement; the arithmetic is a forecast,
not proof.

### 3. Make replacement wiring explicit

Every proposed helper must appear in the replacement block or a named call-site step. Specify
signature, return type, mutated state, exceptions, and ownership of side effects. Search all callers
before changing a signature; a private-looking method may be patched, registered, or called across
files.

Open the real test module before prescribing fixtures or stubs. If it does not exist, name the actual
test location and how a new file integrates with current conventions rather than inventing a path.

### 4. Preserve control flow with explicit sentinels

An extracted polling or retry loop cannot directly `break` or `continue` its caller. Define a closed
signal type (enum or discriminated result) for every state such as continue polling, retry outer
operation, complete successfully, or abort/fail. Show the caller mapping for every value. Avoid a
bare Boolean once more than two actions exist.

Specify edge inputs. An empty replies dictionary, exhausted iterator, timeout, cancellation, and
exception path may each change which sentinel returns. Tests must exercise all signals and prove
side-effect ordering, not merely the happy return value.

### 5. Preserve class seams with delegates

Before moving a method, search for `patch.object(instance, "_method")`, subclass overrides, bound
method capture, and direct private calls. Keep a thin method with the same name/signature on the
original class when that seam exists; delegate internally to the collaborator. Tests that patch the
instance should still intercept the call.

Choose an intra-class helper when the code remains tightly coupled to many sibling methods or
mutable fields. Choose an injected collaborator when responsibility is cohesive and dependencies can
be expressed as a small stable constructor/protocol. Count distinct sibling `self._...` calls; use the
count as evidence, not as an automatic threshold. A collaborator that merely receives the whole god
object usually moves text without reducing coupling.

### 6. Prevent circular imports

If moved code needs a module-level helper from the god module, do not import the god module back into
the collaborator. Move the helper to a cycle-free leaf that imports neither side. Import it from the
leaf in both modules and re-export from the old module when compatibility requires the old name:

```python
# cycle_free_leaf.py
def inspect_check(...): ...

# god_module.py
from .cycle_free_leaf import inspect_check as inspect_check

# collaborator.py
from .cycle_free_leaf import inspect_check
```

The explicit `as same_name` communicates intentional re-export to linters. Add an import smoke test
for both modules and an architectural assertion that the leaf does not import either parent.

### 7. Audit the plan before handoff

1. Re-run AST measurements and all cited file/line searches.
2. Match each helper definition to a concrete replacement call.
3. Enumerate all return/sentinel states and caller branches.
4. Verify every test path and existing fixture seam.
5. List patch/subclass/direct-call compatibility requirements.
6. Show dependency direction and any re-export.
7. Label unexecuted signatures, thresholds, and collaborator boundaries unverified.
8. Require targeted tests, full relevant suite, lint/type checks, and post-extraction AST counts.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trust issue line numbers | Planned from stale coordinates | Refactors changed path and span | Re-locate and AST-measure current source |
| Count only body lines | Ignored signature/docstring/decorators | The enforcing policy counted full AST span | Use the same metric as the gate |
| Define but do not wire | Added helper prose without replacement call | Plan could leave dead helper and unchanged function | Show each call site explicitly |
| Use one Boolean sentinel | Collapsed retry, continue, success, and abort | Caller semantics became ambiguous | Define a closed multi-state result |
| Invent test stubs | Named nonexistent files/fixtures | Plan could not be implemented mechanically | Open the real tests first |
| Delete moved class methods | Removed original private seam | Hundreds of `patch.object` sites could break | Retain thin compatible delegates |
| Extract every large method | Created collaborators still coupled to many siblings | Text moved without responsibility isolation | Decide from cohesion and sibling-call evidence |
| Back-import the god module | Collaborator imported its old module for a helper | Circular import at module initialization | Move helper to a leaf and re-export |
| Eyeball arithmetic | Claimed the result would meet a cap | Retained syntax and multiple helpers were omitted | Show subtraction and verify after implementation |

## Results & Parameters

| Decision | Required evidence |
| --- | --- |
| Current size | AST full span on the implementation base |
| Meets cap | Explicit subtraction plus post-change AST measurement |
| Helper is real | Signature, effects, return type, and named call site |
| Poll extraction | Closed sentinel set and caller mapping for every value |
| Test compatibility | Existing paths, fixtures, patch sites, subclass/direct callers |
| Internal helper | High mutable/sibling coupling retained intentionally |
| Collaborator | Cohesive responsibility with small explicit dependencies |
| Import direction | Cycle-free leaf; optional explicit same-name re-export |
| Verification | Remains unverified until targeted and relevant full tests run |

## Verified On

- Planning reviews through 2026-06-30 identified these risks, but no end-to-end decomposition is
  claimed here. Status remains `unverified`.
- Case sources and individual observations are indexed in
  [the notes](./architecture-god-function-decomposition-planning-risks.notes.md).

## Companions

- [Case notes](./architecture-god-function-decomposition-planning-risks.notes.md)
- [Version history and exact superseded snapshot](./architecture-god-function-decomposition-planning-risks.history)
