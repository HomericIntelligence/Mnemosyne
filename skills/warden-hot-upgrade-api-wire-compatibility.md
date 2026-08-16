---
name: warden-hot-upgrade-api-wire-compatibility
license: BSD-3-Clause
description: "Use when: (1) tightening an existing Warden or control-plane request field while rolling hot upgrades must remain possible, (2) an optional API field should have stricter CLI or wizard validation without narrowing the predecessor wire contract, (3) hot-upgrade preflight rejects a target because its request schema no longer accepts every predecessor-valid payload."
category: architecture
date: 2026-08-03
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - warden
  - hot-upgrade
  - api-compatibility
  - json-schema
  - cli-validation
---

# Warden Hot-Upgrade API Wire Compatibility

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-03 |
| **Objective** | Tighten operator input without making an existing rolling-upgrade request schema incompatible with its predecessor. |
| **Outcome** | Verified that preserving the existing API wire shape while validating new CLI input separately allows the real predecessor-to-target compatibility check to pass. |

## When to Use

- A hot-upgrade preflight compares the active control plane's API schema with the target schema.
- An existing optional string schema permits empty and whitespace-only strings, but a new CLI or wizard should reject that explicit input.
- Runtime normalization already treats an empty optional value as omission, yet adding `minLength`, `pattern`, `enum`, or a required-field constraint breaks upgrade compatibility.
- Endpoint tests pass in isolation but do not prove that every payload accepted by the predecessor remains accepted by the target.

## Verified Workflow

### Quick Reference

1. Treat the predecessor's published request schema as the compatibility floor for the lifetime of that API version.
2. Do not narrow an existing field in place. Preserve its type, requiredness, enum, length, and pattern constraints unless the API version changes under an explicit migration contract.
3. Put stricter validation at the new operator entry point, such as a CLI or wizard, before it submits the request.
4. Keep server-side normalization for predecessor-valid sentinel values when omission is the intended semantic result.
5. Run the real predecessor-to-target compatibility checker in a behavior test, then test the operator and API boundaries independently.

### Detailed Steps

1. Obtain the predecessor schema from the immutable active revision or construct the exact predecessor property shape in a focused compatibility fixture.
2. Identify every narrowing change in the target request schema. Common incompatible changes include:
   - optional to required;
   - broader type to narrower type;
   - adding or shrinking an enum;
   - adding `minLength`, `maxLength`, or `pattern`;
   - reducing accepted object properties or array shapes.
3. Restore the target field to the predecessor wire shape. For an optional string that historically accepted all strings, retain only `type: string` at that API version.
4. At the CLI or wizard boundary, reject an explicitly supplied empty or whitespace-only value before any network submission.
5. At the API boundary, preserve predecessor behavior exactly. For example, continue normalizing the empty string to omission when that is established, while leaving whitespace or unknown-name handling unchanged.
6. Add three behavior tests:
   - the real compatibility checker accepts predecessor to target;
   - the CLI or wizard rejects an explicitly blank value without submitting;
   - the API accepts the predecessor-valid blank value and the resolved request observes omission semantics.
7. Run focused tests and the repository's complete validation before attempting a dry-run or live hot upgrade.

The compatibility test must exercise the production compatibility algorithm. Comparing schema hashes, asserting raw schema text, or checking documentation wording does not prove substitutability.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Tighten the existing API schema | Added non-empty and non-whitespace constraints to an optional string field. | The target no longer accepted all requests accepted by the active predecessor, so hot-upgrade compatibility correctly failed closed. | A same-version rolling target may extend a request schema compatibly, but it must not narrow it. |
| Rely on runtime normalization | Kept code that converted blank input to omission and expected upgrades to remain compatible. | The compatibility gate compares accepted wire shapes before runtime normalization executes. | Runtime semantic equivalence cannot repair transport-level incompatibility. |
| Use one strict rule for CLI and API | Rejected blank values at both the new wizard and the existing API endpoint. | This improved new UX by breaking old clients and rolling upgrades. | Validate more strictly at the new operator boundary while preserving the established API contract. |
| Test endpoint behavior only | Verified current requests against the target without invoking the predecessor-to-target checker. | A target can pass standalone tests while still rejecting a predecessor-valid request. | Add an executable cross-version compatibility regression using the real checker. |

## Results & Parameters

### Configuration

Preserve the established wire shape:

```yaml
properties:
  promotion_policy:
    type: string
```

Apply stricter validation at the new operator boundary:

```python
value = supplied_value.strip()
if not value:
    parser.error("the explicit policy selection must not be blank")
```

Preserve established API semantics without broadening normalization:

```python
def optional_payload_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text or None
```

### Expected Output

- The predecessor-to-target compatibility check succeeds for the same API version.
- New CLI and wizard users receive an immediate error for explicitly blank input.
- Existing API clients can still send the predecessor-valid empty string, which resolves identically to omission; other strings retain their predecessor semantics.
- Hot-upgrade preflight remains fail-closed for genuine incompatible schema changes.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Inference360 | PR #528 optional promotion-policy publication | The real hot-upgrade API compatibility regression, focused suites, and full repository validation passed after restoring the predecessor wire shape and retaining strict wizard validation. |

## References

- [Inference360 PR #528](https://github.com/LLM360/Inference360/pull/528)
- [Warden hot-upgrade listener isolation](warden-hot-upgrade-listener-isolation.md)
