---
name: experiment-evidence-store-consolidation
description: "Consolidate the sealed evidence of a closed experiment campaign into a durable categorized store, then delete the superseded material without breaking hash-referenced records. Use when: (1) a long research or training campaign has closed and its results are scattered across an origin root, (2) a user asks where the results are and what can be cleaned up, (3) sealed records cite sibling artifacts by content hash and absolute path, (4) hundreds of gigabytes must move between filesystems, or (5) a bulk delete leaves a tree behind with a permission error."
category: tooling
date: 2026-11-01
version: "1.0.0"
user-invocable: false
tags: []
---

# Experiment Evidence Store Consolidation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-01 |
| **Objective** | Find the result of a closed experiment campaign, move the durable evidence into one categorized archive store, and delete the superseded material safely |
| **Outcome** | Successful: the sealed proof chain, deliverable artifacts, champion checkpoints, bulk evidence, and provenance moved to a shared store; all superseded trees deleted; no hash-referenced record rewritten |

## When to Use

- A long research or training campaign has closed, and its artifacts sit in one origin root plus older sibling roots from earlier attempts.
- The user asks what the result was, where the results live, and what can be cleaned up.
- Sealed decision records cite sibling artifacts by sha256 identity and absolute path.
- A large relocation between filesystems is necessary, and the destination must keep the evidence valid.
- A bulk delete must not silently leave partial trees behind.

## Verified Workflow

### Quick Reference

```bash
# Move one tree per file: the source file is unlinked only after the copy verifies
rsync -a --remove-source-files "$SRC/tree/" "$DST/category/tree/"

# Remove the emptied source directories after each stream
find "$SRC/tree" -depth -type d -empty -delete

# Parallel streams: one background stream per independent top-level tree

# Fix a delete blocker: a read-only file in a write-protected directory survives rm -rf
chmod -R u+w "$SRC/tree" && rm -rf "$SRC/tree"

# Confirm nothing remains under the cleaned prefix
ls -d "$SRC"/prefix* 2>/dev/null || echo "prefix empty"
```

### Suggested Approach

1. **Start from the closure or decision record.** The final decision record of a
   sealed campaign cites each source artifact by path and content hash. Read it
   first. Use those citations as the index of what constitutes the result:
   the comparison, gate, leaderboard, and paired-outcome records, plus the
   champion lineage. Material that no citation reaches is a cleanup candidate.
2. **Sort keep material into five categories** before any move:
   sealed proofs (small decision, audit, submission, and receipt records);
   deliverable artifacts (final model weights and frozen inputs); lineage
   checkpoints (intermediate checkpoints of the passing variants only);
   archived bulk evidence (per-run evaluation records); and provenance
   (protocol source, manifests, run logs). Losing-variant checkpoints,
   rebuildable compiler caches, and superseded lineage roots stay outside the
   store. State the split to the user before moving.
3. **Move per file, not per tree.** Across filesystems, `rsync -a
   --remove-source-files` unlinks each source file only after the copy
   verifies. Run independent top-level trees as parallel background streams.
   Flatten the origin layout into the category directories, and keep each
   moved tree's internal layout unchanged so the mapping stays mechanical.
4. **Do not rewrite sealed records.** Their embedded absolute paths name the
   origin root, and relocation makes those paths stale. The content hashes
   stay valid because they do not depend on path. Record the
   origin-root-to-category mapping and the recorded identities in a README at
   the store root instead of editing any sealed record.
5. **Verify the destination before deleting sources.** Parse each key sealed
   record as JSON at the destination and confirm the recorded decision fields
   are present. Only then remove the sources.
6. **Delete, then confirm emptiness.** A `rm -rf` chained with `&&` stops
   output at the first denied file, and the operator can mistake partial
   progress for completion. List the prefix afterward and finish any remainder.
7. **Write a store README** that names the result in one paragraph, lists the
   recorded identities, maps the layout, and states the caveat about embedded
   origin paths and excluded material.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Plain `mv` across filesystems | Move a large evidence tree with `mv` | `mv` falls back to copy-plus-unlink with no per-file verification, no resume, and an opaque partial state after interruption | Use `rsync -a --remove-source-files`; the source file survives until its copy verifies |
| Repair stale paths in sealed records | Consider rewriting embedded absolute paths after relocation | Sealed records are immutable evidence; path edits corrupt provenance, and the hashes are path-independent | Record the origin-root mapping in a store README; never edit sealed content |
| Delete sources before verification | Remove the origin trees immediately after the copy starts | A copy error would then destroy the only copy | Parse the key destination records first; delete only after verification |
| Trust one chained `rm -rf` | Run `rm -rf a b c && echo done` | One read-only file raised `Permission denied`, hid the rest of the progress, and left a tree behind | `chmod -R u+w` the denied subtree, delete again, then list the prefix to confirm it is empty |

## Results & Parameters

### Configuration

```bash
# One stream per independent tree; set -e so a failed rsync stops that stream
set -e
rsync -a --remove-source-files --stats "$SRC/evaluations/" "$DST/archived-json/evaluations/"
find "$SRC/evaluations" -depth -type d -empty -delete

# Delete blocker fix for owner-readable-only material
chmod -R u+w "$SRC/tree" && rm -rf "$SRC/tree"
```

Store layout:

```text
<store>/
  README.md              # result, identities, origin-path caveat, layout map
  sealed-proofs/         # decision, closure, comparison, gate, audit records
  artifacts/             # deliverable weights and frozen inputs
  champion-checkpoints/  # intermediate checkpoints of passing variants only
  archived-json/         # bulk per-run evaluation evidence
  provenance/            # protocol source, manifests, run logs
```

### Expected Output

- Each `rsync --stats` block reports `Number of regular files transferred` with a zero error count.
- Each key sealed record parses at the destination and shows the recorded decision fields.
- The origin prefix listing is empty after the final delete.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| A closed machine-learning research campaign | Consolidation of a sealed sha256-identified result chain from a parallel filesystem home into a shared project store | About 190 GB of evaluation evidence and the full proof chain moved in parallel streams with zero transfer errors; superseded trees deleted after verification; see [notes](experiment-evidence-store-consolidation.notes.md) |

## References

- [Large data relocation between storage tiers with a service cutover](homelab-nextcloud-data-dir-nfs-migration.md)
- [Gentle bulk reads on fragile storage servers](nfs-server-oom-recursive-metadata-ops.md)
- [Path binding versus remembered session paths](session-cwd-path-alias-repo-binding.md)
