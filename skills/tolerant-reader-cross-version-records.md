---
name: tolerant-reader-cross-version-records
description: "Choose strict or tolerant parsing or path-level versioning for a record that a writer persists or publishes and a reader of another release parses. Use when a client command fails with a strict-schema error such as extra inputs are not permitted after a service adds one optional field, when a new record removes required fields that deployed readers still expect, or when you design a read-side model for a status or metadata record that crosses release boundaries."
category: architecture
date: 2026-11-04
version: "1.1.0"
user-invocable: false
tags:
  - schema-evolution
  - tolerant-reader
  - extra-forbid
  - extra-ignore
  - pydantic
  - rollout-skew
  - schema-version
  - backward-compatibility
---

# Tolerant Reader for Cross-Version Records

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-04 |
| **Objective** | Stop an additive field in a shared record from breaking older readers. |
| **Outcome** | Successful - the read model ignores unknown fields, keeps its identity and integrity checks, and a behavior test locks this. |

## When to Use

- A client command fails to parse a status or metadata record that a newer service wrote. The error is a strict-schema one, for example "Extra inputs are not permitted" from a model with `extra="forbid"`.
- The failure started after a service added one optional field.
- A new writer removes required fields or adds fields that a strict older reader forbids, and that reader is already deployed and cannot be rebuilt before the writer rolls out.
- You design or review a model that reads a persisted or published record. The writer and the reader ship on different schedules.

Do not use this entry for a record that has one release owner for both sides, or for input from an untrusted caller that must fail closed.

## Verified Workflow

### Quick Reference

```python
class RecordView(BaseModel):          # read side of a cross-version record
    model_config = ConfigDict(extra="ignore")
    ...                               # keep identity and integrity validators
```

### Suggested Approach

1. Find the cause. A closed model (`extra="forbid"`) sits on the read side of a record that other versions share. The writer and the reader roll out separately, so each added field breaks every older reader.
2. Decide by the kind of change:
   - Additive field, existing meaning unchanged: set `extra="ignore"` on the read model.
   - Meaning, type, or unit of an existing field changes: ignoring is not safe. Bump `schema_version` and make the reader reject or branch on versions it does not know.
   - A breaking change meets deployed strict readers that cannot be rebuilt: keep the predecessor shape at the original path, publish the new schema under a distinct versioned path, and make current readers use the new path. Tolerance in a future reader does not repair an older deployed reader.
3. Keep strict models for writes. Keep strict models for records that have no cross-version reader.
4. Keep the identity and integrity validators on the tolerant model (record identity, digest, required fields, value ranges). Tolerance applies to unknown names only.
5. Add one behavior test: a record with an unknown field parses, and every known field keeps its value. When you use path-level versioning, parse the predecessor projection with a strict older reader and the new record with the current reader. Do not add tests that pin the config value itself.
6. State the rollout limit. A reader that is already deployed keeps failing until it is rebuilt or replaced. The fix protects only later releases.

If the writer owner can delay the new field, that is an optional extra step. It does not replace the read-side fix.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Keep forbid on both sides | Treat the strict error as proof that the writer is wrong. | Every additive field repeats the failure for each older reader. | Strictness belongs on the write side. |
| Ignore on a changed field | Rely on `extra="ignore"` after a field changed meaning. | The old reader parses the value and uses the wrong meaning without an error. | Bump `schema_version` for meaning changes. |
| Expect an immediate cure | Fix the model and assume that all clients recover. | Deployed readers still contain the closed model. | Report the rollout limit and the rebuild need. |
| Publish a breaking record at the original path | Replace the record with a new schema and expect older strict readers to adapt. | Missing required fields and forbidden extra fields make the deployed client fail at startup. | Keep a predecessor projection at the original path and publish the new schema under a versioned path. |

## Results & Parameters

### Configuration

```yaml
read_side_cross_version_record:  {extra: ignore, validators: keep}
write_side_or_single_owner:      {extra: forbid}
existing_field_meaning_changed:  {action: bump schema_version}
breaking_change_with_deployed_strict_reader:
  original_path: predecessor_shape
  new_path: versioned_record
```

### Expected Output

- A new optional field in the record no longer breaks a rebuilt reader.
- The unknown-field test passes and known fields are unchanged.
- The report names the older readers that still fail.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Anonymized service and client | A client status command rejected a record after one optional field was added. | The read model changed to ignore unknown fields. |
| Anonymized deployed service | A new publisher replaced a discovery record with a schema that removed required fields and added fields forbidden by a deployed strict reader. | The original path kept the predecessor projection and a versioned path carried the new schema. |

## References

- [Related entry on additive fields and identity digests](descriptor-digest-readmission-additive-fields.md)
