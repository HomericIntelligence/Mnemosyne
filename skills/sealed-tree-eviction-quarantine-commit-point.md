---
name: sealed-tree-eviction-quarantine-commit-point
description: "Delete a sealed, read-only artifact tree under a lifecycle policy without ever exposing a half-deleted live tree. Use when: (1) programmatic eviction or retirement removes trees whose files are mode 0444 and directories are mode 0555, (2) one deletion spans a tree plus sidecar records and derived outputs, (3) a crash mid-deletion must self-heal on the next pass, or (4) a durable record decides deletion candidacy."
category: architecture
date: 2026-11-23
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [filesystem, permissions, eviction, atomic-rename, quarantine, tombstone, crash-safety, sealed-artifacts, fail-safe, liveness-guard]
---

# Evict Sealed Trees With a Quarantine Rename Commit Point

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-23 |
| **Objective** | Remove sealed, read-only artifact trees under an automated lifecycle policy so a crash or permission failure at any point never leaves a broken artifact under its live name. |
| **Outcome** | Operational. The pattern is implemented and merged: an eviction pass removes sealed trees through a quarantine rename, unlocks and deletes best-effort, reclaims stale quarantines on the next pass, and keeps candidacy records outside the deletion target. |

A lifecycle policy such as space-pressure eviction or artifact retirement deletes
trees that were sealed on purpose: files carry mode 0444 and directories carry
mode 0555, so an owner cannot unlink them in place. An in-place delete of such a
tree fails partway at the first sealed entry and leaves a half-deleted tree
under the live name. Consumers then see a broken artifact, and no atomic undo
exists.

Make one atomic rename the commit point instead. Rename the tree to a reserved
quarantine name first; readers see the full artifact or none. Do the destructive
work after the rename, as best-effort work that a later pass can finish.

## When to Use

- A change adds programmatic eviction, garbage collection, or retirement that deletes sealed or read-only trees (files 0444, directories 0555).
- One logical deletion spans several artifacts: the tree, sidecar records, and derived outputs such as rendered or generated files.
- A deletion pass can crash or be killed, and the next pass must finish the work without operator help.
- A durable record outside the deleted content decides whether an artifact is a deletion candidate.

For a manual bulk delete of scratch trees that fails with `Permission denied`, use the chmod-then-delete repair entry instead; that flow repairs modes in place and needs no quarantine state machine.

## Verified Workflow

### Quick Reference

```python
# 1. Guard: every live-state signal agrees on zero; junk reads count as live.
if has_live_state(slug):
    return  # never evict

# 2. Commit point: one atomic rename out of the live identity.
quarantine = root / f".{QUARANTINE_PREFIX}{slug}.{token_hex(4)}"
tree.rename(quarantine)          # atomic; readers see all or nothing

# 3. Best-effort destruction after the commit point.
remove_readonly_tree(quarantine) # chmod unlock on PermissionError, retry
remove_derived_outputs(slug)     # sidecars, rendered files, images
# 4. Stamp the durable record AFTER removal; the record lives OUTSIDE the target.
mark_deleted(models_root, slug, now)
```

### Suggested Approach

1. **Rename before you delete.** Pick one atomic `rename` to a reserved
   quarantine name (a dot-prefix plus a random suffix) as the commit point.
   Everything after the rename is cleanup. A reader that resolves the live name
   never meets a half-deleted tree.
2. **Unlock sealed entries during cleanup.** On `PermissionError`, chmod the
   entry (file 0600, directory 0700), then retry the unlink or rmdir. Treat
   `FileNotFoundError` as success; a concurrent cleaner may have won. Do the
   same unlock for the parent directories that the tree sealed.
3. **Clean derived outputs after the tree rename.** Remove sidecar records and
   generated outputs by a bounded name pattern (exact name plus a strict
   revision suffix regex). A loose glob can delete unrelated artifacts.
4. **Reclaim stale quarantines at the start of every pass.** A crash between
   rename and cleanup leaves a quarantine directory. The next pass removes
   those leftovers first, so the system self-heals without an operator.
5. **Keep candidacy records outside the deletion target.** A record that the
   eviction pass reads must not live under the tree it condemns. Put it in a
   sibling directory and write the deletion stamp there after removal. Make a
   missing or unreadable record mean "never a candidate"; fail safe against
   deletion, never toward it.
6. **Guard candidacy with a zero-state check that treats junk as live.** Every
   live-state signal must agree on zero: no replica or donor entries, all
   status counters zero, and no desired-state demand. A status file that is
   unreadable, is not a dictionary, or names unknown states counts as live. An
   eviction that races an activation is worse than a deferred eviction.
7. **Document the race window instead of hiding it.** The guard read and the
   rename are not one transaction; a pool can start between them. State the
   one-pass window in the docstring and accept it, or add a second check under
   the same lock if the workload cannot tolerate it.
8. **Let the caller decide sufficiency.** An eviction helper that frees space
   should evict ordered candidates until the space check passes or the
   candidate list is done, then return a count. The caller re-checks space and
   fails with its own error code if the freed space is not enough.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Delete the sealed tree in place | Called tree removal directly on the live path | The first mode-0444 entry raised `PermissionError` and the pass died with a half-deleted tree under the live name | Make the atomic rename the commit point; destruction after the rename is best-effort cleanup |
| Read candidacy state from inside the target | Stored the lifecycle record under the tree that eviction removes | The record dies with the artifact, so a retry pass loses the timeline that decides candidacy | Keep the record in a sibling directory; write the deletion stamp there after removal |
| Trust every status read | Let the status reader catch only missing-file and bad-JSON errors | A path that is a directory, or another `OSError`, crashed the eviction pass instead of being treated as a live signal | Catch `OSError` in the guard and treat an unreadable record as live |
| Delete derived outputs with a loose glob | Matched all files with the artifact prefix | The glob also matched unrelated artifacts that share the prefix | Match the exact name plus a strict revision-suffix pattern, and keep a quarantine prefix reserved |

## Results & Parameters

### Configuration

```text
QUARANTINE_PREFIX   dot-prefixed name fragment, one per domain, for example ".evicting-"
QUARANTINE_SUFFIX   random token (for example 4 bytes hex) so concurrent passes never collide
MAX_EVICTIONS       per-pass cap (for example 8) that bounds the blast radius of one pass
```

### Expected Output

- The live artifact name disappears in one atomic step; no consumer ever observes a partial tree.
- A killed pass leaves at most a quarantine directory, and the next pass removes it.
- An artifact with any live signal, or with a missing or unreadable candidacy record, stays untouched.
- The durable record shows the deletion stamp only after the artifacts are gone.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A model-deployment control plane with sealed model trees | Eviction on the disk-capacity path; sealed modes 0444/0555; dedicated unit tests for the rename commit point, stale-quarantine cleanup, and the live-state guard matrix | Suite green locally before merge; the change merged with all hosted checks green. Measured cases in [notes](sealed-tree-eviction-quarantine-commit-point.notes.md) |

## References

- [Repair a bulk delete that fails with permission denied](rm-permission-denied-owner-readonly-repair.md) — the manual cleanup flow with the same chmod-unlock mechanics
- [Sealed artifact public hardlink projection](sealed-artifact-public-hardlink-projection.md) — the publication-side counterpart for sealed trees
