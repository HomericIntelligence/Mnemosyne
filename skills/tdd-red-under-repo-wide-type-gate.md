---
name: tdd-red-under-repo-wide-type-gate
description: "Pair TDD red-phase tests with the implementation in one commit, or park the red file outside the scanned tree, when a type-check hook gates every commit. Use when: (1) a red-phase test file imports a module that does not exist yet by design, (2) a pre-commit hook reports unresolved-import diagnostics in files that are not even staged, or the hook aborts a commit whose staged files are clean, (3) you recover split or salvaged work and must decide what may be committed before the implementation exists."
category: testing
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [tdd, red-phase, unresolved-import, commit-granularity, pass-filenames-false, typecheck-hook, pre-commit, working-tree-scan, salvage]
---

# Red-Phase Tests Under a Repo-Wide Type Gate

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Keep test-driven red-green deliveries committable when a type-check hook gates every commit over the whole working tree. |
| **Outcome** | Successful; clean files landed after the red file moved outside the scanned tree, and the red file landed together with the implementation in one later commit. |
| **Verification** | verified-local; commit-gate outputs observed for three commit attempts, and the paired commit passed the same gate. |

Red-green-refactor expects an early red commit: a test that fails for the
right reason. Some repositories type-check the whole working tree on every
commit, for example a hook with `pass_filenames: false`. A red file that
imports a not-yet-implemented module then blocks every commit while it sits
in the scanned tree, even when the file is not staged. The remedy is commit
granularity: pair the red file with the implementation in one commit, or move
the red file outside the scanned tree while other work commits. Never weaken
the red content to pass the gate.

## When to Use

- A red-phase test imports a module that does not exist yet, by design.
- The commit gate shows unresolved-import diagnostics in files your `git
  status` does not list as staged; that signature marks a whole-tree scan.
- A hook such as `uv run <typechecker> check` with `pass_filenames: false`
  aborts a commit even though every staged file would pass a file-scoped run.
- You salvage interrupted work and must choose what may be committed before
  the implementation exists.
- The diagnostics live in committed files you never edited instead; that is the pre-existing-drift case, covered by
  [ci-precommit-whole-dir-format-drift-blocks-unrelated-commits](ci-precommit-whole-dir-format-drift-blocks-unrelated-commits.md),
  a different cause with a different repair.

## Verified Workflow

### Quick Reference

```bash
# 1. Is the type gate file-scoped or whole-tree?
grep -B2 -A3 '<typechecker>' .pre-commit-config.yaml | grep -n 'pass_filenames'
# 2. Prove where the diagnostics live. With a whole-tree scan, they can name
#    files that are not staged at all:
<the hook's exact type command> 2>&1 | grep -oE '  --> .*' | cut -d: -f1 | sort -u
# 3. Whole-tree gate: move the red file OUT of the scanned directories before
#    you commit other work; leave it staged nowhere. Restore it afterwards.
mv <red test file> <staging area outside the tree>
git add <files whose staged content passes the hooks>
git commit -S -s ...
mv <staging area>/<red test file> <original path>
# 4. Land the red file together with the implementation in ONE commit.
# 5. Confirm the commit with git log, not with a hook-output tail:
git log --oneline -1 --format='%h %G? %s'
```

### Suggested Approach

1. Read the gate shape before you plan commit order. A file-scoped hook sees
   only staged files, so a red file kept out of the index does not block a
   commit. A whole-tree hook (`pass_filenames: false`) scans the working tree,
   so the same file blocks the commit from outside the index.
2. Prefer the paired commit. Commit the red tests and the implementing module
   in one commit whenever the pairing is already possible. The commit is green
   and honest: the reason for the test's failure is resolved in the same
   commit.
3. Never weaken the red to pass the gate. Do not stub the module early, add an
   import guard, or mark the test expected-fail only to make the gate accept
   it. A test that begins green proves nothing about the repair.
4. When other work must land first, park the red file outside the scanned
   directories. Move it with the working tree, not only with the index. A
   whole-tree gate still fails while the file stays anywhere in the scanned
   paths. Restore it at the original path immediately after the commit.
5. Confirm each commit with `git log`, not with the hook-output tail. Hook
   lists can continue past the visible window; a later hook can fail after the
   lines you saw as passed.
6. Give resume lanes and salvage hands the same constraint in text: "the red
   file pairs with the implementation commit; keep it out of the scanned tree
   until then."

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Commit the full salvaged set with the red file included | Staged the red spec file with every other deliverable | The whole-tree type check reported all its unresolved-import diagnostics against the red file and aborted the commit; nothing landed | A red file with unresolved imports makes every commit fail while it sits in the scanned tree; pairing or parking is the only path |
| Commit only the clean files after unstaging the red file | Left the red file in the worktree but out of the index | The same diagnostics returned; `pass_filenames: false` makes the hook read the working tree, so the index is irrelevant | Unstaging is not enough under a whole-tree scan; the file must leave the scanned directories, here by `mv` to a staging area |
| Confirm a commit from the hook-output tail until `git log` showed otherwise | Read several `Passed` lines and continued | The commit did not exist; a later hook line past the visible window had failed | A hook-output tail is not commit evidence; `git log --oneline -1` is |

## Results & Parameters

### Configuration

```yaml
# Hook shape that creates the constraint (names vary by repository):
- id: ty
  entry: uv run ty check
  language: system
  pass_filenames: false   # the constraint: the hook scans the whole tree
```

### Expected Output

- File-scoped gate: a commit without the red file passes; the red file may
  stay in the worktree unstaged.
- Whole-tree gate: the same commit fails until the red file leaves the
  scanned directories; after the `mv` park, the commit of the remaining files
  passes every hook.
- The paired red-plus-implementation commit passes the same gate with zero
  unresolved-import diagnostics, and the hosted run later merges the work.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A Python monorepo with a whole-tree type check in pre-commit | An interrupted lane left a red spec file plus clean deliverables; three commit attempts mapped the gate behavior; parked and paired commits landed, and the work merged | Measured commit sequence and diagnostic counts in [notes](tdd-red-under-repo-wide-type-gate.notes.md) |

## Related Entries

- [ci-precommit-whole-dir-format-drift-blocks-unrelated-commits](ci-precommit-whole-dir-format-drift-blocks-unrelated-commits.md) — whole-tree hooks that fail on pre-existing drift in committed files; fix the drift, do not park it
- [tdd-workflow-and-test-coverage-expansion](tdd-workflow-and-test-coverage-expansion.md) — red-green-refactor practice and test design; this entry adds the commit-granularity constraint a whole-tree type gate imposes
