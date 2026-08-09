---
name: testing-percentile-nearest-rank-excludes-slow-tail
description: "A hand-rolled p95/p99 latency gate that computes the percentile with the nearest-rank formula `index = ceil(n * p) - 1` (clamped to [0, n-1]) SILENTLY EXCLUDES the slow tail, so an `assert measured.p95 <= budget` gate passes even when a full p*n fraction of requests are catastrophically slow. Proof (a real NOGO'd perf suite, Hephaestus #2229 repairing PR #2212): for n=100 samples where the slowest 5 are 9999ms and the rest 10ms, nearest-rank p95 = ordered[ceil(100*0.95)-1] = ordered[94] = 10.0 — it lands BELOW all 5 tail samples, so a 500ms p95 gate reports PASS while 5% of traffic is 20x over budget. The fix is linear interpolation between closest ranks (numpy's default `linear` method, equivalently `statistics.quantiles(..., method='inclusive')`): `rank = p*(n-1); return o[lo] + frac*(o[lo+1]-o[lo])`, which returns 509.45 on that same input and 554.5 for [10]*9+[1000]. Use when: (1) reviewing or writing ANY test/CI gate that asserts a measured p95/p99/tail-latency against a budget, (2) you see a hand-written percentile using `ceil`/`floor`/`round` + integer indexing instead of interpolation, (3) an issue says a latency gate 'underreports tail latency' or 'the suite passes but tail is slow', (4) porting a percentile helper that has no dependency on numpy/statistics. The regression test that PROVES the defect must assert the OLD formula's wrong value (==tail-excluding number) AND the NEW formula's tail-inclusive value on the SAME fixed sample array — a deterministic unit test on a literal list, never a measured/timed run."
category: testing
date: 2026-07-17
version: "1.0.0"
user-invocable: false
verification: verified
tags:
  - percentile
  - p95
  - tail-latency
  - nearest-rank
  - linear-interpolation
  - latency-gate
  - regression-test
  - performance-testing
---

# Skill: Nearest-rank percentile silently excludes the slow tail

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2026-07-17 |
| Project | ProjectHephaestus |
| Objective | Repair a NOGO'd performance suite whose p95 latency gate underreports tail latency |
| Outcome | Root-caused: nearest-rank `ceil(n*p)-1` excludes the tail; fix = linear interpolation + a regression test on a fixed array |
| Issue | HomericIntelligence/Hephaestus#2229 (repairs PR #2212, Closes #2145) |

A "performance suite" gated `assert report.end_to_end_latency_ms.p95 <= load_config.p95_budget_ms`,
but its `_percentile` helper computed the percentile by **nearest rank**:

```python
from math import ceil
def _percentile(samples: list[float], percentile: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, ceil(len(ordered) * percentile) - 1))
    return ordered[index]
```

For `p=0.95` and `n=100`, the index is `ceil(100 * 0.95) - 1 = 94`, i.e. `ordered[94]` — the
95th-smallest sample. That deliberately lands **below** the slowest `n - (index+1) = 5` samples.
So if the slowest 5% are pathological, `_percentile` returns a fast value and the budget gate
reports PASS. The gate is real code that protects nothing — the classic "green but wrong" test.

## When to Use

Use this skill when:
- Reviewing or writing ANY test / CI check that asserts a measured `p95`/`p99`/tail latency against a budget (`assert measured.p95 <= budget`).
- You see a hand-written percentile using `ceil`, `floor`, `round`, or `int()` plus integer list indexing instead of interpolation between two ranks.
- An issue or PR review says a latency gate "underreports tail latency", "passes but the tail is slow", or "p95 doesn't cover the correct tail population".
- Porting or generalizing a percentile helper that (correctly) avoids a `numpy` runtime dependency but reaches for nearest-rank as the "simple" alternative.

## Key Insight: nearest-rank is an *exclusive* boundary, not a tail estimate

The `ceil(n*p)-1` nearest-rank index is the rank at or just below the `p` cut point. For the tail
percentiles teams actually care about (p95, p99), that index sits on the boundary that **excludes**
the slow tail rather than reaching into it. Two failing witnesses on fixed arrays:

| samples | nearest-rank p95 | linear-interp p95 | tail present? |
| --- | --- | --- | --- |
| `[10.0]*95 + [9999.0]*5` (n=100) | `10.0` (`ordered[94]`) | `509.45` | the 5 slow samples are entirely missed by nearest-rank |
| `[10.0]*96 + [9999.0]*4` (n=100) | `10.0` | `509.45` | still missed |
| `[10.0]*9 + [1000.0]` (n=10) | `1000.0` | `554.5` | small-n coincidentally catches it — do NOT let a small-n test hide the bug |

The n=10 row is why the original suite *looked* correct: its only tail test used 10 samples where
nearest-rank happens to hit the slow sample. Always add a witness with `n` large enough that
`(1-p)*n >= 2` so the tail is a *population*, not a single element.

## Verified Workflow

### 1. Replace nearest-rank with linear interpolation between closest ranks

This matches numpy's default `linear` method and `statistics.quantiles(data, n=100, method="inclusive")`,
with no third-party dependency and correct behavior for `n == 1`:

```python
def _percentile(samples: list[float], percentile: float) -> float:
    """Return the linearly interpolated percentile (tail-inclusive)."""
    if not samples:
        return 0.0
    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]
    rank = percentile * (len(ordered) - 1)
    low = int(rank)
    frac = rank - low
    if low + 1 < len(ordered):
        return ordered[low] + frac * (ordered[low + 1] - ordered[low])
    return ordered[low]
```

Prefer this hand-rolled 6-line form over `numpy` when numpy is not already a runtime dependency
(`grep -n numpy pyproject.toml` first), and over calling `statistics.quantiles` directly — its
`n`-bucket API is awkward for a single arbitrary percentile and it raises on `n < 2`.

### 2. Write a regression test that pins BOTH formulas on the SAME fixed array

The test must fail against the old code and pass against the new code — encode the defect, not just
the fix. Assert the old formula's tail-*excluding* value AND the new helper's tail-*inclusive*
value on one literal list, so the comparison is the evidence:

```python
from math import ceil
import pytest

def _nearest_rank_p95(samples: list[float]) -> float:  # the pre-fix formula, inlined
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, ceil(len(ordered) * 0.95) - 1))
    return ordered[index]

def test_prior_nearest_rank_underreported_the_tail() -> None:
    samples = [10.0] * 95 + [9_999.0] * 5
    assert _nearest_rank_p95(samples) == 10.0          # old: missed the whole slow tail
    assert _latency_summary(samples).p95 > 500.0       # new: tail-inclusive, over a 500ms budget

def test_repaired_p95_catches_a_single_slow_completion() -> None:
    assert _latency_summary([10.0] * 9 + [1_000.0]).p95 == pytest.approx(554.5)
```

This is a deterministic unit test on a literal list — never a timed/measured load run. The measured
run (real threads, a `--load-duration-s` budget) is separate evidence collected from CI, per
ADR-014; do not make a measured latency number a deliverable of the fix. See
[[regression-test-already-merged-fails-before]] for the fails-before discipline and
[[dryrun-process-metrics-assertions]] for asserting artifact fields rather than timings.

### 3. Fix the existing tests that PINNED the wrong behavior

The old suite had `test_percentile_uses_nearest_rank` asserting p95 of `1..10` == `10.0` and a tail
test asserting `1000.0`. Under interpolation those become `9.55` and `554.5`. Rewrite them — keeping
them would re-freeze the underreporting bug into the test suite. A test named after the *buggy
algorithm* ("uses_nearest_rank") is a smell: it locks in the method, not the property.

### 4. Also fix the latent forward-reference surfaced while reading

The tail test called `_latency_summary` defined *below* it in the module — it worked only because
pytest imports the module fully before calling tests. Move `_percentile`/`_latency_summary` above
their callers; drop the now-unused `from math import ceil` (ruff F401).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trust the existing tail test | The suite shipped `test_p95_..._includes_slow_tail_completion` on `[10.0]*9 + [1000.0]`, which passed | With n=10, nearest-rank index `ceil(10*0.95)-1 = 9` coincidentally hits the single slow sample, so the buggy formula passed | A passing tail test on tiny n does not prove tail coverage; require `(1-p)*n >= 2` so the tail is a population |
| Reach for `numpy.percentile` | Considered numpy for a correct `linear` method | numpy is not a runtime dependency (`grep numpy pyproject.toml` → none); adding it for one 6-line helper violates YAGNI | Hand-roll the interpolation; it equals numpy's default `linear` method exactly |
| Call `statistics.quantiles` directly | Tried `statistics.quantiles(samples, n=100, method="inclusive")[94]` | Its `n`-bucket API is clumsy for one arbitrary percentile and it raises `StatisticsError` on `n < 2` | Prefer the explicit `rank = p*(n-1)` interpolation with an explicit `n == 1` guard |
| Keep the old assertions | Left `test_percentile_uses_nearest_rank` in place | It pins the exact buggy value; keeping it re-freezes the underreporting into CI | Rewrite tests named after the buggy *method*; assert the *property* (tail inclusion) instead |

## Results & Parameters

- **Root cause**: `_percentile` used nearest-rank `index = ceil(n*p)-1` (clamped), which excludes the slow tail for tail percentiles; the p95 budget gate consequently passed on catastrophic tails.
- **Fix**: linear interpolation between closest ranks — `rank = p*(n-1); o[lo] + frac*(o[lo+1]-o[lo])`, with `n == 1` guard. Dependency-free; equals numpy `linear` / `statistics.quantiles(method="inclusive")`.
- **Witness values** (verified with a throwaway Python check on literal arrays):
  - `[10.0]*95 + [9999.0]*5`: nearest-rank p95 = `10.0`; interpolation = `509.45`.
  - `[10.0]*96 + [9999.0]*4`: nearest-rank p95 = `10.0`; interpolation = `509.45`.
  - `[10.0]*9 + [1000.0]`: nearest-rank p95 = `1000.0`; interpolation = `554.5`.
  - `list(1..10)`: interpolation p50/p95/p99 = `5.5 / 9.55 / 9.91`.
- **Regression-test contract**: assert the old formula's tail-excluding value AND the new value on one fixed literal array; deterministic, no timing.
- **Boundary discipline (ADR-014 / RUNNABLE-EVIDENCE)**: the measured load run's latency/throughput numbers are collected from an unauthored CI run, not committed as evidence; only the deterministic correctness tests are a deliverable of the fix.
- **Parameters that generalize**: applies to any `p` in `(0,1)`, any language with sorted-index percentile helpers; the exclusion is worst for high-`p` (p95/p99) tail gates and negligible for medians.
