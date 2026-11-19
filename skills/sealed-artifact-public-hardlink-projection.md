---
name: sealed-artifact-public-hardlink-projection
license: BSD-3-Clause
description: "Expose existing sealed artifacts through a public read-only tree without changing a closed administrative ancestor or copying the data. Use when: (1) the source and public roots can support hardlinks, (2) a verifier requires one link or records ctime, (3) receipts or manifests must stay single-link, or (4) rollback must leave the source store intact."
category: architecture
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags: [shared-storage, hardlinks, sealed-artifacts, public-projection, permissions, manifest, link-count, ctime, rollback]
---

# Project Sealed Artifacts Through a Public Hardlink Farm

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Give ordinary readers access to approved sealed artifacts through a service-owned public tree while the administrative source tree stays closed and canonical. |
| **Outcome** | Design reviewed. Source and filesystem inspection identified the required link-count, metadata-identity, permission, and rollback boundaries. Implementation and rollout were not executed in the source session. |

A symbolic link does not bypass a closed source ancestor. A full copy can cost too much capacity. A permanent hardlink can expose the same sealed inode through a traversable public tree, but it also shares mode, ownership, link count, and ctime with the source. Treat those effects as part of the publication contract, not as implementation details.

## When to Use

- Existing immutable models, images, or other large artifacts must become readable below a public root, and an administrative ancestor must keep its current mode.
- The source and destination can support hardlinks, and duplicating the artifact bytes is not acceptable.
- A source verifier requires `st_nlink == 1`, or a manifest records `st_ctime_ns` for each artifact.
- Small metadata records must keep one link even when the large data file has a public second link.
- Removing the public projection must leave the administrative source and its bytes intact.

Do not use this pattern for a mutable source tree. A hardlink shares later content and metadata changes. Do not use it to avoid license, reader-set, or ownership approval. For a temporary link-then-unlink publication whose reader requires one link, keep the strict reader and use a no-replace rename instead.

## Verified Workflow

### Quick Reference

```text
APPROVE READERS -> PROBE THE EXACT LINK OPERATION -> SEAL SOURCE FILES
  -> HARDLINK IMMUTABLE DATA -> COPY SINGLE-LINK RECORDS
  -> REFRESH CTIME-ONLY IDENTITY -> VERIFY SOURCE AND PUBLIC TREE
  -> PUBLISH -> VERIFY AS AN ORDINARY READER

Rollback:
UNLINK ONLY THE EXPECTED PUBLIC NAMES -> REFRESH CTIME-ONLY IDENTITY
  -> VERIFY THE SOURCE WITH ITS ORIGINAL STRICT CONTRACT
```

### Suggested Approach

1. **Approve the new reader boundary before publication.** Record the approved artifact set and reader set. Check the license or distribution terms for each artifact. Prove that an ordinary reader can traverse every public ancestor but cannot traverse the administrative source ancestor. Publish only the approved names below the public root.
2. **Probe the exact hardlink operation on the execution node.** Use disposable files in the real source and destination parents, outside the artifact tree. Equal `st_dev` values are supporting evidence, not a guarantee on every distributed filesystem. Stop on `EXDEV` or another link refusal. Do not silently start a full copy. A symbolic link is not an alternative while the source ancestor remains closed.
3. **Seal the source before creating links.** Derive the file list from the sealed manifest or receipt. Reject symlinks, special files, foreign-owned entries, and names outside that list. Set only the approved source data files to their final read-only mode. Keep source directories and the administrative root unchanged. Never recursively chmod the source or public root. After linking, a chmod through either name changes both names.
4. **Separate immutable data from single-link records.** Hardlink the large immutable data files. Copy manifests, receipts, sidecars, and selection pointers as independent read-only files when their verifier requires one link. Stage the public tree privately, apply exact owner and mode policy, and publish with a non-replacing atomic operation. Reuse an existing public name only when it names the expected inode and has the expected metadata; refuse a different inode instead of replacing it.
5. **Scope every link-count exception to the artifact that needs it.** Keep the default verifier at one link. At the approved data-reader call sites, allow exactly the expected maximum, normally two links. Keep receipts, probes, and unrelated callers at one link. Retain regular-file, owner, read-only mode, approved-path-chain, digest, and embedded-record checks. Include `st_nlink` in the before-and-after verification identity so a link change during validation is visible. Do not weaken all artifact verification to support one public projection.
6. **Refresh metadata identity after every link or mode transition.** Creating or removing a hardlink and changing a mode updates ctime without changing the file bytes. If a manifest records ctime, a stale record can cause a full rehash on every verification. Before a refresh, require device, inode, size, mtime, and the sealed content identity to remain unchanged; update only the metadata fields explained by the operation. Preserve the content-derived artifact ID. Replace a manifest atomically when its parent is writable. If the parent is read-only and cannot change, use a separately reviewed recovery-safe metadata update or a writable metadata record; do not describe an in-place rewrite as atomic. Copy the refreshed public manifest after the source update. Repeat the refresh after rollback removes public links.
7. **Verify both views and future releases.** Verify the public data by digest and verify the expected link count for data and records. Verify that the source still passes its content checks without a repeated full rehash. Read the public artifacts as a user outside the administrative group. Update path policy and release publication together so later releases cannot omit the public projection. A user who needs a writable copy must copy and verify the bytes into a user-owned destination; the shared hardlink must not become that user's writable file.
8. **Make rollback remove names, not source data.** Confirm each public name still names the expected inode, then unlink only that public name. Do not remove or chmod the administrative source. Refresh ctime-bound metadata again and prove that strict one-link verification passes where the original contract requires it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Open the administrative ancestor or link to it | Evaluated a public symlink into a tree whose ancestor stayed closed | Source review showed that ordinary readers still could not traverse the source ancestor, and the required root-mode change was unavailable | Project approved files into a traversable public tree; do not expect a symlink to bypass permissions |
| Mirror the full artifact store | Evaluated a full copy of every model and image into public storage | The available capacity could not hold a second full store | Probe permanent hardlinks and stop cleanly when the filesystem cannot support them |
| Hardlink every publication record | Considered giving receipts and manifests a second link along with the data | Source review showed that consumers requiring `st_nlink == 1` would reject those records | Hardlink immutable data; copy records that must remain single-link |
| Remove the link-count guard | Considered letting every image or record consumer accept multiple links | The change would weaken unrelated trust boundaries | Allow a bounded link count only at approved data-reader call sites |
| Link first and seal through the public name | Considered a chmod of the public hardlink after creation | The operation would also change the administrative inode and its ctime | Seal source files before linking and never manage source metadata through the public name |
| Leave a ctime-bound manifest unchanged | Considered treating link creation as a namespace-only operation | Source review showed that verification would see stale identity and could rehash the full artifact on every run | Refresh only the explained metadata fields while preserving content identity, and repeat after rollback |
| Infer link support from device numbers | Considered equal `st_dev` values as proof, with a full-copy fallback | Distributed filesystems can reject the exact operation, and the fallback can exceed capacity | Probe the exact parent pair and primitive; stop on failure |

## Results & Parameters

### Configuration

```yaml
source:
  administrative_directories: unchanged
  data_files: seal to final read-only mode before the first link
  file_allowlist: sealed manifest or receipt
public_projection:
  immutable_data: permanent hardlink
  single_link_records: independent read-only copy
  example_directory_mode: "0555"
  example_file_mode: "0444"
verification:
  default_max_links: 1
  approved_data_max_links: 2
  receipt_and_probe_max_links: 1
  metadata_refresh_fields: [st_ctime_ns]
  preserve: [st_dev, st_ino, size, st_mtime_ns, content_digest, content_id]
link_probe_failure: stop; do not start an unapproved full copy
rollback: unlink expected public names only, then refresh metadata identity
```

### Expected Output

- Ordinary readers can read approved public artifacts without access to the administrative ancestor.
- Public data names and administrative names share only the intended immutable data inodes.
- Public and administrative receipts or manifests that require one link remain independent single-link records.
- Source verification keeps its content identity and does not rehash solely because a public link was added or removed.
- Strict consumers keep their original default; only the approved data path accepts the bounded second link.
- Public removal leaves the source bytes present and restores the source link count.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An anonymized shared-cluster artifact service | Design review of source verifiers, manifests, path policy, and live filesystem metadata | The review established the closed-ancestor, capacity, link-count, and ctime constraints. One target filesystem pair shared a device number; the exact hardlink probe remained a rollout prerequisite. Another cluster was not inspected. No production publication or code change was executed. See [notes](sealed-artifact-public-hardlink-projection.notes.md). |

## References

- [Relocate large artifacts on shared storage](slurm-shared-storage-artifact-relocation.md) — probe the exact operation and keep an independent-copy workflow separate.
- [Publish anchor files fully configured](publish-anchor-files-fully-configured.md) — keep single-link readers strict for transient link-then-unlink publication.
- [Revive a sealed receipt runtime](sealed-receipt-runtime-revival.md) — a shared inode propagates metadata changes to every name.
- [Prove the whole path to a per-user writable directory](per-user-writable-path-under-closed-root.md) — validate every ancestor and access class.
- [Repair a directory leaf without widening permissions](directory-repair-leaf-only.md) — do not change foreign ancestors during leaf publication.
- [Model-weight license scope for internal hosting](model-weight-license-internal-hosting-scope.md) — review the actual license when the reader set grows.
