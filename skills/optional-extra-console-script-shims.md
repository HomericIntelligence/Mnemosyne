---
name: optional-extra-console-script-shims
license: BSD-3-Clause
description: "Ship console scripts that need an optional extra as base-importable shims. Use when a published package's command crashes with ModuleNotFoundError on a base install, or when a dependency moves into an optional extra while [project.scripts] targets keep importing the extra's modules."
category: architecture
date: 2026-10-28
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [python, packaging, console-scripts, optional-extra, entry-points, error-boundaries, import-surface, distribution]
---

# Optional-Extra Console-Script Shims

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-10-28 |
| Objective | Keep console scripts usable on a base install when their targets need modules that only an optional extra provides. |
| Outcome | Successful. Shim entry points replaced direct targets, the regression shipped in six releases went away, and a published release passed the base-install and extra-install matrix from the package registry. |

Python packaging cannot make a console script conditional on an optional extra.
A `[project.scripts]` entry always ships in the base wheel. If its target module
imports an extra-only dependency, every command fails at load time with a raw
`ModuleNotFoundError` traceback. The user sees the failure before any
documentation can help. The fix is a small shim module in the base package: it
checks for the extra, reports a boundary error with the install command, and
imports the real target only when the check passes.

## When to Use

- A command from a base install crashes with `ModuleNotFoundError` for a module
  that an optional extra provides, even for `--version` or `--help`.
- You move a runtime dependency from base dependencies into an optional extra,
  and console-script targets keep importing modules that need it.
- You add a console script for a subpackage that lives behind an optional extra.
- You review a package that documents an extra, but ships commands that crash
  without it.

## Verified Workflow

### Quick Reference

```python
# Base-importable shim module. It imports nothing from the product layer at
# module load, so the base import surface stays clean.
import importlib
import importlib.util

REQUIRED_MODULES = ("module_a", "module_b")  # modules the extra provides


def _require_extra() -> None:
    missing = [n for n in REQUIRED_MODULES if importlib.util.find_spec(n) is None]
    if missing:
        raise ConfigurationError(
            "this command needs the optional product layer "
            f"(missing modules: {', '.join(sorted(missing))})",
            recovery="install it with: pip install 'PACKAGE[extra]'",
        )


def command_main(argv: list[str] | None = None) -> int:
    def entry(args: list[str] | None) -> int:
        _require_extra()
        main = importlib.import_module("pkg.product.module").main
        return int(main(args))

    return boundary_main(entry, argv)  # one stderr line, one exit code
```

Point each `[project.scripts]` entry at a shim function:

```toml
[project.scripts]
pkg-command = "pkg.cli.entry_shims:command_main"
```

### Suggested Approach

1. Diagnose on the installed artifact. Run the command from a directory that is
   not the source checkout. A raw `ModuleNotFoundError` for an extra-only
   module at load time means the entry point imports the target first.
2. Write one shim module per package, not per command. Each public function is
   one line that names its target module. The module-level imports stay limited
   to the standard library and the base error helper.
3. Check every module the extra provides, not only the one that failed first.
   A user who installs one missing module by hand then hits the next failure.
4. Report the failure through the package's boundary error helper, so the same
   cause always produces the same stderr text and exit code. Name the install
   command in the recovery text.
5. Import the real target inside the function. Pass `argv` through unchanged.
   Let `SystemExit` keep its code, so `--help` and `--version` still work.
6. Point the script entries at the shims. Update the contract documents that
   list entry modules.
7. Prove the matrix on the built wheel in clean virtual environments: without
   the extra, every command prints the boundary error and exits with the
   configuration code; with the extra, every command runs the real target.
   Then verify the same matrix from the published registry artifact.
8. Keep the import-surface and boundary regression tests green. The shims must
   not pull the product layer or its dependencies into `import pkg`.

If the boundary error helper does not exist, raise a configuration-class error
with a recovery message and let the process exit non-zero. Do not catch the
error and continue; a missing extra makes the command unusable.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Keep the script entries in base `[project.scripts]` and document the extra in the README. | Users hit the traceback before any documentation. Six published releases carried the defect. | Documentation does not run before the import fails. |
| 2 | Put a dependency guard inside each product module's `main()`. | The generated console script imports the target module before `main()` runs, so the guard never executes. | The check must run in a module that the import of the target cannot fail. |

## Results & Parameters

### Configuration

- Exit code: use the package's configuration-error code (commonly `4`), not a
  generic error code, so operators can script around it.
- Stderr: one error line and one recovery line. The recovery names the exact
  install command.
- Module check list: every runtime module the extra provides. Store the list as
  one tuple next to the check, so a dependency change has one edit point.

### Expected Output

Base install, any invocation of a gated command:

```text
ConfigurationError: this command needs the optional product layer (missing modules: module_a, module_b)
Recovery: install it with: pip install 'PACKAGE[extra]'
```

Exit code `4`. No traceback. Commands that do not need the extra are unchanged.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| A Python CLI distribution with an opt-in product layer | Console-script hardening release | Six commands fixed; base-install and extra-install matrix verified on the built wheel and on the published registry artifact. See [notes](optional-extra-console-script-shims.notes.md). |

## References

- [Python packaging: entry points](https://packaging.python.org/en/latest/specifications/entry-points/)
- [Related skill](library-product-import-boundary-enforcement-test.md) — regression
  tests that keep the base import surface clean when a product layer moves
  behind an optional extra.
