---
name: typed-errors-systemexit-transition
license: BSD-3-Clause
description: "Replace SystemExit raised inside importable library modules with module-specific typed errors that keep SystemExit as a base for one deprecation window. Use when a review says library or SDK callers cannot catch a typed error, when embedding a library in a long-lived process can exit the interpreter, or when the broad except Exception handlers of a supervisor must not start to swallow refusals."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - exception-design
  - systemexit
  - baseexception
  - deprecation-window
  - library-boundary
  - supervisor-swallow
  - entry-point-wrapper
  - transition-subclass
  - verified-local
---

# Typed Errors for a SystemExit Control-Flow Refactor

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Give library and SDK callers a typed error in place of `SystemExit` without an unplanned change to CLI exit behavior, supervisor recovery, or a protected exception contract. |
| **Outcome** | Successful local implementation. Contract, import, lint, format, and type checks passed. CI passed none of the gated jobs because the required review label was absent. |
| **Verification** | verified-local. Several test files fail in the source environment because of host path and identity policy; the same failures reproduce on the base commit. |

The central rule: a typed error replaces `SystemExit` in library code, but the typed class keeps
`SystemExit` as a base for one deprecation window. This keeps existing `except SystemExit` callers
working and keeps the error outside every `except Exception` handler until a dedicated audit
decides which handlers may then catch it.

## When to Use

- A review says `SystemExit`, `sys.exit`, or an equivalent process-exit call is raised in an
  importable module and library callers cannot catch a typed error.
- A library or SDK can run inside a long-lived process (dashboard, agent, service), where an abrupt
  interpreter exit is unacceptable.
- The published contract documents `SystemExit` as the raised exception, so a same-release hard
  cutover breaks the project's own deprecation policy.
- A supervisor, worker, or retry loop wraps the same operation in broad `except Exception`
  handlers, and a change to a plain `Exception` subclass would turn refusals into swallowed
  failures.
- A module has both a library function and its own script entry point (a `__main__` block or a
  console-script wrapper).

## Verified Workflow

### Quick Reference

```python
# 1. One errors module per library. The base keeps SystemExit for the window.
class LibraryError(SystemExit):
    """Base for typed library errors. Subclasses SystemExit during the
    deprecation window; see the project deprecation policy."""


class StateRefusalError(LibraryError):
    """The current state forbids the requested operation."""


# 2. Library code raises the typed error; the message text does not change.
raise StateRefusalError(f"pool {name} does not exist; use `pool up {name}`")

# 3. The script entry point converts the typed error to the process exit.
def main() -> None:
    try:
        run()
    except StateRefusalError as error:
        raise SystemExit(str(error)) from error


# 4. Prove both contracts in tests.
with pytest.raises(StateRefusalError, match="does not exist"):
    disabled_state_operation()
assert issubclass(StateRefusalError, SystemExit)   # window compatibility
```

```python
# Invariant: inherit __init__ so the message lands in args and code.
error = StateRefusalError("some message")
assert error.args == ("some message",)
assert error.code == "some message"
```

### Detailed Steps

1. **Re-derive every cited site at the current head.** Review line numbers drift while plan
   branches stay open. Grep the exact symbol (`SystemExit`) in each named module and record the
   current count. Do not edit by a planned line number. A plan that names 7 sites can be 9 at the
   current head.

2. **Separate the three layers before you edit.** Classify each site:
   - **library boundary** — an importable function raises the error: convert it;
   - **script entry point** — the module's own `__main__` block or console wrapper: keep
     `SystemExit`, and convert the typed error there;
   - **child process source** — a string that a generated script runs (`python -c`) is not
     importable library code. Keep its `SystemExit` and add a comment that names the parent gate.
   Record the last two as deviations in the pull request body.

3. **Grep for `except Exception` that would newly catch the error.** This check decides the base
   class. Count the broad handlers in the supervisor, scheduler, and recovery modules. `SystemExit`
   is a `BaseException`, so it escapes those handlers today. A plain `Exception` subclass does not.
   When such handlers exist, the transition subclass is mandatory, not optional.

4. **Check the published contract.** Read the project deprecation or compatibility policy and the
   contract tests. Find the documented exception, the version rules, and the notice channels. If
   the policy names a window of two releases plus a calendar period, a same-release change to the
   exception family is a policy violation.

5. **Create one errors module with a base plus specific subclasses.** Group the subclasses by
   failure meaning, not by function. Typical splits for one library are: gateway or endpoint
   unavailable, publication or contract mismatch, operator override conflict, credential
   unavailable, credential invalid, optional dependency missing. Add a base for the credential
   family only when callers must catch the family as a group. Do not add fields in the first
   change: a message-only class keeps `args` and `code` working.

6. **Keep every message byte-identical.** Retarget the existing factory helpers, not each raise
   site. One helper such as `_local_storage_error()` that returns `SystemExit(...)` becomes the
   single place that returns the typed class, and every raise site follows. Compare the old and
   new diff to confirm that no message string changed.

7. **Preserve behavior splits between the types.** When a caller distinguishes a migration
   refusal from a storage fault (a re-raise arm before a broad arm), keep that split. Make the
   refusal a subclass of the invalid-credential type, and keep the broad arm after the specific
   arm. Check the arm order after the rename.

8. **Replace the private refusal class by name.** Give the private class its new public name and
   verify that no reference exists outside the module:
   `rg -n "OldPrivateName" src tests scripts`. A rename that leaves one caller behind turns into a
   `NameError` at run time, not at import time.

9. **Convert the script entry point.** Wrap the library call in `try`/`except TypedError` and
   `raise SystemExit(str(error)) from error`. The message and the nonzero exit status stay the same.
   Add a subprocess test that asserts the message in stderr, a nonzero status, no `Traceback`, and
   an empty stdout.

10. **Add module-level error classes where the library is not the SDK.** A scheduler or pool module
    gets its own class (`PoolStateError(SystemExit)`) in its own module. Do not make internal
    modules import the SDK errors module; that inverts the dependency order.

11. **Update the contract tests in the same change.** Change `pytest.raises(SystemExit)` to
    `pytest.raises(TypedError)` for each converted site. Add one compatibility test that asserts
    `issubclass(TypedError, SystemExit)` and one path that still catches `SystemExit`. The policy
    usually requires the contract data change to appear in the same reviewed change.

12. **Update the user documentation.** Change the exception in the retry example to the typed name.
    State that `except SystemExit` keeps working during the window, and cite the policy page. Do
    not delete the `SystemExit` sentence without a replacement sentence.

13. **Open a dated follow-up issue before the merge.** The issue owns: both written notices, the
    `except Exception` audit (supervisor first), the typed catch needed in the control-plane
    service before the base drop, the base drop itself, and the absence tests. Keep the transition
    and the removal in different reviewed changes.

14. **Report the result as a transition, not a closure.** Do not mark the issue complete as if the
    SDK no longer exits the interpreter. State the base class, the window, and the follow-up
    issue number.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | -------------- |
| Plain `Exception` subclasses | Replaced `SystemExit` with ordinary `Exception` subclasses in one release | Broad `except Exception` recovery handlers in the supervisor would start to swallow refusals; the published contract documents `SystemExit` | Keep `SystemExit` as the base for one window; audit the broad handlers before the drop |
| Wrappers only at the entry point | Left the library raises alone and converted only at the CLI | Library and long-lived-process callers still cannot catch a typed error | Raise the typed error at the library boundary and convert only in the entry point |
| Converting the child-script raise | Replaced the `SystemExit` inside a generated `python -c` script | The string is not importable library code, and its `SystemExit` is the child's only failure channel | Classify child-script sources as an entry-point boundary; add a comment and record the deviation |
| Editing by planned line numbers | Used the site list from the approved plan | The plan predated the worktree head, and the site count had grown | Re-grep the symbol at the current head before each edit |
| Adding fields in the first change | Designed typed errors with structured attributes | A custom `__init__` that skips `super().__init__(message)` empties `args`/`code`, and caller code that reads `str(exc.code)` degrades silently | Start message-only and inherit `__init__`; assert `args` and `code` in a test |
| Same-release hard cutover | Ended the exception contract change when the code merged | The deprecation policy requires two releases plus a calendar window before a protected contract changes | Open the removal issue with the notices and the window dates before the merge |

## Results & Parameters

- **Transition base:** the typed root class subclasses `SystemExit`. Specific errors subclass the
  root; the credential family adds one intermediate base.
- **Site classes:** library boundary (convert), script entry point (convert there), child-script
  source (keep, comment).
- **Message contract:** byte-identical strings; inherited `__init__`, so `args == (message,)` and
  `code == message`.
- **Test contract:** one `pytest.raises(TypedError)` per converted site, one `issubclass(..., SystemExit)`
  test, one catch-path test, and one subprocess failure-path test for the entry point.
- **Verification used:** focused pytest for the touched modules, `ruff check`, `ruff format --check`,
  and the project type checker. A full-suite claim needs CI.

## Verified On

| Project | Context | Details |
| ------- | --------- | --------- |
| ProjectComet | Issue #2359, transition refactor of `SystemExit` control flow | SDK errors module, pool and internal-auth typed errors, contract tests, and onboarding docs. Local focused runs passed; the remaining local failures reproduce on the base commit because of host path and identity policy. |