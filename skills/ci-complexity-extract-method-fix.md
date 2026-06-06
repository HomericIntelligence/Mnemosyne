---
name: ci-complexity-extract-method-fix
description: "Fix C901 cyclomatic complexity CI failures by extracting helper functions. Use when: (1) pre-commit or CI fails with 'is too complex (N > 10)', (2) adding conditional blocks to an existing function pushes it over the CC limit, (3) multiple rendering/processing passes can be isolated."
category: ci-cd
date: 2026-06-06
version: "1.1.0"
user-invocable: false
tags:
  - pre-commit
  - complexity
  - refactoring
  - ruff
  - C901
  - method-extraction
  - rendering-passes
---

# Fix C901 Cyclomatic Complexity CI Failures

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-03-25 |
| **Objective** | Fix CI pre-commit failure where adding new conditional blocks to `_restore_run_context()` pushed cyclomatic complexity from ~8 to 11, exceeding the C901 limit of 10 |
| **Outcome** | Successful — extracted two helper functions, CC dropped below 10, all CI checks pass |

## When to Use

- CI fails with `C901 _function_name is too complex (N > 10)`
- Adding new `if`/`else` blocks to an existing function that is near the complexity limit
- Pre-commit hook "Check Cyclomatic Complexity" fails
- Ruff reports C901 violations

## Verified Workflow

### Quick Reference

```python
# BEFORE: All logic inline (CC=11)
def _restore_run_context(ctx, current_state):
    # ... agent restore (CC +3) ...
    # ... judge_prompt restore (CC +2) ...
    # ... judgment restore (CC +3) ...    <-- NEW
    # ... run_result restore (CC +3) ...   <-- NEW

# AFTER: Extract new blocks into helpers (CC=7)
def _restore_run_context(ctx, current_state):
    # ... agent restore (CC +3) ...
    # ... judge_prompt restore (CC +2) ...
    if condition:
        _restore_judgment(ctx)       # CC counted in helper
    if condition:
        _restore_run_result(ctx)     # CC counted in helper

def _restore_judgment(ctx):          # CC=3 (separate function)
    ...

def _restore_run_result(ctx, state): # CC=2 (separate function)
    ...
```

### Detailed Steps

1. **Identify the violation**: CI error shows function name and CC score (e.g., `_restore_run_context is too complex (11 > 10)`)

2. **Count branches**: Each `if`, `elif`, `else`, `for`, `while`, `except`, `and`, `or` adds +1 CC. The function starts at CC=1.

3. **Extract self-contained blocks**: Look for conditional blocks that:
   - Have their own imports
   - Operate on a clear subset of parameters
   - Don't share mutable state with surrounding code beyond `ctx`

4. **Create module-level helpers**: Place extracted functions near the original, with clear docstrings. Keep the same parameters — don't over-abstract.

5. **Verify locally**:
   ```bash
   pre-commit run --all-files  # Check both ruff C901 and custom CC hook
   pixi run python -m pytest tests/unit/e2e/ -x -q  # Ensure no regressions
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Inline all restore logic in one function | Added judgment + run_result restore as new `if` blocks in `_restore_run_context()` | CC went from ~8 to 11, exceeding C901 limit of 10 | Always check CC budget before adding conditional blocks to existing functions near the limit |
| Using `# noqa: C901` suppression | Considered suppressing the warning | ProjectScylla prohibits `--no-verify` and suppression of lint rules | Extract-method is the correct fix, not suppression |

## Results & Parameters

### CC Budget Rule of Thumb

| CC Score | Status | Action |
| ---------- | -------- | -------- |
| 1-7 | Safe | Can add 1-3 branches freely |
| 8-9 | Warning zone | One more `if/else` block hits the limit |
| 10 | At limit | Any new branch will fail CI |
| 11+ | CI failure | Must extract helpers |

### ProjectScylla CC Configuration

- **Ruff C901**: `max-complexity = 10` (in `pyproject.toml` or `.pre-commit-config.yaml`)
- **Custom hook**: `Check Cyclomatic Complexity` — runs separately from ruff, same threshold
- Both must pass for CI green

### Extract-Method Pattern

```python
# Pattern: delegate to helper, keep guard clause in parent
if is_at_or_past_state(run_state, RunState.JUDGE_COMPLETE) and ctx.judgment is None:
    _restore_judgment(ctx)  # All branching logic moves here

# Helper gets its own CC budget (starts at 1)
def _restore_judgment(ctx: Any) -> None:
    """Restore ctx.judgment from on-disk judge result."""
    from scylla.e2e.judge_runner import _has_valid_judge_result, _load_judge_result
    judge_dir = get_judge_dir(ctx.run_dir)
    if _has_valid_judge_result(ctx.run_dir):
        ctx.judgment = _load_judge_result(judge_dir)
        # ... timing loading ...
```

## Multi-Pass Rendering Pattern (ProjectHephaestus Issue #804)

**New Pattern**: Extract multiple sequential rendering/processing passes into instance methods with **return-value threading** to avoid mutable state.

### When This Pattern Applies

- Method has multiple sequential rendering passes (workers → separator → logs)
- Each pass computes state (e.g., row offsets) that feeds the next pass
- Method exceeds CC limit due to pass complexity + conditional branches

### Quick Reference

```python
# BEFORE: All 69 lines inline (CC too high, noqa: C901)
def _refresh_display(self, screen, height, width):
    """Monolithic display refresh with three rendering passes."""
    # ... workers rendering (5-7 branches) ...
    # ... separator rendering (3-4 branches) ...
    ... logs rendering (4-5 branches) ...

# AFTER: Extract passes as instance methods (each ~20-25 lines, CC <10)
def _refresh_display(self, screen, height, width):
    """Orchestrate three rendering passes."""
    start_row = 0
    start_row = self._draw_workers(start_row, height, width)
    start_row = self._draw_separator(start_row, height, width)
    start_row = self._draw_logs(start_row, height, width)

def _draw_workers(self, start_row: int, height: int, width: int) -> int:
    """Render worker status. Returns next free row."""
    # ... worker logic ...
    return next_row

def _draw_separator(self, start_row: int, height: int, width: int) -> int:
    """Render separator line. Returns next free row."""
    # ... separator logic ...
    return next_row

def _draw_logs(self, start_row: int, height: int, width: int) -> int:
    """Render log output. Returns next free row."""
    # ... logs logic ...
    return next_row
```

### Key Principles

1. **Return-value threading**: Each helper takes `(start_row, height, width)` and returns the next free row
2. **No mutable state**: Helpers don't modify shared state beyond their immediate scope
3. **Instance methods**: Use `self` to access class state (e.g., workers, logs buffers)
4. **Single responsibility**: Each method owns one rendering pass
5. **Test independently**: Unit test each helper for boundary handling and return values

### Test Structure

```python
def test_draw_workers_returns_next_row(self):
    """Test return value threading."""
    rows = self.display._draw_workers(start_row=0, height=10, width=80)
    assert rows > 0
    assert rows < 10  # Must not overflow

def test_draw_separator_at_boundary(self):
    """Test boundary handling."""
    rows = self.display._draw_separator(start_row=8, height=10, width=80)
    assert rows == 9  # Separator is 1 line
    assert rows <= 10  # Must fit in height

def test_draw_logs_truncates_long_lines(self):
    """Test text truncation."""
    long_log = "x" * 120
    self.display.logs.append(long_log)
    rows = self.display._draw_logs(start_row=0, height=5, width=80)
    assert rows <= 5  # Must not overflow height
```

### Verified On

| Project | PR | Details |
| --------- | --------- | --------- |
| ProjectScylla | #1546 | Extracted `_restore_judgment()` and `_restore_run_result()` from `_restore_run_context()`, CC 11 -> ~7 |
| ProjectHephaestus | #1050 | Extracted `_draw_workers()`, `_draw_separator()`, `_draw_logs()` from `_refresh_display()`, 69 lines → 3 methods, 8 tests → 23 tests, removed `# noqa: C901` |
