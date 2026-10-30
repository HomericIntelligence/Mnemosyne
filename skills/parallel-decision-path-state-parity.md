---
name: parallel-decision-path-state-parity
description: "When you add a second decision path beside a legacy path, perform the legacy path's state updates before any early exit, or allowed decisions are silently dropped. Use when: (1) a new exact or precise accounting, veto, or eligibility path is added beside an approximate legacy path, (2) a skip or continue precedes bookkeeping such as charging a capacity ledger, applying a hold, or moving a queue entry, (3) a decision the policy allows never happens with no error, or (4) you review a new branch in a shared decision funnel."
category: architecture
date: "2026-10-30"
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [state-parity, decision-paths, side-effects, early-exit, accounting, autoscaling, regression-testing]
---

# Parallel Decision Paths Need State-Update Parity

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-10-30 |
| **Objective** | Keep a newly added decision path from silently dropping decisions that the policy allows, because the path exits early before it updates the shared state. |
| **Outcome** | An exact-capacity veto path in a fleet autoscaler charged the shared slot ledger before its early skip. The allowed scale-up decision reappeared, and a parity test now asserts the decision and the resulting state for both paths. |

## When to Use

- You add a precise variant of an existing decision path beside the legacy path: different units, stricter checks, or an extra veto.
- The legacy path updates state with each decision: it charges a capacity ledger or counters, applies holds, sets flags, or moves queue entries.
- A decision the policy allows stops happening. No error appears; candidates silently vanish.
- You review a new branch that shares a decision funnel or a ledger with an existing branch.

## Verified Workflow

### Quick Reference

```python
# WRONG: the skip precedes the bookkeeping
def decide(job):
    if exact_veto(job):
        return              # the ledger never sees the demand
    charge_ledger(job.total_slots)
    return allow_or_hold(job)

# RIGHT: state updates happen before any early exit
def decide(job):
    charge_ledger(job.total_slots)
    if exact_veto(job):
        return
    return allow_or_hold(job)
```

### Suggested Approach

1. Inventory the legacy path's state updates. List every mutation between entry
   and exit: charges, holds, counters, flags, and queue moves. Put that list
   beside the new path.
2. Before the new path's first early exit, perform the state updates that
   downstream logic reads. A skip or continue that precedes the bookkeeping turns
   a recorded decision into a dropped one, with no error.
3. Record deliberate differences. If the new path updates state in different
   units or adds holds, write that in the path contract. A reviewer then reads
   the difference as policy, not drift.
4. Keep the shared bookkeeping in one helper that both paths call, when the
   updates are identical. One owner cannot drift.
5. Add a parity test. Run the legacy input class through both paths. Assert the
   allowed-decision outcome and the resulting state: equal, or the documented
   deliberate difference. An assertion that only checks "no exception" proves
   nothing.

This rule has a mirror image. A new dispatch must also not repeat a shared side
effect; see
[planning-cross-pr-interface-dependency](planning-cross-pr-interface-dependency.md).
Inventory the shared side effects first. Then dedupe the ones that must run once,
and port the ones each path must run before its early exits.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Early skip before the charge | The new exact-capacity veto path continued to the next candidate with no bookkeeping | The shared ledger never saw the demand, so a scale-up the policy allowed never happened; no error marked the loss | Perform the legacy path's state updates before any early exit, and assert the allowed decision and the state in a parity test |

## Results & Parameters

### Decision Table

| Situation | Required behavior |
| --------- | ----------------- |
| New path exits early after the legacy-equivalent state updates | Decision trail and ledger state stay consistent |
| New path exits early before the updates | Allowed decisions silently drop; fix before merge |
| New path updates state in different units or adds holds | Documented deliberate difference, covered by a test |
| Both paths need identical updates | One shared bookkeeping helper owns them |

### Expected Output

- The parity test passes for both paths on the same input class.
- A decision the policy allows appears in the ledger and in the emitted decision.
- Review finds one helper that owns the shared state updates.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Private fleet-autoscaling service | Exact node-capacity accounting added beside legacy slot counting | The new veto path's bare skip dropped an allowed scale-up decision. Charging the shared slot ledger before the skip restored the decision. A parity test asserts the decision and the state for both paths. Identifying details are generalized. |

## References

- [shared-predicate-gate-discovery-parity](shared-predicate-gate-discovery-parity.md) — classification parity between paths through one pure predicate; state updates are a separate concern
- [planning-cross-pr-interface-dependency](planning-cross-pr-interface-dependency.md) — the mirror image: place a new dispatch before shared side effects to avoid double mutation
- [license-scan-marker-excluded-fallback](license-scan-marker-excluded-fallback.md) — fall through to a common check instead of duplicating branch logic
- [mojo-parallelize-worker-stash-parity-testing](mojo-parallelize-worker-stash-parity-testing.md) — parity-testing discipline for parallel and serial paths
