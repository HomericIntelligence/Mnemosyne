---
name: logging-handler-registry-deduplication
description: "Fix Python logging duplicate handlers on repeated calls. Use when: (1) get_logger() adds duplicate StreamHandlers, (2) setup_logging() accumulates handlers, (3) basicConfig force=True for root logger idempotency, (4) file handler silently skipped on second call."
category: debugging
date: 2026-03-25
version: "3.0.0"
user-invocable: false
verification: verified-local
history: logging-handler-registry-deduplication.history
tags:
  - python
  - logging
  - deduplication
  - handlers
  - basicConfig
---

# Logging Handler Registry Deduplication

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-03-25 |
| **Objective** | Fix duplicate handler accumulation in both `get_logger()` and `setup_logging()` when called multiple times |
| **Outcome** | Successful — three verified approaches: module-level registry (v1), isinstance-based inspection (v2), and `basicConfig(force=True)` for root logger (v3) |
| **Verification** | verified-local |
| **History** | [changelog](./logging-handler-registry-deduplication.history) |

## When to Use

- `get_logger("name")` called multiple times produces duplicate log lines (one per call)
- `setup_logging()` called multiple times accumulates duplicate handlers on root logger
- `if not logger.handlers` guard prevents adding a file handler on a subsequent call
- Parent logger propagation causes double output (e.g., root logger + child logger both emit)
- Need to track which specific handlers have been configured per logger name
- Factory function wraps `logging.getLogger()` and needs idempotent handler setup
- `logging.basicConfig()` called without `force=True` is a no-op after first call (but separate `addHandler()` calls still accumulate)

## Verified Workflow

Three approaches are verified. Choose based on which logger API you're fixing.

### Approach A: isinstance-based handler inspection (for named loggers)

Inspect `logger.handlers` directly with type checks. No module-level registry needed.

#### Quick Reference

```python
import os

def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)

    # Console: only add if no StreamHandler (non-FileHandler) exists
    # IMPORTANT: FileHandler is a subclass of StreamHandler, so exclude it
    has_console = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in logger.handlers
    )
    if not has_console:
        logger.addHandler(logging.StreamHandler(sys.stdout))

    # File: only add if no FileHandler for this resolved path exists
    if log_file:
        resolved = os.path.abspath(log_file)
        has_file = any(
            isinstance(h, logging.FileHandler) and h.baseFilename == resolved
            for h in logger.handlers
        )
        if not has_file:
            logger.addHandler(logging.FileHandler(log_file))

    return logger
```

**Key gotcha**: `logging.FileHandler` is a subclass of `logging.StreamHandler`. The console handler check must use `and not isinstance(h, logging.FileHandler)` to avoid counting file handlers as console handlers.

### Approach B: Module-level registry (more explicit, handles custom handler types)

#### Quick Reference

```python
# Module-level registry — tracks handler keys per logger name
_configured_loggers: dict[str, set[str]] = {}

def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    configured = _configured_loggers.setdefault(name, set())

    if "console" not in configured:
        logger.addHandler(logging.StreamHandler(sys.stdout))
        configured.add("console")

    if log_file and log_file not in configured:
        logger.addHandler(logging.FileHandler(log_file))
        configured.add(log_file)

    logger.propagate = False
    return logger
```

### Approach C: `basicConfig(force=True)` (for root logger / `setup_logging()`)

Use when configuring the **root logger** via `logging.basicConfig()`. The `force=True` parameter (Python 3.8+) clears all existing root handlers before adding new ones, making repeated calls idempotent.

#### Quick Reference

```python
def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    format_string: str | None = None,
    log_to_stderr: bool = False,
) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_to_stderr:
        handlers.append(logging.StreamHandler(sys.stderr))

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    # force=True clears existing root handlers before adding new ones
    logging.basicConfig(level=level, format=format_string, handlers=handlers, force=True)
```

**Key insight**: Without `force=True`, `basicConfig()` is a no-op if the root logger already has handlers. But handlers added via `addHandler()` *outside* of `basicConfig()` still accumulate on each call. Moving all handler creation (including `FileHandler`) into the `handlers` list and using `force=True` solves both problems in one shot.

### Detailed Steps (all approaches)

1. **Replace `if not logger.handlers` with per-handler-type checks** (Approaches A/B) or **use `force=True`** (Approach C) — The naive guard fails because:
   - It's all-or-nothing: if handlers exist, no new ones can be added
   - It doesn't distinguish handler types (console vs file)
   - Python's logging hierarchy means `logger.handlers` can be empty while parent handles output

2. **Check each handler type independently** (A/B):
   - Console: only add if no console StreamHandler exists
   - File: only add if no FileHandler for the same resolved path exists

3. **Compare file paths using resolved absolute paths** — `FileHandler.baseFilename` stores the absolute path, so compare against `os.path.abspath(log_file)` to handle relative vs absolute equivalence

4. **Always update level** — Call `logger.setLevel()` on every invocation so subsequent calls with a different level take effect

5. **Consider `logger.propagate = False`** — Prevents parent loggers (especially root) from duplicating messages that child loggers already handle

### When to prefer each approach

| Criterion | Approach A (isinstance) | Approach B (registry) | Approach C (force=True) |
|-----------|------------------------|----------------------|------------------------|
| Target | Named loggers | Named loggers | Root logger |
| External state | None | Module-level dict | None |
| Test cleanup | No cleanup needed | Must clear registry between tests | Save/restore root handlers |
| Custom handler types | Requires isinstance checks for each type | Just add a string key | N/A (replaces all) |
| Incremental handlers | Yes (add file handler later) | Yes | No (replaces all each time) |
| Simplicity | Moderate | More complex | Simplest |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| `if not logger.handlers` guard | Check if logger already has any handlers before adding | All-or-nothing: blocks adding file handler on second call; doesn't prevent duplicates if handlers are removed and re-added | Track handler types individually, not just presence/absence |
| Check `type(h)` without attribute inspection | Inspect `type(h)` for existing handlers | Doesn't distinguish between two different file paths; would need to inspect `baseFilename` attribute | Must compare `baseFilename` (absolute path) to deduplicate file handlers |
| Rely on `propagate=True` (default) | Let parent loggers handle output | Parent + child both emit when both have handlers, causing duplicate lines | Set `propagate=False` on any logger that has its own handlers |
| isinstance check without FileHandler exclusion | Check `isinstance(h, logging.StreamHandler)` for console detection | FileHandler is a subclass of StreamHandler, so file handlers are counted as console handlers, preventing console handler from being added | Always use `isinstance(h, StreamHandler) and not isinstance(h, FileHandler)` for console detection |
| `basicConfig()` without `force=True` + separate `addHandler()` | Call `basicConfig()` for console, then `addHandler()` for file handler separately | `basicConfig()` is a no-op after first call, but `addHandler()` always appends — so file handlers accumulate on repeated calls while console handlers don't | Move all handlers into the `handlers` list and use `force=True` to clear-and-replace atomically |

## Results & Parameters

### Key behavior after fix

```python
# get_logger() — repeated calls, no duplicate handlers
logger1 = get_logger("app")           # 1 StreamHandler
logger2 = get_logger("app")           # Still 1 StreamHandler

# get_logger() — incremental handler addition works
logger3 = get_logger("app", log_file="app.log")  # 1 StreamHandler + 1 FileHandler

# get_logger() — same file path doesn't duplicate
logger4 = get_logger("app", log_file="app.log")  # Still 1 StreamHandler + 1 FileHandler

# setup_logging() — repeated calls, no duplicate handlers
setup_logging(log_file="app.log")   # 1 StreamHandler + 1 FileHandler
setup_logging(log_file="app.log")   # Still 1 StreamHandler + 1 FileHandler

# setup_logging() — log message appears exactly once
root.warning("test")  # One line in file, not two
```

### Test pattern for setup_logging() idempotency

```python
def test_idempotent_handler_count() -> None:
    root = logging.getLogger()
    saved = list(root.handlers)
    root.handlers.clear()
    try:
        setup_logging(level=logging.INFO)
        count_first = len(root.handlers)
        setup_logging(level=logging.INFO)
        count_second = len(root.handlers)
        assert count_first == count_second
    finally:
        root.handlers.clear()
        root.handlers.extend(saved)
```

### Environment

- Python 3.8+ (for `force=True` in `basicConfig`)
- Standard library `logging` module
- Works with `LoggerAdapter` wrappers (e.g., `ContextLogger`)

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #32 — PR #70 | Fixed duplicate console handlers with registry approach, 389 tests pass |
| ProjectHephaestus | Issue #54 — PR #98 | Fixed file handler silently dropped on subsequent calls with isinstance approach, 438 tests pass |
| ProjectHephaestus | Issue #59 — PR #119 | Fixed setup_logging() duplicate handlers with basicConfig(force=True), 16 logging tests pass |
