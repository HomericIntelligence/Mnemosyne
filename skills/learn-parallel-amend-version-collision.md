---
name: learn-parallel-amend-version-collision
license: BSD-3-Clause
description: "Coordinate the frontmatter version stamp when several learn lanes amend the same skill entry in parallel: the stamp is shared allocator state across lanes, a merge between an amend's branch creation and its own merge invalidates its claim, and a merge-time repair leaves the PR title and commit subject disagreeing with the frontmatter. Use when: (1) two learn or amend pull requests touch one skill entry at the same time, (2) consecutive merged amends to one entry carry the same version number in their commit subjects, (3) an entry's current version must be resolved and history text and frontmatter disagree, or (4) a planned amend is based on a checkout whose freshness was verified only at discovery time."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - learn
  - amend
  - parallel-lanes
  - version-stamp
  - allocator-state
  - freshness-gate
  - merge-time-repair
  - dependency-ordered-stack
  - message-stamp-divergence
  - knowledge-corpus
---

# Learn Parallel Amend Version Collision

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-30 |
| **Objective** | Keep per-entry frontmatter version stamps unique and truthful when independent learn lanes amend the same skill entry in parallel. |
| **Outcome** | Rule set derived from a live parallel learn wave. Two independent amend pull requests to one entry both claimed the same next version; the second merge carried a merge-main repair that re-stamped the later amend, preserved both changes, and left the pull-request title and merge-commit subject claiming the pre-repair number while the frontmatter held the post-repair number. |
| **Verification** | Reconstructed from the merged git history of the knowledge corpus: consecutive amend commits to one entry with the same version subject, the later commit whose parent merge re-stamped its frontmatter, and the frontmatter state on the default branch after the wave. |

## When to Use

- Two or more learn or amend pull requests modify the same skill entry at the same time.
- `git log` on one entry shows consecutive amend subjects that claim the same version number.
- An entry's frontmatter version and its latest amend's commit subject disagree, and you must decide which one is the truth.
- A planned amend sits on a branch whose base freshness was verified at discovery time, not at delivery time.

## Verified Workflow

### Quick Reference

```text
Version stamp = shared allocator state across lanes, not entry content.
Claim the stamp from upstream main at delivery time, not at discovery time.
Before opening or merging an amend PR:
  merge upstream main into the branch; entry drifted -> re-stamp to the
  free next version. Never force the original claim.
Planned multi-lane wave   -> dependency-ordered stack; stamps serialize by
                             construction.
Independent lanes         -> serialize at merge time; same re-stamp rule.
Current version of record -> the frontmatter on the default branch.
  Commit subjects and PR titles keep the stale claim after a repair.
  Do not rewrite merged history to fix the divergence.
Detector: consecutive same-version amend subjects on one entry = a raced
pair that needed (or still needs) a merge-time repair.
```

### Suggested Approach

1. Treat the frontmatter `version` as shared allocator state across lanes. An amend claims the next stamp at branch-creation time. Every competing amend merged before yours occupies the claim. The claim is not part of the change's semantics; re-stamping it later preserves the change.
2. Gate freshness at both ends. A checkout verified fresh at discovery time decays while the change waits. At delivery time — before opening the pull request, and the merger again before merging — fetch upstream main and diff the target entry against the branch base. No drift: the claim stands. Drift: merge main into the branch (or rebase) and re-stamp to the free next version. Never force the original number.
3. Serialize by construction when the wave is planned. When competing knowledge pull requests are known up front, use a dependency-ordered stack: each lane stacks on the previous one, so the stamps serialize by construction and no merge-time repair is necessary. When independent agents open amends independently, accept serialization at merge time with the rule in step 2.
4. Read the current version from the corpus, never from history text. After a merge-time repair, the frontmatter on the default branch holds the post-repair stamp while the pull-request title and the merge-commit subject keep the pre-repair claim. Resolve every "what is the current version" question against the frontmatter.
5. Absorb message divergence; do not rewrite history. A subject/stamp mismatch on a merged commit is the trace of a correct repair. Leave it, and let the next honest amend to the entry move the number forward. Force-pushing merged branches to fix a stamp text rewrites shared provenance for a cosmetic gain.
6. Detect raced pairs during audits. Scan one entry's amend subjects: two consecutive subjects claiming the same version mark a pair that raced. If the later entry on the default branch carries a higher frontmatter stamp, the repair already happened; if both landed with the same frontmatter stamp, the next amend re-stamps from the higher free number and notes the repair in its notes.

### If a step is unavailable

- No upstream access at delivery time: hold the merge. A delayed amend is recoverable; a duplicate stamp in shared history is not.
- The entry drifted and the merge produces conflicts in prose sections: resolve by preserving the landed change and the in-flight change both (preserve existing work), then re-stamp; do not drop the competing amend to make the merge clean.
- The wave was planned but no stack was used: do not retrofit the stack after lanes merge; apply the merge-time re-stamp rule to what remains.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust discovery-time freshness through delivery | Delivered an amend pull request based on a checkout whose upstream freshness was verified at discovery time, three days before merge | A competing lane amended the same entry to the same next version and merged first; the open pull request then claimed an occupied stamp | Freshness verified at discovery time does not protect delivery. Re-gate against upstream main at delivery; on entry drift, merge main and re-stamp to the free next version |
| Read the current version from history text | Consulted the later merge's commit subject to determine the entry's version after the wave | The subject kept the pre-repair claim while the frontmatter held the post-repair stamp; the two disagreed, so history text was not a truthful source | The version of record lives only in the frontmatter on the default branch. After a race repair, commit subjects and pull-request titles are stale allocator claims; do not rewrite merged history to align them |

## Results & Parameters

### Configuration

```text
single lane, no drift                -> claim next stamp; deliver normally
entry drifted before PR opens        -> merge main into branch; re-stamp to
                                        the free next version
entry drifted with PR open           -> merger merges main into branch;
                                        same re-stamp rule; PR text stays stale
planned multi-lane wave              -> dependency-ordered stack; stamps
                                        serialize by construction
"current version" question           -> read frontmatter on default branch;
                                        never commit subjects or PR titles
merged subject/stamp divergence      -> absorb; no history rewrite; next
                                        amend moves the number forward
audit finds duplicate frontmatter    -> next amend re-stamps from the higher
                                        free number and notes the repair
```

### Expected Output

- A delivered amend carries the free next stamp at its merge time, with both competing changes preserved in the entry.
- A merge-time repair leaves one commit whose subject disagrees with its own frontmatter; the divergence is documented and left, never rewritten.
- Audits resolve each entry's current version from one truthful source: the frontmatter on the default branch.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Knowledge-corpus learn lanes (knowledge repository) | Parallel learn wave across four days: two independent amend pull requests to one review-exchange entry both claimed version 1.2.0; the later merge carried a merge-main repair that re-stamped it to 1.3.0, preserved both changes, and left the pull-request title and merge subject claiming 1.2.0 | [notes](learn-parallel-amend-version-collision.notes.md) |

## References

- [git-stacked-prs-rebase-merge-worktree-orchestration](git-stacked-prs-rebase-merge-worktree-orchestration.md) — the general stacked-PR mechanics behind the planned-wave branch of step 3.
- [enumerated-registry-assertion-drift](enumerated-registry-assertion-drift.md) — the same parallel-merge-lane hazard on test registries; this entry covers it on skill version stamps.
