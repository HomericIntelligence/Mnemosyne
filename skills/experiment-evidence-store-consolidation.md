---
name: experiment-evidence-store-consolidation
description: "Consolidate the sealed evidence of a closed experiment campaign into a durable categorized store, then delete the superseded material without breaking hash-referenced records. Use when: (1) a long research or training campaign has closed and its results are scattered across an origin root, (2) a user asks where the results are and what can be cleaned up, (3) sealed records cite sibling artifacts by content hash and absolute path, (4) hundreds of gigabytes must move between filesystems, (5) a bulk delete leaves a tree behind with a permission error, (6) sibling copies of the origin root make a delete-only consolidation possible, or (7) a published deliverable store may already supersede lineage material."
category: tooling
date: 2026-11-01
version: "1.1.0"
user-invocable: false
tags: []
---

# Experiment Evidence Store Consolidation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-01 |
| **Objective** | Find the result of a closed experiment campaign, move the durable evidence into one categorized archive store, and delete the superseded material safely |
| **Outcome** | Successful: the sealed proof chain, deliverable artifacts, champion checkpoints, bulk evidence, and provenance moved to a shared store; all superseded trees deleted; no hash-referenced record rewritten; delete-only duplicates verified by zero-unique-content inventory; the recorded winner verified from the ranking before losing lineages were pruned |

## When to Use

- A long research or training campaign has closed, and its artifacts sit in one origin root plus older sibling roots from earlier attempts.
- The user asks what the result was, where the results live, and what can be cleaned up.
- Sealed decision records cite sibling artifacts by sha256 identity and absolute path.
- A large relocation between filesystems is necessary, and the destination must keep the evidence valid.
- A bulk delete must not silently leave partial trees behind.
- Sibling copies of the origin root exist, so consolidation can delete copies instead of moving content.
- A published deliverable store (a manifest binding model hashes to candidate identities, plus a ranked leaderboard) may already exist, so lineage checkpoints must be split into deliverable-published and lineage-only before retention.
- The winner was never formally declared, or a recorded winner field must be verified before losing trials are pruned.

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

# Delete-only dedupe proof: full inventory of the tree being deleted
find "$DOOMED" -type f -printf '%P\t%s\n' | sort > inv-doomed.txt
find "$KEEP"  -type f -printf '%P\t%s\n' | sort > inv-keep.txt
# pass condition: zero missing paths and zero byte-size mismatches

# Per-class prune manifest (audit trail), written before deleting
find "$ROOT" -path '*/checkpoints/<stage>/*' -printf '%y\t%s\t%P\n' \
  > "$REPORT/<stage>-deletion-manifest.tsv"

# Protected-path count guard: stop when it differs from expectation
test "$(find "$ROOT" -type d -path '*/checkpoints/<stage>' | grep -cE '<protected-ids>')" -eq "$N"
```

### Suggested Approach

1. **Start from the closure or decision record.** The final decision record of a
   sealed campaign cites each source artifact by path and content hash. Read it
   first. Use those citations as the index of what constitutes the result:
   the comparison, gate, leaderboard, and paired-outcome records, plus the
   champion lineage. Material that no citation reaches is a cleanup candidate.
2. **Find and verify the deliverable store first.** Before classifying any
   material, look for a published result store in sibling roots: a manifest
   binding model content hashes to candidate identities plus a ranked
   leaderboard. Verify it before relying on it: entry counts match the
   manifest, the leaderboard parses, and the top-ranked model trees exist on
   disk. Then classify materials as deliverable-published (prunable at stage
   granularity, since the evaluated models survive regardless) or lineage-only
   (retain until a replay decision).
3. **Sort keep material into five categories** before any move:
   sealed proofs (small decision, audit, submission, and receipt records);
   deliverable artifacts (final model weights and frozen inputs); lineage
   checkpoints (intermediate checkpoints of the passing variants only);
   archived bulk evidence (per-run evaluation records); and provenance
   (protocol source, manifests, run logs). Losing-variant checkpoints,
   rebuildable compiler caches, and superseded lineage roots stay outside the
   store. State the split to the user before moving.
4. **Prove the winner from the ranking before pruning losers.** Compute the
   winner from the leaderboard's ranking array; a recorded winner or incumbent
   field can name a lower-scored candidate than the same file's ranking. For
   equal scores, run the frozen paired-sample rule on identical sample IDs. A
   perfectly balanced result (equal total correctness and equal per-sample win
   counts) makes the leaders one evidence class: no losing lineup may be
   derived from the score alone, so no losing-lineage pruning is justified.
5. **Move per file, not per tree.** Across filesystems, `rsync -a
   --remove-source-files` unlinks each source file only after the copy
   verifies. Run independent top-level trees as parallel background streams.
   Flatten the origin layout into the category directories, and keep each
   moved tree's internal layout unchanged so the mapping stays mechanical.
6. **Do not rewrite sealed records.** Their embedded absolute paths name the
   origin root, and relocation makes those paths stale. The content hashes
   stay valid because they do not depend on path. Record the
   origin-root-to-category mapping and the recorded identities in a README at
   the store root instead of editing any sealed record.
7. **Verify the destination before deleting sources.** Parse each key sealed
   record as JSON at the destination and confirm the recorded decision fields
   are present. For a delete-only duplicate or mirror tree, the retained tree
   is the destination: compare a full file inventory (path and byte size) of
   the tree being deleted against it; zero missing paths and zero size
   mismatches is the pass condition. On any size mismatch, keep the larger
   file regardless of which tree holds it. Before pruning by content class
   (for example every intermediate-stage weight payload), re-verify the
   deliverable store, write the per-file manifest first, and confirm the
   remaining count is zero afterward. Only then remove the sources.
8. **Delete, then confirm emptiness.** A `rm -rf` chained with `&&` stops
   output at the first denied file, and the operator can mistake partial
   progress for completion. List the prefix afterward and finish any remainder.
   When protected paths must survive a class prune, count them first and stop
   the operation when the count differs from expectation. Remove emptied
   checkpoint or husk directories as a separate explicit pass, not inside the
   payload deletion.
9. **Write a store README** that names the result in one paragraph, lists the
   recorded identities, maps the layout, and states the caveat about embedded
   origin paths and excluded material. For an executed operation whose
   completion record was never persisted, write the record post hoc and cite
   the inventory evidence; when the surviving plan copy hashes differently
   than the plan's embedded hash, record both values and state that the copy
   is not known to be byte-identical to the executed revision. Never present a
   store copy as the executed plan.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Plain `mv` across filesystems | Move a large evidence tree with `mv` | `mv` falls back to copy-plus-unlink with no per-file verification, no resume, and an opaque partial state after interruption | Use `rsync -a --remove-source-files`; the source file survives until its copy verifies |
| Repair stale paths in sealed records | Consider rewriting embedded absolute paths after relocation | Sealed records are immutable evidence; path edits corrupt provenance, and the hashes are path-independent | Record the origin-root mapping in a store README; never edit sealed content |
| Delete sources before verification | Remove the origin trees immediately after the copy starts | A copy error would then destroy the only copy | Parse the key destination records first; delete only after verification |
| Trust one chained `rm -rf` | Run `rm -rf a b c && echo done` | One read-only file raised `Permission denied`, hid the rest of the progress, and left a tree behind | `chmod -R u+w` the denied subtree, delete again, then list the prefix to confirm it is empty |
| Name-level directory diff for dedupe | Compared top-level entries and file names between two near-copy trees | The name sets matched while a same-name file was truncated on one side: a few-hundred-MiB prefix of a multi-GiB export | Compare path and byte size per file across the full inventory; on any size mismatch keep the larger file |
| Trust the recorded winner field | Took the frozen leaderboard's stored incumbent value as the champion | The field named a candidate scored lower than the top of the same file's ranking array | Compute the winner from the ranking; if scores tie, run the frozen paired-sample rule before designating losers |
| Whole-dir deletion to cut stage weight | Weighed removing candidate directories to shed training weight | Each directory mixes records, exports, protected winners, and payloads, and payload deletion alone leaves empty husk directories behind | Prune by content class: write the per-file manifest first, guard protected paths with a count check, remove husk dirs as a separate pass |

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
- A delete-only dedupe check reports zero missing paths and zero size mismatches over the full inventory of the tree being deleted.
- Each class prune leaves a written per-file manifest, a zero remaining-count afterward, and protected-path counts equal to expectation before the delete runs.
- A post-hoc completion record cites inventory evidence for target absence and discloses every hash discrepancy between a surviving plan copy and the plan's embedded hash.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| A closed machine-learning research campaign | Consolidation of a sealed sha256-identified result chain from a parallel filesystem home into a shared project store | About 190 GB of evaluation evidence and the full proof chain moved in parallel streams with zero transfer errors; superseded trees deleted after verification; see [notes](experiment-evidence-store-consolidation.notes.md) |
| A closed time-bounded model-training campaign | Consolidation that also owned duplicate-store deletion, stage-class pruning, and result verification across roughly 4 TiB in three sibling copies plus a published model store | About 3.5 TiB removed: a 1.9 TiB duplicate verified by zero-unique-content inventory, stage payloads pruned by class with per-file manifests, terminal-cycle records kept; the winner check exposed a stale incumbent field and a perfectly balanced two-way tie, blocking loser classification until the paired rule ran; see [notes](experiment-evidence-store-consolidation.notes.md) |

## References

- [Large data relocation between storage tiers with a service cutover](homelab-nextcloud-data-dir-nfs-migration.md)
- [Gentle bulk reads on fragile storage servers](nfs-server-oom-recursive-metadata-ops.md)
- [Path binding versus remembered session paths](session-cwd-path-alias-repo-binding.md)
