---
name: ty-classmethod-isinstance-cls-no-narrow
license: BSD-3-Clause
description: "In a classmethod that rebuilds one of two types from a union parameter, narrow with the concrete class name, not `isinstance(value, cls)` - ty treats `cls` as an unbound `type[Self]` and skips narrowing, so attribute access on the other union member fails the type check. Use when ty reports a union-assignability or missing-attribute error on the line after an isinstance check against `cls`."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - ty
  - type-checker
  - narrowing
  - isinstance
  - classmethod
  - type-self
  - union
  - pydantic
  - dataclass
  - python
---

# Narrow a Union in a Classmethod With the Concrete Class, Not `cls`

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-30 |
| **Objective** | Make a classmethod that accepts either of two types return one of them without a type-check error. |
| **Outcome** | A `from_verified`-style classmethod typed `value: Raw | Cooked` started with `if isinstance(value, cls): return value`. The checker did not narrow: after the branch, `value` stayed `Raw | Cooked`, and building the result from the remaining branch failed with an assignability error, because `cls` is an unbound `type[Self]` to the checker, not the concrete class. Writing the concrete class name in the isinstance test fixed the check with no annotation tricks. |

## When to Use

- A classmethod (for example a transport-form rebuild such as `from_dict` or `from_verified`) accepts a union of two types and returns one of them.
- The first branch tests `isinstance(value, cls)` to pass an already-built instance through.
- The type checker reports, on the lines after the branch, that the value is still the full union: an attribute exists on only one member, or a field of one member is not assignable to the other's.

## Verified Workflow

1. Reproduce the diagnostic. Run the checker on the module:

```
error: Object of type `Raw | Cooked` is not assignable to `Raw`
```

on the line that builds the result from `value`'s fields, after an `isinstance(value, cls)` early return.

2. Replace `cls` with the concrete class name in the test:

```python
@classmethod
def from_verified(cls, value: Raw | Cooked) -> Cooked:
    if isinstance(value, Cooked):   # concrete name, not cls
        return value
    return cls(
        field=value.raw_field.decode("utf-8"),
    )
```

The negative branch now narrows `value` to `Raw`, and the checker accepts the attribute access.

3. Re-run the checker on the module and on every caller of the classmethod; the early-return branch also gives callers that already hold a built instance a no-op pass-through with no cast.

### Quick Reference

```python
if isinstance(value, cls):        # no narrowing: cls is type[Self]
    ...
if isinstance(value, Cooked):     # narrows the union
    ...
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | Keep `isinstance(value, cls)` and annotate an intermediate variable with the expected type (`source: Raw = value`) | The checker rejected the assignment itself: the union was never narrowed, so the annotation only moved the error to a new line | Fix the narrowing, not the annotation downstream of it |
| 2 | Read the error as a decode problem on the field type | The field types were correct on both classes; the defect was that the union still contained the wrong member at that line | A union-assignability error after a branch test means the branch did not narrow |

## Results & Parameters

- Diagnostic signature: a union-assignability error on the first line after `if isinstance(value, cls):` inside a classmethod.
- Fix: one identifier change in the isinstance test; no `cast`, no `type: ignore`, no added runtime checks.
- Scope note: the same pattern applies to any classmethod rebuild over a union, not only serialization helpers.
- Verification: verified-local; the module type-checks clean after the change, and the focused tests pass.
- Freshness limit: observed with one ty release; later releases may narrow `type[Self]` differently. Re-run the checker before relying on either behavior.
