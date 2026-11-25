---
name: gate-pass-with-warning-is-not-confirmation
license: BSD-3-Clause
description: "Treat a gate or step that passes with a warning as unconfirmed for the feature that the warning names. Use before you write that a feature works in a status report, release note, or announcement, and whenever a pass summary hides warning text inside the step output."
category: testing
date: 2026-11-25
version: "1.0.0"
user-invocable: false
tags:
- verification
- gate
- warning
- claims
- release
- status-report
- evidence
---

# Skill: gate-pass-with-warning-is-not-confirmation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Make only claims that the evidence supports when a gate reports pass but its output carries a warning |
| **Outcome** | Operational. A status report said that a key request worked end to end. The step had passed, but its own output said that the request ended in an error state. The claim was wrong and needed a correction. |

## When to Use

- You are about to write "X works" or "X is confirmed" in a status table, a release note, an announcement, or a hand-off, and your evidence is a step or gate that passed.
- A gate is built to warn and not to fail (for example a check that must not block a release). Its pass then means only "it ran".
- The summary of a run shows pass or done per step, and the step output is long or is in a separate log.
- A check runs under a service account, a different credential store, or a different host from the one an end user has.

## Verified Workflow

### Quick Reference

```bash
# Read the step output, not only the pass line.
grep -n -i -E "warn|error|denied|degraded|skipp|not (found|ready)" <step-output-file>
# List what the step actually exercised (the commands it ran, the endpoints it called).
grep -n -E "^(run|call|probe|request)" <step-output-file> | head
```

### Suggested Approach

1. **Open the step output before you claim anything.** A pass marker comes from the step logic. A warning in the same output can name the exact feature you want to claim.
2. **Name what the gate exercised.** Write the list of actions the step ran. A feature is confirmed only if one of those actions used it and succeeded without a warning that names it.
3. **Choose one of three words for each feature.**

   | Evidence | Word to use |
   | ---------- | ------------- |
   | The step exercised the feature, passed, and has no warning about it | Confirmed |
   | The step passed, but a warning names the feature or its dependency | Unconfirmed: quote the warning |
   | No step exercised the feature | Untested |

4. **Check whose environment the gate used.** A result from a service account or a different storage path does not show what an end user sees. State that limit.
5. **Confirm directly when you can.** Run a safe, read-only probe of the feature. If the probe needs a credential you do not have, list the feature as untested and say what is missing.
6. **Correct an earlier claim at once.** When you find that a past claim was wrong, say what you claimed, what the evidence shows, and what changed. Do this in the next message, before you continue.
7. **Keep announcements to confirmed items.** Put unconfirmed and untested features in a separate list for the owner to settle before publication.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the summary only | Reported a feature as working because its step showed pass in the run summary. | The step output said that the feature's request ended in an error state. The step only warned, so the run still passed. | A pass line is not a result. Read the step output. |
| Warn-only means harmless | Assumed that a non-blocking warning had no meaning. | The gate was non-blocking by design, so the warning was the only signal of failure. | A warn-only gate moves the decision to the reader. |
| Same environment | Assumed that the gate ran as an end user would. | It ran under a service identity with its own credential directory, and that directory caused the error. | State which identity and environment the evidence came from. |

## Results & Parameters

### Configuration

```text
Claim line format in a status report:
  <feature> - <word: Confirmed | Unconfirmed | Untested> - <evidence or the missing piece>
```

### Expected Output

- Every feature in the report carries one of the three words, with its evidence.
- Each Unconfirmed item quotes the warning and names who can settle it.
- An announcement lists only Confirmed items.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Release run on a shared cluster | A public-client step passed with a warning about the key request. A status report called the key request confirmed. | The report was corrected, and the announcement draft separated Confirmed from Untested. |

## References

- [acceptance-check-receipt-requires-explicit-success](acceptance-check-receipt-requires-explicit-success.md)
- [agents-pr-review-evidence-discipline](agents-pr-review-evidence-discipline.md)
- [doc-claim-drift-liveness-and-provenance-gate](doc-claim-drift-liveness-and-provenance-gate.md)
