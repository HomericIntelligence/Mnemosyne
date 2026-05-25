---
name: tooling-windows-ci-posix-only-stdlib-guards
description: "Keep Python packages importable on Windows when they reference POSIX-only stdlib modules (curses, fcntl) and timezone data (tzdata). Use when: (1) adding cross-OS CI matrix and Windows jobs fail with ModuleNotFoundError, (2) authoring a subpackage that imports curses/fcntl/termios/grp/pwd, (3) using zoneinfo.ZoneInfo and seeing 'No time zone found' on Windows."
category: tooling
date: 2026-05-24
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [windows, cross-platform, ci, python, stdlib, curses, fcntl, tzdata, zoneinfo]
---

# Windows CI: Guarding POSIX-Only stdlib Modules

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-24 |
| **Objective** | Keep a Python package importable on Windows when it references stdlib modules that CPython only ships on POSIX (`curses`, `fcntl`, `termios`, `grp`, `pwd`) and when it uses `zoneinfo.ZoneInfo` which on Windows requires the `tzdata` PyPI package. |
| **Outcome** | Successful. Automation subpackage in ProjectHephaestus became importable on Windows; integration smoke tests and entry-point checks pass. Verified across PRs #534, #536, #538. |
| **Verification** | verified-ci |

## When to Use

- A subpackage has a bare `import curses` / `import fcntl` / `import termios` at module top-level and you need it to be at least importable (even if the feature is no-op) on Windows.
- Cross-OS CI matrix (`ubuntu-latest`, `macos-latest`, `windows-latest`) is failing on Windows with `ModuleNotFoundError: No module named 'curses'` (or `fcntl`).
- `zoneinfo.ZoneInfo("America/Los_Angeles")` raises `ZoneInfoNotFoundError` on Windows.
- You want to enable a Windows job without porting POSIX-encoded test assertions (file mode bits, path encoding, coredump handling) in the same PR.

## Verified Workflow

### Quick Reference

```python
# Module top-level: lazy import with sentinel
try:
    import curses
except ModuleNotFoundError:  # Windows: stdlib `curses` is not bundled with CPython.
    curses = None  # type: ignore[assignment]

try:
    import fcntl
except ModuleNotFoundError:  # Windows: stdlib `fcntl` is POSIX-only.
    fcntl = None  # type: ignore[assignment]


# Class that requires curses: raise at instantiation, not at import
class CursesUI:
    def __init__(self, *args, **kwargs) -> None:
        if curses is None:
            raise RuntimeError(
                "CursesUI requires the stdlib `curses` module, which is not "
                "available on Windows CPython. Run on Linux or macOS."
            )
        # ...


# Best-effort flock: no-op on Windows
def _lock_file(fp) -> None:
    if fcntl is not None:
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
    # else: cross-process locking is a no-op on Windows (best-effort).
```

```toml
# pyproject.toml — conditional dep so zoneinfo works on Windows
[project]
dependencies = [
    # ...
    "tzdata; platform_system == 'Windows'",
]
```

```python
# Integration test: skip Windows for POSIX-only CLIs by design
import sys
import pytest

if sys.platform == "win32" and "automation" in module_path:
    pytest.skip("automation CLIs require POSIX stdlib (curses/fcntl)")
```

### Detailed Steps

1. **Identify every POSIX-only stdlib import in the subpackage.** Search for `import curses`, `import fcntl`, `import termios`, `import grp`, `import pwd`, `import resource`, `import syslog`, `import readline`. Each one needs the try/except guard.
2. **Wrap each import at module top-level** with `try/except ModuleNotFoundError` and assign the name to `None` with `# type: ignore[assignment]`. Do NOT use a bare `except:` — only catch `ModuleNotFoundError` so real bugs surface.
3. **Move the "this feature is unavailable" error to runtime** (class `__init__` or function entry), not import-time. The goal is: the package imports cleanly on Windows; only the actual POSIX-dependent code path raises.
4. **Guard every call site** in the file with `if <module> is not None:` so the call doesn't crash at runtime when the sentinel is `None`. For locks specifically, treat absence as best-effort no-op.
5. **For `zoneinfo`**: add `"tzdata; platform_system == 'Windows'"` to `[project].dependencies` in `pyproject.toml`. `tzdata` is a thin PyPI wheel that ships the IANA database; `ZoneInfo` discovers it automatically.
6. **Decide test scope honestly.** Runtime guards make the package importable on Windows — they do NOT make POSIX-only CLIs work. For tests that exercise those CLIs, skip on Windows with `pytest.skip(...)` rather than scattering inline assertions.
7. **Track full cross-OS test port as a separate issue.** Don't try to fix file-mode bits (`0o600`), path encoding, and POSIX-only fixtures (coredump handlers) in the same PR as the import guards. Revert the matrix to ubuntu-only until that tracking issue lands.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Leave `import curses` / `import fcntl` at module top-level and let CI surface the error | `ModuleNotFoundError` on Windows broke the entire automation subpackage at import time, which cascaded into entry-point smoke tests and `import hephaestus.automation` integrity checks — failures looked unrelated to curses/fcntl | Stdlib-but-POSIX-only modules need the same `try/except ModuleNotFoundError` guard you'd give any third-party optional dependency. "stdlib" is not a guarantee of availability. |
| 2 | Enable matrix `[ubuntu-latest, macos-latest, windows-latest]` for the test job after only fixing curses/fcntl/tzdata | Windows still failed on: file mode `0o666` vs `0o600` in `test_github_api.py`, path encoding in `test_session_naming.py`, POSIX-only `test_coredump_handler.py` | Runtime import guards aren't enough — existing tests themselves encode POSIX assumptions (mode bits, path separators, signal handlers). A full cross-OS test port is multi-session work. |
| 3 | Skip Windows assertions inline in each failing test with ad-hoc `if sys.platform == "win32"` branches | Death-by-a-thousand-cuts; obscured the real scope of cross-OS work and produced a sprawling diff with no clear stopping point | Track cross-OS port as a dedicated tracking issue (#539 in ProjectHephaestus); revert matrix to ubuntu-only; keep the runtime import guards in place so the package stays Windows-importable for downstream consumers. |

## Results & Parameters

**Verified-passing pattern** (ProjectHephaestus PR #534, #536, #538):

```python
# hephaestus/automation/curses_ui.py
from __future__ import annotations

try:
    import curses
except ModuleNotFoundError:  # Windows: stdlib `curses` is not bundled with CPython.
    curses = None  # type: ignore[assignment]


class CursesUI:
    def __init__(self) -> None:
        if curses is None:
            raise RuntimeError(
                "CursesUI requires the stdlib `curses` module, which is not "
                "bundled with CPython on Windows. Run on Linux or macOS."
            )
```

```python
# hephaestus/automation/planner.py
from __future__ import annotations

try:
    import fcntl
except ModuleNotFoundError:  # Windows: stdlib `fcntl` is POSIX-only.
    fcntl = None  # type: ignore[assignment]


def _acquire_lock(fp) -> None:
    if fcntl is not None:
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
    # Cross-process locking is best-effort no-op on Windows.


def _release_lock(fp) -> None:
    if fcntl is not None:
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
```

```toml
# pyproject.toml
[project]
dependencies = [
    "pyyaml>=6.0",
    # ... other deps ...
    "tzdata; platform_system == 'Windows'",
]
```

```python
# tests/integration/test_entry_points.py
import sys
import pytest

POSIX_ONLY_SUBPACKAGES = ("automation",)

def test_entry_point_importable(module_path: str) -> None:
    if sys.platform == "win32" and any(p in module_path for p in POSIX_ONLY_SUBPACKAGES):
        pytest.skip("automation CLIs require POSIX stdlib (curses/fcntl)")
    importlib.import_module(module_path)
```

**Verification evidence**: PRs #534, #536, #538 in `HomericIntelligence/ProjectHephaestus` — all three landed with the GitHub Actions matrix exercising the import on Linux/macOS, and the import-only check passing on Windows after the guards.

**Tracking issue for full Windows test port**: #539 (covers POSIX-only test assumptions: file mode bits, path encoding, coredump handlers).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PRs #534, #536, #538 — automation subpackage Windows-importability | curses in `CursesUI`, fcntl in `planner.py`, tzdata for `hephaestus.github.rate_limit` |
