---
name: newton-schulz-fixed-iteration-test-contract
description: "Test fixed-iteration Newton-Schulz orthogonalization against its actual approximation contract. Use when: (1) strict `Q.T @ Q == I` assertions reject a valid finite iteration, (2) rank-deficient inputs are supported, or (3) cross-language parity needs both a spectral band and an absolute anchor."
category: testing
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [newton-schulz, orthogonalization, singular-values, rank-deficient, numerical-testing]
---

# Fixed-Iteration Newton-Schulz Test Contract

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-07 |
| Objective | Replace exact-orthogonality assertions with tests that match a finite polynomial iteration. |
| Outcome | Bind tests to the chosen coefficients and iteration count, check the reachable singular-value band, handle null-space values, and retain a fixed absolute anchor. |

## When to Use

- A finite Newton-Schulz step fails a strict identity-Gram assertion.
- The implementation intentionally uses a small fixed iteration count.
- Inputs may be rank deficient.
- Two implementations agree qualitatively but need a meaningful parity contract.

## Verified Workflow

### Quick Reference

For the commonly used quintic update with coefficients `(3.4445, -4.7750, 2.0315)` and five iterations, observed nonzero singular values lie approximately in `[0.68, 1.13]`. Treat those numbers as algorithm parameters, not universal Newton-Schulz constants.

```python
import numpy as np


def assert_spectral_contract(output, *, rank, lower, upper, tolerance=1e-3):
    singular = np.sort(np.linalg.svd(output, compute_uv=False))[::-1]
    active = singular[:rank]
    null = singular[rank:]
    assert active.min() >= lower - tolerance
    assert active.max() <= upper + tolerance
    assert np.all(null <= tolerance)
```

1. Freeze the polynomial coefficients, normalization rule, precision, and iteration count in the test description.
2. Compute the expected spectral envelope from the reference recurrence or a trusted implementation.
3. Test a full-rank input against that envelope.
4. For rank-deficient input, apply the lower bound only to the leading known-rank singular values; the iteration cannot create rank from exact zeros.
5. Add one fixed input/output anchor or trusted-reference comparison. A band alone is necessary but not sufficient.
6. Keep cross-language tolerances separate from the algorithmic band so rounding tolerance does not silently widen the contract.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Require an identity Gram matrix | Asserted `output.T @ output` was nearly identity after five iterations | The finite polynomial is an approximation and its intended spectrum is not exactly one | Test the fixed-iteration spectral contract |
| Tighten around one | Required every singular value in `[0.95, 1.05]` without deriving it | Legitimate outputs from the selected coefficients fell outside the guessed band | Derive bounds from the exact recurrence and iteration count |
| Bound every singular value below | Applied the positive lower bound to a rank-deficient input | Exact null-space singular values remain near zero | Split active-rank and null-space assertions |
| Use only a broad band for parity | Accepted two implementations whenever both landed inside the envelope | Both could share the same wrong recurrence | Add a fixed absolute anchor or trusted-reference comparison |

## Results & Parameters

| Parameter | Reference value |
|-----------|-----------------|
| Coefficients | `(3.4445, -4.7750, 2.0315)` |
| Iterations | `5` |
| Active singular-value band | approximately `[0.68, 1.13]` |
| Numerical tolerance | `1e-3` around the derived band |

Re-derive the envelope whenever coefficients, normalization, precision, or iteration count changes.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Optimizer implementation | Five-step quintic orthogonalizer | Full-rank and rank-deficient tests matched a numerical reference after replacing exact-orthogonality assumptions with the spectral contract. |
