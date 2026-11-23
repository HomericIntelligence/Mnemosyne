---
name: provenance-absence-warns-when-digest-check-remains
description: "Register or admit an artifact whose optional provenance record is absent or unverifiable with a warning instead of a refusal, when independent content-digest verification remains. Classify optional-record gaps by producer-owned exception type or structured reason, not message text. Keep required trust-receipt mismatches, unreadable artifact bytes, and unrelated verification failures on their failure paths. Use when an admission or adoption gate must distinguish a typed trace gap from an unrelated error with the same message."
category: architecture
date: 2026-11-17
version: "1.1.0"
user-invocable: false
tags:
  - provenance
  - admission
  - digest
  - fail-open
  - fail-closed
  - warning
  - traceability
  - gate-classification
  - degraded-mode
---

# Provenance Absence Warns When Digest Check Remains

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-17 |
| **Objective** | Stop an admission or registration gate from refusing an artifact only because optional provenance is missing or unverifiable, while independent content-digest verification still protects every use. Prevent message text from selecting that degraded path for an unrelated failure. |
| **Outcome** | Operational. A producer-owned optional-record gap type selects digest-only admission, records the gap, and prints one warning. An unrelated error with the same message keeps its failure outcome and causes no durable adoption or registration change. Required trust-receipt mismatches and unreadable artifact bytes still refuse. Focused negative and positive regressions pass. |

## When to Use

Use this skill when:

- An admission, adoption, or registration step refuses an input because a
  provenance artifact is absent, unreadable, or fails schema checks. Examples
  of such artifacts: a build record embedded in a disk image, a sidecar
  receipt, a signature block, a dependency lock digest.
- The same artifact passes the later trust check. A digest that is pinned at
  registration and re-verified against the bytes at each use is such a check.
- A deployment lane or offline environment cannot obtain artifacts that carry
  the provenance record, so the gate blocks all serving or builds there.
- One error message serves both the refusal and the warning, so callers and
  tests cannot tell an integrity failure from a missing record.
- A consumer searches exception text for an optional-record marker. An
  unrelated exception can contain that text and incorrectly select adoption.
- The producer already has an exception type or structured reason for an
  optional-record gap, but the adoption boundary does not use it.

Do not apply this rule when the record is itself required trust evidence. A
signature that authenticates the publisher, an entitlement that authorizes the
use, or a receipt whose digest defines the required artifact identity is not
optional traceability. Its absence or mismatch stays a refusal. Unreadable
artifact bytes and unrelated verification failures also keep their failure
outcomes.

## Verified Workflow

### Quick Reference

Classify the evidence role and failure before you choose the outcome:

| Case | Outcome |
| ----- | ------- |
| Optional trace record absent, unreadable, or schema-invalid, identified by a producer-owned type or reason | Register or admit on the independently verified content digest alone. Record the gap. Emit one warning. |
| Optional trace record has a typed mismatch, while independent required content verification succeeds | Same as absent: digest-only with a warning. Do not apply this row to a required trust receipt. |
| Required trust receipt is absent, invalid, or pins different bytes than the artifact | Refuse. This is a trust failure, not an optional gap. |
| Unrelated verification exception, even when its message contains an optional-record marker | Keep its existing failure outcome. Do not adopt, register, or change durable state. |
| Artifact bytes cannot be hashed or read | Refuse. |

### Suggested Approach

1. Classify the evidence role. A record that explains who built an artifact
   and from which inputs can be optional traceability. A digest or signature
   that the runtime requires to establish content identity or authority is
   trust evidence. Name this role in the contract; the same record format can
   have different roles at different boundaries.
2. Classify the failure at its producer. Use the exception type or structured
   reason raised where the record is read, parsed, or compared. Do not infer
   the failure family from message text. If a lower boundary erases the type,
   preserve the cause there instead of adding a text classifier at the
   consumer.
3. Find the independent verification points. A required check must compare
   the artifact bytes against the pinned digest before adoption, and every
   later use must repeat that comparison. Add either missing check before you
   relax the gate. Without continuing verification, a changed artifact serves
   silently.
4. Split the messages. Give the warning and the refusal different text. A
   warning names the missing record and the command that restores it. A
   refusal names the integrity failure. Messages are diagnostics, not branch
   discriminators.
5. Record the gap in the durable record, not only in the log. Put a
   provenance mode (for example, `receipt-verified` or `digest-only`) and the
   gap reason in the same record that carries the pinned digest. A later
   process then reads the gap without a log search.
6. Emit one warning per decision, through the same channel as other drift
   events. Do not add a second warning at each later use; the record already
   carries the mode.
7. Keep the refuse set exact. A mismatch in required trust evidence is
   tampering evidence. Unreadable or unhashable artifact bytes are a refusal.
   Authentication, path, malformed-evidence, and unrelated verification
   failures keep their existing failure outcomes. Do not convert these cases
   into optional-record gaps to make adoption succeed.
8. Test both classifier directions. An unrelated exception containing the
   optional-record marker must keep its failure outcome and leave registration
   unchanged. Typed absent and mismatched optional records must adopt only
   after independent content verification succeeds. Retain required-receipt
   refusal and unreadable-byte tests. After the split, re-check that each test
   reaches the branch it names; a refusal wrapper can mask coverage.

If the downstream re-verification point is unavailable and cannot be added,
keep the refusal. Report that condition instead of degrading silently.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | One refusal message wrapped every verification failure, including a byte mismatch against the receipt. | A byte-mismatch test passed through the refusal branch while its fixture was not even readable in the intended way. The test never reached the digest check it claimed to test. | A wrapper message masks test coverage. Split the messages first, then repair the fixture so it reaches the branch the test names. |
| 2 | Treating every verification error as one failure family. | The missing-record case and the mismatch case then share one outcome. A caller cannot tell a gap from tampering, and the operator reads the same text for both. | Classify before the outcome. The failure family, not the command result, decides warn versus refuse. |
| 3 | Classifying optional-record gaps with message substrings at the consumer. | An unrelated verification exception contained the marker and incorrectly selected digest-only adoption. The positive gap cases passed, so they did not expose the false-positive branch. | Preserve a producer-owned type or structured reason. Add a marker-lookalike regression that asserts refusal and unchanged durable state, in addition to typed positive adoption cases. |

## Results & Parameters

### Expected Output

A digest-only decision produces three artifacts:

- The record carries the pinned digest plus a provenance mode and the gap
  reason.
- The decision path prints one warning that names the missing record and the
  builder command that restores it.
- The later trust check runs unchanged and compares the bytes against the
  pinned digest at every use.

An unrelated exception with the optional-record marker produces no adoption,
registration, or other durable state change. Its original failure remains
visible to the caller.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| An inference-serving control plane | An admission verb that registers a serving image for one model | The image lacked an embedded build record and sidecar receipt; registration moved from refusal to digest-only with a warning, and the launch walk re-verified the digest at each submission. See [notes](./provenance-absence-warns-when-digest-check-remains.notes.md). |
| An inference-serving control plane | Optional embedded-record classification at adoption | A marker-lookalike regression exposed text-based false-positive adoption. Producer-owned exception identity restored refusal for unrelated errors while typed optional gaps retained digest-only adoption. See [notes](./provenance-absence-warns-when-digest-check-remains.notes.md). |

## References

- [Supporting evidence](./provenance-absence-warns-when-digest-check-remains.notes.md)
- Related skill: [derived-artifact-gate-non-vacuity](./derived-artifact-gate-non-vacuity.md) —
  the complement: make a gate fail closed when a derived artifact degrades
  silently.
