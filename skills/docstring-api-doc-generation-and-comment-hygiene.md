---
name: docstring-api-doc-generation-and-comment-hygiene
description: "Use when: (1) updating, fixing, or extending docstrings and API documentation in source files to match current implementation semantics — changed signatures, memory semantics, orphaned fragments, undocumented methods; (2) creating API reference documentation from docstrings for a public module interface; (3) generating docstrings for undocumented functions and classes; (4) auditing and cleaning up inline NOTE/TODO/FIXME/placeholder comments — normalization, removal of shipped-feature placeholders, magic-number extraction; (5) using a package's public __version__ attribute in demo/example scripts rather than hardcoded strings, so version references stay in sync with releases."
category: documentation
date: 2026-06-07
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: mixed
history: docstring-api-doc-generation-and-comment-hygiene.history
tags: [docstring, api-docs, comment-hygiene, note-cleanup, placeholder, copy-vs-view, module-docstring, error-handling-contract, version-management, mojo, python]
---

# Docstring, API Documentation, and Comment Hygiene

## Overview

Keep public documentation synchronized with executable behavior. This includes authoring missing
docstrings, generating API references from the public surface, correcting copy/view and error
contracts, maintaining catalogs, and removing misleading inline comments. Evidence is mixed: the
case index in [the notes](docstring-api-doc-generation-and-comment-hygiene.notes.md) distinguishes
CI-verified, locally verified, and historical-only material.

## When to Use

- Public or private functions/classes lack docstrings, a signature changed, or an example still
  names a removed parameter or helper.
- A module needs generated API reference pages based on its exported interface.
- Copy versus view behavior, ownership/refcount behavior, mutation, exceptions, or special failure
  return shapes are missing or contradicted across sibling methods.
- A module summary and function docstring disagree, or an `__init__` docstring has orphaned text,
  stale re-export guidance, or an undocumented trait/dunder method.
- A developer guide/catalog needs a module section, formula, limitations, or synchronized counts.
- `NOTE`, `TODO`, `FIXME`, placeholder, or magic-number comments may be obsolete or malformed.
- A demo prints a hard-coded package version instead of importing the public `__version__`.

Do not use this workflow to change runtime behavior while calling the change documentation-only.
If the implementation is wrong or the comment exposes a likely bug, open or link the defect and
keep the documentation honest about the current behavior.

## Verified Workflow

### Quick Reference

```bash
# Find public surface and undocumented definitions.
rg -n '^(class|def|fn|struct|trait) ' <package>
rg -n '^(from .* import|__all__|pub )' <package>/__init__* <package>

# Find drift and comment debt.
rg -n 'FAILS LOUDLY|FAILS WITH|CONTRACT|RAISES|NOTE:|TODO|FIXME|placeholder' <paths>
rg -n '^[[:space:]]*[a-z].*' <package>/**/__init__.*

# Generate or inspect references using tools already declared by the repository.
pdoc <package> --output-directory <docs/api>
sphinx-apidoc -o <docs/api> <package>

# Validate the changed surfaces.
python3 -m py_compile <changed-python-files>
python3 <demo-script>
pre-commit run --files <all-changed-files>
```

### 1. Bind documentation to the current implementation

Read the implementation, callers, tests, exports, and existing documentation before editing.
Record the exact signature, return type, mutation/ownership semantics, exceptions, failure return
shape, and supported version. Search for the actual symbol rather than trusting an issue's
pre-refactor name.

For each documented callable:

- begin with one imperative summary line;
- document every parameter and return value using the repository's existing style;
- describe exceptions or explicitly state a non-raising failure shape such as `(False, "")`;
- state copy/view behavior and aliasing/refcount consequences when they change caller choices;
- include a runnable snippet only when prose cannot make the contract clear.

Private Python helpers are not exempt from ruff D401. Prefer “Run”, “Return”, “Build”, or
“Validate” over “Helper to” or “Utility that”.

### 2. Audit cross-level consistency

After changing a function docstring, search the containing module's summary blocks (`CONTRACT`,
`RAISES`, `FAILS LOUDLY`, `NOTE`) and sibling methods. Update all levels atomically when they
describe the same behavior. A copy-returning slice and a view-returning `slice()` must say so in
both their individual docs and any memory-semantics table.

For package initializers, turn an inline re-export comment into a module-docstring `Note:` only
after verifying actual export behavior. Remove orphaned lowercase continuation fragments. Document
new trait or dunder methods in the owning type and public package surface.

### 3. Generate API reference from the public surface

1. Enumerate exports and exclude private/internal helpers unless the project deliberately exposes
   them.
2. Fill missing source docstrings first; generated pages reproduce source defects.
3. Use the repository's configured generator (`pdoc`, Sphinx, or equivalent), not an undeclared
   substitute.
4. Inspect navigation, links, signatures, code formatting, and omitted exports in rendered output.
5. Re-run generation from a clean tree when generated files are product artifacts. Do not commit
   generated pages when the repository builds them only in CI.

### 4. Maintain guides and test documentation atomically

Insert a new catalog module section before the established summary table, not after it. When a
catalog header contains module, implementation, documented, and missing counts, recompute and
update all related values together. Preserve formulas and thresholds that change test selection;
move case-specific arithmetic and inventories to notes.

For each test-file `NOTE`, classify it before rewriting:

- expected limitation: document precisely and include the relevant version;
- tracked limitation: retain the issue link and resolution condition;
- likely defect: open/link a defect rather than normalizing it into accepted behavior;
- obsolete placeholder: remove or replace it only after confirming implementation/tests exist.

Renaming a test or documented helper requires a repository-wide caller search, including manual
`main()` entry points and catalog references.

### 5. Normalize comments without erasing intent

Use the repository's canonical marker syntax. For Mojo limitations:

```mojo
# NOTE (Mojo v<version>): <current limitation>
# NOTE(#<issue>, Mojo v<version>): <limitation>. Implement when <condition>.
```

Keep an already-linked multi-line note linked once; do not append duplicate issue references.
Convert future work phrased as a note into a `TODO`, remove shipped-feature placeholders only after
verification, and extract repeated magic numbers into named constants. Plain runtime status output
is not a `NOTE` merely because it uses that word.

### 6. Keep demo versions dynamic

Import the package's public version attribute rather than copying a release string:

```python
from <package> import __version__

print(f"<package> {__version__}")
```

Confirm that `__version__` is backed by the project's canonical metadata (for example,
`importlib.metadata.version("<distribution>")`) and smoke-run the installed demo. Do not infer the
distribution name from the import package when they differ.

### 7. Validate at the right boundary

Run syntax/format/lint checks for every changed source and documentation file, then the narrow tests
that exercise documented behavior. For a docs-only change, verify no executable line changed.
Render generated docs when that is the consumer. On a host with GLIBC below 2.34, the Mojo
formatter may be unavailable; run the remaining hooks explicitly and report the skip:

```bash
SKIP=mojo-format pixi run pre-commit run --files <changed-mojo-and-doc-files>
```

Rely on the repository's container/CI gate for that formatter and never claim it passed locally.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trusting the issue symbol | Edited a name quoted by the ticket | The implementation had already been refactored | Search the current symbol and callers first |
| Function-only update | Fixed a callable docstring but not the module contract | Readers saw contradictory behavior at the top of the file | Audit module, function, sibling, and export docs together |
| “Helper to” opener | Used a descriptive noun phrase on a private helper | ruff D401 requires imperative mood there too | Start with an imperative verb |
| Normalizing a bug note | Reworded suspicious behavior as an expected limitation | Documentation hid an unresolved defect | Classify and link defects before cleanup |
| Partial catalog counts | Updated one summary statistic | The catalog became internally inconsistent | Recompute every dependent count atomically |
| Hard-coded demo version | Copied the current release string | The demo drifted at the next release | Import the public version attribute |
| Blind generation | Ran an API generator before auditing exports/docstrings | Generated pages amplified missing and stale contracts | Repair the source surface first |

## Results & Parameters

| Contract | Required disposition |
| --- | --- |
| Signature | Exact current parameters, defaults, and return type |
| Memory | Explicit copy/view, aliasing, mutation, and ownership behavior |
| Errors | Raised exceptions or precise non-raising failure shape |
| Public surface | Export inventory matched to generated reference |
| Comments | Current limitation, linked future work, tracked defect, or removal |
| Catalog updates | Placement, formula, and all dependent counts synchronized |
| Demo version | Public `__version__` backed by canonical package metadata |
| Verification | Syntax/lint plus behavior or rendered-doc consumer; gaps stated |

## Companions

- [Case index and detailed verification](docstring-api-doc-generation-and-comment-hygiene.notes.md)
- [Version history and superseded content](docstring-api-doc-generation-and-comment-hygiene.history)
