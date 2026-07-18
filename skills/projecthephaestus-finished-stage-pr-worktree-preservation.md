---
name: projecthephaestus-finished-stage-pr-worktree-preservation
description: "Use when debugging or testing ProjectHephaestus finished-stage cleanup for failed PR-only work items whose preserved worktree records must keep the PR number instead of collapsing to 0. Applies to coordinator preserved-list ownership, summary formatting, and regression tests for PR-only pipeline items."
category: testing
date: 2026-07-07
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - projecthephaestus
  - pipeline
  - finished-stage
  - worktree-preservation
  - pr-only
  - pytest
  - regression-test
---

# ProjectHephaestus Finished-Stage PR Worktree Preservation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-07 |
| **Objective** | Preserve failed PR-only worktree entries with a stable PR identifier instead of recording `(0, worktree_path)` |
| **Outcome** | Proposed regression pattern captured for ProjectHephaestus issue #1897; not executed in this workflow |
| **Verification** | unverified |

ProjectHephaestus issue #1897 exposed a finished-stage preservation edge case:
failed PR-only work items may have `issue=None` and `pr=<number>`. The preserved
worktree tuple must therefore use a stable item identifier of
`item.issue or item.pr or 0` when appending `(item_number, worktree_path)` to the
coordinator preserved list. Otherwise, PR-only failures collapse to `(0,
worktree_path)`, and multiple failed PR-only records can become indistinguishable
when the same worktree path appears with different PRs.

The ownership boundary matters: `hephaestus/automation/pipeline/stages/finished.py`
owns `_cleanup()` and the coordinator `_preserved` entries. The summary module only
formats the resulting tuple, so the fix belongs in the finished stage, not in
`hephaestus/automation/pipeline/summary.py`.

## When to Use

- A ProjectHephaestus failed PR-only pipeline item has `issue=None` but a real `pr` number.
- Finished-stage cleanup records preserved worktrees as `(0, path)` for PR-driven work.
- Two failed PR-only items with different PR numbers and the same worktree path collapse or become ambiguous.
- You are writing regression tests for `hephaestus/automation/pipeline/stages/finished.py`.
- A proposed fix targets summary formatting instead of the code that appends `_preserved` entries.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a
> hypothesis until the ProjectHephaestus test and ruff commands below pass.

### Quick Reference

```python
# In hephaestus/automation/pipeline/stages/finished.py:_cleanup()
item_number = item.issue or item.pr or 0
coordinator._preserved.append((item_number, worktree_path))
```

```bash
pixi run pytest tests/unit/automation/pipeline/stages/test_stage_finished.py -k "pr_only" -v
pixi run pytest tests/unit/automation/pipeline/stages/test_stage_finished.py -v
pixi run pytest tests/unit/automation/pipeline/test_summary.py -v
pixi run ruff check hephaestus/automation/pipeline/stages/finished.py tests/unit/automation/pipeline/stages/test_stage_finished.py tests/unit/automation/pipeline/test_summary.py
```

### Detailed Steps

1. Inspect `hephaestus/automation/pipeline/stages/finished.py:_cleanup()`.
   This function owns cleanup and appends entries to the coordinator preserved
   list. Put the identifier fix here.

2. Use the stable item number expression:

   ```python
   item_number = item.issue or item.pr or 0
   ```

   This keeps issue-driven work unchanged, preserves PR-only work with its PR
   number, and leaves `0` only for items that truly have neither identifier.

3. Do not fix this in `hephaestus/automation/pipeline/summary.py`.
   Summary formatting consumes the tuple after preservation has already happened;
   changing formatting there cannot recover a PR number that was already stored
   as `0`.

4. Extend the local `_item()` helper in
   `tests/unit/automation/pipeline/stages/test_stage_finished.py` to accept
   `kind`, `issue`, and `pr`. Construct PR-only items as:

   ```python
   _item(kind=ItemKind.PR, issue=None, pr=1234)
   ```

5. Add a focused regression test for a single failed PR-only item. The test
   should assert that the preserved tuple contains the PR number, not `0`.

6. Add a second regression test with two PR-only failures that share the same
   worktree path but have different PR numbers. Assert the preserved entries do
   not collapse onto duplicate `(0, worktree_path)` records.

7. Run the focused PR-only tests, then the full finished-stage test file,
   summary tests, and ruff for the changed source/test files.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Formatting-only fix | Treat `hephaestus/automation/pipeline/summary.py` as the place to repair displayed item numbers | Summary only formats the tuple it receives; if `_cleanup()` stored `0`, the PR number is already lost | Fix the tuple at the append site in `finished.py:_cleanup()` |
| Issue-only identifier | Preserve failed worktrees with `item.issue or 0` | PR-only items legitimately have `issue=None`, so they are recorded as `0` | Use `item.issue or item.pr or 0` for stable mixed issue/PR identification |
| Single-case regression only | Test one PR-only failed item with a preserved worktree | This catches `0` for one item but may miss collapse behavior when paths repeat | Add a two-PR test with the same worktree path and different PRs |

## Results & Parameters

| Parameter | Value |
|-----------|-------|
| Stable identifier | `item.issue or item.pr or 0` |
| Source owner | `hephaestus/automation/pipeline/stages/finished.py:_cleanup()` |
| Formatting-only consumer | `hephaestus/automation/pipeline/summary.py` |
| Regression test file | `tests/unit/automation/pipeline/stages/test_stage_finished.py` |
| PR-only item shape | `ItemKind.PR`, `issue=None`, `pr=<number>` |
| Verification level | `unverified` until the listed ProjectHephaestus pytest and ruff commands pass |

Expected regression assertions:

```python
assert (1234, worktree_path) in coordinator._preserved
assert (0, worktree_path) not in coordinator._preserved
```

For the duplicate-path case, assert both PR numbers remain represented:

```python
assert (1234, worktree_path) in coordinator._preserved
assert (5678, worktree_path) in coordinator._preserved
assert coordinator._preserved.count((0, worktree_path)) == 0
```
