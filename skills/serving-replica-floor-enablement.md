---
name: serving-replica-floor-enablement
license: BSD-3-Clause
description: "Verify that a serving replica floor enables the intended pool before you claim a warm lane. Use when: (1) a change raises, lowers, or adds a replica floor and the plan claims a warm or default lane, (2) a zero-floor pool must become available and the on-demand load path is the only documented start mechanism, (3) the same floor appears in a per-model recipe layer and a deployment-policy layer, or (4) a capacity check that sums floors disagrees with a recorded scheduler grant."
category: architecture
date: 2026-11-10
version: "1.0.0"
user-invocable: false
tags: [autoscaling, serving, replica-floor, pool-enablement, config-layers, runtime-authority, capacity-check, sealed-record, release]
---

# Serving Replica Floor Enablement

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-10 |
| **Objective** | Change a serving replica floor and prove that the pool is enabled, that the runtime reads the edited layer, and that the sealed record and capacity checks agree. |
| **Outcome** | Operational. A floor-policy change merged with full CI after the plan corrected two claims: a floor does not create a pool, and the on-demand load path refuses a pool whose floor is above zero. |

## When to Use

Use this skill when these conditions apply:

- A change raises, lowers, or adds a replica floor, and the plan says the model is warm, default, or always available.
- A zero-floor pool must become available, and the on-demand load path is the documented start mechanism.
- The same floor appears in a per-model recipe layer and a deployment-policy layer, and you must know which one the runtime reads.
- A capacity check that sums floors disagrees with a recorded scheduler grant, and you must decide if the result blocks a release.
- A floor change must ride a release that pins a content-addressed pool record.

## Verified Workflow

### Quick Reference

Keep four rules:

```text
1. Find the layer the runtime reads before you edit a floor.
2. A floor configures an enabled pool. It does not create the pool.
3. Pick the start path from the floor value: zero permits the on-demand load, above zero requires the operator pool start.
4. A floor rotates the sealed pool record. Add the model to the release re-authoring list.
```

### Suggested Approach

1. **Resolve the effective layer first.** Read the runtime resolver, not only the configuration files. A deployment with bounded capacity applies the policy floor and can apply a ceiling. A deployment with unbounded capacity applies the resolved per-model recipe floor at runtime; the policy floor is inert there. The mandatory-cost check uses the larger of the policy floor and the recipe floor when capacity is bounded and the policy declares a floor. Otherwise it uses the recipe floor. Edit the effective layer. Keep the other layer equal, because a repository test may pin the pair or allow only zero or the recipe value.

2. **Check that the pool exists.** The supervisor reconciles only pools that have a desired-state record. A floor keeps an enabled pool at a count. It does not create the record. List the desired records. If the record is absent, run the operator pool start once, for example `pool up <model> --replicas 1`.

3. **Select the start path from the floor.** A pool with a floor of zero has no uptime guarantee. The on-demand load request creates the pool and a time-bounded hold. A pool with a floor above zero is a protected tier: the load request fails with a protected-tier code and changes no state. After you raise a floor, do not tell users to use the on-demand load command. Give them the operator start command or the pool status.

4. **Check the sealed record.** A content-addressed pool record hashes the resolved recipe, including the floor. A floor change rotates the record. Find the release-prep re-authoring list. Confirm that an existing issue covers the model. If it does not, open a follow-up for that release boundary. Do not hand-edit a sealed record.

5. **Read the capacity check before you claim a result.** A grant check can charge every declared floor, including pools with no desired record and floors that are unrelated to the change. A shortfall can be a warning, not a refusal, when the supervisor starts anyway. Report the exact check, its demand model, and whether it blocks. Do not report a sum of only the policy floors as the check result.

6. **Expect identity rotation.** A deployment-policy edit can rotate the deployment context identity. Operator requests or holds bound to the old identity must be reissued. State this in the release notes, not only in the code change.

7. **Verify the pair and the behavior.** Run the tests that pin the policy floor to the recipe floor, the deployment-context tests, and the capacity checks. Record the exact command and result. If the live operator tree is not writable, state that the change ships in the next release and give the one-time operator start commands.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Changed only the deployment-policy floor in an unbounded deployment. | The runtime used the per-model recipe floor, so the effective count did not change. | Resolve the runtime authority before you edit a floor. Edit the layer the runtime reads. |
| Attempt 2 | Claimed that the new floor would create a warm lane. | The pool had no desired-state record, so the supervisor never reconciled it and no replica started. | A floor does not create a pool. Check the desired record and run the operator start once when it is absent. |
| Attempt 3 | Told users to use the on-demand load command for the newly protected model. | The request failed with a protected-tier code because the resolved floor was above zero. | Choose the start path from the floor value: zero uses load, above zero uses the operator pool start. |
| Attempt 4 | Summed only the policy floors to predict the capacity check. | The check charged every declared recipe floor, including pools with no desired record, so the reported footprint was much larger. | Read the check's demand model. A shortfall can be a warning, not a refusal. Record the check type. |

## Results & Parameters

### Configuration

Keep the effective and the mirrored layer equal:

```yaml
# Per-model recipe layer: the runtime floor in an unbounded deployment.
clusters:
  <cluster>:
    autoscale_min_replicas: 1
    autoscale_max_replicas: <ceiling>

# Deployment-policy layer: the mirrored floor and its slots.
policy:
  models:
    <model>:
      slots_per_replica: <gpu-slice>
      autoscale_min_replicas: 1
      autoscale_max_replicas: <ceiling>
```

Start an enabled pool once when the desired record is absent:

```bash
<operator-cli> pool up <model> --replicas 1
```

### Expected Output

- The cookbook floor and the policy floor agree.
- The pool reports one live or desired replica after the operator start.
- The on-demand load path refuses the model with a protected-tier code.
- The sealed-record re-authoring has an owner in the release-prep list.
- The capacity check result names its demand model and says whether it blocks.
- The targeted floor, deployment-context, and capacity tests pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production model-serving control plane | Merged floor-policy change for five model families, with a sealed-record follow-up and a full CI pass. | [notes.md](./serving-replica-floor-enablement.notes.md) |

## References

- [serving-lane-zero-floor-demotion.md](./serving-lane-zero-floor-demotion.md): the related demotion decision, where a lane keeps its registration and loses its floor.
- [live-hotfix-content-addressed-identity-rotation.md](./live-hotfix-content-addressed-identity-rotation.md): the identity chain that a recipe or floor edit rotates.
- [inert-registration-policy-omission.md](./inert-registration-policy-omission.md): policy layers that can name a model before the allow-list admits it.