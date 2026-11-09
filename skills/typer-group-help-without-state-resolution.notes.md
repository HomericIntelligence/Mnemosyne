# Notes: typer-group-help-without-state-resolution

Supporting evidence for the main skill. The main skill holds the decision rules; this file holds
the provenance, commands, and measurements.

## Provenance

- Source: a public open-source issue in an operations CLI repository
  ([LLM360/comet#2878](https://github.com/LLM360/comet/issues/2878)): a group `--help` for an
  operator CLI exited 1 with a raw `ValueError` traceback whenever the registered state selector
  was unset, stale, or non-canonical. Root help rendered fine; leaf help crashed.
- Fix: the exact mechanism now in the main skill (`TyperGroup.parse_args` + `ctx.meta` flag, early
  return after strict process state, `typer.BadParameter` wrap with whitespace-folded message).
- Review feedback that shaped the durable rules:
  - the plan's generator expression for the scan slice was a `SyntaxError` in comprehension
    position — compute the slice into a local variable first (the main skill's snippet does this);
  - the completion guard is defensive-only because completion never invokes group callbacks;
  - a help-token-as-option-value case needs fail-closed reasoning and ordering;
  - line-exact assertions break on Click's usage-error panel.

## Empirical checks behind the behavioral rules

Observed on Typer 0.20.x / Click 8.4.2 / CPython 3.12:

1. `leaf --title --help` → the leaf runs with `title == "--help"`. Click consumes the next token
   as an option value even when it starts with dashes.
2. Root `--help` → the group callback never runs (eager help option). Group `gateway --help` →
   the group callback runs first with `invoked_subcommand == "gateway"`.
3. Completion invocation (complete-word environment set) → the group callback never runs;
   completion resolves contexts silently. A `resilient_parsing` guard alone changes nothing
   observable on this version.
4. `typer.testing.CliRunner` on a `BadParameter` → exit code 2 and the message rendered inside a
   boxed panel with border glyphs; long messages wrap mid-word. `click.unstyle` does not remove
   border glyphs; translate them out before whitespace folding.

## Validation evidence (focused, offline)

- RED: the new 23-case regression suite run against the unmodified callback — 23 failed, 0 passed.
- GREEN: same suite against the fixed callback — 23 passed.
- Focused regression scope (the new file plus the existing CLI suites that touch the callback):
  271 passed, 1 skipped (a pre-existing quarantined case owned by another issue); no full-suite
  run was claimed locally.
- Static gates on the changed files: Ruff lint, Ruff format check, and the project type checker all
  passed. The type checker required the override annotation to use exactly the shim symbol the
  parent class uses (`typer._click.Context`); plain `click.Context` resolved as a different symbol
  and failed the Liskov check.
- Live-environment verification of the fix on a deployed build was deliberately out of scope
  (read-only boundary); it is a separate step after deployment.

## False-positive analysis kept with the fix

The false-positive (help token as option value) was reasoned through for every leaf class on the
affected app:

- leaves that read state only through the bound accessor refuse closed (the accessor raises when
  nothing is bound);
- the one leaf that echoes a constant without reading state has no stateful side effects, so the
  strict umask ordering is irrelevant to it;
- a special-cased bootstrap command has its own required-input validation before effects.

The remaining exotic corner (a leaf that both consumes `--help` as a value and performs effects
before reading state) was not present in the reviewed surface, and the strict-state-first ordering
removes the process-state half of that risk for future leaves.

## Utility parameter record

| Parameter | Value | Reason |
| ----------- | ------- | -------- |
| Scan boundary | first `--` token | After `--`, every token is a positional value, never an option |
| Meta key | `"<cli>.help_requested"` | Namespaced to the app; `ctx.meta` survives to the callback |
| BadParameter hint | `param_hint=<selector option>` | Produces `Invalid value for <option>: ...` |
| Panel border glyphs | `╭╮╰╯│─` | Removed in test normalization via `str.translate` |
| One-line fold | `" ".join(str(error).split())` | Collapses newlines and whitespace runs from wrapped registry errors |
