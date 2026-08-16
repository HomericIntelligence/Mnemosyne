---
name: variance-estimator-ddof-contract
license: BSD-3-Clause
description: "Make variance estimator semantics explicit and consistent. Use when: (1) small-sample metrics disagree across libraries, (2) coefficient-of-variation or consistency scores change unexpectedly, or (3) code mixes population variance (`ddof=0`) with sample variance (`ddof=1`)."
category: evaluation
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [statistics, variance, standard-deviation, ddof, metrics, evaluation]
---

# Variance Estimator `ddof` Contract

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-07 |
| Objective | Prevent silent disagreement between population and sample variance implementations. |
| Outcome | Select the estimator from the data-generating contract, pass `ddof` explicitly, and test downstream metrics with a hand-computable sample. |

## When to Use

- Two statistics helpers return different standard deviations for the same values.
- A small-sample evaluation reports implausibly stable results.
- A downstream score uses standard deviation or coefficient of variation.
- Library defaults differ or are implicit.

## Verified Workflow

### Quick Reference

```python
import numpy as np

values = np.asarray([2.0, 4.0, 6.0])
population_variance = values.var(ddof=0)  # 8 / 3
sample_variance = values.var(ddof=1)      # 4
```

Choose by semantics, not merely by sample size:

- Use `ddof=0` when the values are the complete population whose dispersion is being described.
- Use `ddof=1` when the values are a sample used to estimate a wider population variance.

Then apply the choice consistently.

1. Document what one observation represents and whether the collected values are a population or a sample.
2. Inventory every variance and standard-deviation call, including library methods whose defaults differ.
3. Pass `ddof` explicitly at each boundary; do not depend on a library default.
4. Trace downstream consumers such as coefficient of variation, confidence summaries, and ranking thresholds.
5. Add a hand-computable test such as `[2, 4, 6]`, plus `n < 2`, zero-mean, and zero-variance behavior required by the API.
6. Compare sibling statistics modules to ensure they encode the same estimator contract or clearly document why they differ.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Assume every small dataset needs Bessel's correction | Switched to `N-1` solely because `N` was small | Small size does not determine whether the values are a sample or the complete population | Select the estimator from the measurement contract |
| Fix one helper only | Changed a custom variance function but left a library call on its default | Sibling metrics still disagreed | Audit all producers and pass `ddof` explicitly |
| Test only variance | Verified the corrected number without checking downstream scores | Coefficient-of-variation and consistency thresholds changed unnoticed | Re-test every derived metric that consumes standard deviation |

## Results & Parameters

| Input | `ddof=0` | `ddof=1` |
|-------|----------|----------|
| `[2, 4, 6]` variance | `2.666666...` | `4.0` |
| `[2, 4, 6]` standard deviation | `1.632993...` | `2.0` |

Define behavior for fewer than two samples before choosing `ddof=1`; many libraries return `NaN` or warn when the denominator is non-positive.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Small-sample evaluation library | Consistency metric audit | A custom population calculation disagreed with a sample-standard-deviation caller; explicit estimator semantics reconciled the pipeline. |
