---
name: python-metric-validation-api-cli-domain-parity
description: "Enforce explicit metric domains across Python APIs and argparse CLIs. Use when: (1) helpers accept negative counts or durations, (2) percentages permit NaN, infinity, or impossible ranges, (3) CLI inputs must exit 2 while programmatic callers receive documented ValueErrors."
category: tooling
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [python, argparse, valueerror, metrics, validation, telemetry, finite, boundary-testing]
---

# Python Metric Validation API and CLI Domain Parity

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Give metrics explicit domains, reject misleading telemetry programmatically with `ValueError`, and map invalid CLI inputs to standard `argparse` usage errors with exit code 2. |
| **Outcome** | A reviewed validator and boundary-test pattern; implementation and CI validation are pending. |
| **Verification** | unverified |

Metric-rendering helpers often begin as permissive formatters. Once they are called directly by
other Python code and through a CLI, permissiveness becomes ambiguity: negative counts,
non-finite percentages, or unsupported status strings can render plausible but false telemetry.
The two entry surfaces need different error presentation while enforcing the same domain.

## When to Use

- Public helpers accept elapsed times, counts, thresholds, percentages, or enumerated statuses.
- Invalid programmatic values currently produce a fallback such as `0.0` or a misleading table.
- A Python `bool` must not be accepted merely because `bool` is a subclass of `int`.
- A CLI should emit standard usage text and `SystemExit(2)` for invalid arguments.
- Negative deltas are meaningful but impossible upper bounds or non-finite values are not.
- Values computed elsewhere can bypass validation unless rendering functions validate again.

## Verified Workflow Status

No end-to-end workflow has been verified. The design below comes from a reviewed
ProjectHephaestus implementation plan and must remain a proposal until the focused tests and CI
suite pass.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms.

### Quick Reference

```python
import argparse
import math

_VALID_STATUSES = ("failed", "passed")


def _require_non_negative_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")


def _require_finite_percentage(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite percentage in 0..100")
    if not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError(f"{field_name} must be a finite percentage in 0..100")


def _parse_non_negative_int(value: str) -> int:
    parsed = int(value)
    _require_non_negative_int(parsed, "value")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--elapsed", type=_parse_non_negative_int, required=True)
    parser.add_argument("--files", type=_parse_non_negative_int, default=0)
    parser.add_argument("--status", choices=_VALID_STATUSES, default="passed")
    parser.add_argument("--threshold", type=_parse_non_negative_int, default=120)
    return parser
```

Public functions validate and document their own contracts:

```python
def check_threshold(elapsed_s: int, threshold_s: int = 120) -> bool:
    """Return whether elapsed time exceeds the threshold.

    Raises:
        ValueError: If either duration is not a non-negative integer.
    """
    _require_non_negative_int(elapsed_s, "elapsed_s")
    _require_non_negative_int(threshold_s, "threshold_s")
    return elapsed_s > threshold_s
```

### Detailed Steps

1. Write each metric's domain before writing validation:
   - Positive integer: denominators such as a cold-build duration.
   - Non-negative integer: elapsed time, counts, warm duration, and thresholds.
   - Closed percentage: finite value in `0..100`.
   - Directional delta: finite value with a meaningful negative range and an upper bound such as
     `<= 100`.
   - Enumeration: exactly the states the renderer implements.
2. Use small local validators when domains are module-specific. Reject `bool` explicitly before
   `int` or `(int, float)` checks.
3. Validate in every public programmatic function, including renderers that receive derived
   values. Do not assume another helper computed the argument.
4. Raise `ValueError` with the field name and domain, and add a Google-style `Raises:` section to
   public docstrings.
5. For CLI integer arguments, use an `argparse` type converter that calls the same domain
   validator. `argparse` converts the resulting conversion failure into usage output and
   `SystemExit(2)`.
6. Use `choices=` for closed string domains. Avoid reproducing enumeration checks after parsing.
7. Preserve semantically valid negative deltas. For a build reduction, a negative value can
   accurately mean the warm build regressed; reject non-finite values and values above `100`, not
   all negatives.
8. Add boundary-first tests before implementation: zero where valid, one or another positive
   value where required, exact `0` and `100` percentages, negative deltas, just-outside values,
   `NaN`, infinities, booleans, unsupported statuses, and CLI exit code `2`.

### Domain-Specific Example: Build Reduction

```python
def compute_reduction(cold_seconds: int, warm_seconds: int) -> float:
    """Compute percentage reduction in build time.

    Raises:
        ValueError: If cold_seconds is not positive or warm_seconds is negative.
    """
    if isinstance(cold_seconds, bool) or not isinstance(cold_seconds, int) or cold_seconds <= 0:
        raise ValueError("cold_seconds must be a positive integer")
    _require_non_negative_int(warm_seconds, "warm_seconds")
    return round((cold_seconds - warm_seconds) / cold_seconds * 100, 1)


def _require_reduction(value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("reduction must be a finite number no greater than 100")
    if not math.isfinite(value) or value > 100:
        raise ValueError("reduction must be a finite number no greater than 100")
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Return `0.0` for a zero or negative denominator | Treat invalid cold duration as a harmless reduction fallback. | It hides invalid input and emits plausible telemetry with no indication that the calculation was undefined. | Reject invalid denominators with a documented `ValueError`. |
| Validate only in CLI parsing | Trust CLI validation to protect helpers. | Direct Python callers and tests can still supply invalid values. | Public helpers own programmatic contracts; CLI parsing adapts those contracts for operators. |
| Validate only in the computation helper | Assume a renderer always receives values from the trusted calculator. | Renderers are public and can receive externally computed `NaN`, infinity, or impossible percentages. | Validate at every public boundary that promises a metric domain. |
| Use `isinstance(value, int)` alone | Accept booleans as integer metrics. | In Python, `isinstance(True, int)` is true, but boolean durations and counts are misleading. | Reject `bool` before numeric type checks. |
| Reject every negative percentage | Apply a generic `0..100` rule to directional reductions. | Negative reduction is valid telemetry for a regression or slower warm build. | Model each metric's semantics; finite and `<= 100` is the correct reduction domain. |
| Raise ad hoc CLI exceptions | Let `ValueError` escape from the entrypoint or print a custom error and return an arbitrary code. | Operators receive a traceback or nonstandard exit behavior. | Use `type=` and `choices=` so `argparse` owns usage diagnostics and exit code 2. |

## Results & Parameters

Example domain table:

| Metric | Valid domain | Invalid examples |
|--------|--------------|------------------|
| Cold duration denominator | Integer `> 0` | `0`, `-1`, `True` |
| Warm duration, elapsed time, count, threshold | Integer `>= 0` | `-1`, `False`, `1.5` |
| Acceptance threshold | Finite number in `0..100` | `-0.1`, `100.1`, `NaN`, infinity |
| Reduction/directional improvement | Finite number `<= 100`; negatives allowed | `100.1`, `NaN`, infinity |
| Hook status | Exact implemented states | Unknown strings, alternate casing |

Boundary tests:

```python
import math
import pytest


def test_zero_boundaries_are_valid() -> None:
    assert check_threshold(0, 0) is False
    assert compute_reduction(100, 0) == 100.0


def test_negative_reduction_is_preserved() -> None:
    assert compute_reduction(100, 120) == -20.0


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, 100.1])
def test_reduction_rejects_invalid_values(value: float) -> None:
    with pytest.raises(ValueError):
        _require_reduction(value)


@pytest.mark.parametrize(
    "argv",
    [
        ["--elapsed", "-1"],
        ["--elapsed", "1", "--files", "-1"],
        ["--elapsed", "1", "--threshold", "-1"],
        ["--elapsed", "1", "--status", "unknown"],
    ],
)
def test_cli_rejects_invalid_inputs_with_usage_error(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(argv)
    assert exc_info.value.code == 2
```

Suggested verification commands:

```bash
<package-manager> pytest <metric-helper-test-path> <cli-test-path> -v
<package-manager> pytest <ci-helper-test-directory> -v
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Reviewed implementation plan for Docker timing and pre-commit benchmark metric validation | Not implemented; local and CI validation pending. |
