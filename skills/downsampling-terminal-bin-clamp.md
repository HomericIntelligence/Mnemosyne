---
name: downsampling-terminal-bin-clamp
description: "Clamp the last output bin to the source extent when a grid maps cells to samples. Use when: (1) a loop computes begin and end indices with integer division and forces at least one sample per cell, (2) the output cell count can exceed the source length, or (3) a renderer or resampler maps a tensor to pixels, bands, or bins."
category: debugging
date: 2026-11-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - index-bounds
  - off-by-one
  - downsampling
  - resampling
  - out-of-bounds
  - clamp
  - raster
---

# Downsampling Terminal Bin Clamp

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-24 |
| **Objective** | Prevent an out-of-bounds read in the last output cell of a resampling loop. |
| **Outcome** | A review found a high-severity over-read in a renderer. The fix clamped the last bin to the source length. A test with more output cells than source samples now guards the behavior. |

## When to Use

- A loop maps M output cells (pixels, bands, bins) to N source samples.
- The loop uses integer division and a forced minimum, such as `end = max(begin + 1, (i + 1) * N / M)`.
- M can be larger than N, or the last cell touches the end of the source.
- The loop indexes a tensor or array and does not check each access.

## Verified Workflow

### Quick Reference

```cpp
// M output cells, N source samples. N > 0.
const int begin = std::min(static_cast<int>((qint64)i * N / M), N - 1);
const int end = std::clamp(
    static_cast<int>((qint64)(i + 1) * N / M), begin + 1, N);
```

- `begin` is clamped to `N - 1`. The last cell keeps one valid sample.
- `end` is clamped to `N`. The forced minimum cannot pass the source length.
- Apply the clamp to each axis. A row range and a column range overrun independently.

### Suggested Approach

1. Find each range that forces at least one sample.
2. Calculate the terminal cell by hand with `i = M - 1` and `N < M`. In the unclamped formula, `begin = N`, so the range `[N, N + 1)` reads one element past the source.
3. Clamp `begin` to `N - 1` and `end` to `[begin + 1, N]`.
4. Add a test where the output cell count is larger than the source length. Use a source spike that only a within-cell reduction can find. A point sample and a correct range reduction then give different results.
5. Add a second test where the source is larger than the output grid. The two tests cover both directions of the mapping.
6. Run the tests before and after the fix. Confirm that the new test fails on the unclamped code.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| 1 | Forced one sample per cell with `end = max(begin + 1, floor((i + 1) * N / M))`. | With `N < M`, the last cell starts at `begin = N` and the range `[N, N + 1)` reads past the source. | The sample guarantee must stop at the source length. Clamp `begin` and `end`. |
| 2 | Tested the reduction with more output cells than source samples but asserted only a whole-image inequality. | The test passed with point sampling because it did not require a within-cell maximum. | Add a spike inside one cell and assert that the reduced results differ. |
| 3 | Clamped only the column range. | The terminal row range still overran, and the terminal column of other rows still crossed into the next row. | Clamp each axis independently. |

## Results & Parameters

### Configuration

```text
Source samples    N, at least 1
Output cells      M, at least 1
Begin index       min(floor(i * N / M), N - 1)
End index         clamp(floor((i + 1) * N / M), begin + 1, N)
```

### Expected Output

- Each cell reads at least one sample and no sample index is `>= N`.
- The last cell reads the final source sample.
- A spike inside one cell changes the reduced value.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| C++ probability-surface renderer | Review of a tensor-to-pixel reduction | The terminal row and column read past the tensor. The clamped version passed the test suite. |

## References

- [Test-driven development and test coverage expansion](tdd-workflow-and-test-coverage-expansion.md)
- [Testing non-vacuous regression guards](testing-non-vacuous-regression-guards-behavior-unchanged.md)