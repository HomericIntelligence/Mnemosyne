---
name: cli-format-output-pola-silent-fallback
description: "When an audit flags a CLI utility for silently ignoring invalid format_type, the fix can be 'document + test the fallback' rather than raising ValueError — especially when callers depend on the fallback. Use when: (1) an audit flags POLA violation on silent fallback in format_output(), (2) deciding whether to raise ValueError vs document behavior, (3) writing tests to pin CLI format_type fallback behavior."
category: debugging
date: 2026-06-27
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: []
---

# CLI format_output POLA: Silent Fallback vs ValueError

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-27 |
| **Objective** | Fix POLA violation in `format_output()` where invalid `format_type` silently fell through to text formatting |
| **Outcome** | Successful — documented fallback behavior + added pinning tests; CI green |
| **Verification** | verified-ci |

## When to Use

- When an audit flags a function for silently ignoring invalid input (POLA violation)
- When deciding between raising `ValueError` vs documenting silent fallback in a CLI utility
- When writing tests to pin CLI `format_type` fallback behavior in `hephaestus/cli/utils.py`
- When a PR title says "raise ValueError" but the implementation keeps silent fallback — commit message must match actual behavior

## Verified Workflow

### Quick Reference

```python
# Option A — Document + test (preferred if callers depend on fallback)
# In docstring, explicitly state the fallback:
# "Any unrecognized format_type falls back to 'text' format rather than raising."

# Option B — Raise ValueError (preferred if callers should never pass invalid input)
valid = ("text", "json", "table")
if format_type not in valid:
    raise ValueError(f"Unknown format_type {format_type!r}. Expected one of {valid}")
```

```python
# Test pinning silent-fallback behavior (for Option A):
def test_invalid_format_falls_back_to_text():
    # hephaestus/cli/utils.py: format_output() — else branch falls through to text
    result = format_output({"key": "value"}, format_type="invalid")
    assert "key" in result  # text representation, not an exception

def test_table_format_on_dict_falls_back_to_text():
    # hephaestus/cli/utils.py: 'table' branch requires list/tuple; dict falls to else (text)
    result = format_output({"key": "value"}, format_type="table")
    assert "key" in result  # text fallback, not an exception
```

### Detailed Steps

1. Identify if callers depend on the silent fallback behavior (grep call sites for `format_type=`)
2. If callers pass arbitrary strings or rely on "text" as a safe default: **use Option A** (document + test)
3. If `format_type` only comes from validated sources (CLI argparse choices): **use Option B** (raise ValueError)
4. For `hephaestus/cli/utils.py` specifically: the actual branching logic is `if format_type == 'json': ... elif format_type == 'table' and isinstance(data, (list, tuple)): ... else: # text`
5. Update the docstring to describe exact fallback behavior including case-sensitivity (`"JSON"` != `"json"`)
6. Add non-vacuous test comments citing the specific code path and line numbers exercised

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Attempt 1 | Titled PR "raise ValueError" but implementation kept silent fallback | Misleading mismatch between PR title/body and actual code change; commit message must describe what actually changed | PR title and commit message MUST describe the actual behavior change, not the originally intended one |

## Results & Parameters

**hephaestus/cli/utils.py — format_output() branching logic (as of PR #1663)**:

```python
# Effective branching (simplified):
if format_type == 'json':
    # JSON output
elif format_type == 'table' and isinstance(data, (list, tuple)):
    # Table output
else:
    # Text fallback — reached for: unrecognized format_type, case mismatch ("JSON"),
    # or 'table' on non-sequence data (dict, str, etc.)
```

**Docstring pattern for documenting fallback behavior**:
```
Args:
    format_type: Output format. One of "text", "json", "table".
        Matching is case-sensitive ("JSON" != "json"). Unrecognized
        values and "table" applied to non-list/tuple data both fall
        back silently to text format.
```

**Test comment pattern** (explains which code path is exercised):
```python
# hephaestus/cli/utils.py: format_output() — else branch falls through to text
# when format_type is not 'json' and not ('table' on a sequence).
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1509, PR #1663 — fix(cli): raise ValueError on invalid format_type in format_output | CI green 2026-06-27 |
