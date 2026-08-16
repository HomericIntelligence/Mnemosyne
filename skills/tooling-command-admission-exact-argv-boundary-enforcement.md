---
name: tooling-command-admission-exact-argv-boundary-enforcement
license: BSD-3-Clause
description: "Replace prefix-based admission of documentation-derived commands with parsed, exact argv grammars, and enforce the grammar again at the subprocess sink. Use when: (1) README or documentation code fences can be executed by a validator, (2) command.startswith(...) or a similar prefix check admits extra programs, options, or paths, (3) callers can reach an execution helper without passing through an outer safety loop, or (4) custom command overrides must preserve an exact least-privilege policy."
category: tooling
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - python
  - subprocess
  - shlex
  - argv
  - allowlist
  - command-injection
  - readme-validation
  - least-privilege
  - fail-closed
---

# Exact Argv Admission at the Subprocess Boundary

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Prevent documentation edits from broadening an executable command surface beyond a small set of host-approved commands. |
| **Outcome** | Proposed a reusable boundary contract: parse with POSIX `shlex`, compare the complete argv tuple against an immutable allowlist, preserve empty custom policies, and repeat admission at the subprocess sink before executing the parsed argv with `shell=False`. |
| **Verification** | unverified — the source, documented command inventory, execution sink, and proposed regression cases were analyzed, but the implementation, tests, and CI were not run. |

## When to Use

- A README validator extracts shell commands from executable code fences and may run them.
- Admission currently uses `command.startswith(prefix)` or another textual prefix check.
- An approved launcher such as `uv run` can select arbitrary programs, dependencies, options, or script paths after the accepted prefix.
- A public execution helper can be called directly, bypassing the quick or comprehensive loop that normally checks safety first.
- A constructor or configuration option supplies custom approved commands and must mean exact commands, including when the supplied collection is empty.
- Tests cover obvious metacharacters but not valid-looking prefix collisions such as `pytest-malicious`, extra test paths, or launcher options.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a
> hypothesis until focused tests and CI confirm it.

### Quick Reference

```python
import shlex
import subprocess
from typing import ClassVar


class CommandValidator:
    """Admit only host-approved argv tuples before launching a process."""

    DEFAULT_ALLOWED_ARGV: ClassVar[frozenset[tuple[str, ...]]] = frozenset(
        {
            ("uv", "run", "pytest"),
            ("uv", "run", "pytest", "tests/unit"),
            ("uv", "run", "ruff", "check", "src", "tests"),
            ("uv", "sync"),
        }
    )

    def __init__(self, allowed_commands: list[str] | None = None) -> None:
        if allowed_commands is None:
            self.allowed_argv = self.DEFAULT_ALLOWED_ARGV
        else:
            self.allowed_argv = frozenset(
                tuple(shlex.split(command, posix=True))
                for command in allowed_commands
            )

    def parse_command(self, command: str) -> tuple[str, ...] | None:
        try:
            argv = tuple(shlex.split(command, posix=True))
        except ValueError:
            return None
        return argv or None

    def is_allowed_command(self, command: str) -> bool:
        argv = self.parse_command(command)
        return argv is not None and argv in self.allowed_argv

    def execute(self, command: str) -> subprocess.CompletedProcess[str]:
        argv = self.parse_command(command)
        if argv is None or argv not in self.allowed_argv:
            raise ValueError("command is not in the allowed argv grammar")
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
```

### Detailed Steps

1. **Treat documentation as untrusted execution input.** A command can look like documentation and still select an arbitrary program, dependency, option, or path. The host owns the executable grammar; README text does not expand it.

2. **Inventory only the commands that must execute.** Parse the repository's current executable documentation fences and approve the complete commands that validation genuinely needs. Do not approve a launcher family such as `uv run`, a tool family such as `uv run pytest`, or every command mentioned anywhere in prose.

3. **Store the policy as immutable argv tuples.** Use `ClassVar[frozenset[tuple[str, ...]]]`. Tuple membership expresses the real process contract and prevents accidental runtime mutation of the default policy.

4. **Tokenize with `shlex.split(command, posix=True)` before admission.** This normalizes quoting and whitespace into the arguments the process will receive. Catch `ValueError` for unterminated quotes and reject an empty token list. Never fall back to text-prefix matching after tokenization fails.

5. **Require complete tuple membership.** An argv tuple is admitted only if every element and its position match an approved tuple. For example, approving `("uv", "run", "pytest")` must not admit an extra path, `--with`, `python -c`, a sibling executable named `pytest-malicious`, or an absolute script path.

6. **Keep existing lexical blocks as defense in depth.** Shell-metacharacter and blocked-pattern checks remain useful diagnostics and protect future refactors. They do not replace exact argv admission: many dangerous launcher expansions contain no shell metacharacters.

7. **Distinguish omitted overrides from empty overrides.** Use `if allowed_commands is None` for defaults. Do not write `allowed_commands or DEFAULTS`; an explicitly empty list is a deliberate deny-all policy and must remain empty. Parse custom strings into exact tuples at construction time, so a custom command does not become a prefix.

8. **Enforce admission inside the execution sink.** Outer quick/comprehensive loops are convenience layers, not a security boundary. The function containing `subprocess.run` must independently tokenize, reject malformed or empty input, apply blocked and exact-grammar checks, and return a failed result without launching a process.

9. **Execute the admitted argv, not the original command string.** Pass the parsed sequence to `subprocess.run(..., shell=False)`. This keeps the checked representation identical to the executed representation and avoids a second shell interpretation.

10. **Preserve report semantics deliberately.** If comprehensive validation historically counts unsafe documentation commands as skipped, retain that behavior and assert `passed == 0`, `failed == 0`, and `skipped_commands == 1`. A rejected command must never reach the subprocess mock.

11. **Test both the classifier and the sink.** Positive tests should enumerate every approved argv form. Negative tests should be parameterized over arbitrary programs, launcher options, script paths, extra test paths, unlisted tools, prefix collisions, malformed quoting, empty input, and empty/custom overrides. For every bypass, assert both classification rejection and `subprocess.run.assert_not_called()` after a direct execution-helper call.

12. **Assert the successful subprocess contract exactly.** For an admitted command, check the precise parsed argv plus `shell=False`, `cwd`, timeout, text/capture settings, and `check=False`. This catches a later regression that validates one representation but executes another.

## Verified Workflow

_Not applicable yet._ The actionable methodology is under **Proposed Workflow**.
This placeholder exists for corpus validation and makes no verification claim.
Promote the workflow only after implementation tests pass; use `verified-local` for
local evidence or `verified-ci` after CI confirms it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Prefix admission | Used `command.startswith("uv run")` or `command.startswith("uv run pytest")` | The accepted prefix can be followed by `python -c`, `--with`, arbitrary scripts, extra test paths, or a colliding executable name | Approve complete parsed argv tuples, never launcher or textual prefixes |
| Metacharacter filtering as the policy | Rejected pipes, redirects, substitutions, or similar shell syntax | Many policy bypasses are ordinary argv with no shell syntax at all | Keep lexical filters only as defense in depth behind an exact grammar |
| Safety only in outer loops | Quick and comprehensive callers invoked `is_safe_command()` before the execution helper | A direct call to the public or internally reachable execution sink bypasses the caller convention | Put the fail-closed admission check in the function that owns `subprocess.run` |
| Re-execute the original string | Parsed a string to classify it, then launched the original string or enabled `shell=True` | The checked representation was not guaranteed to be the executed representation | Execute the already parsed argv sequence with `shell=False` |
| Truthiness fallback for overrides | Used `configured_commands or DEFAULT_COMMANDS` | An explicit empty override unexpectedly re-enabled defaults | Default only on `None`; preserve an empty collection as deny-all |
| Custom prefix semantics | Accepted a custom entry such as `myapp run` with `startswith` | `myapp run untrusted-path` inherited admission without explicit approval | Parse each custom string once and require exact tuple equality |
| Positive-only tests | Verified the documented commands still passed | The vulnerable surface consisted of near-miss commands that were never exercised | Parameterize bypass families and assert the subprocess mock is untouched at the direct sink and comprehensive path |

## Results & Parameters

Host-owned grammar example for a documentation validator:

```python
DEFAULT_ALLOWED_ARGV = frozenset(
    {
        ("uv", "run", "pytest"),
        ("uv", "run", "pytest", "tests/unit"),
        ("uv", "run", "pytest", "tests/integration"),
        ("uv", "run", "pytest", "-m", "not integration"),
        ("uv", "run", "ruff", "format", "hephaestus", "scripts", "tests"),
        ("uv", "run", "ruff", "check", "hephaestus", "scripts", "tests"),
        ("uv", "sync"),
    }
)
```

Required rejection matrix:

```text
uv run python -c "print(1)"        -> reject; subprocess not called
uv run --with requests python ...  -> reject; subprocess not called
uv run scripts/untrusted.py        -> reject; subprocess not called
uv run /tmp/untrusted.py           -> reject; subprocess not called
uv run pytest tests/unit/extra.py  -> reject unless that exact argv is approved
uv run mypy src                    -> reject; subprocess not called
uv run pytest-malicious            -> reject; subprocess not called
uv sync-malicious                  -> reject; subprocess not called
echo unlisted                      -> reject; subprocess not called
unterminated 'quote                -> reject as malformed; subprocess not called
```

Security invariants:

```text
admitted(command) iff shlex.split(command, posix=True) is a nonempty tuple in allowed_argv
subprocess invocation implies admitted(command)
executed argv == admitted argv
shell == False
allowed_commands=[] means no command is admitted
```

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Plan to harden executable README validation commands in `hephaestus.validation.readme_commands` | Design and bypass matrix inspected on 2026-08-07; implementation and tests pending, so this skill remains unverified. |
