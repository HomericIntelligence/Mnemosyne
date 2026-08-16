---
name: testing-parametrized-console-script-test-incomplete-implementation
license: BSD-3-Clause
description: "Use discovery-backed parametrized tests for executable CLI contracts. Use when: (1) console scripts are registered in project metadata, (2) a hand-maintained module list has drifted from parser builders, (3) every validation command must expose shared version behavior, (4) every importable parser with --dry-run must toggle one boolean contract, or (5) a discovered sweep exposes an incompletely wired entry point."
category: testing
date: 2026-08-05
version: "1.2.0"
history: testing-parametrized-console-script-test-incomplete-implementation.history
user-invocable: false
verification: unverified
tags:
  - testing
  - parametrize
  - console-scripts
  - project-scripts
  - cli-entry-points
  - parser-discovery
  - dry-run
  - version-flag
  - auto-discovery
  - behavior-contracts
  - hephaestus
---

# Discovery-Backed CLI Contract Sweeps

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-05 |
| **Objective** | Make executable registries and importable parser builders define the CLI test matrix, eliminating hand-maintained module lists, source-string counts, and help-wording assertions. |
| **Outcome** | The original `[project.scripts]` sweep is verified in CI. A proposed extension discovers validation entry points from project metadata and dry-run parsers from importable modules, then asserts their public parse/exit behavior. |
| **Verification** | `unverified` for the v1.2 discovery extension; the original version/JSON console-script sweep remains `verified-ci`. |
| **History** | [changelog](./testing-parametrized-console-script-test-incomplete-implementation.history) |

## When to Use

- A parametrized test should apply a shared contract to every registered console script,
  importable module, parser builder, plugin, or command.
- A static `VALIDATION_MODULES`, `CLI_PARSER_BUILDERS`, or similar list must be updated by
  hand whenever a module is added or renamed.
- Source-string counts or minimum-count floors are used as a proxy for whether parsers call
  a shared helper.
- Help-text substring and punctuation assertions are standing in for the behavior of a
  boolean flag.
- A newly registered command fails an existing discovered sweep because its implementation
  did not wire the shared option contract.

## Proposed Workflow

> **Warning:** The v1.2 registry/module discovery extension has not been validated end-to-end. Treat it as a hypothesis until CI confirms.

### Quick Reference

Discover public console scripts from the packaging source of truth and invoke the registered
callable:

```python
import importlib
import sys
import tomllib
from collections.abc import Callable


def entry_points(project_file: Path, prefix: str) -> list[tuple[str, str]]:
    project = tomllib.loads(project_file.read_text(encoding="utf-8"))
    return sorted(
        (command, target)
        for command, target in project["project"]["scripts"].items()
        if target.startswith(prefix)
    )


def load_entry_point(target: str) -> Callable[..., int]:
    module_name, function_name = target.split(":", 1)
    return getattr(importlib.import_module(module_name), function_name)


@pytest.mark.parametrize(("command", "target"), entry_points(PROJECT_FILE, "project.validation."))
def test_version_contract(command, target, monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", [command, "--version"])
    with pytest.raises(SystemExit) as exited:
        load_entry_point(target)()
    assert exited.value.code == 0
    assert capsys.readouterr().out.strip()
```

Discover importable parser builders and test dry-run state directly:

```python
def discover_dry_run_parsers(package) -> list[tuple[str, argparse.ArgumentParser]]:
    discovered = []
    for info in pkgutil.iter_modules(package.__path__, prefix=f"{package.__name__}."):
        module = importlib.import_module(info.name)
        builder = getattr(module, "_build_parser", None)
        if not callable(builder):
            continue
        parser = builder()
        if any("--dry-run" in action.option_strings for action in parser._actions):
            discovered.append((info.name, parser))
    return discovered


def required_arguments(parser: argparse.ArgumentParser) -> list[str]:
    argv: list[str] = []
    for action in parser._actions:
        if action.required and action.option_strings:
            value = next(iter(action.choices)) if action.choices else "1"
            argv.extend([action.option_strings[0], str(value)])
    return argv
```

For each discovered parser, assert only:

```python
required = required_arguments(parser)
assert parser.parse_args(required).dry_run is False
assert parser.parse_args([*required, "--dry-run"]).dry_run is True
```

### Detailed Steps

1. **Identify the executable authority.** Use `[project.scripts]`, an importable package,
   plugin metadata, or another runtime registry. Do not invent a parallel test list.
2. **Filter by the contract's real boundary.** A validation-only sweep can filter entry
   point targets by module prefix. A dry-run sweep can include only parser builders whose
   actions actually expose `--dry-run`.
3. **Load and execute the public seam.** Import the registered callable, set `sys.argv`, and
   assert exit code and non-empty output for `--version`. Build parsers and call
   `parse_args()` for parser-local option behavior.
4. **Satisfy required options mechanically.** Derive required option strings and a valid
   representative choice from each parser action so the dry-run test does not need
   per-module fixtures.
5. **Keep a direct helper test.** Test the isolated `add_dry_run_arg` helper for false by
   default and true when present; the discovery sweep proves callers expose the same
   behavior.
6. **Keep deeper per-command tests.** Discovery proves breadth, not every command outcome.
   Retain focused repository-root handling, JSON envelope, and error-path tests for the
   public commands.
7. **Run the complete discovered sweep before merge.** Auto-discovery expands faster than
   manually wired implementation. A red new parameter usually identifies the missing
   implementation, not a test that should be excluded.

## Verified Workflow

The original `[project.scripts]` console-script sweep is verified in CI: it caught commands
that omitted a shared `--version` option. The broader registry and importable-module
discovery pattern under **Proposed Workflow** is not yet verified.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Partial implementation | Added an auto-discovered `--version` sweep but wired the helper on only a subset of scripts | The test expanded to every registered script and exposed three unpatched commands | Treat each red discovered parameter as an implementation gap unless the registry entry is intentionally outside the contract |
| Hand-maintained module dictionary | Listed known validation modules beside the production registry | The list named fewer modules than source discovery and required synchronized edits | Derive public entry points from packaging metadata |
| Source-string counts and minimum floors | Counted helper-call strings or required at least N modules | Formatting and alternate valid call shapes can fail the proxy, while a stale floor can pass after new modules are added | Execute the shared public behavior for every discovered member |
| Static dry-run parser list | Enumerated parser builders manually | New importable modules with `--dry-run` silently escaped the sweep | Discover modules, select callable builders, and inspect parser actions |
| Help wording assertions | Pinned descriptions, prefixes, punctuation, and token-cost sentences | Editorial CLI help changes failed tests without changing option semantics | Assert parsed boolean state and keep text tests only for intentionally public wording APIs |
| Skipping the full sweep | Ran spot checks or pre-commit without the complete parametrization | The missed commands surfaced only when every discovered entry ran | Execute the full discovered test matrix before merge |

## Results & Parameters

### Stable contract layers

| Layer | Discovery source | Observable assertion |
| ----- | ---------------- | -------------------- |
| Packaged validation commands | `[project.scripts]` targets filtered by module prefix | `--version` exits `0` and emits output |
| Automation dry-run parsers | Importable modules with callable `_build_parser` and a `--dry-run` action | Absent is `False`; present is `True` |
| Shared dry-run helper | Isolated `ArgumentParser` | Same false/true boolean toggle |
| Command-specific behavior | Focused public CLI tests | Repository root, JSON result, and error semantics |

### Proposed ProjectHephaestus verification

```bash
uv run pytest \
  tests/unit/validation/test_validation_parser_usage.py \
  tests/unit/cli/test_dry_run_help.py \
  tests/unit/validation/test_validation_cli_contracts.py -v
```

Original verified failure: three registered scripts omitted `add_version_arg(parser)` and
failed the full sweep with `unrecognized arguments: --version`; wiring the shared helper
made all 237 entry-point tests pass.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | PR #1035 and PR #1174 | `[project.scripts]` version sweep exposed three incompletely wired commands; fixed and verified in CI. |
| ProjectHephaestus | PR #1570 / issue #1554 | The same sweep caught a newly added script missing `add_version_arg`. |
| ProjectHephaestus | Issue #1950 behavior-first test refactor plan | Validation-entry-point and dry-run parser discovery are proposed; implementation and CI are pending. |
