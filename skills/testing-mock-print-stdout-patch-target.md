---
name: testing-mock-print-stdout-patch-target
description: "Python's built-in print() resolves sys.stdout from the live sys/builtins module at CALL TIME, so @patch('mypkg.mymod.sys.stdout') does NOT intercept a bare print() inside that module — the write mock stays empty and the assertion passes vacuously (false green). Subtly, the SAME patch DOES intercept mymod.sys.stdout.isatty(). Use when: (1) writing a unit test that mocks stdout/stderr, (2) asserting on captured print() output, (3) a stdout-mock test passes but doesn't actually verify anything."
category: testing
date: 2026-06-14
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - python
  - testing
  - mock
  - patch
  - stdout
  - print
  - pytest
  - unittest-mock
  - false-green
  - sys-stdout
---

# Testing: Mock the Right Target for print() / sys.stdout

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-14 |
| **Objective** | Stop a stdout-mocking unit test from passing vacuously against a bare `print()` |
| **Outcome** | Pitfall identified; fix = route production output through `sys.stdout.write()` so the test's patch genuinely intercepts it |
| **Verification** | verified-local — Python's name-resolution semantics are well-established and trivially reproducible, but THIS fix has not yet been run through CI for ProjectHephaestus issue #1330 (still at the planning stage). Caught at plan-review (NOGO); fix not yet CI-validated for #1330. |
| **History** | n/a (initial version) |

## When to Use

- Writing a unit test that mocks `stdout`/`stderr` to capture program output
- Asserting on captured `print()` output (e.g. `"".join(c.args[0] for c in mock_stdout.write.call_args_list)`)
- A stdout-mock test is green but you suspect it is not actually verifying anything (the write mock has zero calls)
- Reviewing a plan/PR whose test mocks `module.sys.stdout` while the production code uses a bare `print()`
- A test that mixes an `isatty()` branch check with an output-capture check and only half of it seems to work

## Verified Workflow

### Quick Reference

```python
# ─────────────────────────────────────────────────────────────────────────
# THE PITFALL: bare print() inside mymod, patched at the module-local sys
# ─────────────────────────────────────────────────────────────────────────
# mypkg/mymod.py
import sys
def render():
    if sys.stdout.isatty():       # reads the PATCHED attribute → intercepted OK
        ...
    print("hello world")          # resolves sys.stdout from the LIVE sys at
                                  # call time → NOT intercepted by the patch below

# test (BROKEN — vacuous green):
@patch("mypkg.mymod.sys.stdout")
def test_render(mock_stdout):
    render()
    out = "".join(c.args[0] for c in mock_stdout.write.call_args_list)
    assert "hello world" in out   # out == "" → fails spuriously OR passes vacuously

# ─────────────────────────────────────────────────────────────────────────
# FIX OPTIONS (in order of preference)
# ─────────────────────────────────────────────────────────────────────────

# FIX 1 (PREFERRED): route production output through sys.stdout.write()+flush().
# Now BOTH the isatty() check and the writes go through the same patched ref.
# mypkg/mymod.py
def render():
    if sys.stdout.isatty():
        ...
    sys.stdout.write("hello world\n")
    sys.stdout.flush()
# test stays exactly as above and now genuinely intercepts the writes.

# FIX 2: keep bare print(), patch builtins.print directly
@patch("builtins.print")
def test_render(mock_print):
    render()
    mock_print.assert_any_call("hello world")

# FIX 3: patch the GLOBAL sys.stdout (no module prefix). Works because print
# resolves sys.stdout from the live sys module — but it is blunter and can
# collide with the test runner's own output capture (pytest capsys/capfd).
@patch("sys.stdout")
def test_render(mock_stdout):
    ...
```

### Detailed Steps

1. **Identify where the name is looked up, not where it is defined.** `print()` is a
   builtin; it reads `sys.stdout` from the live `sys` module each call. It never
   consults the `sys` name your module imported, so a patch on `mypkg.mymod.sys.stdout`
   cannot see it.
2. **Understand the subtle asymmetry.** `@patch("mypkg.mymod.sys.stdout")` *does*
   correctly intercept `mypkg.mymod.sys.stdout.isatty()` — because that call reads the
   patched attribute through the module's own `sys` name. So a test that selects a
   branch via `isatty()` AND captures output via `print()` will have its branch-selection
   half work while its output-capture half silently does nothing. This is why the bug
   hides: half the test "works."
3. **Prefer Fix 1.** Change the production code to `sys.stdout.write(...)` (+ `flush()`).
   Then the test's existing `@patch("mypkg.mymod.sys.stdout")` intercepts both the
   `isatty()` check and the writes through one reference, and the assertion verifies
   real behavior. This is the option chosen for ProjectHephaestus #1330.
4. **Otherwise patch where the lookup actually happens** — `builtins.print` (Fix 2) or
   the global `sys.stdout` (Fix 3).
5. **Never trust a `mock_stdout.write` assertion against a bare `print()`.** If the
   write mock's `call_args_list` is empty, the join is `""` and `"x" in ""` is `False`
   (spurious failure) or, if you assert non-membership / emptiness, it passes vacuously.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | `@patch("module.sys.stdout")` (or `mock.patch.object(module.sys, "stdout", ...)`) while the code under test emits via a bare `print()` | `print()` resolves `sys.stdout` from the live `sys`/`builtins` at call time, not through the module's imported `sys` name, so the write mock's `call_args_list` stays empty; the assertion is vacuous (false green) | `@patch('module.sys.stdout') + bare print() → write mock empty, assertion vacuous → patch builtins.print or route through sys.stdout.write()` |
| 2 | Assumed that because the same `@patch("module.sys.stdout")` correctly drove the `isatty()` branch, it must also be capturing the printed output | `isatty()` reads the patched attribute through the module's `sys` name (intercepted), but `print()` reads `sys.stdout` from the live module (not intercepted) — the asymmetry masked the bug | Half a test "working" (branch selection via `isatty()`) does not prove the output-capture half works; verify the write mock actually received calls |
| 3 | Considered patching the global `@patch("sys.stdout")` as the default to keep bare `print()` | It works, but it is broad/blunt and can interfere with the test runner's own stdout capture (pytest `capsys`/`capfd`) | Prefer routing production code through `sys.stdout.write()` so the narrow module-local patch is sufficient; reserve global stdout patching for cases that must keep bare `print()` |

## Results & Parameters

**General principle:** patch where the name is **looked up**, not where it is defined.
For stdlib functions like `print()` the lookup target is the live `sys`/`builtins`,
not your module's imported `sys`. When a test mocks output, force the production code
to route through the SAME reference the test patches — otherwise the assertion is theater.

Minimal reproducible contrast:

```python
# ── BROKEN: false-green test ────────────────────────────────────────────
# mypkg/report.py
import sys

def emit(line: str) -> None:
    if sys.stdout.isatty():
        line = f"\033[1m{line}\033[0m"   # bold only on a tty
    print(line)                          # NOT intercepted by module-local patch


# tests/test_report.py
from unittest.mock import patch
from mypkg import report

@patch("mypkg.report.sys.stdout")
def test_emit(mock_stdout):
    mock_stdout.isatty.return_value = False
    report.emit("done")
    captured = "".join(c.args[0] for c in mock_stdout.write.call_args_list)
    assert "done" in captured   # captured == ""  → FALSE GREEN / spurious fail


# ── FIXED (preferred): route through sys.stdout.write() ──────────────────
# mypkg/report.py
import sys

def emit(line: str) -> None:
    if sys.stdout.isatty():
        line = f"\033[1m{line}\033[0m"
    sys.stdout.write(line + "\n")        # intercepted by the module-local patch
    sys.stdout.flush()


# tests/test_report.py  — unchanged, now genuinely verifies behavior
@patch("mypkg.report.sys.stdout")
def test_emit(mock_stdout):
    mock_stdout.isatty.return_value = False
    report.emit("done")
    captured = "".join(c.args[0] for c in mock_stdout.write.call_args_list)
    assert "done" in captured   # captured == "done\n"  → REAL assertion passes
```

Expected outcomes:

- Broken version: `mock_stdout.write.call_args_list == []`, `captured == ""`; the
  membership assertion fails spuriously, or an emptiness/non-membership assertion
  passes without guarding anything.
- Fixed version: `mock_stdout.write.call_args_list` contains the `"done\n"` call;
  `isatty()` branch selection and output capture both flow through the one patched
  reference; the assertion guards real behavior.

**Applicability note:** Caught at the plan-review stage (reviewer NOGO) for
ProjectHephaestus issue #1330 before any code shipped. Fix 1 was selected for #1330 but
has not yet been run through CI for that issue — hence `verification: verified-local`.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1330 — plan review caught a stdout-mock test that would have passed vacuously against a bare `print()`; chose Fix 1 (route through `sys.stdout.write()`) | Fix not yet CI-validated for #1330 (planning stage) |
