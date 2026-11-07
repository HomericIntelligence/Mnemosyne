---
name: inert-registration-policy-omission
description: "Keep every serving-policy layer that selects a new model out of an inert registration change until the model can actually serve. Use when: (1) a new model is registered before its engine image, weights, or checkpoint manifest exist, (2) the registration adds routing, admission partition, or allow-list entries for a model that stays at zero replicas, (3) a review finds a routed model that the deployment policy refuses as not registered or cannot assign a replica job name, or (4) an activation document lists the fields to set but omits the policy registration step."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
tags: [serving, model-registration, allow-list, routing, admission-partition, zero-replica, fail-closed, activation-runbook, review-finding]
---

# Inert Registration With Policy Omission

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Register a new serving model without activation, and keep the deployment policy consistent with the layers that the change adds. |
| **Outcome** | Operational. A review of a registration-only change found one required finding: the change added a routing entry while the model stayed outside the policy allow-list. |

## When to Use

Use this skill when all of these conditions apply:

- A serving model is registered in a repository before its engine image, its
  weights, or its sealed checkpoint manifest exist.
- The deployment policy decides from one model allow-list whether a model can
  get a replica job name and whether a load request is accepted.
- Other policy layers, such as a routing map or admission partitions, can name
  a model independently of that allow-list.
- An activation document is the only record that tells an operator which
  fields to set later.

## Verified Workflow

### Quick Reference

Keep one rule: a policy layer that selects a model must not name the model
before the allow-list names it.

```text
allow-list entry  ->  routing entry, admission partition, replica job name
```

When those inputs are absent, choose one of these two results:

- omit the routing and partition entries, so the default route and the default
  partition apply and no layer names the model; or
- add the allow-list entry with a zero replica floor, so the model is
  registered, routable, and not started.

Do not add a routing or partition entry for a model that the allow-list
refuses.

### Suggested Approach

1. Identify the policy gate first. Find the check that refuses a model as not
   registered and the check that builds a per-model job name. Both usually read
   the same allow-list. Read the error path, not only the configuration file.
2. Enumerate every layer that can name the model without the gate: the routing
   map, the admission partitions, the fair-share weights, and the per-model
   capacity policy. A model in one of these layers is a policy claim even with
   zero replicas.
3. Prefer the smallest omission. A registration that fails closed often needs
   no routing entry and no partition entry. A zero-replica policy entry is the
   alternative when the repository requires every routed model to be allowed.
4. Record the omission in the activation document as an ordered set of steps,
   not only as a list of fields. The steps must name the allow-list entry and
   the layers that arrive in the same change as the image, the weights, and
   the sealed manifest.
5. Confirm render and load behavior for the zero-replica model. Add the model
   to a render list only if it renders without an image. A cookbook that
   renders no launch command does not belong in a render list that starts a
   replica.
6. Check whether a shell-glob test enumerates every catalog file. A new file
   in such a catalog must validate even when it cannot launch.
7. In review, check the inverse of the usual direction: list each model in the
   routing map and the admission partitions, then confirm that the allow-list
   names it. This check finds the omission that a cookbook-only review misses.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| Attempt 1 | Add the routing entry and the admission partition with the zero-replica cookbook, and no policy entry. | The dry-run policy refused the model as not registered, and the routed model had no replica job name. | A zero floor is not the only inert layer. The allow-list is a separate gate. |
| Attempt 2 | Describe activation as a list of fields to set on the override. | The list set the image, the weights, the manifest, and the bounds, but not the allow-list entry, so the documented path ended at a refused model. | Write activation as ordered steps that end in an accepted load, not as field names. |
| Attempt 3 | Add the new model to a production render list with the rest of the active models. | The model had no image, so a launch render had nothing to start. | Keep a non-launchable cookbook out of render lists that start a replica. |

## Results & Parameters

### Configuration

```yaml
# Alternative: allowed, routable, and not started.
policy:
  models:
    <new-model>:
      autoscale_min_replicas: 0
      autoscale_max_replicas: 0
```

### Expected Output

- Every model in the routing map and the admission partitions is in the model
  allow-list.
- A zero-replica model renders no launch command and returns a refusal other
  than not registered.
- The activation document ends with one load command that an operator can run.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production model-serving control plane | Review of a registration-only change for a new model with no engine image and no staged weights | One required review finding; the change removed the routing and partition entries. [notes.md](./inert-registration-policy-omission.notes.md) |

## References

- [serving-lane-zero-floor-demotion.md](./serving-lane-zero-floor-demotion.md): the related capacity decision, where a lane keeps its registration and loses only its replica floor.
- [forked-engine-model-support-evidence.md](./forked-engine-model-support-evidence.md): how to establish that an engine supports a model before activation.
- [inert-registration-policy-omission.notes.md](./inert-registration-policy-omission.notes.md): privacy-safe source evidence for this skill.