---
name: metrics-bessels-correction-sample-variance
description: "Fix population variance (÷N) to sample variance (÷N-1) in small-N evaluation metrics. Use when: (1) reviewing variance/std_dev calculations with N<30, (2) consistency scores seem inflated, (3) ablation comparisons show suspiciously low variability."
category: debugging
date: 2026-03-25
version: "1.0.0"
user-invocable: false
verification: verified-local
supersedes: []
tags: [statistics, variance, bessel, sample-variance, metrics, ablation]
---

# Bessel's Correction for Small-N Evaluation Metrics

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-03-25 |
| **Objective** | Fix systematically underestimated variance in ablation study metrics by switching from population variance (÷N) to sample variance (÷N-1) |
| **Outcome** | Successful — all 4785 unit tests pass after fix |
| **Verification** | verified-local |

## When to Use

- Reviewing variance or standard deviation calculations where sample size is small (N < 30)
- Consistency scores (1 - CV) appear inflated — components that should add variance appear negligible
- Ablation comparisons produce suspicious false positives (a component appears to have no impact)
- Two statistics modules in the same codebase produce conflicting results for the same data (one uses ddof=0, the other ddof=1)

## Verified Workflow

### Quick Reference

```python
# WRONG — population variance (biased for samples)
variance = sum(squared_diffs) / len(values)

# CORRECT — sample variance with Bessel's correction
variance = sum(squared_diffs) / (len(values) - 1)
```

### Detailed Steps

1. **Identify affected functions**: Search for `/ len(values)` or `/ N` in variance calculations. Also check for `ddof=0` in numpy/scipy calls.

2. **Check the guard clause**: Ensure `len(values) < 2` returns 0.0 — this prevents division by zero when N-1 = 0.

3. **Fix the denominator**: Change `/ len(values)` to `/ (len(values) - 1)`.

4. **Update docstrings**: Change "population variance" to "sample variance" and mention Bessel's correction.

5. **Update tests**: Tests asserting exact variance values will break. For `[2, 4, 6]`:
   - Population variance: `(4+0+4)/3 = 8/3 ≈ 2.667`
   - Sample variance: `(4+0+4)/2 = 4.0`

6. **Check downstream consumers**: `calculate_std_dev()` inherits the fix automatically. `calculate_consistency()` (1 - std/mean) will now report slightly lower (more accurate) consistency scores.

7. **Verify other statistics modules**: If the codebase has a separate `analysis/stats.py` using pandas/scipy, check whether those use `ddof=1` (pandas default) or `ddof=0` (numpy default). Inconsistency between modules causes conflicting results.

### Bias Magnitude by Sample Size

| N (runs) | Pop. Variance Bias | Underestimate |
|----------|-------------------|---------------|
| 9 | ÷9 vs ÷8 | 12.5% |
| 10 | ÷10 vs ÷9 | 11.1% |
| 20 | ÷20 vs ÷19 | 5.3% |
| 30 | ÷30 vs ÷29 | 3.4% |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| N/A | Fix was straightforward | N/A | The tricky part is not the fix itself but finding all affected call sites and understanding which downstream metrics are impacted |

## Results & Parameters

**Before (population variance)**:
```python
# [2.0, 4.0, 6.0] → variance = 2.667, std_dev = 1.633
calculate_variance([2.0, 4.0, 6.0])  # 2.6667
```

**After (sample variance)**:
```python
# [2.0, 4.0, 6.0] → variance = 4.0, std_dev = 2.0
calculate_variance([2.0, 4.0, 6.0])  # 4.0
```

**Key insight**: The `analysis/stats.py:compute_consistency()` function takes pre-computed mean/std as inputs — callers use pandas `.std()` which defaults to `ddof=1`. So that module was already correct; only `metrics/statistics.py` needed fixing.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectScylla | Issue #1508, PR #1552 | 4785 tests pass locally, pre-commit hooks pass |
