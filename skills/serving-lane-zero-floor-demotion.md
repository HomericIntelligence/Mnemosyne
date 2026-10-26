---
name: serving-lane-zero-floor-demotion
license: BSD-3-Clause
description: "Demote a superseded serving lane to a zero replica floor with a bounded autoscale ceiling instead of removing it. Use when: (1) a validated replacement lane can carry primary production traffic, (2) the superseded lane must stay selectable as a tested rollback profile, (3) autoscale bounds are declared in a global default plus per-cluster overrides and are repeated in deployment policy and bound-pinning tests, or (4) an issue body records bounds that the checked-out base commit no longer matches."
category: architecture
date: 2026-10-24
version: "1.0.0"
user-invocable: false
tags: [autoscaling, serving, replica-floor, replica-ceiling, lane-demotion, rollback, capacity-policy, kv-cache]
---

# Serving-Lane Zero-Floor Demotion

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Release idle production capacity from a superseded serving lane without losing its tested rollback path. |
| **Outcome** | Operational. A merged pull request held a superseded precision lane at a zero floor and a bounded ceiling on every cluster while the validated replacement lane kept the production floor; full CI passed. |

## When to Use

Use this skill when all of these conditions apply:

- A replacement lane, for example a lower-precision or lower-cost serving
  profile, has parity evidence and can hold the production replica floor.
- The superseded lane still has rollback or explicit-serving value, so its
  removal is premature.
- Autoscale bounds appear in more than one layer: a global default, per-cluster
  or per-environment overrides, a deployment policy, and tests that pin the
  production bounds.
- The change request cites bound values from an issue or plan that the
  checked-out base commit can no longer match.

## Verified Workflow

### Quick Reference

Do not delete the lane. Zero the floor and bound the ceiling:

```yaml
# Global default: steady-state desired count becomes 0.
autoscale_min_replicas: 0
clusters:
  <cluster-a>:
    # Explicit override: a cluster inherits the global floor when unset.
    autoscale_min_replicas: 0
    # Bounded demand-driven scale-up after the floor drops.
    autoscale_max_replicas: 50
  <cluster-b>:
    autoscale_max_replicas: 50
```

### Suggested Approach

1. Confirm parity evidence for the replacement lane before the demotion:
   matched qualification results, latency and throughput parity, and no
   evaluation regression between the two lanes. Confirm that the replacement
   lane holds its own replica floor.
2. Demote instead of delete. A zero floor releases idle capacity: the pool
   holds no replica at steady state, but the model stays registered,
   selectable, and tested, and demand-driven autoscale can still start
   replicas. Deletion loses the tested rollback profile and its qualification
   gating.
3. After the floor is zero, the ceiling is the only bound on demand-driven
   scale-up. Select a maximum that still exceeds the measured burst headroom
   and apply it on every cluster.
4. Enumerate each layer that declares or asserts the bounds before you edit:
   the global default, each per-cluster or per-environment override, the
   deployment-context policy, and the tests that pin the production bounds.
   A missed layer leaves the policy or the tests in disagreement with the
   primary configuration.
5. Compute the change against the checked-out base commit, not against the
   values in the issue body. Issue bodies go stale when intermediate bounds
   land. Record the actual base values in the pull request when they differ.
6. Keep profile behavior parameters, such as precision and qualification
   gating, unchanged. This change is capacity policy only.
7. Update the operator or release directive that recorded the old floor, so
   the release record and the configuration agree.
8. Declare concurrent edits to the same bound lines from other worktrees in
   the pull request notes, because these lines will conflict if both land.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Run the related tests in a fresh worktree with a no-sync runner. | Environment error: the fresh worktree had no virtual environment and the no-sync runner refused to build one. | Run the repository bootstrap script in a fresh worktree before you collect a test baseline. |
| Attempt 2 | Re-run with test node identifiers copied from an earlier run. | Collection error: one node identifier came from a stale test cache and did not exist in the tree. | Re-derive the current test node identifiers from the checked-out tree; do not reuse cached identifiers. |
| Attempt 3 | Collect a pre-change baseline after the operator waived it. | The waiver superseded the attempt: the replacement lane was already validated, so effort moved to post-change evidence. | Record each baseline waiver, its authority, and the replacement evidence explicitly in the pull request. |

## Results & Parameters

### Configuration

```yaml
# Superseded lane: zero floor, bounded ceiling, unchanged profile behavior.
autoscale_min_replicas: 0
clusters:
  <cluster-a>:
    autoscale_min_replicas: 0
    autoscale_max_replicas: 50
  <cluster-b>:
    autoscale_max_replicas: 50
# Replacement lane (unchanged): keeps its own floor.
#   autoscale_min_replicas: 2
```

### Expected Output

- The superseded pool reports a desired count of 0 at steady state while the
  model stays registered for demand-driven autoscale up to the new ceiling.
- The superseded profile stays tested; rollback is a bounds-only
  configuration change.
- The bound-pinning tests, the deployment-policy checks, lint, and type
  checks pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production model-serving capacity control plane | Zero-floor demotion of a superseded precision lane behind a validated lower-precision lane | Merged pull request with full CI green. [notes.md](./serving-lane-zero-floor-demotion.notes.md) |

## References

- [autoscaling-template-promotion-evidence.md](./autoscaling-template-promotion-evidence.md): template-level admission evidence for autoscaling pools.
- [inference360-dynamic-serving-capacity.md](./inference360-dynamic-serving-capacity.md): deriving per-replica request limits from checkpoint KV-cache geometry.
- [serving-lane-zero-floor-demotion.notes.md](./serving-lane-zero-floor-demotion.notes.md): privacy-safe source evidence for this skill.
