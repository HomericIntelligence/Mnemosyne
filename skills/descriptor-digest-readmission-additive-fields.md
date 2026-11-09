---
name: descriptor-digest-readmission-additive-fields
description: "Decide deliberate re-admission versus an exclusion view when a serialized-identity digest guard fails after additive defaulted model fields. Use when a golden-vector or canonical-bytes guard breaks on schema growth, a registered or admitted identity derives from a full-spec serialization, a defaulted policy field feeds several independent identity digests, or a review asks whether new operational fields are admission-visible."
category: testing
date: 2026-10-29
version: "1.2.0"
user-invocable: false
verification: verified-local
tags:
  - golden-vector
  - descriptor-digest
  - serialized-identity
  - additive-fields
  - re-admission
  - exclusion-view
  - contract-test
  - full-spec-dump
  - gate-list
  - branch-attributable
  - multi-digest
  - nested-overrides
  - identity-projection
---

# Serialized-Identity Digest: Re-Admit or Exclude After Additive Fields

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Give a digest-guard rotation caused by additive defaulted model fields an explicit adjudication, so the rotation is a recorded re-admission or a designed exclusion view, never a silent side effect. |
| **Outcome** | Successful — an independent review caught an un-adjudicated rotation through a label-triggered CI run; envelope-convention evidence selected re-admission; the recomputed vector matched the independent reproduction byte-for-byte and the previously failed suite turned green. |

## When to Use

- A golden-vector, canonical-bytes, or sha256-of-serialized-spec guard fails on a change that only adds defaulted model fields, and the failure was not expected.
- The descriptor envelope serializes the full model (for example a `model_dump` call with every `exclude_*` switch off), so every additive field moves the digest, whether the author intended admission-visibility or not.
- A review asks for a ruling: keep the admitted descriptor stable by excluding the new fields, or rotate the admitted vector and record a re-admission.
- You decide whether a new operational field (a timeout, a retry budget, a backoff) belongs to a registered or admitted identity at all.
- Design time: a model that feeds such a digest gains a knob that must leave the byte-level digests of every existing record unchanged while the knob is unset (runtime-neutral-when-unset), and the same model already carries fields that serialize only when set.
- Design time: a defaulted, non-optional operational policy field must stay in the schema and status projections but must not change recipe, artifact, or fast-start identities, and the model also serializes a nested override map.

Do not use this entry when the guard failure comes from host or environment noise; prove that first with the base-versus-head reproduction below.

## Verified Workflow

### Quick Reference

```bash
# Reproduce the guard against the merge base and the branch head.
pytest <guard-suite>                 # at the merge base: expect pass
pytest <guard-suite>                 # at the branch head: expect fail, with actual digest in the assertion

# Recompute the admitted values on the branch tree with the guard's own helpers.
python3 -c '<load spec; print(digest and target identity)>'
```

### Suggested Approach

1. **Prefer exclusion-by-construction when the knob must be runtime-neutral-when-unset and the model supports it.** Design before any guard failure: when unchanged records must keep byte-identical digests, give the new field an exclusion-declared optional default (for pydantic ≥ 2.12, `Optional` with `Field(exclude_if=lambda value: value is None)`; the equivalent declaration in another serializer) so an unset value serializes to absence. Wire the value path as "omitted" (unset, default, absent from input) in every direction, and render the downstream behavior only when the field is set. Verify with a direct probe (dump a default instance; the key must be absent), lock it with a serialization-invariance test plus a field-limits contract test, and regenerate the derived schema with the repository exporter — include the exporter diff in the change evidence when no byte-sync gate exists for the generated file.
2. **When the field must serialize, exclude it at each digest boundary.** Use this branch when the field has a meaningful default that the schema and status must show, so `exclude_if` cannot make it absent. Find every identity that serializes the model: search for `model_dump`, the identity functions, and their callers. Add the field to each digest exclusion. Strip nested override maps too: an override model serializes the field as `null` or a value even when no override is set, so a top-level pop alone leaves the digest rotated. Use one shared strip helper when two owners serialize the same shape. Keep a separate exclude-set owner only when it already drops the whole nested map. Add one invariance test for each owner: change the top-level field and one nested override, and keep every sibling override in the fixture. A fixture that replaces the whole override map changes the digest for an unrelated reason and gives a false positive. Do not exclude a launch or artifact input; keep those fields in the identity.
3. **Prove the rotation is branch-attributable first.** Run the guard at the merge base (pass) and at the head (fail). Compare the failing digest between your run and any independent CI reproduction; a byte-for-byte match removes host-noise doubt and confirms delta attribution to the change itself.
4. **Read the envelope convention before you rule — scoped to the same model and family.** Ask one question: do same-class operational fields (the pre-existing timeout, retry, or budget family in the same model) already appear in the serialized identity?
   - **Yes — the convention serializes operational fields.** Select **deliberate re-admission**: the new fields share that class, so a new exclusion only for them invents a second, inconsistent contract and silently weakens the guard's "rotation is a deliberate admission event" rule for exactly the fields operators need to notice. Recompute the descriptor digest and every derived identity on the admitting tree with the guard's own helper functions, or take the exact actual values from the failing assertion, and confirm they equal the independent CI reproduction. Update the bound constants. Update the guard's provenance comment so the record names the cause of the rotation.
   - **No — the envelope is identity-curated** (an explicit field allowlist or a named stability projection). Select **descriptor stability**: extend the curation so the new fields are excluded, and keep the admitted vector unchanged. Implement the view in one place; do not scatter exclusions across call sites.
   - **The model carries both conventions** (one family always serializes; another serializes only when set through an exclusion declaration). Apply the family-local rule to the new field: a member of the always-serialized family takes re-admission; a member of the exclude-when-unset family takes the exclusion-by-construction path from step 1; a field that must stay serialized but is policy-only takes the projection path from step 2. Do not average the two conventions into a third one.
5. **Close the gate gap.** If the guard suite was absent from the change's own validation list, add it permanently. A full-spec dump makes any future spec-model change a candidate rotation; the suite is the only detector.
6. **Keep generated companions machine-regenerated.** If schema or documentation files derive from the same model, regenerate them with the repository exporter. Do not hand-edit generated bytes.

Continue without stopping when an optional step is unavailable: a missing independent CI run does not block the local convention analysis, and a local reproduction with the guard's helper functions is enough to bind the new values.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Exclude only the new fields because "operational fields are not identity" | Exclusion has no convention basis when the envelope already serializes the same-class operational family | It creates an ad-hoc second contract and re-opens the same guard failure for the next reviewer | Convention evidence (what same-class fields already do) outranks category-label intuition |
| Rely on reduced local gates and let the label-triggered CI catch the rotation | The rotation was detected, but a full review round and head re-freeze were spent on attribution | Label CI works as a fallback, not as the primary detector | Pin every golden-vector or digest guard in the permanent gate list of any change that touches the underlying model |
| Consider stripping only the top-level field from a digest that also serializes a nested override map | The override map still carried the key (verified in the model dump), so the digest would rotate | A model dump has more than one copy of a nested policy field | Enumerate each serialized position, including every override entry |
| Change one scope override but replace the whole override map in the invariance fixture | The sibling override disappeared, so the digest changed for an unrelated reason | The test compared two variables at once | Keep every sibling override and change only the target key |

## Results & Parameters

### Configuration

```yaml
# Record layout after re-admission, in the guard source:
bound_descriptor_digest: "<new-sha256>"      # recomputed on the admitting tree
bound_target_identity:   "<prefix>-<new-sha256>"
provenance_comment:      "rotation cause, named fields, tree used for recomputation"
gate_list_addition:      "<guard-suite path>"  # permanent, for every spec-model change
```

```python
# One shared projection helper for every digest that serializes the same model.
def strip_policy_field(payload):
    payload.pop("policy_field", None)
    overrides = payload.get("overrides")
    if isinstance(overrides, dict):
        payload["overrides"] = {
            name: {key: value for key, value in entry.items() if key != "policy_field"}
            for name, entry in overrides.items()
        }
```

Build a new override mapping. A caller that passes a shallow mapping copy must
keep its own nested dictionaries.

### Expected Output

- The guard passes at the head with the updated bound values.
- The recomputed values equal the failing assertion's actual values and any independent CI reproduction, byte-for-byte.
- The change records name the ruling (re-admission or stability), the convention evidence, and the recomputed values.
- Generated schema and documentation companions stay byte-identical to exporter output.
- Each digest owner is byte-identical when only the policy field changes, at the top level and in a nested override.
- The schema still contains the field, and each nested override still accepts it.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A deployment-runtime repository | Independent PR review round against a serialized admission descriptor; label-gated CI | [notes](../skills/descriptor-digest-readmission-additive-fields.notes.md) |
| A deployment-runtime repository | Design-time exclusion-by-construction for a runtime-neutral-when-unset serving knob on a full-dump policy model; probe plus invariance-test verification | [notes](../skills/descriptor-digest-readmission-additive-fields.notes.md) |
| A deployment-runtime repository | A defaulted operational policy field on a model with nested per-scope overrides; recipe, runtime-contract, and fast-start digest invariance tests | [notes](../skills/descriptor-digest-readmission-additive-fields.notes.md) |

## References

- [Address-Review: Pre-Existing / Unrelated Local Gate Failure](address-review-preexisting-unrelated-precommit-failure.md)
