---
name: git-bundle-refusal-partial-clone
description: Recover when `git bundle create` fails with "Refusing to create empty bundle" in a blob:none partial clone; archive local-only worktree tips with format-patch plus lightweight tags and a containing branch before removing worktrees.
category: tooling
date: 2026-11-20
version: 1.0.0
tags:
  - git
  - bundle
  - partial-clone
  - archive
  - format-patch
  - worktree
---

# git-bundle-refusal-partial-clone

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-11-20 |
| Objective | Preserve unique commits from detached-HEAD worktrees before removing them, when `git bundle create` refuses to run in a `blob:none` partial clone. |
| Outcome | Bundles refused in every argument form. `git format-patch` archive plus lightweight tags and a containing local branch preserved the work; the worktrees were then removed safely. |

## When to Use

- A worktree or branch holds commits that exist nowhere on the remote, and the worktree must be removed.
- `git bundle create` fails with `fatal: Refusing to create empty bundle` while you can still count local-only commits.
- You must decide whether an empty-bundle error proves that a tip is reachable (it does not).
- A repository is configured as a partial clone (`remote.origin.promisor = true`, `remote.origin.partialclonefilter = blob:none`).

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm the clone type before trusting any bundle failure.
git config remote.origin.promisor            # true means partial clone
git config remote.origin.partialclonefilter  # blob:none here

# 2. PROVE what is local-only. Never trust the empty-bundle error as evidence.
git rev-list --count <tip> --not <base>      # > 0 means unique commits exist
git merge-base <tip> <base>                  # archive start point

# 3. Create lightweight safety tags at each tip.
#    Lightweight on purpose: annotated tags can open an interactive editor
#    and hang an automation session.
git tag archive/<date>/<worktree-name> <tip>

# 4. Fallback archive when bundle refuses: patches instead of a bundle.
git format-patch <base>..<tip> -o <archive-dir>/
git branch --contains <tip>                  # note any local branch; it blocks gc

# 5. Write a README (restore steps, why bundles failed), then remove the worktree.
git worktree remove <worktree-path> && git worktree prune
```

### Suggested Approach

1. Check the clone type first. A `blob:none` promisor clone changes how archive
   tools behave.
2. Prove tip uniqueness with `git rev-list --count <tip> --not <base>`. The
   count, not the bundle error, is the evidence.
3. Create a lightweight tag at each tip. Record any local branch that contains
   the tip; both protect the commits from garbage collection after the
   worktree disappears.
4. Produce the fallback archive with `git format-patch <base>..<tip>` into a
   dedicated directory, and write a README that records the merge base, the
   failed bundle attempts, and the restore command.
5. Remove the worktree and prune only after the archive directory and the tags
   exist.

### Restoring From the Archive

```bash
git am 00xx-*.patch   # from any checkout at or after the recorded merge base
```

Restoration from patches was not executed in the source session; it is the
documented, standard inverse of `git format-patch`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | `git bundle create <file> <tip> --not <base>` | `fatal: Refusing to create empty bundle`, despite dozens of local-only commits | The empty-bundle error does not prove the tip is reachable in a partial clone. |
| 2 | `git bundle create <file> <base>..<tip>` | Same refusal | The argument form is not the cause. |
| 3 | System git (2.34.1) instead of git 2.56.0 | Same refusal | Not a single-version defect. |
| 4 | `git bundle create <file> --filter=blob:none <base>..<tip>` | Same refusal | Bundles are unusable here; stop debugging and switch archive method. |
| 5 | Annotated tag creation during automation | Tag configuration opened an interactive editor; the session hung and had to be killed | Use lightweight `git tag <name> <tip>` in automation, or disable the editor/signing config explicitly. |

## Results & Parameters

### Configuration

```yaml
repository:
  promisor: true
  partialclonefilter: blob:none
git_versions_tested:
  - 2.56.0
  - 2.34.1
archive:
  method: format-patch
  patches: 41
  size_kb: 243
safety_nets:
  - lightweight tags at each tip
  - local branch containing both tips
```

### Expected Output

- One `0001-<subject>.patch` file per commit under the archive directory.
- A README recording the merge base, the failed bundle attempts, and the
  restore command.
- `git worktree list` no longer shows the removed worktrees; the tagged tips
  still resolve with `git rev-parse`.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| A large internal working clone | `blob:none` partial clone; two detached-HEAD worktrees pending removal | 40- and 41-commit local-only tips archived as 41 patches (243 KB), tagged, then both worktrees removed. Session evidence: [git-bundle-refusal-partial-clone.notes.md](git-bundle-refusal-partial-clone.notes.md) |

## References

- `git-bundle(1)`, `git-format-patch(1)`, `git-am(1)`, `git-worktree(1)`
- Related entries: `ambient-partial-clone-lazy-fetch-read-hazard`,
  `prematerialize-git-objects-before-fail-closed-verification`,
  `git-branch-state-triage-and-recovery`
