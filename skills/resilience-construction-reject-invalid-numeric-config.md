---
name: resilience-construction-reject-invalid-numeric-config
license: BSD-3-Clause
description: "Fail-fast validation for retry decorator factories and circuit-breaker constructors. Use when: (1) invalid retry counts can skip protected work, (2) zero or non-finite breaker limits can wedge recovery, (3) Python bool values may pass integer checks, (4) zero is valid for delays but not thresholds or capacities."
category: architecture
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - python
  - resilience
  - retry
  - circuit-breaker
  - validation
  - fail-fast
  - numeric-invariants
  - value-error
---

# Fail Fast on Invalid Resilience Construction Configuration

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-06 |
| **Objective** | Reject invalid retry and circuit-breaker numeric configuration at the public construction boundary, before protected work can be skipped or recovery can be permanently blocked |
| **Outcome** | The negative-retry, zero-capacity, and non-finite-timeout failures were reproduced locally; the validation and regression-test workflow is proposed but was not implemented in this session |
| **Verification** | unverified — failure modes reproduced locally; remediation and CI validation pending |

## When to Use

- A decorator factory accepts counts or timing values that later control a `range()`, sleep, retry, or suppression loop.
- A state-machine constructor accepts thresholds, probe capacities, or timeouts that determine whether recovery remains reachable.
- A negative retry count can make `range(max_retries + 1)` empty, returning without ever invoking the protected function.
- A zero half-open capacity admits no recovery probes, or a `NaN` timeout makes an elapsed-time comparison permanently false.
- Runtime validation uses `isinstance(value, int)` and must reject booleans explicitly because `bool` subclasses `int` in Python.
- Boundary values are intentional: zero retries means one initial attempt, zero delay means no waiting, and zero recovery timeout means immediate half-open eligibility.

## Verified Workflow

> **Warning — proposed workflow only:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms. The failure modes were reproduced locally, but the proposed code and tests were not applied in this session.

### Quick Reference

```python
import math

# Validate in the decorator factory, before returning the decorator.
if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
    raise ValueError("max_retries must be a non-negative integer")

if (
    isinstance(initial_delay, bool)
    or not isinstance(initial_delay, (int, float))
    or (isinstance(initial_delay, float) and not math.isfinite(initial_delay))
    or initial_delay < 0
):
    raise ValueError("initial_delay must be a finite non-negative number")

if (
    isinstance(backoff_factor, bool)
    or not isinstance(backoff_factor, int)
    or backoff_factor < 1
):
    raise ValueError("backoff_factor must be a positive integer")

if max_delay is not None and (
    isinstance(max_delay, bool)
    or not isinstance(max_delay, (int, float))
    or (isinstance(max_delay, float) and not math.isfinite(max_delay))
    or max_delay < 0
):
    raise ValueError("max_delay must be a finite non-negative number or None")
```

```python
# Validate at the start of the state-machine constructor, before field assignment.
for parameter, value in (
    ("failure_threshold", failure_threshold),
    ("half_open_max_calls", half_open_max_calls),
    ("success_threshold", success_threshold),
):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{parameter} must be a positive integer")

if (
    isinstance(recovery_timeout, bool)
    or not isinstance(recovery_timeout, (int, float))
    or (
        isinstance(recovery_timeout, float)
        and not math.isfinite(recovery_timeout)
    )
    or recovery_timeout < 0
):
    raise ValueError("recovery_timeout must be a finite non-negative number")
```

### Detailed Steps

1. **Write the invariant table before editing execution logic.** Classify each parameter by meaning, not merely by numeric type:
   - retry count: integer `>= 0`;
   - delay or timeout: finite numeric value `>= 0`;
   - growth factor, failure/success threshold, or capacity: integer `>= 1`.

2. **Reject `bool` before the normal integer check.** `isinstance(True, int)` is true, so a plain integer check silently accepts `True` as `1` and `False` as `0`. Use the explicit shape `isinstance(value, bool) or not isinstance(value, int)` for count-like values. Apply the same exclusion to numeric delays so booleans never masquerade as seconds.

3. **Reject non-finite floating-point time values.** A sign check alone does not reject `NaN` because both `nan < 0` and `nan >= 0` are false. Use `math.isfinite()` for accepted floats so `NaN`, positive infinity, and negative infinity cannot enter timing comparisons or sleep calculations.

4. **Validate at the earliest public construction surface.** A retry decorator factory must validate before it returns its decorator, not inside the wrapped call. A circuit breaker must validate before assigning any instance state. This makes bad configuration fail deterministically and prevents a partially initialized or registered object from escaping.

5. **Preserve domain-specific zero values.** Do not apply a blanket “all values must be positive” rule. `max_retries=0` still means one initial call; `initial_delay=0`, `max_delay=0`, and `recovery_timeout=0.0` are useful boundary configurations. Thresholds and half-open capacity require `1` as their minimum because zero makes state transitions or recovery impossible.

6. **Prove failure occurs before protected work.** Parameterize invalid values and wrap decorator construction or breaker construction plus a possible `call()` in `pytest.raises(ValueError, match=<field>)`. Keep the target as a `MagicMock`, then assert `target.assert_not_called()`.

7. **Prove the valid minima semantically, not only structurally.** For retries, configure zero retries and assert the initial attempt runs exactly once and propagates its failure. For a breaker, use every threshold/capacity at `1` and `recovery_timeout=0.0`; drive `CLOSED -> OPEN -> HALF_OPEN -> CLOSED` with one failure followed by one successful probe.

8. **Keep delegated factory semantics intact.** Convenience retry helpers should continue delegating to the validated decorator factory. A named-breaker registry should propagate `ValueError` when constructing a new breaker, while returning an existing cached breaker with its established singleton semantics.

9. **Avoid unrelated execution changes.** Once invalid configuration is blocked, leave retry iteration, exception filtering, jitter, backoff calculation, locking, and state transitions unchanged for valid inputs.

10. **Run focused and regression verification.** Start with the new configuration tests, then run the complete retry and circuit-breaker unit files, resilience integration tests, and repository lint/type checks for the touched files.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Let the retry loop handle any integer | `range(max_retries + 1)` is empty for `max_retries=-1`, so the wrapper falls through and returns `None` without calling the protected function | Loop semantics are not input validation; reject invalid counts when creating the decorator |
| Allow zero for every numeric field | `half_open_max_calls=0` makes every half-open probe fail with capacity exhaustion, while zero failure/success thresholds make transition rules nonsensical | Separate zero-valid delays/counts from positive-only thresholds and capacities |
| Check only `value < 0` for time values | `NaN < 0` is false, and elapsed-time comparisons against `NaN` never permit recovery; infinity can also make recovery unreachable | Require finite numbers with `math.isfinite()` in addition to a non-negative check |
| Accept anything passing `isinstance(value, int)` | Python accepts `True` and `False` as integers, hiding configuration mistakes and turning booleans into counts | Reject `bool` before accepting `int` |
| Validate inside the protected call | Invalid decorators or breaker objects can already escape construction, and failure no longer occurs at the configuration boundary | Validate before returning a decorator and before assigning constructor state |
| Make every value strictly positive | This breaks supported boundary behavior such as one initial attempt with zero retries and immediate half-open recovery with a zero timeout | Encode the actual domain minimum for each parameter |

## Results & Parameters

### Validation matrix

| Surface | Parameter | Accepted values | Rejected examples |
| ------- | --------- | --------------- | ----------------- |
| Retry factory | `max_retries` | non-boolean `int >= 0` | `-1`, `True`, `1.0` |
| Retry factory | `initial_delay` | non-boolean finite `int` or `float >= 0` | `-0.1`, `NaN`, infinity, `False` |
| Retry factory | `backoff_factor` | non-boolean `int >= 1` | `0`, `1.5`, `True` |
| Retry factory | `max_delay` | `None`, or non-boolean finite `int` or `float >= 0` | `-0.1`, `NaN`, infinity, `False` |
| Circuit breaker | `failure_threshold` | non-boolean `int >= 1` | `0`, `-1`, `True` |
| Circuit breaker | `half_open_max_calls` | non-boolean `int >= 1` | `0`, `-1`, `False` |
| Circuit breaker | `success_threshold` | non-boolean `int >= 1` | `0`, `-1`, `True` |
| Circuit breaker | `recovery_timeout` | non-boolean finite `int` or `float >= 0` | `-0.1`, `NaN`, infinity, `False` |

### Minimum-boundary regression shapes

```python
def test_zero_retries_still_attempts_once() -> None:
    target = MagicMock(side_effect=RuntimeError("failure"))
    decorated = retry_with_backoff(
        max_retries=0,
        initial_delay=0.0,
        backoff_factor=1,
        max_delay=0.0,
    )(target)

    with pytest.raises(RuntimeError, match="failure"):
        decorated()

    target.assert_called_once_with()
```

```python
def test_minimum_breaker_configuration_recovers() -> None:
    breaker = CircuitBreaker(
        "minimum",
        failure_threshold=1,
        recovery_timeout=0.0,
        half_open_max_calls=1,
        success_threshold=1,
    )

    with pytest.raises(RuntimeError, match="down"):
        breaker.call(MagicMock(side_effect=RuntimeError("down")))

    assert breaker.state is CircuitBreakerState.HALF_OPEN
    assert breaker.call(lambda: "recovered") == "recovered"
    assert breaker.state is CircuitBreakerState.CLOSED
```

### Locally observed pre-fix failures

| Configuration | Observed result |
| ------------- | --------------- |
| `max_retries=-1` | Decorated call returned `None`; target call count remained `0` |
| `failure_threshold=1`, `recovery_timeout=0.0`, `half_open_max_calls=0` | Breaker reached `HALF_OPEN`, then rejected the recovery probe with a half-open-capacity error |
| `failure_threshold=1`, `recovery_timeout=NaN` | Breaker remained `OPEN` after failure because the timeout comparison could never succeed |

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Retry and circuit-breaker construction-boundary plan; current failure behavior reproduced with a local read-only script | Remediation unimplemented; focused unit, integration, lint, type, and CI verification pending |
