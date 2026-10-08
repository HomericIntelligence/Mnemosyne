---
name: changed-path-gate-deletion-classification
license: BSD-3-Clause
description: "Keep a deleted path classified in a fail-closed changed-path gate, and prove it locally with the complete change set. Use when a change deletes a path that has an include, exclude, or owner entry in a deployment-input, ownership, or coverage gate, or when such a gate rejects a deleted path as unclassified."
category: ci-cd
date: 2026-10-08
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [changed-path-gate, fail-closed, deletion, exclusion-row, inventory-gate, unclassified-path, full-diff-verification, ci]
---

# Changed-Path Gate: Deletion Must Stay Classified

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-08 |
| **Objective** | Delete a path that has an entry in a fail-closed changed-path gate without breaking the gate that classifies the complete change set. |
| **Outcome** | Successful — the gate classified the deletion as not-a-production-input and the hosted check passed on the corrected change. |
| **Verification** | verified-ci — a hosted gate failed with `unclassified: <deleted path>` on the first run; after the classification row was restored, the same gate passed on the next run. |
| **History** | n/a (initial version) |

## When to Use

- A change deletes a path that has an entry in a gate that classifies a change set, for example a deployment-input inventory, a `CODEOWNERS`-style ownership gate, or a coverage gate.
- The gate fails closed on each unclassified changed path, for example `unclassified: <path>`.
- The pull request both removes a file and removes its classification row, and you expect the file's absence to make the row unnecessary.
- You verify a cleanup pull request locally before push and choose which paths to smoke.
- A rebase or merge deletes a file that the target branch edited in the gate data or in the file.

## Verified Workflow

### Quick Reference

```bash
# Classify exactly what the gate classifies: the complete change set of the
# pull request, including deletions. Adjust the format to the gate's contract.
git diff --name-status -z <base>..<head> > changes0
<gate-command> classify --changes0 changes0
```

### Suggested Approach

1. Treat a deletion of path `P` as a change to `P`. A fail-closed membership gate classifies the change set, not the resulting tree. The gate reads path strings from the diff; it does not care that `P` no longer exists in the tree.
2. When you delete `P`, keep its classification row. An exclude row then means: this path is not a production input; neither its presence nor its removal selects work. The row costs nothing after the file is gone, and it classifies the deletion event. When the row is an include or owner row, retire or re-point the owning rule set in the same change so that `P` stays classified.
3. Do not remove the row in the same diff as `D P`. The gate sees the row removal and the deletion at one time, so neither order saves the change.
4. If sibling paths share the row or pattern, confirm the survivors keep their entries.
5. Prove the result locally with the complete changed-path set that CI receives, given in the gate's native input format. Do not smoke only hand-picked surviving paths; that shape cannot show a deleted-path gap. A green full-set smoke makes the hosted result predictable.
6. When a merge or rebase intersects the gated area, repeat the full-set smoke on the resulting diff. Gate data and the gated files can change on both sides.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Remove the row with the file | Deleted the file and its exclude row in one change; verified the gate locally on surviving paths only | The hosted gate saw the deleted path in the change set with no covering row and failed closed with `unclassified: <deleted path>` | A deletion is a member of the change set and needs a row; smokes on surviving paths only cannot find the gap |
| Treat the row as dead data | Assumed that file existence makes the classification row unnecessary | The gate input is path strings from the diff, so existence in the tree is irrelevant to classification | Keep the row as the permanent record that the path is not a production input |

## Results & Parameters

- After the fix, the deleted path classifies as not-a-production-input and the complete-diff classify produces a green result with the expected selected checks.
- The gate-data file can become net-zero against the base; a file with no net diff then leaves the pull request's changed-path list, which is correct.
- Supporting evidence and the measured case are in [the notes](./changed-path-gate-deletion-classification.notes.md).
