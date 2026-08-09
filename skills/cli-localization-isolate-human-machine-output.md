---
name: cli-localization-isolate-human-machine-output
description: "Design a stdlib-only Python localization boundary that translates authored human-facing CLI, plain-log, and TUI text without changing machine contracts. Use when: (1) adding localization to argparse CLIs without process-global hooks, (2) preserving JSON, flags, metavars, runtime values, and exit codes, (3) localizing threaded logging or terminal UIs with context-local catalogs."
category: architecture
date: 2026-07-25
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - python
  - localization
  - i18n
  - argparse
  - logging
  - curses
  - contextvars
  - machine-output
  - placeholder-validation
---

# CLI Localization: Isolate Human and Machine Output

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-25 |
| **Objective** | Define one stdlib-only localization boundary for application-authored CLI help, plain logs, direct terminal output, and fixed TUI labels while preserving every machine-readable and parser-syntax contract. |
| **Outcome** | A proposed architecture and migration/testing checklist were produced. English source templates are complete fallback keys; catalogs are immutable and context-local; consumers that outlive the context capture the selected localizer. |
| **Verification** | unverified |

The central design choice is an ownership boundary, not a global locale switch:
application-authored human text is translated explicitly, while stdlib-owned diagnostics,
structured payloads, protocol fields, parser syntax, and runtime values are left alone.

## When to Use

- Adding localization to a Python CLI that uses ordinary `argparse.ArgumentParser`
  instances and must remain safe when unrelated parsers run concurrently.
- Translating human-readable terminal output while JSON or another structured format must
  remain byte-for-byte or parse-tree equivalent.
- Localizing plain logging handlers without changing JSON formatters, custom handlers,
  `LogRecord` fields, interpolation arguments, or the original record.
- Rendering fixed labels from a background thread, curses UI, or formatter after the
  caller's localization context has exited.
- Designing synthetic-catalog tests that prove placeholder compatibility, English
  fallback, isolation, and preservation of flags, metavars, version output, and exit codes.

## Proposed Workflow

<!-- validator compatibility token: ## Verified Workflow -->

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```python
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterator, Mapping


@dataclass(frozen=True, init=False)
class Localizer:
    """Translate English source templates through an immutable catalog."""

    _catalog: Mapping[str, str] = field(repr=False)

    def __init__(self, catalog: Mapping[str, str] | None = None) -> None:
        copied = dict(catalog or {})
        validate_catalog(copied)
        object.__setattr__(self, "_catalog", MappingProxyType(copied))

    def template(self, source: str, /) -> str:
        return self._catalog.get(source, source)

    def text(self, source: str, /, *args: object, **values: object) -> str:
        translated = self.template(source)
        if args and values:
            raise TypeError("cannot mix positional and named formatting values")
        return translated % (args or values) if args or values else translated


_ENGLISH = Localizer()
_ACTIVE: ContextVar[Localizer] = ContextVar("application_localizer", default=_ENGLISH)


def text(source: str, /, *args: object, **values: object) -> str:
    return _ACTIVE.get().text(source, *args, **values)


@contextmanager
def using_localizer(localizer: Localizer) -> Iterator[Localizer]:
    token = _ACTIVE.set(localizer)
    try:
        yield localizer
    finally:
        _ACTIVE.reset(token)
```

```python
# Translate only application-authored parser metadata at construction time.
parser = argparse.ArgumentParser(description=text("Collect system information"))
parser.add_argument(
    "--no-tools",
    metavar="MODE",
    choices=("fast", "complete"),
    help=text("Skip tool version checks"),
)

# Keep runtime values outside the catalog; use named placeholders.
print(text("Processed %(count)d files", count=file_count))
```

### Detailed Steps

1. **Inventory the human/machine boundary before editing.** Find parser descriptions,
   epilogs, usage strings, argument help, group titles, subparser help, direct `print()`
   calls, plain logging formatter selection, fixed TUI labels, and text-versus-JSON
   format branches. Classify every value as authored human text, stdlib-owned text,
   parser syntax, runtime data, or structured output.

2. **Use complete English source templates as catalog keys.** A missing catalog entry then
   falls back naturally to the full English sentence. Keep the sole rendering entry point
   small: look up a template, then interpolate positional or named `%` values.

3. **Validate the entire catalog during construction.** Parse source and translated
   `%` placeholders before any output is rendered. Named placeholders must preserve the
   same names and conversion types; positional placeholders must preserve their ordered
   conversion signature; ignore escaped `%%`. Reject missing, extra, renamed, reordered,
   or type-changed placeholders. Reject calls that mix positional and named values.

4. **Make localizers immutable and context-local.** Defensively copy the caller's mapping,
   wrap it in `MappingProxyType`, and expose no mutable catalog accessor. Select the active
   localizer with a `ContextVar` context manager that always resets its token in `finally`,
   including nested and exceptional exits.

5. **Translate only authored argparse metadata, eagerly.** Continue constructing ordinary
   `argparse.ArgumentParser` objects. Pass `description=text(...)`,
   `epilog=text(...)`, `usage=text(...)`, `help=text(...)`, and translated group/subparser
   labels. In shared factories, translate passed-in metadata exactly once at the parser
   boundary.

6. **Never send parser syntax through the localizer.** Preserve `prog`, option strings,
   `dest`, `metavar`, `choices`, defaults, action classes, types, version payloads, and
   exit codes. Stdlib-owned headings and diagnostics remain in the stdlib's language.
   Never assign `argparse._` or `argparse.ngettext`; those are module globals observed by
   unrelated concurrent parsers.

7. **Separate human branches from structured branches.** Route literal and formatted
   terminal prose through `text()`, converting interpolation to named placeholders.
   Leave JSON serialization, status protocols, blank lines, runtime-only values, field
   names, environment keys, paths, versions, and collected data unchanged.

8. **Translate plain log templates on a copied record.** A plain formatter should capture
   the active immutable localizer when constructed. In `format()`, shallow-copy the
   `LogRecord`, translate `copied.msg` only when it is a string, retain `copied.args` for
   standard logging interpolation, and delegate to `logging.Formatter`. JSON formatters
   and existing/custom handlers must continue receiving the original record.

9. **Capture context for consumers that outlive it.** `ContextVar` state does not
   automatically define the desired context for arbitrary background-thread output.
   Capture `get_localizer()` when constructing a plain formatter or TUI, before its worker
   thread starts. Use that captured immutable object later for fixed labels. Do not
   translate live status text, buffered log bodies, worker identifiers, or dimensions.

10. **Enforce the boundary structurally and behaviorally.** Add an AST test that detects
    untranslated literal/f-string parser metadata and direct human-output literals, plus
    assignments to forbidden argparse globals. Give serializers, status emitters, blank
    output, and runtime-only nodes narrow exemptions. Pair the AST guard with synthetic
    catalog tests; a structural check alone cannot prove parser or JSON compatibility.

11. **Verify invariants at several layers.** Unit-test fallback, catalog validation,
    immutability, nested restoration, exceptional restoration, copied-record isolation,
    and captured-localizer behavior. Integration-test representative direct, shared,
    grouped, and subparser CLIs. Compare parsed JSON inside and outside a localization
    context for exact equality and assert unchanged flags, destinations, metavars,
    choices, version output, and exit codes.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Mutate `argparse._` or `argparse.ngettext` temporarily | Reuse stdlib gettext dispatchers so generated and authored help could share a catalog | Both names are process-global module state; overlapping ordinary parsers can observe the temporary catalog, so a lock around one code path cannot isolate unrelated callers | Translate only owned metadata before passing it to an ordinary parser; leave stdlib-owned text alone and assert dispatcher identities never change |
| Wrap, proxy, or subclass `ArgumentParser` and argparse containers | Intercept parser construction and translate metadata automatically | This expands the compatibility surface to stdlib internals, container return types, action creation, and Python-version behavior; it also obscures which strings are safe to translate | Prefer explicit `text(...)` calls and a narrow shared-factory boundary over a replacement parser hierarchy |
| Translate every string encountered in output code | Treat all strings as localizable for coverage completeness | Flags, metavars, JSON keys, version payloads, paths, runtime values, and protocol text are behavioral contracts or data, not authored prose | Classify ownership first and localize only human-facing source templates |
| Mutate a `LogRecord` in place | Replace `record.msg` before plain formatting | Other handlers, including JSON and custom handlers, receive the same record and would observe translated content or changed fields | Shallow-copy for the localized formatter and preserve the original record and interpolation arguments |
| Read the active `ContextVar` only when a worker renders | Expect a background thread or later callback to inherit the caller's desired catalog | Thread/context propagation and object lifetime do not guarantee that later rendering sees the construction context | Capture the immutable localizer when the formatter or TUI is constructed |
| Claim verification from a detailed plan | Treat source inspection, grep counts, and proposed tests as execution evidence | No implementation, focused tests, full regression, static checks, or CI ran in this session | Keep the skill `unverified` and title the workflow "Proposed Workflow" until end-to-end evidence exists |

## Results & Parameters

### Boundary matrix

| Surface | Translate | Preserve unchanged |
|---------|-----------|--------------------|
| argparse | Authored description, epilog, usage, help, group title, subparser help | Parser class, `prog`, option strings, `dest`, metavar, choices, defaults, actions, types, version payloads, exit codes, stdlib headings/diagnostics |
| direct terminal output | Literal source templates and named `%` formatting | Blank output, runtime-only values, structured serializers and status protocols |
| logging | String message template on a shallow-copied record for newly created plain handlers | Original record, args, fields, JSON formatters, existing/custom handlers, non-string messages |
| curses/TUI | Fixed authored labels via a captured localizer | Live status values, buffered log bodies, indices, colors, truncation, terminal dimensions |
| system/report formatting | Human-readable text branch labels | JSON branch, dictionary keys, environment keys, tool names, paths, versions, collected runtime values |

### Placeholder contract

```text
Source:      "Processed %(count)d files for %(owner)s"
Valid:       "Traitement de %(count)d fichiers pour %(owner)s"
Invalid:     "Traitement de %(total)d fichiers pour %(owner)s"  # renamed key
Invalid:     "Traitement de %(count)s fichiers pour %(owner)s"  # d changed to s

Source:      "Worker %d: %s"
Valid:       "Agent %d : %s"
Invalid:     "Agent %s : %d"  # ordered positional signature changed

Source:      "Progress: 100%%"
Validation:  escaped %% contributes no placeholder
```

### Acceptance checklist

```text
- [ ] Missing catalog keys render complete English templates.
- [ ] Catalog mappings cannot be mutated through caller references or the Localizer.
- [ ] Missing, extra, renamed, reordered, and type-changed placeholders fail at construction.
- [ ] Nested and exceptional localization contexts restore the previous localizer.
- [ ] Localized and ordinary parser formatting can overlap without cross-observation.
- [ ] argparse._ and argparse.ngettext identities remain unchanged.
- [ ] Flags, dests, metavars, choices, defaults, version output, and exit codes are unchanged.
- [ ] Parsed JSON inside and outside localization contexts is exactly equal.
- [ ] Plain handlers localize copied string templates; JSON/custom handlers see originals.
- [ ] TUI fixed labels use the construction-time localizer; live values remain unchanged.
- [ ] AST boundary guard passes with narrow, documented machine-output exemptions.
- [ ] Focused tests, full regressions, formatting, lint, typing, and CI have run.
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Proposed stdlib-only localization boundary for CLI, plain logs, curses UI, and system-info text | Design and test plan only; implementation and CI validation pending |
