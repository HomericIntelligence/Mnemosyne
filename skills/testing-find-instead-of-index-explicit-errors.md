---
name: testing-find-instead-of-index-explicit-errors
description: "Use str.find() + explicit assertions instead of str.index() in tests to produce clear error messages instead of confusing ValueError tracebacks. Use when: (1) test assertions depend on finding substrings, (2) test failures should be self-explanatory, (3) substring position might change."
category: testing
date: 2026-06-05
version: "1.0.0"
verification: verified-local
tags: [test-clarity, error-messages, string-search]
---

# Use str.find() Instead of str.index() for Graceful Test Errors

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-05 |
| **Objective** | Produce clear assertion errors instead of confusing ValueError tracebacks when test assertions depend on finding substrings |
| **Outcome** | Successful — applied in PR #943 review feedback and verified |
| **Verification** | verified-local |

## When to Use

- Tests that search for substrings and assert they exist
- When test failures should produce actionable error messages
- When substring position might change (renamed functions, moved code blocks)
- Any scenario where `text.index()` would raise ValueError

## Verified Workflow

### Quick Reference

**Don't use index():**
```python
pixi_install_pos = text.index("pixi install", start_pos)  # Raises ValueError
```

**Do use find() + explicit assertion:**
```python
pixi_install_pos = text.find("pixi install", start_pos)
assert pixi_install_pos != -1, (
    "README must contain 'pixi install' command in the Getting Started section"
)
```

### Detailed Steps

1. Replace `text.index(substring, start)` with `text.find(substring, start)`
2. Assert the result is not -1 (find returns -1 when not found)
3. Include an explicit error message explaining what's missing
4. The error message becomes the assertion failure output

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Use str.index() | `text.index("pixi install")` | Raises ValueError with confusing stack trace if string moves or is renamed; no context on what's expected | Use find() + explicit assertion |
| No error message | `assert text.find() != -1` | Fails with bare assertion error; no indication of what's missing | Always add descriptive assertion message |

## Results & Parameters

**Applied in:** tests/unit/validation/test_readme_platform_support.py (PR #943, updated in review feedback)

**Before:**
```python
pixi_install_pos = text.index("pixi install", pixi_section_start)
```

**After:**
```python
pixi_install_pos = text.find("pixi install", pixi_section_start)
assert pixi_install_pos != -1, (
    "README must contain 'pixi install' command in the Getting Started section"
)
```

**Benefit:** Test failures now show the assertion message instead of a ValueError traceback; engineers immediately understand what's expected.
