---
name: slurm-shared-storage-artifact-relocation
license: BSD-3-Clause
description: "Relocate large artifact trees through Slurm and shared storage without exposing a partial destination or deleting the only good copy. Use when: (1) a quota-bound checkpoint, model, dataset, or image tree must move to shared storage, (2) cross-parent rename may fail with EXDEV even though stat reports equal st_dev values, (3) login, sandbox, and compute nodes can see different mount or identity metadata, (4) an interrupted copy must resume by verified content, or (5) source retirement needs a separate destructive-authorization gate."
category: tooling
date: "2026-07-31"
version: "1.0.0"
verification: verified-local
user-invocable: false
tags: [slurm, shared-storage, filesystem, exdev, renameat2, artifact-relocation, resumable-copy, atomic-promotion, integrity, quota]
---

# Slurm Shared-Storage Artifact Relocation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-31 |
| **Objective** | Relocate a large immutable artifact tree off quota-limited storage without trusting namespace-dependent metadata, exposing a partial final path, or coupling a verified copy to destructive source deletion. |
| **Outcome** | A compute-node probe disproved a cross-parent rename assumption, so the fresh-run operation became an independent copy with source-stream hashing into fsynced private staging, staging inventory/safety validation, destination normalization, same-parent non-replacing promotion, and an independent full final-tree rehash. The source remained intact pending separate retirement authority. |
| **Verification** | verified-local for the fresh-copy path on a scheduled compute node. The exact cross-parent `renameat2(RENAME_NOREPLACE)` probe returned `EXDEV` despite equal observed `st_dev`; target-side same-parent promotion and an approximately 75 GB copy succeeded. Resume, source retirement, pre-promotion full rehash, formal writer-lock evidence, post-normalization durability sweep, and ambiguous-rename recovery were not exercised in that run; strict review made those hardening gates explicit below. |

## When to Use

- A model, checkpoint, dataset, container image, or other immutable artifact tree must move from a quota-bound namespace to shared storage.
- Slurm compute nodes are authoritative for the operation, while the login shell, sandbox, or control node may expose different mounts, device numbers, ownership translations, or permissions.
- `stat` reports the source and destination parents on the same `st_dev`, but the storage system may still reject a cross-parent rename with `EXDEV`.
- A long copy must resume after preemption without accepting a truncated or stale destination file.
- Consumers must never observe a partially populated final directory.
- Deleting the source is destructive and requires an explicit decision after the mirror has been independently verified.

Do not apply the immutable-tree workflow directly to a live database or application data directory. Quiesce the writer, use a storage snapshot, or follow an application-aware delta/cutover procedure first.

## Verified Workflow

### Quick Reference

Treat relocation as a state machine, not as a single `mv` command:

```text
BIND -> DISCOVER -> PROBE -> SEAL -> STAGE -> COPY
  -> VERIFY -> NORMALIZE -> PROMOTE (or RECONCILE) -> REVERIFY -> STOP
                                                                    |
                                                         separate authority
                                                                    v
                                                                 RETIRE
```

Create a private, immutable JSON configuration with a stable operation ID. Write it through an exclusively created temporary file, `fsync` it, rename it without replacement, and `fsync` its parent. Do not source it as shell code.

```json
{
  "schema_version": 1,
  "operation_id": "<stable-operation-id>",
  "source": "<source-artifact-path>",
  "target_parent": "<private-target-parent>",
  "artifact_name": "<artifact-name>",
  "worker_sha256": "<sha256-of-reviewed-worker>"
}
```

Bind the reviewed configuration to the Slurm job by digest. This submission preflight fails closed, rejects dangling configuration/worker symlinks, and exports no ambient path variables:

```bash
#!/usr/bin/env bash
set -euo pipefail
umask 077
CONFIG="<private-relocation-config.json>"
EXPECTED_CONFIG_SHA256="<sha256-of-reviewed-config>"
WORKER="<relocation-worker>.sbatch"
EXPECTED_WORKER_SHA256="<sha256-of-reviewed-worker>"

case "${CONFIG}${EXPECTED_CONFIG_SHA256}${WORKER}${EXPECTED_WORKER_SHA256}" in
  *'<'*|*'>'*) echo "replace every placeholder before submission" >&2; exit 64 ;;
esac

if [ ! -f "$CONFIG" ] || [ -L "$CONFIG" ]; then
  echo "config must be a regular, non-symlink file" >&2
  exit 66
fi
if [ "$(stat -c '%u' -- "$CONFIG")" -ne "$(id -u)" ]; then
  echo "config owner mismatch" >&2
  exit 77
fi
case "$(stat -c '%a' -- "$CONFIG")" in
  400|600) ;;
  *) echo "config must be owner-readable only" >&2; exit 77 ;;
esac

actual_config_sha256="$(sha256sum -- "$CONFIG")"
actual_config_sha256="${actual_config_sha256%% *}"
if [ "$actual_config_sha256" != "$EXPECTED_CONFIG_SHA256" ]; then
  echo "config digest mismatch" >&2
  exit 65
fi
if [ ! -f "$WORKER" ] || [ -L "$WORKER" ]; then
  echo "worker must be a regular, non-symlink file" >&2
  exit 66
fi
if [ "$(stat -c '%u' -- "$WORKER")" -ne "$(id -u)" ]; then
  echo "worker owner mismatch" >&2
  exit 77
fi
case "$(stat -c '%a' -- "$WORKER")" in
  400|500|600|700) ;;
  *) echo "worker must be owner-accessible only" >&2; exit 77 ;;
esac
actual_worker_sha256="$(sha256sum -- "$WORKER")"
actual_worker_sha256="${actual_worker_sha256%% *}"
if [ "$actual_worker_sha256" != "$EXPECTED_WORKER_SHA256" ]; then
  echo "worker digest mismatch" >&2
  exit 65
fi

sbatch --export=NONE "$WORKER" \
  "$CONFIG" "$EXPECTED_CONFIG_SHA256" "$EXPECTED_WORKER_SHA256"
```

The worker contract is:

1. Recompute the configuration digest, validate its schema, resolve every path, and log the bound facts before mutation.
2. Probe the exact parents and exact filesystem primitive on the execution node.
3. Establish a whole-tree immutability boundary and create a byte-safe, content-addressed manifest.
4. Create or authenticate the stable operation's owner-private staging state.
5. Copy or resume through exclusive temporary files and independently validate every accepted staging file.
6. Verify the complete staging tree, normalize destination metadata, and durably sync the normalized tree.
7. Promote staging with a same-parent, non-replacing rename; reconcile both names on any reported error.
8. Reverify the final tree and stop with the source still present.
9. Retire the source only in a later, explicitly authorized operation.

The exact probes, fresh copy, promotion, final rehash, and source retention were exercised. The stronger binding, whole-tree locking, pre-promotion independent rehash, durability sweep, and error-reconciliation details are review-derived hardening; retain that evidence distinction until they are exercised end to end.

### Detailed Steps

1. **Bind the reviewed configuration to the execution environment.**

   Store the private canonical JSON and reviewed worker on storage visible to the compute node. Pass the configuration path, configuration digest, and expected worker digest as explicit arguments. The worker must reopen the configuration without following links, re-check its owner/mode and digest, validate the schema, reject unknown fields, require the configuration's `worker_sha256` to equal the third argument, and log the operation ID, resolved source/final paths, node, tool revision, and both digests before mutation. Never depend on unexported submission-shell variables.

   Resolve source and target parents to absolute paths, open stable directory descriptors, and anchor later traversal beneath them. Prefer Linux `openat2` with `RESOLVE_BENEATH` and no-symlink constraints; otherwise combine `openat`/`lstat`/`O_NOFOLLOW` with explicit component checks. Reject absolute manifest entries, `.`/`..` components, duplicate paths, path escape, and any final-path object including a dangling symlink.

2. **Probe the exact cross-parent operation.**

   On the execution node, create disposable probe objects beneath dedicated sibling names in the exact source and target parents—never inside the artifact tree—and invoke the same primitive planned for production, such as `renameat2(..., RENAME_NOREPLACE)`. Capture the result and current `stat`/mount evidence. Complete and remove probes before sealing the source; an unaccounted-for probe or cleanup failure stops the operation.

   - `EXDEV` is definitive: that exact cross-parent rename is unavailable in the current view.
   - Equal `st_dev` values do not prove rename compatibility on a distributed, routed, overlaid, or id-mapped filesystem.
   - Success is scoped to that node, those parents, that mount state, and that primitive.
   - Separately probe target-side staging-to-final rename; both names must use the same opened target parent.

   Prefer `RENAME_NOREPLACE` or an equivalent atomic non-replacing primitive. An existence check followed by ordinary rename is a time-of-check/time-of-use race.

3. **Establish whole-tree immutability and a byte-safe manifest.**

   Hold an application-recognized writer lock, quiescence boundary, read-only storage snapshot, or already immutable publication for the entire manifest/copy interval. Per-file before/after checks detect mutation during one read but cannot prevent a manifest assembled from different tree generations. Stop if a whole-tree boundary cannot be established.

   Walk with `lstat`, reject unsupported symlinks, devices, sockets, FIFOs, and hard links, and confirm destination space/quota. Encode raw relative path bytes safely, for example as base64 in canonical JSON sorted by raw path bytes, together with type, size, digest, and metadata policy. A pipe- or newline-delimited human path is not safe for every legal filename.

   Create the manifest under the unique operation ID through an exclusive temporary file, `fsync` it, rename without replacement, `fsync` its parent, and record its digest in the private operation marker. Do not mutate the source with `chmod` or `chown`; those operations change `ctime` and invalidate the seal. The captured run computed source digests while copying; generating and syncing the complete manifest before destination mutation is required hardening for subsequent use.

4. **Choose stable identity facts empirically.**

   Compare submission and execution views before pinning an invariant. Device numbers and numeric group ownership can be translated by mount or sandbox views. In the verified case, root inode and UID were stable while `st_dev` and GID were view-dependent; that is evidence for that object and environment, not a universal list.

   Use the canonical manifest and configuration digests as primary identity. Supplement them with only root facts demonstrated stable for this run, then re-check them before copy and retirement.

5. **Create or authenticate stable staging state.**

   Derive staging, manifest, and marker names from the stable operation ID; retries must reuse that identity rather than generate a new staging path. First use creates staging exclusively beneath the target directory descriptor, mode `0700`, and syncs an owner-private marker containing configuration and manifest digests.

   A retry may resume only when the final name is absent under `lstat`, staging is a real owner-controlled directory with the expected private mode, and its marker/digests match exactly. If final exists, staging is a symlink, ownership/mode is wrong, or either digest differs, enter reconciliation and do not copy, rename, or clean up.

6. **Copy through restart-safe temporary files.**

   Keep staging directories owner-private and use regular-file mode `0600` until normalization. For every manifest entry:

   1. Open the anchored source without following links and record size plus nanosecond `mtime`/`ctime` before reading.
   2. For an existing staging file, reopen and hash all bytes; skip it only when path, type, size, and digest match the manifest.
   3. Otherwise use a unique same-directory temporary file created exclusively with no link following.
   4. Hash the source stream while writing, flush and `fsync` the temporary file, then reopen and hash the temporary file independently against the manifest.
   5. Re-stat the source; discard the temporary and abort if relevant identity or metadata changed.
   6. Rename the verified temporary to its staging name and `fsync` the containing directory.

   Never append blindly or write in place. Reuse a partial file only under a separately verified range-aware protocol; otherwise recopy that file into a fresh temporary name. The independent staging-file rehash is required hardening; the captured fresh run used source-stream hashing plus `fsync` and independently rehashed the full tree only after promotion.

7. **Verify staging before publication.**

   Perform a fresh anchored walk immediately before promotion. Require the exact path set, type, size, and digest for every entry; reject extras, special files, symlinks, and multiply linked files; require the interim private-staging ownership/mode policy; and require the final name to be absent under `lstat`.

   File counts and aggregate bytes are diagnostics, not integrity evidence. This independent pre-promotion full rehash is required hardening and was not part of the captured fresh run.

8. **Normalize and durably sync staging.**

   Apply final ownership, modes, and approved metadata policy only to staging, then verify that policy. `fsync` every metadata-changed regular file and sync every staging directory bottom-up, including empty directories and the staging root. Treat any sync error as a failed durability gate unless the platform has a reviewed, documented equivalent.

   Do not leave fallible normalization or nested-tree durability work until after the final name is visible. The explicit post-normalization durability sweep is review-derived hardening and was not instrumented in the captured run.

9. **Promote and reconcile ambiguous outcomes.**

   Invoke target-side `RENAME_NOREPLACE` using the opened target parent descriptor. On reported success, `fsync` the target parent. Atomicity comes from that successful same-parent operation, not from equal device numbers or the word "rename" alone.

   On any error or timeout, freeze the operation and inspect both staging and final with anchored `lstat`. Never retry or clean up blindly: a network filesystem can perform a server-side rename and still report failure after a retry. Staging-only means not committed but requires revalidation before a deliberate retry; final-only may mean committed and requires full manifest/configuration verification; both or neither is inconsistent and requires operator investigation. Classify success only from a coherent verified state and durable operation record.

10. **Reverify the published tree and stop.**

    Walk final from scratch and compare it to the canonical manifest. Record root identity, exact paths, bytes, digests, ownership/modes, operation/configuration/manifest digests, and parent-sync result. Run any non-destructive consumer smoke required by the artifact format.

    Finish with the source intact. A successful copy is not implicit authority to delete data.

11. **Make source retirement a separate destructive transaction.**

    Require explicit instruction naming the exact source and verified final destination. Re-establish the writer/cutover boundary, rehash final, re-check source and stable root identity against the bound manifest/configuration, and abort immediately on any mismatch. Resolve every deletion target beneath the pinned source descriptor without globs, symlink traversal, or unresolved environment variables.

    This capture verified separation and source retention; it did not execute deletion. Keep retirement mechanics and evidence distinct from the copy/promotion record.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ------- | ------- | ------- |
| Infer renameability from `st_dev` | A reviewed plan treated equal source/destination parent device numbers as evidence that cross-parent `renameat2` would work | The exact compute-node operation returned `OSError: [Errno 18] Invalid cross-device link` | Probe the exact primitive, exact parent pair, and actual execution node; `st_dev` equality is not a rename contract |
| Trust a non-execution namespace | Filesystem identity and ownership observations were taken from a sandbox/control view | The compute node exposed different device and group metadata | Treat mount and id-mapped metadata as view-local until cross-environment checks prove a fact stable |
| Pin device and group IDs as universal guards | The first design used numeric `st_dev` and GID values as hard preconditions | Those values changed across views even though the underlying object was the intended one | Pin the sealed content manifest and only empirically stable root facts; do not hard-code namespace-local observations |
| Submit unbound shell preflight | Standalone `test` commands checked shell variables, then submitted a worker that received none of them | Without strict shell exit or explicit arguments, a failed check could fall through and the worker could resolve different paths | Use strict fail-closed submission plus a private canonical configuration bound to the worker by digest |
| Assume per-file checks freeze the tree | Before/after metadata was checked around each individual read | Another file can change between reads, producing a mixed-generation manifest | Hold a writer lock, quiescence boundary, immutable publication, or storage snapshot across manifest and copy |
| Use delimiter-separated human paths | A simple path/size/digest row was treated as an unambiguous manifest | Legal filenames can contain delimiters and newlines, and malformed entries can escape the intended root | Encode raw relative path bytes canonically, reject traversal/duplicates, and anchor all opens beneath directory descriptors |
| Cross-parent move followed by cleanup | The initial transaction moved first and left normalization or verification afterward | The move itself was unsupported, and any later failure would have left no original path for rollback | Copy independently, normalize and verify staging, then use only a same-parent target-side promotion |
| Normalize the source before copying | A permission change was considered to simplify the destination policy | It changes source `ctime` and invalidates a seal intended to detect mutation | Leave the source untouched; normalize the independent destination staging tree |
| Combine copy and source deletion | One scheduled operation was proposed to copy, verify, promote, and then reclaim source storage | A fallible long copy and an irreversible deletion shared one authority boundary; deletion had not been explicitly authorized | End the copy operation with both verified copies present and request separate retirement authority |
| Accept counts and bytes as verification | Tree file count and aggregate size were available as quick checks | Different or corrupted content can have identical counts and byte totals | Compare exact path sets and per-file cryptographic digests in independent verification passes |
| Blindly retry a failed rename | Treat a reported network-filesystem rename error as proof that nothing happened | The server may have committed the rename even when the client reports failure | Freeze, inspect both names through anchored descriptors, and reconcile the actual state before retry or cleanup |

## Results & Parameters

### Required Invariants

| Phase | Required invariant |
| ------- | ------- |
| Bind | Private canonical configuration is atomically stored, synced, schema-valid, and bound to the reviewed worker by both digests |
| Discover | Whole-tree immutability is established, capacity is sufficient, and tree shape is supported |
| Probe | Exact compute-node cross-parent and target-side same-parent operations have recorded outcomes |
| Seal | Byte-safe canonical manifest is atomically stored, synced, and bound by digest |
| Resume | Stable staging identity, owner/mode, marker, and config/manifest digests authenticate an existing run |
| Copy | Only private staging changes; every accepted file is independently reopened, hashed, and synced |
| Verify | Fresh staging walk has the exact path/type/size/digest set; anchored `lstat` finds no final object |
| Normalize | Final policy is verified and every changed file/directory is synced before publication |
| Promote | Non-replacing same-parent rename succeeds and the target parent is synced |
| Reconcile | Any reported promotion failure is classified from both anchored names before retry or cleanup |
| Reverify | Final independently matches the sealed manifest and required metadata policy |
| Retire | Separate authority plus fresh bound source/final validation; deletion was not verified here |

### Verified Scale and Outcome

```text
Execution:             one scheduled compute node, fresh-run path
Cross-parent probe:    EXDEV despite equal observed st_dev
Target-side probe:     same-parent RENAME_NOREPLACE succeeded
Artifact scale:        34 regular files, 74,915,365,556 bytes
Destination policy:   owner-private; files 0600, directories 0700, link count 1
Copy evidence:         source stream hashed while writing/fsyncing each new file
Staging evidence:      exact inventory and safety policy checked; no full reopen/rehash
Final evidence:        independent full content validation after promotion
Scheduled job elapsed: 00:09:08; no per-phase copy timing was instrumented
Worker SHA-256:        c8db2f16df1deab02019d38b30075ee9a8ea6420b951e19181d75948f0c02425
Wrapper SHA-256:       7ab8b6124efa25c49b13c39b2fc566c3014fdf2bb6d7432134f1eb13c7b3fbb4
Source state:          retained and independently readable
Resume:                designed/reviewed, not interruption-tested in this run
Retirement:            intentionally not executed
```

The captured result verifies the fresh-copy core and the central `EXDEV` lesson. Before reuse, require the review-derived hardening above—especially a whole-tree boundary, byte-safe bound manifest, independent pre-promotion rehash, post-normalization durability sweep, and promotion-error reconciliation. Successful output keeps a complete evidence record and the original source until later authorized retirement.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Generalized model-artifact mirror | Quota-safe fresh copy from a private source namespace into shared scheduled-compute storage | Exact compute-node probing disproved cross-parent renameability. Source-stream hash checks, staging inventory/safety checks, same-parent non-replacing promotion, and an independent full final-tree validation completed for approximately 75 GB. Resume and deletion were not exercised; the source was deliberately retained. |

## References

- [Linux `rename(2)` and `renameat2(2)`](https://man7.org/linux/man-pages/man2/rename.2.html)
- [Linux `fsync(2)`](https://man7.org/linux/man-pages/man2/fsync.2.html)
- [Machine-local container artifact validation](machine-local-container-artifact-validation-lane.md)
- [Slurm verification in a shared worktree](hephaestus-slurm-verification-shared-worktree.md)
- [Application-aware NFS data relocation](homelab-nextcloud-data-dir-nfs-migration.md)
