---
name: provenance-absence-warns-when-digest-check-remains
description: "Register or admit an artifact whose provenance record is absent or unverifiable with a warning instead of a refusal, when an independent content-digest check still guards every use. Refuse a pinned-digest mismatch or unhashable bytes. Use when an admission or adoption gate refuses inputs for missing provenance, when the same artifact passes the later trust check, when a deployment lane cannot obtain provenance-built artifacts, or when one message serves both the refusal and the warning."
category: architecture
date: 2026-11-17
version: "1.0.0"
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
| **Objective** | Stop an admission or registration gate from refusing an artifact only because a provenance record is missing, while a content-digest check still protects every use. |
| **Outcome** | Operational. The admission path registers such an artifact on its digest alone, records the gap in the durable record, and prints one warning. A receipt that pins different bytes still refuses. Focused suites pass; one environment-dependent failure is unrelated. |

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

Do not apply this rule when the provenance record is itself the trust
boundary. A signature that authenticates the publisher, or an entitlement
that authorizes the use, is not traceability. Its absence stays a refusal.

## Verified Workflow

### Quick Reference

Classify each verification failure before you choose the outcome:

| Case | Outcome |
| ----- | ------- |
| Provenance record absent | Register or admit on the content digest alone. Record the gap. Emit one warning. |
| Provenance record present but unreadable or schema-invalid | Same as absent: digest-only with a warning. |
| Provenance record present but it pins different bytes than the artifact | Refuse. This is an integrity failure, not a gap. |
| Artifact bytes cannot be hashed or read | Refuse. |

### Suggested Approach

1. Classify the check. A record that explains who built an artifact and from
   which inputs is traceability. A digest or signature that the runtime
   compares against the bytes is the trust check. Only the trust check may
   refuse on absence.
2. Find the downstream re-verification point. The digest-only path is safe
   only when some later step compares the artifact bytes against a digest
   that the registration pinned. If no such step exists, add it before you
   relax the gate. Without it, a changed artifact serves silently.
3. Split the messages. Give the warning and the refusal different text. A
   warning names the missing record and the command that restores it. A
   refusal names the integrity failure. One wrapper message for all failures
   hides which branch ran.
4. Record the gap in the durable record, not only in the log. Put a
   provenance mode (for example, `receipt-verified` or `digest-only`) and the
   gap reason in the same record that carries the pinned digest. A later
   process then reads the gap without a log search.
5. Emit one warning per decision, through the same channel as other drift
   events. Do not add a second warning at each later use; the record already
   carries the mode.
6. Keep the refuse set exact. A digest mismatch between the artifact and its
   own receipt is tampering evidence. Unreadable or unhashable bytes are a
   refusal. Both stay fatal.
7. Update the tests that asserted the refusal. A refusal wrapper can mask a
   test: see Failed Attempts. After the split, re-check that each test
   reaches the branch it names.

If the downstream re-verification point is unavailable and cannot be added,
keep the refusal. Report that condition instead of degrading silently.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | One refusal message wrapped every verification failure, including a byte mismatch against the receipt. | A byte-mismatch test passed through the refusal branch while its fixture was not even readable in the intended way. The test never reached the digest check it claimed to test. | A wrapper message masks test coverage. Split the messages first, then repair the fixture so it reaches the branch the test names. |
| 2 | Treating every verification error as one failure family. | The missing-record case and the mismatch case then share one outcome. A caller cannot tell a gap from tampering, and the operator reads the same text for both. | Classify before the outcome. The failure family, not the command result, decides warn versus refuse. |

## Results & Parameters

### Expected Output

A digest-only decision produces three artifacts:

- The record carries the pinned digest plus a provenance mode and the gap
  reason.
- The decision path prints one warning that names the missing record and the
  builder command that restores it.
- The later trust check runs unchanged and compares the bytes against the
  pinned digest at every use.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| An inference-serving control plane | An admission verb that registers a serving image for one model | The image lacked an embedded build record and sidecar receipt; registration moved from refusal to digest-only with a warning, and the launch walk re-verified the digest at each submission. See [notes](./provenance-absence-warns-when-digest-check-remains.notes.md). |

## References

- [Supporting evidence](./provenance-absence-warns-when-digest-check-remains.notes.md)
- Related skill: [derived-artifact-gate-non-vacuity](./derived-artifact-gate-non-vacuity.md) —
  the complement: make a gate fail closed when a derived artifact degrades
  silently.
