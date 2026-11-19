---
name: autoscaler-hold-trace-effective-ceiling-layers
description: "Diagnose an autoscaler that runs but does not scale out. Use when the decision log shows a hold at a ceiling, or when pool sizes fell after a deployment-policy handover."
category: debugging
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags:
  - autoscaling
  - diagnosis
  - effective-bound
  - configuration-layers
  - handover
---

# Autoscaler Hold: Trace the Effective Ceiling Through Every Layer

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Find why an autoscaler that is running does not add capacity. |
| **Outcome** | Operational. The cause was an outer policy layer that set a ceiling lower than the workload spec. |

## When to Use

- A user reports "autoscaling does not start", but the controller logs decisions.
- The decision log shows `hold N->N` with a reason that names a ceiling, a pending-replica limit, or a budget veto.
- Pool sizes fell in one step after a release, a policy change, or a context handover.
- The workload spec shows a high maximum, but the live pool never exceeds a small number.

## Verified Workflow

### Quick Reference

1. Read the last decision lines for each pool. The hold reason names the gate that stopped the step.
2. If the reason is a ceiling, compute the effective ceiling. It is the minimum of every layer that can set one.
3. Compare the layer values with the pool size before the change. A fall in size at one timestamp points to a changed layer.

### Suggested Approach

- Treat "the autoscaler is off" as a hypothesis, not a fact. First prove that decisions are made. A controller that logs `hold` is on.
- Separate the hold gates. Each one has a different owner and fix:
  - ceiling: bounds from configuration;
  - pending-replica limit: capacity that is still starting;
  - budget veto: fleet-wide node limit;
  - residency or cooldown: time gates that expire.
- List all layers that bound the replica count. Typical layers are the workload spec, the per-workload entry in the deployment policy, and one global per-workload cap. The code takes the minimum. A lower outer layer silently overrides a higher workload spec. Do not read only the workload spec.
- Find the active layer files from the running process, not from the default branch. A handover can change the active deployment policy while the checkout shows another value.
- Check a second, separate cause. A circuit breaker on scale-out or a missing workload file can block growth even when the ceiling is high. Look for open breakers and file-not-found errors in the same log.
- Report the layer and the value that set the bound. Do not change a production policy without the owner's approval. Offer the change as a reviewed pull request.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Read the workload spec ceiling. | The spec showed a high maximum, but the active policy capped it lower. | Compute the minimum of all layers. |
| 2 | Look for an on/off switch. | The controller was always on and made decisions. | Read the decision log before you look for a switch. |

## Results & Parameters

### Configuration

```text
effective_ceiling = min(spec.max, policy.per_workload.max, policy.global_per_workload_cap)
effective_floor   = policy floor (or spec floor) + elastic baseline
```

A step up is allowed only when `desired < effective_ceiling`, the pending-replica limit has room, and the budget does not veto.

### Expected Output

A one-line cause that names the gate, the layer that set it, its value, and the time of the change. Add any second blocker, such as an open breaker.
