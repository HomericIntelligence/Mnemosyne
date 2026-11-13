---
name: serving-idle-baseline-per-model-opt-out
description: "Keep a protected replica floor and let selected models opt out of a deployment-wide idle baseline. Use when: (1) an idle or warm baseline adds replicas above each model's protected floor, (2) the owner wants selected models at zero while the other models keep the baseline, (3) an operator drain is proposed as the opt-out, or (4) several consumers read the baseline value directly."
category: architecture
date: 2026-11-11
version: "1.0.0"
user-invocable: false
tags: [autoscaling, serving, replica-floor, idle-baseline, per-model-override, resolver, identity-rotation, operator-drain, capacity-policy]
---

# Serving Idle Baseline: Per-Model Opt-Out

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-11 |
| **Objective** | Remove an additive idle baseline from selected models without weakening their protected floors or the operator drain. |
| **Outcome** | Operational. A deployment-wide baseline stayed at one replica for ten models and five models opted out. Two protected-floor reductions were outside this decision. Targeted tests and full CI passed. |

## When to Use

Use this skill when these conditions apply:

- A serving control plane has two replica layers: a protected floor and an idle baseline that adds replicas above it.
- The owner wants selected models at zero replicas when idle, while other models keep the baseline.
- An operator drain command can zero a pool, and someone proposes it as the opt-out.
- The baseline value is a single deployment-wide setting that several consumers read.

Do not use this entry to demote a superseded lane by changing its protected floor. Use [serving-lane-zero-floor-demotion](serving-lane-zero-floor-demotion.md) for that decision.

## Verified Workflow

### Quick Reference

```yaml
policy:
  autoscale:
    idle_baseline_replicas: 1      # Deployment default.
  models:
    <inheriting-model>: {}          # Absent value inherits 1.
    <opt-out-model>:
      idle_baseline_replicas: 0     # 0 opts out; the protected floor stays.
```

```text
1. Keep the protected floor unchanged.
2. Use a nullable per-model override: absent inherits, 0 opts out, positive overrides.
3. One resolver answers the baseline for a model; every consumer calls it.
4. Exclude the unset value from the serialized identity; re-register a record that sets it.
5. Do not use the operator drain as the opt-out.
```

### Suggested Approach

1. **Separate the layers.** The protected floor is the availability guarantee. The idle baseline is additional capacity on a preemptible tier. The opt-out removes only the baseline. Record this boundary in the change plan, because both layers often share one configuration block.

2. **Add a nullable per-model override.** A non-null value overrides the deployment value; an absent value inherits it. Validate the value as non-negative. Do not encode "inherit" as `0`; that makes the opt-out indistinguishable from an override of a different deployment default.

3. **Use one resolver in every consumer.** Enumerate each site that reads the deployment baseline: the steady-state autoscale loop, event recovery or eligibility, pool reconcile, status and tier reporting, the mandatory footprint check, the QoS or elastic envelope, and operator CLI notes. Replace each direct read with the per-model resolver. A missed consumer keeps the baseline for the opt-out model or reports a floor that does not exist.

4. **Bound the effective floor.** Reject a per-model value that makes the effective floor exceed the model ceiling or the per-model capacity limit. For a bounded deployment, the capacity check often uses the larger of the declared and resolved floors; apply the override before that comparison.

5. **Preserve the operator drain.** A pool at `desired=0` is an operator drain: the autoscaler must not restore it. The opt-out is a policy value that produces zero desired replicas only when the pool is otherwise idle. Do not implement the opt-out by setting the drain state.

6. **Handle identity separately from behavior.** Exclude the unset value from the serialized identity, for example with an exclusion-declared optional default, so records that do not set the field keep their digest. A record that sets the override rotates its identity; re-register it and state that step in the rollout.

7. **Test each decision branch.** Cover inheritance, `0`, and a positive override in the resolver; an opt-out pool that goes to zero while a sibling keeps the baseline; the footprint and the envelope charging only the inheriting model; event recovery for a zero baseline; the CLI note; and every checked-in context.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| Attempt 1 | Used the operator drain to opt out the selected models. | The drain also removes the protected floor, and an operator must start the pool again. A model with a large floor lost its availability guarantee. | Change the baseline layer only. Keep the protected floor and the drain authority. |
| Attempt 2 | Read the deployment baseline directly in the main autoscale loop and left the other consumers unchanged. | The opt-out leaked through event recovery, status, and the capacity checks, so the policy disagreed with the reported floor. | One resolver answers the baseline for every consumer. Enumerate the consumers before you edit. |
| Attempt 3 | Serialized the new field as `null` for every model that did not set it. | Every record digest rotated, including records with no configuration change, and bound plans refused on mismatch. | Exclude the unset value from the serialized identity. Re-register only the records that set it. |
| Attempt 4 | Zeroed the protected floor to force the idle count to zero. | The model lost its protected placement and could not recover without an operator. | Remove the additive baseline, not the protected floor. |

## Results & Parameters

### Configuration

```yaml
# Deployment layer: one warm replica above each protected floor.
policy:
  autoscale:
    idle_baseline_replicas: 1
  models:
    <model-a>:
      protected_floor_replicas: 2
    <model-b>:
      protected_floor_replicas: 0
      idle_baseline_replicas: 0   # Fully cold when idle.
    <model-c>: {}                 # Inherits the baseline.
```

### Decision Table

| Situation | Required result |
| --------- | --------------- |
| Model has no override | Keeps the deployment baseline above its protected floor |
| Model sets `0` | Holds no idle baseline; the protected floor still applies |
| Model sets a positive value | Holds that value above the protected floor |
| Pool is operator-drained | Stays at zero until an operator starts it |
| Record sets the override | Identity rotates; re-register the record |
| Record does not set the override | Identity stays stable |

### Expected Output

- The opt-out models report zero desired replicas when idle.
- The other models keep the baseline.
- The protected floors are unchanged.
- The status, the footprint check, the envelope check, and the CLI note agree on the effective baseline.
- The checked-in contexts load and pass their capacity checks.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private model-serving control plane | A deployment-wide one-replica baseline, five per-model opt-outs, and two protected-floor reductions outside this decision | Merged changes with targeted tests and full CI green. [notes](serving-idle-baseline-per-model-opt-out.notes.md) |

## References

- [serving-lane-zero-floor-demotion](serving-lane-zero-floor-demotion.md): changes the protected floor of a superseded lane; this entry keeps the floor and changes only the baseline.
- [descriptor-digest-readmission-additive-fields](descriptor-digest-readmission-additive-fields.md): exclusion-declared defaults and digest invariance for additive fields.
- [live-hotfix-content-addressed-identity-rotation](live-hotfix-content-addressed-identity-rotation.md): identity rotation after a policy or recipe edit.