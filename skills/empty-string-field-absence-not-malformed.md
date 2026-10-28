---
name: empty-string-field-absence-not-malformed
description: "Map an external system's documented absence encoding, such as an empty-string field, to an absent value instead of malformed input. Use when: (1) you add strict validation to a parser for external records, (2) an integration encodes 'not present' as an empty string or another sentinel, or (3) strict validation rejects the common no-value case."
category: tooling
date: "2026-10-28"
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [parsing, validation, empty-string, absence, sentinel, external-integration, slurm]
---

# Empty-String Field Means Absent, Not Malformed

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-10-28 |
| **Objective** | Stop strict external-input validation from turning the documented absence encoding of an optional field into a hard error for the common no-value case. |
| **Outcome** | A resource-accounting parser for a workload-scheduler integration maps an empty reservation-name field to an absent value and raises only for present values that fail their format check. Focused tests cover both branches. |

## When to Use

- You add or harden validation in a parser for an external system's output: CLI records, controller dumps, API payloads, or job and resource descriptions.
- The external system documents "not present" or "not applicable" for a field as an empty string, a missing key, or another sentinel.
- Strict validation starts to reject the majority of records because most of them lack the optional value.
- You must decide how an empty optional field differs from a corrupt or unsupported value.

## Verified Workflow

### Quick Reference

```python
def parse_optional_field(raw: str | None) -> Value | None:
    if raw is None or raw == "":
        return None           # documented absence encoding -> absent
    return parse_strict(raw)  # present but invalid -> malformed
```

### Suggested Approach

1. Before you add strict validation, list the interface's absence and sentinel
   encodings: empty string, missing key, `None`, and placeholder tokens such as a
   bare hyphen. Each documented encoding maps to "absent". No documented
   encoding is "malformed".
2. Validate only values that are present. A present value that fails the
   documented format is malformed. Raise or reject it with a message that names
   the field and the value.
3. Keep the two branches separate in tests. Test A: the absence encoding returns
   the absent value. Test B: a present value that fails the format raises. A
   suite that covers only B proves nothing about A.
4. Record the encoding in the parser or the integration contract. The next
   hardening pass then does not classify absence as corruption again.
5. If the interface uses more than one absence encoding, map each one on
   purpose. Collapse encodings only when the contract says that they are
   equivalent.

This rule governs parsing of external records. It does not change internal
configuration fallbacks; for that case see
[shared-default-fallback-single-source](shared-default-fallback-single-source.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| One strict check for all values | The parser design applied a single format check to every field value, with no absence branch | The workload manager encodes "no reservation" as an empty reservation-name field, so every record without a reservation failed validation; the common case became a hard error | Map the documented absence encoding to an absent value first; classify only present values as valid or malformed |

## Results & Parameters

### Decision Table

| Observed field value | Correct classification |
| -------------------- | ---------------------- |
| Empty string (documented absence encoding) | Absent; return the absent value |
| Missing key or documented placeholder sentinel | Absent |
| Present value that matches the documented format | Valid; parse it |
| Present value that fails the documented format | Malformed; raise with field context |

### Expected Output

- The parser accepts records that lack the optional value.
- The parser raises only for present values that are invalid.
- Two focused tests cover the absence branch and the malformed branch.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Private scheduler-integrated fleet service | Parser hardening for resource accounting | The workload manager encodes "no reservation" as an empty reservation-name field. The parser maps that encoding to an absent value and raises for present-but-malformed capacity fields. Both branches have unit tests. Identifying details are generalized. |

## References

- [scontrol(1) — Slurm documentation](https://slurm.schedmd.com/scontrol.html) — public reference for the workload-manager example
- [shared-default-fallback-single-source](shared-default-fallback-single-source.md) — internal configuration fallback semantics; a different decision for internal configuration
- [slurm-account-partition-discovery](slurm-account-partition-discovery.md) — absence at the result level: empty command output means no association, not a broken query
