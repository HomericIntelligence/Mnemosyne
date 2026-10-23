---
name: backup-before-state-mutation
license: BSD-3-Clause
description: "Never mutate shared persistent state without a verified restorable snapshot of the affected scope first; when a full dump is impractical, snapshot exactly the mutation's effect surface with a manifest and restore instructions. Use before database writes, bulk deletes, revocations, or migrations, especially when full-backup tooling or volume makes naive dumps infeasible."
category: architecture
date: 2026-10-23
version: "1.0.0"
user-invocable: false
tags:
- backup
- mutation-safety
- snapshot
- restore-executability
- operations
---

# Skill: backup-before-state-mutation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Guarantee that every irreversible state mutation can be reverted from a verified snapshot, without letting full-backup cost block the gate |
| **Outcome** | Standing gate adopted mid-operation after a team directive; scoped-snapshot procedure engineered, verified, and used before the day's only database mutation |

## When to Use

Use this skill when:

- You are about to run a mutating command against shared or persistent state: database writes, bulk deletes, credential revocations, migrations, queue surgery.
- A revert path may be needed (incident response, first-time procedure, manually assisted recovery).
- A full backup is impractical: the datastore's volume is dominated by history you will not touch, the platform's dump client is not installed on your access nodes, or credentials for the backup tool are unavailable — but the mutation touches a small, identifiable scope.
- A standing rule applies: "no changes without a backup." Treat the gate as part of the mutation, not optional prep.

## Verified Workflow

### Quick Reference

```text
1. IDENTIFY   the mutation's effect surface (objects it can create/change/delete,
              plus direct dependencies a restore would need, e.g. FK parents).
2. SNAPSHOT   every object in that scope — no mutation runs before this completes.
3. VERIFY     the snapshot (integrity check + content spot-check against live,
              e.g. row-count parity). An unverified dump is not a backup.
4. RECORD     manifest: timestamp, purpose, per-object counts, excluded scopes,
              executable restore instructions, snapshot location.
5. MUTATE,    then note the snapshot id next to the mutation in the change log,
              so any later revert can cite exactly which state it restores.
```

### Suggested Approach

Make the gate unconditional. "Backup first" fails in practice when it is slow or heavyweight, because the operator under time pressure skips the step exactly when risk is highest. A scoped snapshot that completes in seconds removes that failure mode. If the dump is expected to be slow, that is a signal to reduce scope, not to drop the gate.

Scope deliberately rather than fully when the datastore partitions cleanly. In a typical relational deployment the bulk volume is append-only history (telemetry, events, metrics) that no credential or configuration mutation can touch, while the mutable domain (accounts, entitlements, registry, desired-state) is small. Snapshot the mutable domain in full plus the mutation's dependencies; record the excluded scopes explicitly in the manifest so a restorer later knows precisely what is not covered. Never let "we could not dump everything" degrade silently into "we dumped nothing."

Make restoration executable, not aspirational. Put the exact restore commands (or a pointer to them) in the snapshot directory itself, keep a machine-readable manifest, and prefer formats that restore per-object (per-table CSV/COPY dumps restore selectively; opaque full-system dumps often cannot be read without the original tooling). When platform tooling is missing, use the application's own client library export (e.g. `COPY ... TO STDOUT`) — tooling independence matters more than format elegance.

Verify before you depend. Check decompression integrity and parity of counts against live objects. Then mutate, and leave the coupling record: snapshot id ↔ mutation id, in whichever log is canonical for the operation. See [notes](backup-before-state-mutation.notes.md) for the generalized procedure, manifest fields, and verification checklist used in production.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Full-dump plan | Default first plan: take a complete dump before a targeted single-row revocation | No platform dump client existed on the access nodes, and the datastore volume (~0.4 TB) was ~99% history tables outside the mutation path; a full dump would have been the slowest, most fragile, least restorable option | Feasibility of the naive plan must be checked before promising it; volume dominated by unrelated history is itself the scoping signal |
| Unverified write path | First snapshot run crashed mid-write (text/binary mode mismatch in the compression writer) | Caught only because verification ran before the mutation; had the crash happened silently, the gate would have existed on paper with a corrupt snapshot behind it | Run verification as part of the gate, and re-run the whole snapshot from scratch rather than resuming a partial dump into the same directory |

## Results & Parameters

### Configuration

```text
required:   snapshot of every object in the mutation effect surface
verify:     archive integrity check + live-parity spot check (row counts / file counts)
manifest:   timestamp, purpose, per-object counts, excluded scopes, restore commands, snapshot id
coupling:   mutation log references snapshot id; restore log references mutation id
exclusions: allowed only when justified by volume/irrelevance, and must be listed explicitly
```

### Expected Output

- Every irreversible mutation has a same-day verified snapshot whose scope provably covers the mutation.
- A revert can be executed from the snapshot directory alone (manifest + restore commands), without rediscovering procedure.
- Zero skipped backups due to dump cost; procedure time stays in the seconds-to-minutes range.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal model-serving platform | Production rollout: standing "backup before any DB change" rule adopted mid-operation; snapshot engineered and verified before a credential revocation | [notes.md](backup-before-state-mutation.notes.md) |

## References

- Neighbor in the mutation-safety family (post-mutation unknown-outcome reconciliation): [reconcile-before-retry-mutation-status-loss.md](reconcile-before-retry-mutation-status-loss.md)
- Destructive local recovery gating (client-side mirror of this gate): [destructive-reset-requires-explicit-rejection.md](destructive-reset-requires-explicit-rejection.md)
