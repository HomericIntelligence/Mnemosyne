---
name: python-scaffolding-avoid-fabricated-behavior-stubs
description: "Keep Python package scaffolders structural and behavior-neutral. Use when: (1) a generator emits a same-name module with a placeholder function, (2) generated tests assert fabricated return values, (3) a mirrored test-layout policy requires a substantive test, or (4) changing generated artifacts must preserve validation, overwrite refusal, dry-run, JSON, and optional CLI behavior."
category: tooling
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [python, scaffolding, code-generation, package-layout, import-contract, structural-testing, cli, json]
---

# Keep Python Scaffolds Free of Fabricated Behavior

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Reduce a Python subpackage scaffolder to the files required for an importable package and a durable structural test, without inventing application behavior. |
| **Outcome** | Proposed correction: generate the package and test `__init__.py` files plus an import-contract test; omit the same-name implementation module and `placeholder()` return-value test. Preserve the generator's existing operational controls. |
| **Verification** | **unverified** — the repository structure and relevant validation contract were inspected during planning, but the template change and its tests were not executed in this session. |

## When to Use

- A package generator creates `<package>/<name>/<name>.py` even though existing first-level subpackages do not follow that pattern.
- A generated function such as `placeholder()` exists only to give the generated test something to assert.
- A generated test proves a constant or package name is returned, but does not protect any real application requirement.
- Removing a behavior stub would leave both the source and mirrored test directories with only `__init__.py`, violating a repository layout validator.
- The generator exposes stable modes such as name validation, overwrite refusal, `--dry-run`, machine-readable JSON, or an optional CLI shim that must remain unchanged while the artifact set shrinks.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the implementation passes local tests and CI.

The repository validator currently requires a literal `## Verified Workflow` section. The proposed, unverified steps therefore appear under that compatibility heading below.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms it.

### Quick Reference

```python
PACKAGE_INIT = '''\
"""{title} utilities."""
'''

TEST_INIT = ""

IMPORT_TEST = '''\
"""Import contract for ``{package}.{name}``."""

from __future__ import annotations

import importlib


def test_package_is_importable() -> None:
    """Verify the generated subpackage is importable by its public name."""
    module = importlib.import_module("{package}.{name}")
    assert module.__name__ == "{package}.{name}"
'''
```

```python
expected_files = {
    Path("<package-root>/<name>/__init__.py"),
    Path("<test-root>/<name>/__init__.py"),
    Path("<test-root>/<name>/test_<name>.py"),
}

assert generated_files == expected_files
assert "placeholder" not in generated_test.read_text(encoding="utf-8")
assert check_test_structure(scaffold_root, src_package="<package>") is True
```

### Detailed Steps

1. **Inspect architectural precedent before editing the template.** Enumerate existing first-level packages and check whether they use a same-name implementation module. Do not make a generator establish a layout that the repository itself does not use.

2. **Pin the exact base artifact set in tests.** Compare all generated files relative to the scaffold root against a set containing only the package `__init__.py`, test `__init__.py`, and import-contract test. Exact set equality catches both missing files and accidental new stubs.

3. **Add a negative regression assertion for fabricated behavior.** Assert that the same-name implementation module is absent and that neither generated package nor test content contains the retired placeholder symbol.

4. **Make the generated test protect a durable contract.** Import the package through `importlib.import_module("<package>.<name>")` and assert its canonical module name. This proves package structure and public importability without guessing future APIs.

5. **Exercise the repository's structural validator directly.** If the repository enforces mirrored package/test layout, invoke that validator against the generated tree. Keeping a real import test avoids the invalid state where both mirrored directories contain only `__init__.py`.

6. **Shrink only the artifact plan and templates.** Remove the production-module template and its plan entry. Keep name validation, target-existence checks, write ordering, filesystem error handling, and optional CLI-shim branching intact.

7. **Treat the artifact plan as the machine-output contract.** Assert the exact ordered `files_created` and `files_planned` JSON arrays after the file-count change. For JSON dry-run, also prove neither the source nor test root was written.

8. **Update human-facing guidance to defer behavior decisions.** Describe the result as a minimal importable package with a structural test. Tell users to add implementation modules and behavior-focused tests when requirements exist; do not tell them to fill in a generated stub.

9. **Verify preserved modes separately before the full module.** Run focused tests for invalid names, overwrite refusal, plain dry-run, JSON output, underscore names, output hints, and the optional CLI shim, followed by the complete scaffolder test module.

```bash
<test-command> <scaffolder-test-module>::<valid-name-class>::test_creates_only_minimal_structure
<test-command> <scaffolder-test-module>::<valid-name-class>::test_generated_tree_satisfies_test_layout_policy
<test-command> <scaffolder-test-module>::<invalid-name-class> <scaffolder-test-module>::<json-class>
<test-command> <scaffolder-test-module>
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Generate a same-name application module | The scaffolder emitted `<package>/<name>/<name>.py` containing `placeholder()` | The module shape had no repository precedent and forced an application API before any requirement existed | A package scaffold should establish importable structure, not invent production behavior |
| Test the placeholder return value | The generated test asserted that `placeholder()` returned the subpackage name | The assertion verified only behavior fabricated by the generator; it protected no durable user contract | Test package importability until real behavior is specified |
| Remove the test along with the stub | Considered leaving only `__init__.py` on the package and mirrored test sides | A structural layout policy can reject mirrors where both sides contain only `__init__.py` | Retain one substantive structural import test to satisfy the repository invariant |
| Assert only the new file count | Checked that JSON or filesystem output contained three items | A count cannot distinguish the intended files from three wrong files or detect an accidental replacement | Assert exact relative paths and exact ordered machine-readable output |
| Rewrite the generator flow while changing templates | Coupled the artifact correction to validation, overwrite, dry-run, or write-path changes | Those controls are independent, already-established contracts and expand the regression surface unnecessarily | Keep runtime control flow stable; change templates, plan contents, descriptions, and hints only |

## Results & Parameters

### Minimal Base Artifact Contract

| Artifact | Purpose |
|----------|---------|
| `<package-root>/<name>/__init__.py` | Makes the generated subpackage importable and gives it package documentation |
| `<test-root>/<name>/__init__.py` | Maintains the repository's mirrored unit-test package layout |
| `<test-root>/<name>/test_<name>.py` | Proves the public package import contract and makes the mirror structurally substantive |
| `<scripts-root>/<name>.py` | Optional only when the existing CLI-shim flag is requested |

### Acceptance Invariants

- Base generation creates exactly three files; the optional CLI flag adds exactly one established shim.
- No same-name implementation module or placeholder symbol is generated.
- The generated test imports `<package>.<name>` through `importlib` and asserts the canonical module name.
- The generated tree passes the repository's real package/test layout validator.
- Invalid-name behavior, overwrite refusal, dry-run non-mutation, JSON field names and ordering, and user-facing hints remain covered.
- No dependency, public API, configuration surface, or architectural boundary is added solely for the scaffolder correction.

### Verification Boundary

Repository inspection and a behavior-first implementation plan support this workflow, but no code was changed and no tests or CI ran during capture. Keep the skill at `unverified` until the correction is executed and the focused plus complete scaffolder suites pass.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planned correction to `hephaestus-scaffold-subpackage` | Repository precedent and structural-validator requirements were inspected; implementation and CI validation are pending |
