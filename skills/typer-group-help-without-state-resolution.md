---
name: typer-group-help-without-state-resolution
license: BSD-3-Clause
description: "Keep Typer (Click) group help trees renderable without resolving operation state. Use when a Typer group callback resolves configuration, credentials, or environment selectors on every invocation and a group or subcommand --help then crashes with a raw traceback whenever that state is missing, stale, or invalid; when real operations must refuse invalid state as one concise usage error (exit code 2) instead of a traceback; when considering ctx.protected_args for help detection (deprecated in Click 8.2+); or when Click usage-error output must be asserted renderer-independently in tests."
category: architecture
date: 2026-11-09
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [typer, click, cli, help-tree, group-callback, parse-args, ctx-meta, typergroup, badparameter, traceback, fail-closed, documentation-path, option-value-consumption, click-usage-panel, clirunner]
---

# Typer Group Help Without State Resolution

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Make `--help` a read-only documentation path: it must render even when the state that a group callback resolves for real operations is missing, stale, or invalid, and it must not touch that state. |
| **Outcome** | Operational. Group and leaf `--help` exit 0 with no state access; real operations refuse invalid state with one concise usage-error line and exit code 2; the strict process-state discipline (for example, a private-record umask) stays in effect even when help detection misfires. |

The core rule: **documentation paths must not require the state that operations need.** Click runs a
group callback *before* it parses the subcommand arguments, so a callback that resolves state on
every invocation crashes `group --help` whenever that state is bad — precisely the moment an
operator needs the command surface. Root `--help` is different: Click processes it eagerly, so the
callback never runs.

## When to Use

- `mycli <group> --help` or `mycli <group> <leaf> --help` exits nonzero with a traceback when the
  selector, config file, or credential the group callback resolves is absent or stale, while
  `mycli --help` works.
- An operator or regression suite must read command help without environment authority.
- Real operations with invalid state should print one short message and exit with usage-error code 2,
  not raise a library traceback.
- You consider `ctx.protected_args` or other leftover-argument introspection to detect help (deprecated
  since Click 8.2).
- Your Click 8.3+ usage errors render as boxed panels and line-exact test assertions fail.

## Verified Workflow

### Quick Reference

```python
from __future__ import annotations
from typing import TYPE_CHECKING

import typer
from typer.core import TyperGroup

if TYPE_CHECKING:
    from typer import _click  # static checkers need the parent's exact symbol

_HELP_REQUESTED = "mycli.help_requested"


class _HelpAwareGroup(TyperGroup):
    """Record a subcommand help request before the group callback runs."""

    def parse_args(self, ctx: _click.Context, args: list[str]) -> list[str]:
        scan = args[: args.index("--")] if "--" in args else list(args)
        ctx.meta[_HELP_REQUESTED] = any(token in ctx.help_option_names for token in scan)
        return super().parse_args(ctx, args)


app = typer.Typer(cls=_HelpAwareGroup, no_args_is_help=True)


@app.callback()
def require_operation_state(command_context: typer.Context) -> None:
    # Strict process state (example: a private-record umask) comes first and is
    # restored on command close; a false help hit must not relax it.
    if command_context.resilient_parsing or command_context.meta.get(_HELP_REQUESTED):
        return  # Help output and shell completion need no authority.
    try:
        state = resolve_state()  # project-specific resolution call
    except (OSError, ValueError) as error:
        detail = " ".join(str(error).split())  # keep the message one line
        raise typer.BadParameter(
            f"State selection failed: {detail}. Select one valid state with --state-option.",
            param_hint="--state-option",
        ) from error
    bind_state(state)
```

### Suggested Approach

1. **Confirm the order before designing.** Invoke the broken help path and check whether the group
   callback runs at all. On Click 8.x: root `--help` is eager and never reaches the callback; group
   and leaf `--help` reach the callback first with `invoked_subcommand` set; shell-completion parsing
   (`resilient_parsing=True`) never invokes group callbacks (verified on Click 8.4.x), so completion
   needs no skip test.
2. **Detect help through the public API.** A group sees the raw subcommand arguments in its
   `parse_args(ctx, args)`; scan the tokens before the first `--` against `ctx.help_option_names`
   and record the result in `ctx.meta`. Do not use `ctx.protected_args`; it is deprecated since
   Click 8.2.
3. **Fail closed against a false positive.** Click consumes `--help` as the VALUE of another option
   (`leaf --title --help` sets `title="--help"`), so a raw token scan can detect help that is not
   help. Structure the callback so a misfire is still safe: apply strict process state (umask and
   its close-restore) before the skip, and require every leaf to read bound state through an accessor
   that refuses when nothing is bound.
4. **Present refusal as one concise line.** Wrap the resolution call in `typer.BadParameter` (usage
   error, exit code 2) with the embedded error text whitespace-folded to one line —
   `" ".join(str(error).split())` — so a multi-line registry/library error cannot break the contract.
   Keep the strict refusal for operations; only documentation paths skip resolution.
5. **Test renderer-independently.** Click 8.3+ usage errors render inside a display-width panel even
   under capture. Wish assertions on flat text: `click.unstyle`, drop the panel border glyphs
   (`╭╮╰╯│─`), then `" ".join(output.split())`, and substring-match. Never assert on physical line
   boundaries. Regression matrix with `typer.testing.CliRunner`, RED first:
   - group and leaf `--help` × state unset / stale / non-canonical → exit 0, resolver patched to
     `pytest.fail` to prove no state access;
   - the same matrix through the explicit option form of the selector;
   - operations with invalid state → exit 2, no traceback, one folded error line;
   - option-consumed `--help` (`leaf --str-opt --help` with all required options otherwise filled)
     must NOT start the operation — the leaf refuses on the unbound state;
   - one help invocation leaves the process umask unchanged.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read `ctx.protected_args` in the group callback to see a pending `--help` | Attribute exists on older Click | Deprecated on Click 8.2+; the pin in the target tree was 8.4.x | Use a `TyperGroup.parse_args` override plus `ctx.meta`; that path is public API |
| Shell-completion regression test | Expected a completion invocation to hit the unfixed callback | Click resolves completion contexts without invoking group callbacks (verified on 8.4.x), so the test passed on unfixed code | A completion test is not RED evidence; keep a one-line `resilient_parsing` guard for version drift only |
| Line-exact refusal assertions | Asserted the one-line error as exactly one physical output line | Click 8.3+ wraps usage errors in a boxed panel at display width, splitting the text mid-message | Normalize before asserting: de-style, drop border glyphs, whitespace-fold, then match |
| Help skip before strict process state | Returned early for help before setting the private-record umask, to keep help side-effect free | A false-positive skip (help token as option value) would run leaves with the ambient umask, and a leaf not reading bound state loses the record discipline | Strict state first; help then differs only by skipping authority, which still renders with zero durable side effects |

## Results & Parameters

### Configuration

```yaml
help_detection:
  mechanism: "TyperGroup.parse_args override records ctx meta flag"
  scan_boundary: "tokens before the first -- token only"
  public_api_only: true
callback_order:
  strict_process_state: "before the help/completion skip; restored on command close"
  skip_condition: "ctx.resilient_parsing OR recorded help flag"
refusal_contract:
  exception: "typer.BadParameter"
  exit_code: 2
  message: "one whitespace-folded line, param_hint names the selector option"
```

### Expected Output

- `<group> --help` and `<group> <leaf> --help` exit 0 and print `Usage:` with the selector unset,
  stale, or invalid, and the resolver is provably untouched.
- A real operation with an invalid selector prints a usage error (`Invalid value ... : <one-line
  message>`), exits 2, and shows no traceback.
- The process umask after any help invocation equals the value before it.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A Typer operations CLI (Typer 0.20.x, Click 8.4.x, Python 3.12) | Offline `CliRunner` regression suite plus static gates on 2026-11-09; no live environment access | [notes.md](typer-group-help-without-state-resolution.notes.md) |

## References

- [Typer documentation: using Click classes](https://typer.tiangolo.com/tutorial/using-click/)
- Click API: `Group.parse_args(ctx, args)`, `Context.meta`, `Context.help_option_names`,
  `Context.resilient_parsing`, `BadParameter` (usage error, exit code 2)
- Related skill: [console-scripts-exit-code-discipline](console-scripts-exit-code-discipline.md) —
  route many scripts' failures through one exit-code boundary
