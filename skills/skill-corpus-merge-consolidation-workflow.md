---
name: skill-corpus-merge-consolidation-workflow
description: "Maintain a skill corpus through complete cluster enumeration, semantic consolidation, snapshot history, format/directory migration, cross-repo generalization, obsolete notices, post-drain salvage audits, and fix-forward recovery from stranded or accidentally recreated skills. Use when overlapping skills or layouts must change without losing unique retrievable content."
category: tooling
date: 2026-06-15
version: "3.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
history: skill-corpus-merge-consolidation-workflow.history
tags: [skill-merge, deduplication, consolidation, history, migration, salvage, corpus]
---

# Skill Corpus Merge Consolidation Workflow

## Overview

Corpus consolidation is semantic migration, not file deletion. Enumerate the complete cluster from
the product source, choose one retrieval surface, preserve every superseded main in history, audit
unique commands and failure modes, and validate that discovery/count interfaces remain coherent.

Detailed migrations and salvage cases are indexed in
[`skill-corpus-merge-consolidation-workflow.notes.md`](skill-corpus-merge-consolidation-workflow.notes.md).
The complete prior source is archived in
[`skill-corpus-merge-consolidation-workflow.history`](skill-corpus-merge-consolidation-workflow.history).

## When to Use

- Several skills share a prefix or materially overlap.
- An epic lists representative members rather than a complete cluster.
- Originals will be absorbed and their exact content must remain retrievable.
- Hierarchical skill files must migrate to a flat corpus or duplicate directories must consolidate.
- Repository-specific paths need portable placeholders.
- A topic is obsolete but still valuable as a retrieval warning.
- Closed/superseded PRs may contain unique content never merged.
- Work is stranded in a nested clone or a deliberately absorbed skill was recreated.

## Verified Workflow

### 1. Inventory from authoritative sources

Enumerate retrievable skill names and paths from the corpus manifest/discovery code, not examples in
an issue. Group candidates by topic/prefix, then inspect every main and existing history. Record:

```text
cluster | proposed canonical | absorbed members | versions | verification | unique material
```

Before edits, enforce two collision gates: an absorbed skill cannot belong to two clusters, and one
cluster’s canonical cannot appear in another cluster’s absorbed set. A canonical/absorbed collision
can silently delete the intended retrieval surface.

### 2. Audit nuance before choosing the canonical

For each member compare triggers, commands, flags, parameters, failure modes, verification limits,
and examples. Keep any item whose omission changes what a reader would do. Remove only redundancy,
obsolete duplication, or case-specific detail preserved in notes/history.

Select the canonical by durable retrieval intent and content coverage, not filename age alone. Keep
at most a few materially different examples. Use a major version bump for a semantic merge and
preserve the strongest accurate evidence boundary without upgrading unverified material.

### 3. Preserve exact superseded content

Append a newest-first history entry per superseded retrievable artifact with source name/version,
immutable revision, byte count, SHA-256, reason, and exact snapshot in a fence wider than any fence
inside the source. Preserve existing history below it. Verify the extracted snapshot byte-for-byte
against `git show <base>:<path>` and retain provenance for absorbed names so searches remain useful.

Do not rely on a changelog summary as preservation. A summary cannot recover a command, error mode,
or contradictory evidence boundary.

### 4. Rewrite and delete only after coverage proof

Build the canonical from the nuance matrix, link notes/history, then run source-to-canonical checks
for every decision-changing item. Delete absorbed mains only when their content and provenance are
retrievable and the issue authorizes removal. Make deletion skip-missing-safe for idempotent reruns,
but never hide a manifest mismatch.

Reconcile any consumer manifest manually from the post-edit source of truth; do not regenerate
inventories or docs without a demonstrated consumer. Verify the retrievable count and absence of
stale member references.

### 5. Migrate layouts idempotently

For hierarchical-to-flat moves, discover all legacy paths, derive the destination name, preserve
frontmatter, add only required missing fields, and refuse overwrite when a different destination
already exists. After copying and validation, remove the legacy source only within approved scope.

For duplicate `plugins/` and `skills/` layouts, first identify the canonical source consumed by all
hosts. Redirect manifests/readers, validate discovery, then remove the redundant tree. Never create
a second generated mirror that can drift.

### 6. Generalize without erasing provenance

Replace project-specific paths, owners, and commands in reusable guidance with placeholders or
capability descriptions. Move project cases and immutable links to notes/history. Preserve concrete
parameters when they change behavior; “portable” does not mean vague.

For an obsolete topic, keep the retrieval identity and add a prominent status section explaining
why it is obsolete, what replaces it, and when legacy guidance remains relevant. Do not silently
delete the warning surface.

### 7. Audit a closed-PR drain for lost content

Enumerate closed-but-unmerged PRs in the drain window and map each to target skill artifacts. For
each target, inspect current main and the closed head/diff. An add-new-skill PR whose target does not
exist on main is highest-priority loss; a carrier PR may bundle unrelated unique amendments.

Salvage one coherent skill family per amendment PR: integrate unique material into the canonical,
bump version appropriately, append history, and validate. Record why duplicate/stale portions were
not carried forward. Aggregate closure rates are signals for audit, not proof of loss.

### 8. Recover stranded or de-consolidated work

For uncommitted work in a stray clone, make a patch/file backup before touching Git, create a fresh
worktree from canonical `origin/main`, reapply only intended artifacts, validate, commit, and publish
there. Leave the stray clone untouched for its owner to remove.

Before recreating a missing skill, search Git history for consolidation/supersession and inspect
bundle histories. If a deliberately absorbed standalone reappears, fix forward: move any genuinely
new nuance into the canonical, preserve the accidental artifact in history if material, then remove
the duplicate through a normal reviewed change. Do not revert blindly and resurrect older corpus
state.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Example-only inventory | Treated epic examples as full cluster | Members were omitted | Enumerate authoritative corpus source |
| Prefix-only merge | Combined names without nuance audit | Unique triggers/commands disappeared | Compare decision-changing material |
| Summary preservation | Wrote a prose changelog | Exact source could not be recovered | Archive byte-exact snapshots |
| One collision check | Checked absorbed duplicates only | Another canonical was deleted | Check canonical-versus-absorbed too |
| Blind flat copy | Overwrote an existing destination | Different skills collided | Refuse nonidentical destination |
| Generated mirror | Kept two writable skill trees | Host copies drifted | One canonical source for all hosts |
| Trust closed label | Assumed superseded PR had no value | Unique content was stranded | Audit closed head against current main |
| Work in stray clone | Committed nested/misplaced checkout | Change was not publishable from canonical repo | Back up and reapply in fresh worktree |
| Revert de-consolidation | Restored old tree wholesale | Lost later canonical evolution | Fix forward into canonical |

## Results & Parameters

```text
authoritative discovery command and pre/post retrievable count
cluster/canonical/absorbed matrix and collision-gate output
per-member name, version, verification, bytes, SHA, immutable source
nuance matrix: triggers, commands, flags, failure modes, examples
canonical version and notes/history links
layout source/destination map and overwrite disposition
closed-PR audit window, target artifact, unique-content disposition
stranded-work backup and fresh worktree path
validation, lint, snapshot-integrity, and discovery results
```

## Verified On

- Cluster consolidation, exact-history preservation, flat/single-source migrations, salvage audits,
  and fix-forward de-consolidation through 2026-06-15.
- Verification remains `verified-ci`; project-specific observations are classified in notes/history.
