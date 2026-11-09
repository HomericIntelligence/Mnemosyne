---
name: pydantic-discriminator-multi-variant-state
license: BSD-3-Clause
description: "Validate a persisted document that has more than one schema variant with a Pydantic v2 callable Discriminator instead of a raw Union. Use when: (1) a state or configuration document on disk has no version field but older and newer writers produce different shapes, (2) raw Union validation gives each failing entity one error per variant and buries the true causes, (3) a checked-in generated JSON Schema must stay equal to the model output, (4) every reader must report the file, the first failing path, and the document identity."
category: tooling
date: 2026-11-09
version: "1.0.0"
user-invocable: false
tags:
  - pydantic
  - discriminator
  - tagged-union
  - schema-migration
  - validation-fan-out
  - json-schema-regeneration
  - actionable-errors
  - python
---

# Pydantic Discriminator for Multi-Variant State

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Validate persisted documents that have more than one historical schema shape, with strictness kept and with errors an operator can use |
| **Outcome** | Verified: one production incident repair; the raw-Union error fan-out of 92 messages collapsed to the 2 true causes; checked-in JSON Schema regenerated; 13 targeted tests RED then GREEN |

A persisted state or configuration document can survive several schema
revisions with no version field. A raw Pydantic v2 `Union[V1, Vn]` tries
each variant in order for each failing entity. The operator receives
entities x variants errors, and the true causes stay invisible. An
`Annotated[Union, Discriminator(callable)]` tags each document with one
variant before validation, so each failure has one message, and the
location path names the variant.

## When to Use

Use this skill when these conditions apply:

- More than one writer generation produced, or will produce, documents with
  the same purpose but different shapes, and the documents carry no version
  field.
- Raw union validation floods the operator: each failing entity causes one
  error per legacy variant, and the real defect is hard to find.
- A boot-time or operator-facing reader must give the file path, the first
  failing location, the cause, and the document identity, without document
  payload values.
- The repository keeps a generated JSON Schema file checked in, and the
  schema must stay equal to `model_json_schema()` output.

Do not use this skill to make invalid legacy data pass. Do not add a
permissive flag that skips validation. Repair the data or route it through
a guarded migration tool.

## Verified Workflow

### Quick Reference

```python
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Discriminator, Tag


def _document_schema_tag(value: object) -> str:
    """Pick one variant for each document. Never raise."""
    # Instance checks first, then mapping checks for raw payloads.
    if isinstance(value, StateV3):
        return "v3"
    if isinstance(value, dict):
        # Structural markers of the newer shape; a version field can be absent.
        return "v3" if "new_required_field" in value or "marker" in value else "v1"
    # Unknown and future shapes go to the earliest variant. The message then
    # names the v1 rules that the document broke.
    return "v1"


DocumentState = Annotated[
    Union[Annotated[StateV1, Tag("v1")], Annotated[StateV3, Tag("v3")]],
    Discriminator(_document_schema_tag),
]
```

### Suggested Approach

1. Enumerate the historical shapes from writer search and shipped release
   tags before you change code. Each shape becomes one variant. Record the
   search commands and results; do not guess the writer set.
2. Give the tag function these properties:
   - Never raise. Unknown or future shapes fall back to the earliest
     variant. A tag function that can miss every variant turns the failure
     into an untyped `union_tag_not_found` error with no actionable
     location.
   - Instance checks before mapping checks, then cheap structural markers
     of the newer shapes. Do not depend on a version field that older
     writers did not emit.
3. Replace each raw `Union[V1, Vn]` alias on the persisted document model
   with the discriminated alias. Keep strict validation everywhere.
4. Expect the error count to collapse. Measure the raw-Union count first
   (RED), then assert the post-change count equals only the true causes
   (GREEN). Location paths include the tag literal, for example
   `('entities', '<name>', 'v1', 'field')`.
5. Regenerate every checked-in generated JSON Schema file in the same
   change. A callable `Discriminator` emits `oneOf` for the union; a plain
   `Union` emits `anyOf`. A regenerated schema diff between `anyOf` and
   `oneOf` is the freshness proof. Verify with
   `Model.model_json_schema()`.
6. Give all readers of the document one shared error-message helper:
   - report the file path, the first failing location, the validator
     cause, and the stable document identity;
   - keep the content digests or identities only; never copy document
     payload values into the message;
   - raise the reader-facing error with `raise ... from error` so
     `__cause__` keeps the `ValidationError` for debugging;
   - wrap every reader of the document, including the migration and
     activation readers, not only the primary boot reader.
7. Add regression tests for these behaviors:
   - a poisoned legacy document causes exactly the true-cause count, not
     the per-variant fan-out;
   - tag edge cases: missing markers select the earliest variant, an
     unknown future shape selects the earliest variant, the function never
     raises;
   - clean documents validate byte-for-byte identical identities before
     and after the change (`release_id`-style integrity unchanged).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Raw `Union` on legacy documents | Validated each document by trying every variant in order | One failure per variant per entity (measured: 92 errors from 18 entities x 5 variant errors plus 2 true causes) buried the real causes | Discriminate each document before validation; validate it once against one variant |
| Change the model only | Added the discriminator without regenerating the checked-in JSON Schema | The checked-in schema still emitted `anyOf` for the union while `model_json_schema()` now emitted `oneOf`; review required the regeneration | Regenerate generated artifacts in the same change and include the diff |
| Depend on a version field, or let the tag miss | A tag function that can return nothing (the default tagged-union behavior) | Missing markers or future shapes fail with an untyped `union_tag_not_found` error and no actionable location | Fall back to the earliest variant; never raise from the tag function |
| Reader pass-through | Let `ValidationError` escape from the boot reader unchanged | The operator received a 92-line dump with no file, no first failing location, and no document identity; more restarts repeated the failure | Wrap all readers with one shared helper; keep `__cause__`; wrap the activation and migration readers too |
| Permissive flag | A post-incident proposal to let invalid legacy documents load silently | Keeps the defect invisible and makes the poisoning state undetectable | Keep validation strict; repair data or use a guarded migration tool |

## Results & Parameters

### Expected Output

- Each failing document produces one `ValidationError` entry per true
  cause. Location paths contain the matched variant tag.
- The reader-facing error contains the file path, the first failing
  location, the cause, and the document identity, with no payload values,
  and keeps the `ValidationError` as `__cause__`.
- `Model.model_json_schema()` for the union field uses `oneOf`; the
  regenerated checked-in schema diff shows `anyOf` to `oneOf`.
- Tests pass with an exact error-count assertion (true causes only), tag
  edge-case tests, and an identity-unchanged test for clean data.

### Behavior Reference

| Item | Value |
| ------- | ------- |
| Plain union alias (no `Discriminator`) in `model_json_schema()` | `anyOf` |
| `Annotated[Union, Discriminator(callable)]` in `model_json_schema()` | `oneOf` |
| Tag function miss (no matching variant) | `union_tag_not_found`; untyped, no entity path |
| Location path with a tag | `(..., '<entity-key>', '<tag-literal>', ...)` |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal deployment-state repository | Production incident repair, merged change | Generalized per privacy rules; measurements, commands, and review evidence in [notes](pydantic-discriminator-multi-variant-state.notes.md) |

## References

- [Pydantic discriminated unions with callable discriminators](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-callable-discriminators)
- [Pydantic JSON Schema generation](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [pydantic-json-schema-dual-validation](pydantic-json-schema-dual-validation.md) — dual-layer enforcement of one cross-field invariant
- [config-validation-and-schema-alignment](config-validation-and-schema-alignment.md) — schema generation from models and loader wiring
