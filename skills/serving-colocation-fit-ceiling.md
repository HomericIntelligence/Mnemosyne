---
name: serving-colocation-fit-ceiling
license: BSD-3-Clause
description: "Size and change a per-node capacity ceiling that derives replica co-location
  counts by floor division without silently losing placement density. Use when: (1) a platform
  computes replicas-per-node as ceiling // per-replica request, (2) you raise one replica's
  memory or resource request and its derived count can drop, (3) you choose a new ceiling and
  must keep every other profile's derived count unchanged, (4) you must say whether another
  service still fits on the node and are tempted to treat the ceiling as a reservation."
category: architecture
date: 2026-11-16
version: "1.0.0"
user-invocable: false
tags: [serving, colocation, capacity-planning, floor-division, derived-limits, config-validation, memory, placement]
---

# Serving Co-Location Fit Ceilings

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-16 |
| **Objective** | Change a per-replica resource request or a per-node capacity ceiling without silently changing derived co-location counts, and size the ceiling so the declared value equals the real packed claim. |
| **Outcome** | Operational. A replica memory request raised past half the ceiling dropped its derived count from two to one. An exact-multiple ceiling restored the count, and a full before/after derivation sweep over every profile proved the change behavior-preserving for placement. |

## When to Use

- A serving platform derives replicas-per-node as `capacity // request` (a bounded minimum with
  GPU, CPU, or port fits), instead of taking a declared replica count.
- You raise a replica's memory or resource request, and the new value can cross a divisor
  boundary of the ceiling.
- You raise or lower the ceiling itself and must not disturb other profiles.
- You reason about whether an unrelated service (a gateway, an agent, a monitoring job) fits on
  the same node and are about to subtract the ceiling from node RAM.

## Verified Workflow

### Quick Reference

```text
derived_count = capacity_ceiling // replica_request   # floor division, per profile
# After ANY request or ceiling change: recompute derived_count for EVERY profile,
# old value vs new value, and require equality for all profiles you did not mean to change.
```

### Suggested Approach

1. Treat the ceiling as fit arithmetic, not a reservation. The derived count is a floor
   division result, so it changes in steps, not smoothly. A request that grows past
   `ceiling / N` drops the count from `N` to `N-1` with no warning in the value itself.
2. After a request increase that drops a count, restore the count with an exact-multiple
   ceiling: `ceiling = N * request`. A round-number ceiling also restores the count, but it
   leaves phantom headroom: the declared ceiling then exceeds the real packed claim
   `N * request`, and the stated reserve below node RAM is overstated by the difference.
3. Keep the exact-multiple ceiling at or below the node's real memory minus the reserve the
   platform intends to keep. The exact multiple documents which packed pair (or triple, and so
   on) the ceiling exists for; record that derivation in the config comment.
4. Do not block the change on "the other service no longer fits" reasoning that subtracts the
   ceiling from node RAM. Check which mechanism actually places the other service. If placement
   sums actual per-job requests against live node free memory, the ceiling change alters no
   real claim, and the worst-case fit is `sum of real requests + other service <= node RAM`.
   State that arithmetic explicitly instead of the ceiling-based approximation.
5. Validate with the platform's own derivation function, not by hand:
   - load every profile (all models, all node shapes), compute the derived count with the old
     and the new value, and assert equality for every profile you did not intend to change;
   - run the platform's canonical derivation sweep or pin tests plus the focused config/render
     suites;
   - hand-check the boundary profiles: the edited one, any profile whose request is near a
     divisor boundary of the old or new ceiling, and the smallest and largest requests.
6. Record the fit table (request, derived count at old ceiling, derived count at new ceiling)
   in the change description. It converts a one-line config edit into reviewable evidence.

If the platform exposes no derivation function or sweep, reproduce the floor division for each
profile in a scratch script and say that the check is a reimplementation, not the platform's
own arithmetic.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Raise only the per-replica memory request after measured host-memory growth. | The request crossed half the ceiling. | The derived count silently fell from two to one, which broke the packed-replica placement contract and halved per-node density. | Recompute derived counts whenever a request changes; the count, not the request, is the placement contract. |
| Restore the count with a round-number ceiling above the exact multiple. | The count recovered, but the ceiling exceeded the real packed claim. | The reserve below node RAM was overstated, and a reviewer had to ask whether another service still fit. | Size the ceiling as `N * request` so the declared value equals the real claim; answer fit questions with real-request arithmetic. |

## Results & Parameters

### Configuration

Generic example (public-equivalent numbers): node RAM 160G, packed pair wanted.

```yaml
# replica request grows 70G -> 75G
# ceiling 140G: 140 // 70 = 2, but 140 // 75 = 1   <- silent density loss
# ceiling 160G: 160 // 75 = 2 (restored) but 160 - 150 = 10G phantom headroom
# ceiling 150G: 150 // 75 = 2 (restored), declared ceiling == real claim 2 * 75G
capacity_ceiling: 150G   # = 2 x 75G, the packed pair; reserve below node RAM: 10G
```

### Expected Output

- The edited profile derives the intended count again.
- Every other profile derives the same count as before the change (sweep assertion passes).
- The fit table in the change description shows request, old-ceiling count, and new-ceiling
  count for each profile.
- The config comment states the exact-multiple derivation and the remaining node reserve.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private manifest-driven GPU serving platform | Per-node memory ceiling retuned to an exact multiple of a packed replica pair after host-memory growth forced a larger replica request. | 36/36 profiles kept their derived counts in a before/after sweep with the platform derivation function; 1225 focused config/render tests passed. See [notes](serving-colocation-fit-ceiling.notes.md). |

## References

- [Slurm QOS group-cap regression diagnosis](slurm-qos-group-cap-regression-diagnosis.md): the
  scheduler-side counterpart, where co-location and capacity arithmetic decide whether a pending
  job needs a cap restoration or a placement change.
