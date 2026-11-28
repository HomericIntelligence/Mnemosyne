---
name: storage-fallback-capacity-independence
license: BSD-3-Clause
description: "Choose and verify a spill, overflow, or failover storage destination whose capacity is independent of the primary. Use when: (1) a write-fallback target must absorb writes while the primary is full, (2) a writable candidate has an unknown quota, (3) the destination is derived as a sibling of the primary directory, or (4) free-space reporting shows large headroom while writes fail with ENOSPC."
category: tooling
date: 2026-11-28
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [storage, quota, fallback, failover, spill, capacity, enospc, shared-storage]
---

# Storage Fallback Capacity Independence

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-28 |
| **Objective** | Select a spill, overflow, or failover storage destination that keeps accepting writes when the primary root is full, and reject candidates that only look available. |
| **Central lesson** | Write access and capacity are different checks. A writable destination is not a fallback when it shares the primary's allocation. On a shared filesystem, whole-mount free space says nothing about one directory allocation. |
| **Outcome** | An access-proven, usage-measured candidate list, a capacity-independence decision, and an explicit escalation when no independent allocation exists. |
| **Verification** | verified-local: a service needed a spill target while its primary root filled. Two writable candidates were rejected: one shared the primary's allocation, and one belonged to another tenant. |

## When to Use

- A service needs a spill, overflow, or degraded-mode write target because its primary root can fill.
- A candidate destination is writable, but its allocation or quota is unknown.
- The destination is derived relative to the primary, for example a sibling directory of the primary store.
- Free-space reporting shows large headroom, but writes still fail with `ENOSPC` or `EDQUOT`.
- Group membership grants write to a tree that belongs to another team.

## Verified Workflow

### Quick Reference

```bash
# Prove write access at a candidate root. Mode and ACL reads are not proof.
(umask 077; printf x > "$candidate/.write-probe.$$") && rm -f "$candidate/.write-probe.$$"

# Measure the candidate's current usage and compare it with the allocation
# that the storage owner declares. Whole-mount free space is not an input.
du -s --block-size=1 "$candidate"
```

The load-bearing rule is:

> A fallback must not share the primary's allocation. A sibling directory of the primary store commonly does.

### Suggested Approach

1. **Bound the primary's allocation scope.** Start from the failing write path. A quota can sit on the write directory, on a deployment root above it, or on the store that the path is derived from. The failure evidence names the path; the storage owner supplies the scope.
2. **Enumerate candidates by numeric identity.** List the process groups, then the group identifier and mode of each shared top-level tree. Keep only trees whose group is one of the process groups. Do not infer access from a group name.
3. **Prove access with a real create and unlink.** Write one small file with a restrictive umask and remove it. Inherited ACLs, ownership changes, and read-only snapshots can differ from the visible mode.
4. **Reject candidates that are not authorized allocations.** Another tenant's group-writable tree, a world-writable scratch area, and the primary's own ancestor are not destinations. Group write permission is not an authorization to consume another allocation.
5. **Measure each remaining candidate against its declared allocation.** Compare current usage from `du` with the quota that the storage owner states. Clients of a shared filesystem usually cannot read per-directory quotas, and `df`/`statvfs` report the whole mount, so the owner is the authority for the number.
6. **Require capacity independence.** The destination allocation must differ from the primary's allocation. A destination that shares the primary's quota fills with the primary and is absent exactly when the fallback is needed. If every writable candidate shares the primary's allocation, request a dedicated allocation or a quota increase. Do not adopt a same-quota sibling.
7. **Probe real headroom before reliance and before each retry.** A shared quota moves between runs. Use the disposable increasing-size write described in [Slurm shared-storage artifact relocation](slurm-shared-storage-artifact-relocation.md#verified-workflow); that skill also explains why `df` cannot show the limit.
8. **Record the decision inputs.** Store the declared allocation, the measured usage, the access evidence, and the independence result next to the fallback configuration so the next incident starts from known numbers.

Continue when a step cannot run. A missing quota CLI or an unavailable storage owner limits the evidence, but it does not block the access proof, the usage measurement, or the rejection of unauthorized candidates. Report the missing number and treat the destination as unproven.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trust whole-mount free space | Read `df` for the shared mount, saw hundreds of terabytes free, and adopted a writable directory. | The directory allocation was already more than four fifths used and had about one sixth free; the mount number was unrelated. | `df` and `statvfs` show the filesystem, not the directory allocation. Measure usage and get the declared quota. |
| Derive the fallback as a sibling of the primary store | Placed the overflow tree next to the store directory. | The sibling shared the store's allocation, so the fallback filled together with the primary. | Capacity independence is a requirement, not a convenience. A same-quota sibling is not a fallback. |
| Accept any group-writable tree | Found several writable shared top-level trees and ranked them by apparent free space. | One tree was another team's allocation; access came from group membership, not from an allocation decision. | Group write permission is not authorization. Ask the allocation owner. |
| Verify access from mode bits and ACL reads | Checked the mode and the inherited ACL and skipped the probe. | Effective access can differ from the visible metadata, and the probe is cheap. | Prove access with a real create and unlink at the exact target directory. |
| Use a world-writable scratch area | Treated an unowned world-writable directory as available space. | The directory had no owner decision, could be cleaned at any time, and was not a sanctioned destination. | An unowned writable path is not a destination. It needs an owner decision first. |

## Results & Parameters

### Configuration

```yaml
primary_allocation: declared_scope_from_storage_owner
candidate:
  path: proven_by_create_and_unlink
  declared_allocation_bytes: owner_stated
  measured_usage_bytes: from_du
  independent: true|false
fallback_decision: dedicated_allocation | quota_increase | none
```

### Expected Output

- A candidate list with access proof and a measured usage for each entry.
- An independence result for each candidate, with the primary allocation named.
- A fallback decision: a dedicated allocation, a quota increase, or an explicit statement that no safe fallback exists.
- The recorded inputs next to the fallback configuration.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Generalized storage-fallback selection | A service needed a spill target while its primary root was full | Two writable candidates existed. One was a sibling of the primary store and shared its allocation; one belonged to another tenant. The adopted destination was already more than four fifths used while the mount reported large free space. See [notes](storage-fallback-capacity-independence.notes.md). |

## References

- [Slurm shared-storage artifact relocation](slurm-shared-storage-artifact-relocation.md): headroom probing and the `df`-blindness mechanics.
- [Btrfs ENOSPC metadata pressure](btrfs-enospc-inheriting-props-metadata-pressure.md): a different ENOSPC cause when free space remains.
- [Pipeline auxiliary-lane capacity isolation](pipeline-auxiliary-lane-capacity-isolation.md): the same independence rule for worker capacity.