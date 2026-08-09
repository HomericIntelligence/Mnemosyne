---
name: testing-newton-schulz-orthogonality-band-assertions
description: "How to correctly test Newton-Schulz / Muon-style orthogonalization output. Use when: (1) a test asserts A^T A ≈ I (strict orthonormality) on a Newton-Schulz-orthogonalized matrix and it fails with off-diagonal or singular-value errors around 0.1–0.3, (2) you are writing regression tests for a Muon optimizer's `zeropower_via_newtonschulz5` / quintic-iteration step, (3) a reviewer claims the orthogonalizer is 'broken' because the result is not exactly orthogonal, (4) you need tolerances for singular values after a fixed 5-iteration Newton-Schulz run, (5) input to the orthogonalizer can be rank-deficient (fewer effective rows/cols than dimension) and the test must not assume full rank, (6) a parity test compares a Mojo/C++ orthogonalizer against a PyTorch reference and the two disagree only in the 3rd decimal."
category: testing
date: 2026-07-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - newton-schulz
  - muon-optimizer
  - orthogonalization
  - singular-values
  - orthonormality
  - tolerance-band
  - mojo
  - rank-deficient
  - parity-testing
---

# Testing Newton-Schulz Orthogonalization: Assert the Singular-Value Band, Not Strict Orthogonality

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-16 |
| **Objective** | Write correct regression tests for a Newton-Schulz / Muon-style orthogonalization step |
| **Outcome** | Tests must assert a singular-value *band* (≈[0.68, 1.13]) — strict `A^T A ≈ I` assertions are wrong and will fail on a correct implementation |
| **Verification** | verified-local (band bounds observed empirically against a working quintic 5-iteration orthogonalizer) |

## When to Use

- A test asserts strict orthonormality (`A^T A ≈ I`, off-diagonals ≈ 0, all singular values ≈ 1) on the output of a Newton-Schulz iteration and fails by ~0.1–0.3.
- You are writing or reviewing tests for a Muon optimizer's `zeropower_via_newtonschulz5` / quintic Newton-Schulz step.
- Someone reports the orthogonalizer as "broken" because the output is not exactly orthogonal — before filing a bug, confirm whether the test's *expectation* is wrong.
- The input matrix can be rank-deficient; the test must not assume the orthogonalizer produces a full-rank near-identity Gram matrix.
- A Mojo/C++ orthogonalizer is being parity-checked against a PyTorch reference and they agree only to ~2–3 decimals.

## Verified Workflow

### Quick Reference

```python
# CORRECT: assert the singular-value BAND that a fixed-iteration
# Newton-Schulz quintic converges to — NOT strict orthonormality.
import numpy as np

def orthogonality_error(A):
    # Singular values of the orthogonalized matrix, not A^T A off-diagonals.
    s = np.linalg.svd(A, compute_uv=False)
    return s

s = orthogonality_error(orthogonalized)   # output of newton-schulz-5
# The quintic (Muon default coeffs 3.4445, -4.7750, 2.0315) is TUNED to pull
# singular values into a band around 1 in ~5 iterations, NOT to 1.0 exactly.
assert s.max() <= 1.13 + 1e-3, f"upper band exceeded: {s.max()}"
assert s.min() >= 0.68 - 1e-3, f"lower band underrun: {s.min()}"
# Do NOT assert np.allclose(A.T @ A, np.eye(n)) — that is FALSE for a
# correct 5-iteration Newton-Schulz output and will fail every time.
```

### Detailed Steps

1. **Understand what Newton-Schulz actually computes.** The Muon-style quintic iteration
   `X <- a·X + b·(X Xᵀ) X + c·(X Xᵀ)² X` with the standard coefficients
   `(a, b, c) = (3.4445, -4.7750, 2.0315)` is a fixed-point map whose stable region pulls
   every singular value of `X` toward 1 — but for a *finite* iteration count (Muon uses 5)
   it deliberately trades exactness for speed. It does **not** converge to an exactly
   orthogonal matrix; it converges to a matrix whose singular values sit in a band around 1.
2. **Measure the band empirically for your iteration count.** For the standard 5-iteration
   quintic, the singular-value band observed is **≈ [0.68, 1.13]**. If you change the
   coefficients or the iteration count, re-measure — the band moves. Capture the observed
   `s.min()`/`s.max()` across a batch of random and structured inputs and set tolerances a
   hair outside the observed extremes.
3. **Assert the band, not the identity.** Take the SVD of the *output* and bound
   `s.min()`/`s.max()`. Do **not** assert `A.T @ A ≈ I` or `‖A.T @ A − I‖ < ε` for small ε —
   those encode strict orthonormality, which the operator does not deliver.
4. **Handle rank-deficient input explicitly.** If the input has fewer effective rows/columns
   than its dimension (e.g. a low-rank gradient), the trailing singular values start near 0
   and the iteration cannot lift them into the band. Either (a) construct test inputs that are
   full-rank, or (b) assert the band **only over the leading `rank` singular values** and
   assert the trailing ones stay near 0 — never assert all singular values are in the band on
   rank-deficient input.
5. **For parity tests, compare bands and per-element tolerances, not bitwise.** A Mojo/C++
   port vs. a PyTorch reference will differ in the low-order bits because the iteration
   amplifies rounding differently. Compare with `rtol≈1e-2, atol≈1e-2` (or compare the
   singular-value bands of both outputs), not exact equality. A parity test that only checks
   the band on BOTH sides can pass while both implementations are subtly wrong in the same
   way — pair it with at least one absolute-correctness anchor (a known input/output pair).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Attempt 1 | Asserted `np.allclose(A.T @ A, np.eye(n), atol=1e-4)` on the orthogonalized output | Off-diagonals were ~0.1 and diagonal entries ranged ~0.46–1.28 (= singular values squared) — nowhere near identity | A 5-iteration Newton-Schulz does NOT produce a strictly orthonormal matrix; the assertion encodes the wrong contract |
| Attempt 2 | Assumed the failure meant the orthogonalizer implementation was buggy and started "fixing" the iteration | The implementation was correct; the *test expectation* was wrong. Wasted effort chasing a non-bug | Before editing the operator, verify the singular-value band of the output against the known ≈[0.68, 1.13] band |
| Attempt 3 | Tightened the band to `[0.95, 1.05]` "to be safe" | The real band is ≈[0.68, 1.13]; the tighter bound failed on legitimate outputs | Measure the band empirically for your exact coefficients + iteration count; do not guess a tighter band |
| Attempt 4 | Asserted the band over ALL singular values on a deliberately rank-deficient input | Trailing singular values stayed near 0 (the iteration can't lift a zero singular value into the band), so `s.min()` violated the lower bound | On rank-deficient input, bound only the leading `rank` singular values; assert the rest stay ≈0 |
| Attempt 5 | Wrote a Mojo-vs-PyTorch parity test asserting only that both outputs land in the band | Both could be wrong in the same way and still pass — the band is a *necessary* not *sufficient* correctness check | Pair band assertions with at least one fixed known-input/known-output anchor for absolute correctness |

## Results & Parameters

**Standard Muon quintic Newton-Schulz (5 iterations):**

- Coefficients `(a, b, c) = (3.4445, -4.7750, 2.0315)`
- Observed singular-value band after 5 iterations: **≈ [0.68, 1.13]**
- Test tolerances used: `s.max() <= 1.13 + 1e-3`, `s.min() >= 0.68 - 1e-3`

```python
# Full-rank correctness test (numpy reference)
import numpy as np

def assert_newton_schulz_band(orthogonalized, lo=0.68, hi=1.13, eps=1e-3):
    s = np.linalg.svd(orthogonalized, compute_uv=False)
    assert s.max() <= hi + eps, f"upper band exceeded: {s.max():.4f} > {hi}"
    assert s.min() >= lo - eps, f"lower band underrun: {s.min():.4f} < {lo}"
    return s

# Rank-deficient case: bound only the leading `rank` singular values.
def assert_band_rank_deficient(orthogonalized, rank, lo=0.68, hi=1.13, eps=1e-3):
    s = np.sort(np.linalg.svd(orthogonalized, compute_uv=False))[::-1]
    leading, trailing = s[:rank], s[rank:]
    assert leading.min() >= lo - eps and leading.max() <= hi + eps
    assert np.all(trailing < 1e-2), f"trailing sv not ~0: {trailing}"
```

**Anti-patterns to reject in review:**

- `assert np.allclose(A.T @ A, np.eye(n))` — wrong contract; fails on correct output.
- `assert abs(s - 1.0).max() < 1e-3` — demands exact orthonormality the operator never provides.
- Band-only parity with no absolute anchor — passes even when both sides are wrong.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | Muon optimizer / Newton-Schulz orthogonalization test review during the HomericIntelligence PR sweep (2026-07-16) | Band ≈[0.68, 1.13] observed; strict-orthonormality assertion identified as the test bug, operator confirmed correct |
