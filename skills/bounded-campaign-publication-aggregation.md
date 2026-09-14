---
name: bounded-campaign-publication-aggregation
description: "Use when an append-only, multi-cycle public report projection approaches its hard total-size cap because each cycle repeats cumulative aggregates, while prior-cycle bytes and hash evidence must stay immutable. Promote the newest cumulative aggregates once at the campaign root, record the per-cycle omission, and verify the atomic extension instead of raising the cap or deleting bound evidence."
category: documentation
date: 2026-09-11
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - campaign-reporting
  - publication
  - size-cap
  - cumulative-aggregate
  - immutable-evidence
  - atomic-extension
---

# Bound Cumulative Reports Without Duplicating Them

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-09-11 |
| **Objective** | Extend a bounded, hash-indexed campaign publication after repeated cumulative reports would exceed its hard size cap. |
| **Outcome** | Operational. Keep prior cycle projections unchanged. Put the newest cumulative aggregate at the campaign root, and record why the new cycle does not contain a duplicate. |

## When to Use

Use this rule when all these conditions apply:

- A public projection contains immutable per-cycle evidence and a campaign-level manifest.
- The projection has a hard total-size limit.
- Each cycle produces one or more cumulative aggregates that include prior-cycle data.
- The latest aggregate is already a required campaign-root artifact.
- Copying the same aggregate into the new cycle would exceed or nearly exhaust the limit.
- Prior published cycles must remain byte-for-byte unchanged.

Do not use this rule for independent per-cycle evidence. An artifact is cumulative only when its
contract says that the newest version replaces the earlier aggregate view without replacing the
earlier source evidence.

## Verified Workflow

### Quick Reference

```text
bind existing payload -> classify cumulative files -> verify RED -> promote latest files
-> record omission -> rebuild tree hash and byte count -> verify prior bytes and atomic rollback
```

### Detailed Steps

1. Bind the existing publication before any extension. Verify its file inventory, payload-tree
   hash, byte count, cycle sequence, and immutable cycle records.
2. Calculate the remaining byte budget. Calculate the projected size with the next cycle. Do not
   change the cap to make a failing extension pass.
3. Classify each large repeated report. Require evidence that the newest file is cumulative and
   that the campaign root is its canonical public location. Keep independent cycle reports inside
   their cycle.
4. Add a behavior-first regression test. The test must initially fail because the extension puts
   the cumulative files in both the new cycle and the campaign root.
5. Require the test to verify these observable results:

   - every existing cycle file is byte-for-byte unchanged;
   - the new cycle does not contain the redundant cumulative copy;
   - each campaign-root aggregate equals the frozen newest source bytes;
   - the cycle report manifest records the omitted filenames;
   - the rebuilt publication stays below the hard cap; and
   - an injected swap failure restores the original publication.

6. Apply promotion only at the extension boundary. Keep the normal cycle projection unchanged for
   other reports. Copy each promoted aggregate verbatim from the frozen new-cycle source to the
   campaign root.
7. Record promoted filenames in the cycle manifest's existing omission inventory. Explain that
   cumulative campaign aggregates are at the campaign root. Do not add a second manifest schema
   when the current omission contract already represents this state.
8. Build the final payload inventory after the root copies are in place. Recalculate the file
   count, total bytes, and deterministic payload-tree hash from the staged tree.
9. Replace the public directory atomically. Keep a recoverable previous directory until the new
   directory is in place. Restore it if the second rename fails.
10. Run the focused regression test, the complete sanitizer suite, the independent publication
    audit, and repository-defined validation.

### Required Invariants

```json
{
  "existing_cycles_unchanged": true,
  "latest_cumulative_aggregate_location": "campaign-root",
  "new_cycle_duplicate_present": false,
  "omission_recorded": true,
  "payload_within_hard_cap": true,
  "atomic_rollback_verified": true
}
```

The cycle closure must bind the frozen aggregate source. The campaign payload manifest must bind
the promoted root file. These two bindings make the omission auditable without another copy.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | --------------- | ------------- | -------------- |
| Raise the hard cap | Increased the limit so one more duplicated aggregate would fit | Repeated growth remained unbounded, and the safety contract changed without a data-layout decision | Remove verified structural duplication before changing a safety limit |
| Delete an older cycle copy | Removed a file from an already published cycle | The operation changed immutable evidence and invalidated its payload-tree hash | Keep all prior cycle bytes unchanged |
| Omit the new copy without a record | Skipped the duplicate but left no manifest explanation | A reader could not distinguish deliberate promotion from a missing report | Record the filename and the campaign-root boundary in the existing omission contract |
| Add a second promotion manifest | Added a new schema only to point at the campaign-root files | The existing closure and payload manifests already supplied both hash bindings | Reuse the smallest audited contract that represents the state |

## Results & Parameters

### Decision Table

| Condition | Action |
| --------- | ------ |
| File is independent cycle evidence | Keep it in the cycle projection |
| File is cumulative and canonical at campaign root | Omit only the new cycle duplicate and promote the frozen newest file |
| Prior cycle contains an old duplicate | Preserve it; do not rewrite history during extension |
| Deduplication is not sufficient for the cap | Stop and design a versioned archive or a new publication boundary |
| Root file is transformed rather than copied verbatim | Record and audit the transformation; do not claim byte equality |

### Expected Output

A successful extension has one current campaign-root copy of each cumulative aggregate, a complete
new-cycle evidence directory without those duplicates, an explicit omission inventory, unchanged
prior-cycle bytes, and a rebuilt payload manifest below the hard cap.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Generalized local implementation | Append-only evaluation publication extension | A focused regression test failed on duplicate cycle copies, passed after root promotion, and the complete sanitizer suite passed. |

## References

- [Evaluation analysis pipeline reporting](evaluation-analysis-pipeline-reporting.md)
- [Statistical claim verification](statistical-claim-verification.md)
- [Verification evidence audit](verification-evidence-audit.md)
