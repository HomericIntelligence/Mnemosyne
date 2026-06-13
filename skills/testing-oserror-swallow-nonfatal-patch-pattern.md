---
name: testing-oserror-swallow-nonfatal-patch-pattern
description: "Use when: (1) you need to test that a function swallows OSError (file write failures, permission errors, disk-full conditions) without raising to the caller; (2) the code under test calls Path.write_text, open().write(), or similar and catches OSError internally; (3) you want to verify that a logging/state-capture helper is non-fatal when I/O fails; (4) you need to inject a file-system error via unittest.mock.patch with side_effect=OSError."
category: testing
date: 2026-06-12
version: "1.0.0"
user-invocable: false
tags:
  - pytest
  - patch
  - side_effect
  - OSError
  - nonfatal
  - swallow
  - write_text
  - pathlib
  - file-io
  - error-handling
  - test-pattern
  - mock
  - unittest-mock
  - python
  - unverified
---

# Testing OSError-Swallowing Code Paths (Non-Fatal Patch Pattern)

## Overview

When code swallows `OSError` internally (treating file-write failures, permission
errors, and disk-full conditions as non-fatal), the correct test pattern is to
inject a simulated `OSError` via `patch(..., side_effect=OSError(...))` and then
assert that the function returned normally — no exception propagated to the caller.

This pattern was identified during the planning phase for
ProjectHephaestus issue #1138 (adding tests for `capture_planner_learnings`).

**Verification level: unverified** — This documents a proposed workflow from a
planning session. The implementation has not been executed yet.

## When to Use

- The production code calls `Path.write_text(...)`, `open(path).write(...)`, or
  another I/O method inside a `try/except OSError` (or `except Exception`) block
  that logs and continues rather than re-raising.
- You want to assert the function is safe to call even when the filesystem is broken.
- The function is a "best-effort" helper (e.g., capturing diagnostics, writing
  metrics, saving a cache file) where the caller must not crash if I/O fails.

## Verified Workflow

> **NOTE: Unverified** — This workflow was derived from a planning session for
> ProjectHephaestus issue #1138. The implementation has not been executed yet.
> Treat as a proposed workflow until the pattern is confirmed by a passing test run.

### 1. Identify the import form in the target module

Before writing the patch path, open the target module and find the `Path` import:

```python
# Form A — most common
from pathlib import Path          # patch as "mypackage.mymodule.Path.write_text"

# Form B
import pathlib                    # patch as "pathlib.Path.write_text"

# Form C — aliased helper
from hephaestus.io import write_safely  # patch the helper directly
```

The patch path must match the name as the module sees it, not where it originates.

### 2. Write the test inside the existing test class

Place the test in the `TestXxx` class that already covers the function under test
(do not create a standalone function):

```python
from unittest.mock import patch

class TestCapturePlannerLearnings:
    def test_oswrite_failure_is_nonfatal(self):
        """File write failures must not propagate — OSError is swallowed silently."""
        with patch(
            "hephaestus.automation.planner_review_loop.Path.write_text",
            side_effect=OSError("disk full"),
        ):
            # Should not raise — completing the block is the assertion
            result = capture_planner_learnings(
                # ... pass whatever args the function requires ...
            )
        # Assert the function returned a normal (non-error) value
        assert result is not None
```

Adjust `"hephaestus.automation.planner_review_loop.Path.write_text"` to match:
- The actual module path of the file under test
- The actual method being patched (`write_text`, `write_bytes`, `open`, etc.)

### 3. What to assert

| Assertion | Why |
|---|---|
| Block completes without raise | Primary proof OSError was swallowed |
| `result is not None` | Function returned a normal sentinel, not an error value |
| `result != ERROR_SENTINEL` | If the function has an explicit error return |
| `mock_log_error.not_called()` | If the code is expected to fail *completely* silently |
| `mock_log_warning.called` | If the code is expected to log a warning on I/O failure |

Do NOT assert only on the return value if the function could silently return
`None` on both success and error — verify distinct paths where possible.

### 4. Optionally assert logging behaviour

If the production code logs the swallowed error, verify that too:

```python
from unittest.mock import patch, MagicMock

class TestCapturePlannerLearnings:
    def test_oswrite_failure_logs_warning(self):
        """File write failure should log a warning but not raise."""
        mock_log = MagicMock()
        with patch(
            "hephaestus.automation.planner_review_loop.Path.write_text",
            side_effect=OSError("disk full"),
        ), patch(
            "hephaestus.automation.planner_review_loop.log",
            mock_log,
        ):
            result = capture_planner_learnings(...)
        assert result is not None
        mock_log.warning.assert_called_once()
```

## Failed Attempts

None recorded yet (unverified — not yet executed).

## Results & Parameters

| Parameter | Value |
|---|---|
| Source issue | ProjectHephaestus #1138 |
| Verification | Unverified (planning session) |
| Python version | 3.10+ |
| Test framework | pytest + unittest.mock |
| Target function | `capture_planner_learnings` (hephaestus.automation.planner_review_loop) |

## Critical Risks / Uncertain Assumptions

1. **Patch path must be verified against the actual import line** — the path
   `"hephaestus.automation.planner_review_loop.Path.write_text"` is inferred
   from the standard `from pathlib import Path` import. If the module uses
   `import pathlib` instead, the patch path must be `"pathlib.Path.write_text"`.

2. **If `Path` is obtained via a helper import**, the patch path may point to
   that helper module, not `planner_review_loop`.

3. **The function may write via multiple I/O calls** — a single patch on
   `write_text` may not cover `open()` writes; check the full production code
   path before declaring coverage complete.

4. **Return value contract is unverified** — `assert result is not None` is
   based on the assumption the function returns a non-None value on success.
   Confirm the actual return type from the function signature before committing
   to this assertion.
