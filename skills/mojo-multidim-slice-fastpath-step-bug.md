---
name: mojo-multidim-slice-fastpath-step-bug
description: "Fix memcpy fast-path in AnyTensor.__getitem__(*slices) that ignores step on non-first dimensions, causing silent data corruption for slices like t[:, ::2]. Use when: (1) multidim step slicing returns wrong values, (2) fast-path optimization bypasses step handling, (3) reviewing tensor slicing with non-unit steps."
category: debugging
date: 2026-03-24
version: "1.0.0"
user-invocable: false
tags:
  - tensor
  - slicing
  - fast-path
  - data-corruption
  - mojo
---

# Mojo Multidim Slice Fast-Path Step Bug

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-03-24 |
| **Objective** | Fix silent data corruption when using stepped slices on non-first dimensions of AnyTensor (e.g., `t[:, ::2]`) |
| **Outcome** | ✅ SUCCESS - Added step check to fast-path guard, fixing wrong values returned by stepped multi-dim slices |

## When to Use

- `__getitem__(*slices: Slice)` returns wrong values for stepped slices on dims >= 1
- Fast-path memcpy optimization in multi-dim slicing produces incorrect results
- Test assertion "Values are not equal" when slicing with step > 1 on non-first dimensions
- Reviewing any tensor slicing optimization that uses memcpy for contiguous regions

## Verified Workflow

### Quick Reference

```mojo
# Bug: fast-path in __getitem__(*slices) checks start/end but NOT step
# for dims >= 1, so [:, ::2] (start=0, end=size) passes the memcpy guard
# and copies contiguous data instead of stepping

# Fix: Add step check BEFORE start/end check in the fast-path loop
for dim in range(1, num_dims):
    var s = slices[dim]
    var size = self._shape[dim]
    var step = s.step.or_else(1)   # <-- ADD THIS
    if step != 1:                   # <-- ADD THIS
        can_use_memcpy = False      # <-- ADD THIS
        break                       # <-- ADD THIS
    var start = s.start.or_else(0)
    var end = s.end.or_else(size)
    # ... rest of start/end bounds checking unchanged
```

### Detailed Steps

1. **Identify the bug**: `test_multidim_step2_second_dim()` tests `t2d[:, ::2]` on a [5,4] tensor. First test `t2d[::2, :]` (step on dim 0) passes because dim-0 step is handled by the memcpy fast-path. But step on dim >= 1 is ignored by the guard.

2. **Trace the code path**: `__getitem__(*slices: Slice)` has a fast-path (lines 1344-1380) that uses memcpy when only dim-0 is non-trivially sliced. The guard checks `start != 0 or end != size` for dims >= 1, but does NOT check `step != 1`.

3. **Why it's silent**: `[:, ::2]` has `start=0, end=4, step=2`. Since start==0 and end==size, the guard says "this is a full slice" and uses memcpy. But step=2 means only every other element should be copied.

4. **Fix**: Add 3 lines to check step before checking start/end bounds. This is minimal and doesn't affect the slow path.

5. **Verify**: The slow path (lines 1387-1401) already handles step correctly via `src_idx = starts[dim] + out_idx * steps[dim]`, so disabling the fast-path for stepped slices produces correct results.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| N/A - diagnosed on first attempt | Direct code inspection of fast-path guard | N/A | Always check ALL slice parameters (start, end, AND step) when deciding if a slice is "trivial" for optimization purposes |

## Results & Parameters

**Before fix**: `t2d[:, ::2]` on `arange(20).reshape([5,4])` returns `[0, 1, 2, 3, ...]` (contiguous memcpy)
**After fix**: `t2d[:, ::2]` correctly returns `[0, 2, 4, 6, ...]` (every other column)

**File**: `shared/tensor/any_tensor.mojo`, lines 1349-1366

**Pattern**: When optimizing tensor operations with fast-paths, the guard condition must check ALL slice properties. A "full slice" means `start==0 AND end==size AND step==1`, not just `start==0 AND end==size`.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | PR #5076 fix-remaining-crashes-round2 | [notes](./skills/mojo-multidim-slice-fastpath-step-bug.notes.md) |
