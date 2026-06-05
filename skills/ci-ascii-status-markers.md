---
name: ci-ascii-status-markers
description: "Use ASCII-friendly status markers ([PASS]/[FAIL]) instead of emoji in machine-readable output for cross-platform compatibility and CI reliability."
category: ci-cd
date: 2026-06-05
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
---

# CI ASCII Status Markers

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-05 |
| **Objective** | Replace non-ASCII emoji status icons with ASCII-friendly markers in pre-commit benchmark output and similar CI tools |
| **Outcome** | Successful — all tests pass without modification; output remains clear and readable |
| **Verification** | verified-local |

## When to Use

- When outputting status in machine-readable formats (CI logs, Markdown tables, console output)
- When cross-platform terminal compatibility is required
- When accessibility is a concern (screen readers, non-Unicode terminals)
- When emoji rendering is unreliable in CI environments
- When aligning with project "no emoji unless requested" conventions

## Verified Workflow

### Quick Reference

**Before:**
```python
status_icon = "✅" if hook_status == "passed" else "❌"
# Output: | Hook status | ✅ passed |
```

**After:**
```python
status_icon = "[PASS]" if hook_status == "passed" else "[FAIL]"
# Output: | Hook status | [PASS] passed |
```

### Detailed Steps

1. Locate status icon assignments in your output formatting code
2. Identify emoji characters (✅, ❌, 🔴, 🟢, etc.)
3. Replace with ASCII bracketed markers:
   - `✅` → `[PASS]` or `[OK]`
   - `❌` → `[FAIL]` or `[ERROR]`
   - `🔴` → `[FAIL]` or `[STOP]`
   - `🟢` → `[OK]` or `[PASS]`
4. Test output rendering in Markdown tables and CI logs
5. Verify no tests break (emoji-specific assertions should not exist)
6. Confirm output is readable in all target environments

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Using emoji (✅/❌) | Render emoji status icons in pre-commit benchmark Markdown table | Emoji rendering unreliable in CI log parsers; accessibility tools struggle with emoji-only content; non-Unicode terminals render as replacement characters | ASCII markers ([PASS]/[FAIL]) are universally compatible, machine-readable, and align with project conventions |

## Results & Parameters

**Example Output — Before:**
```markdown
## Pre-commit Hook Benchmark

| Metric | Value |
|--------|-------|
| Hook status | ✅ passed |
| Elapsed time | 45s |
| Files processed | 300 |
```

**Example Output — After:**
```markdown
## Pre-commit Hook Benchmark

| Metric | Value |
|--------|-------|
| Hook status | [PASS] passed |
| Elapsed time | 45s |
| Files processed | 300 |
```

**Key Parameters:**
- Marker style: `[PASS]` / `[FAIL]` (uppercase, bracketed)
- Alternative styles: `PASS`/`FAIL` (simpler), `OK`/`ERROR` (semantic)
- Works in: Markdown tables, console output, CI logs, terminal multiplexers

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #793, PR #978 | Single-line fix in hephaestus/ci/precommit.py:68; all 43 tests pass locally |
