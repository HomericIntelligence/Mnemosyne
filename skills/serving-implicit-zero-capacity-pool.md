---
name: serving-implicit-zero-capacity-pool
license: BSD-3-Clause
description: "Make a properly set up serving model available without an explicit pool record by deriving an implicit zero-capacity pool from context. Use when: (1) a desired-state record is the sole visibility source for reconcile and autoscale, (2) a model with a complete bring-up recipe must answer demand without an operator start, (3) a scale or apply path refuses a pool that has no record, or (4) a warm floor must not auto-start a pool that has no record."
category: architecture
date: 2026-11-21
version: "1.0.0"
user-invocable: false
tags: [autoscaling, serving, pool-lifecycle, desired-state, implicit-entity, context-derived-trust, resolver, demand-start, scaled-to-zero, backward-compatibility]
---

# Serving Implicit Zero-Capacity Pool

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-21 |
| **Objective** | Remove the operator pool start as a prerequisite for demand-start: a model that the deployment policy declares and whose bring-up recipe is complete must behave as an available zero-capacity pool with no record and no operator action. |
| **Outcome** | Operational. The control plane treats a declared model with a complete recipe and no record as an implicit in-service pool at zero replicas; fresh demand starts it, the operator start remains the warm-capacity path, and the operator drain remains the opt-out. Targeted test suites green and review approved at authoring time; merge was pending required checks. |

## When to Use

Use this skill when these conditions apply:

- A storage-backed record is the sole source of an entity's visibility: the reconcile loop and the autoscaler list records and skip everything else.
- A properly set up entity must be available by default, and someone proposes the operator start command as the enablement step for every model.
- A demand-start or scale-up apply path raises a state error such as "the pool does not exist" for a model that has no record.
- A configured warm floor must not silently start pools that no operator ever started.

Do not use this entry to resolve a per-model configuration value such as a baseline or a floor. Use [serving-idle-baseline-per-model-opt-out](serving-idle-baseline-per-model-opt-out.md) for that decision. Do not use it to verify which configuration layer a floor edit affects; use [serving-replica-floor-enablement](serving-replica-floor-enablement.md) for that decision.

## Verified Workflow

### Quick Reference

```text
1. Synthesize the implicit entity in one resolver: list the real records, then
   overlay an implicit zero-replica in-service entity for every candidate that
   passes the admission gates and has no real record.
2. Derive trust from context, not from storage: the gates are the same ones the
   explicit creation path applies (declared in policy, prerequisite artifact
   complete, not on the absence list).
3. A real record always wins. A corrupt or untrusted existing record still
   counts as a record, so its blocked state is never masked by the overlay.
4. Route every consumer through the overlay: reconcile, autoscale, demand
   verdicts, floor and deficit rules, status and tier reporting.
5. Keep storage read-only for the implicit entity. The first real write creates
   the record through the existing exclusive-claim path.
6. Make the operator drain the opt-out: an explicit out-of-service record.
   Absence now means available at zero.
7. Never let a positive warm floor auto-start an implicit pool. The implicit
   pool always starts at zero; the operator start buys warm capacity.
8. Mark the implicit entity in status output so it is distinguishable from a
   real scaled-to-zero record.
```

### Suggested Approach

1. **Build one overlay resolver, not per-consumer special cases.** Write a supervisor-side resolver that lists the real records and overlays the implicit entities. The reconcile loop and the autoscaler both consume it. Leave the record lister itself unchanged so consumers outside the supervisor keep their real-record contract. Enumerate the consumers before you edit: reconcile, the autoscale loop and its eligibility rules, demand summarization and verdict publication, the floor and footprint-deficit rules, and status or tier reporting. A missed consumer keeps the implicit model invisible or reports a floor that does not exist.

2. **Reuse the creation path's admission gates as the trust basis.** An implicit entity must pass the same gates that the operator start applies: the model is declared in the deployment policy (the same source the request proxy uses for demand records), the bring-up recipe is complete, and the model is not on the absence list. Do not extend directory-permission or storage-presence trust to directory-less implicit entities; the gates are context-derived and cached per pass. An existing record that is corrupt or fails the trust check still counts as a record: the overlay must never mask a blocked state as an available implicit pool.

3. **Keep the implicit entity out of storage until a real write.** The overlay is in-memory for the reconcile and autoscale passes. The first real write — a demand-start scale-up, an operator start, or a floor change — creates the record through the existing exclusive-claim and generation semantics. Both apply paths must handle the record-less case: a scale path that returns "not found" for a missing record treats the demand start as superseded, and a state error that names the operator start as the fix defeats the whole change.

4. **Make absence mean available, and make the drain the opt-out.** Before this change, a missing record meant invisible and an explicit out-of-service marker meant drained. After it, absence means an implicit in-service pool at zero, so the opt-out must be a real record that carries the explicit out-of-service marker. Demand never starts a drained pool. Verify that the drained record and the implicit overlay cannot both apply to one model: the real record wins.

5. **Bound the implicit pool's floor at zero.** A configured warm floor restores replicas only for a pool that a record or an operator started. The implicit pool's effective floor is zero regardless of the configured floor, and every site that reads the floor for restore, deficit, or tier accounting must apply that rule. An operator who wants warm capacity runs the operator start; that record then carries the floor. A recovery branch that reuses a queued floor must not exceed this rule.

6. **Report the implicit state honestly.** Add a boolean implicit marker to the status roll-up and to the public model row, and mark it in the operator CLI output. An implicit pool reports the same service state as a real scaled-to-zero record but is distinguishable from it. Keep the added keys additive: an older client or health checker that reads the roll-up key-wise must tolerate the new key, and a strict public model contract must ignore unknown fields. Pin that older-client behavior with a test.

7. **Test the decision branches, not the wiring.** Cover: an implicit pool appears in reconcile and status with zero replicas; fresh demand produces a verdict and the apply path creates the record; a positive floor never auto-starts the implicit pool; the drain record suppresses demand starts; a corrupt record keeps its blocked state; the older client parses the new row; and the request proxy creates no pool state when it answers a model-starting response for an implicit model.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | --------------- | --------------- | ---------------- |
| Attempt 1 | Kept the pre-existing default that a missing record means "not in service" for demand purposes. | The declared model was invisible to reconcile and autoscale: demand records accumulated but no verdict was published, so the request proxy never answered model-starting and no replica ever started. | Once implicit entities exist, absence must mean the available-by-default zero state, not "not in service". |
| Attempt 2 | Left the scale-up apply path record-only while the resolver answered demand. | The demand start hit the "pool does not exist; run the operator start" state error, and a record-less scale request was treated as superseded. | Both apply paths create the record on the first real write; the refusal message must not remain the only record-less outcome. |
| Attempt 3 | Trusted directory permissions for the implicit entity because the explicit path used a secured state directory. | A directory-less implicit entity would then inherit trust from a directory it never had, so the gate either blocked every implicit model or opened the door to undeclared ones. | Derive implicit-entity trust from the same context gates as the creation path: declared, recipe-complete, not absent. |

## Results & Parameters

### Decision Table

| Situation | Required result |
| --------- | --------------- |
| Declared model, complete recipe, no record | Implicit in-service pool at zero; demand starts it |
| Same model, positive warm floor configured | Still starts at zero; operator start buys warm capacity |
| Operator drain record exists | Out of service; demand never starts it |
| Real record with replicas | Record wins over the overlay |
| Corrupt or untrusted record | Counts as a record; blocked state preserved |
| First real write | Record created by the exclusive-claim path, not by reconcile |

### Expected Output

- A declared model with a complete recipe appears in status at zero replicas without any operator action.
- Fresh demand produces a verdict and a record on the first scale-up; later passes see the real record.
- A drained model stays out of service until an operator starts it.
- The implicit marker distinguishes the implicit pool from a real scaled-to-zero record.
- Older clients and health checkers tolerate the new roll-up key; the strict public model contract ignores it.
- Targeted pool, supervisor, demand, proxy-admission, control-plane, and operator-service tests pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private model-serving control plane | Implicit zero-capacity pools for policy-declared models; the operator start kept only the warm-capacity role | Targeted test suites green and review approved; merge pending required checks at authoring time. [notes](serving-implicit-zero-capacity-pool.notes.md) |

## References

- [serving-replica-floor-enablement](serving-replica-floor-enablement.md): for a deployment without implicit pools, a missing record still means the operator start is required; with implicit pools, this entry supersedes that step for declared models with complete recipes.
- [serving-idle-baseline-per-model-opt-out](serving-idle-baseline-per-model-opt-out.md): the one-resolver enumeration rule this entry applies to existence instead of to a baseline value.
- [serving-lane-zero-floor-demotion](serving-lane-zero-floor-demotion.md): the zero-floor-plus-bounded-ceiling shape; an implicit pool is the record-less form of that availability.
