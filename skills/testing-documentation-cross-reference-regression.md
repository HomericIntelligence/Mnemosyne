---
name: testing-documentation-cross-reference-regression
description: "Add regression tests to prevent documentation anchor drift when README/user docs link to other doc files. Use when: (1) README links to CONTRIBUTING or other files, (2) documentation anchors might be renamed, (3) creating cross-file doc references."
category: testing
date: 2026-06-05
version: "1.0.0"
verification: verified-local
tags: [documentation, regression-testing, anchor-drift]
---

# Documentation Cross-Reference Regression Tests

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-05 |
| **Objective** | Prevent silent documentation anchor drift when README links to CONTRIBUTING sections or other files |
| **Outcome** | Successful — 3 regression tests added and passing in PR #943 |
| **Verification** | verified-local |

## When to Use

- Creating cross-file documentation links (README → CONTRIBUTING, user docs → API docs)
- When documentation anchors are user-facing and might be renamed
- When a docs refactor could break existing links
- To validate that both halves of a cross-file link remain synchronized

## Verified Workflow

### Quick Reference

```python
# Test that target anchor exists
def test_contributing_has_platform_support_heading() -> None:
    text = CONTRIBUTING.read_text(encoding="utf-8")
    assert "### Platform Support" in text

# Test that source file contains the link
def test_readme_links_to_platform_support_section() -> None:
    text = README.read_text(encoding="utf-8")
    assert "CONTRIBUTING.md#platform-support" in text
```

### Detailed Steps

1. Identify cross-file documentation links in your repo (README → CONTRIBUTING, etc.)
2. For EACH link, create two test assertions:
   a. Target file contains the anchor/heading (e.g., `"### Platform Support"`)
   b. Source file contains the link text (e.g., `"CONTRIBUTING.md#platform-support"`)
3. Use TDD red-green cycle:
   - Run tests BEFORE writing docs (they must fail)
   - Apply documentation changes
   - Run tests again (they must pass)
4. Commit tests alongside docs

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| No regression tests for doc links | Manual anchor checks during code review | Anchors can be renamed later without updating links; creates silent drift | Add automated tests to catch renames |
| Test only source link, not target anchor | Check README contains link, skip checking if anchor exists | CONTRIBUTING.md anchor renamed → README link now points to missing anchor; user confusion | Test both halves: source link AND target anchor |

## Results & Parameters

**Applied in:** tests/unit/validation/test_readme_platform_support.py (PR #943)

**Test suite passes:** 3 tests, all passing:
- `test_contributing_has_platform_support_heading()` — validates target anchor exists
- `test_readme_links_to_platform_support_section()` — validates source link present
- `test_readme_flags_pixi_as_linux_only()` — validates context before pixi install command

**Coverage:** Prevents anchor drift with minimal test overhead; catches renames at CI time.
