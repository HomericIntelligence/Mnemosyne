---
name: worktree-stale-snapshot-restore
description: "Classify a large unexpected working-tree diff on a checked-out branch as authored work or as a mechanical restore of an older snapshot, and recover with a local revert plus a sync instead of a pull request. Use when a working tree shows mass unstaged changes and deletions that reverse merged work, when files that the current commit deleted reappear as untracked, when file modification times cluster at a recent fetch or reset second, or when a user asks to revert or ship unexpected changes that no issue explains."
category: tooling
date: 2026-11-02
version: "1.0.0"
user-invocable: false
tags:
  - git
  - worktree
  - stale-snapshot
  - tree-hash
  - fingerprint
  - pull-delta
  - reflog
  - unexpected-changes
  - shared-checkout
  - disposition
---

# Worktree Stale Snapshot Restore

**Supporting cases:** [notes](./worktree-stale-snapshot-restore.notes.md)

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-11-02 |
| **Objective** | Decide whether a large unexpected working-tree diff is authored work or a mechanical restore of an older snapshot, and apply the correct disposition: keep and ship, or revert locally and sync. |
| **Outcome** | Operational. A shared main checkout showed about 200 reverted paths. A subtree tree-hash fingerprint bound the working-tree content to the commit the branch held before the last pull. The diff was the exact inverse of the pull delta. No issue requested the removal. A local revert plus a fast-forward sync restored the branch with zero loss, and no pull request re-deleted the merged work. |
| **Verification** | verified-local on a real incident on a shared automation checkout. |

## When to Use

- A checked-out branch (not a lane worktree) shows many unstaged modifications and
  deletions that you or your automation did not author.
- The diff deletes or reverses work that recently merged, and no issue or pull
  request requests that removal.
- Files that the current commit deleted appear again as untracked files.
- File modification times of the changed paths cluster at the same second as a
  recent `pull`, `fetch`-plus-checkout, or automation sync.
- A user asks to "revert these changes" or "open a PR for these changes" and the
  changes have no clear author.

Do not use this skill for authored work in progress that you can attribute to a
session, or for staged or committed changes. Those cases need normal branch and
PR triage.

## Verified Workflow

### Quick Reference

```bash
# 1. Timeline: does a recent ref move explain the writes?
git reflog --date=iso -10
git diff --name-only | xargs -r stat -c '%y %n' | sort

# 2. Fingerprint: bind the working tree to a commit through subtree hashes.
export GIT_INDEX_FILE="$(mktemp)"; trap 'rm -f "$GIT_INDEX_FILE"; unset GIT_INDEX_FILE' EXIT
git add -A
T=$(git write-tree)
for c in $(git rev-list HEAD -n 100); do
  for sub in src lib app; do   # pick tracked dirs with no untracked files
    [ "$(git rev-parse -q --verify "$c:$sub")" = "$(git rev-parse -q --verify "$T:$sub")" ] && echo "MATCH $sub $c"
  done
done

# 3. Inverse pull-delta test: is the diff exactly the last pull reversed?
git diff --name-status <previous-head>..HEAD | cut -f2 | sort > /tmp/pull-delta
git diff --name-status | cut -f2 | sort > /tmp/worktree-diff
comm -3 /tmp/pull-delta /tmp/worktree-diff   # only paths that returned as untracked

# 4. Attribution: nothing requests this removal?
#    Search the issue tracker for the affected feature names before you classify.

# 5. Disposition for a proven stale restore (all content lives in the bound commit):
git restore --worktree .
# remove only the paths that the restore re-created (untracked, tracked in <previous-head>)
git pull --ff-only
```

### Suggested Approach

1. **Build the timeline first.** Read `git reflog --date=iso` and compare the ref
   moves with the modification times of the changed files. A bulk write within one
   second of a `pull` or a checkout move is mechanical evidence, not authorship
   evidence. A human or an agent edits files over minutes.
2. **Fingerprint the content, not the appearance.** Compute a tree of the working
   tree with a temporary index (`GIT_INDEX_FILE`), then compare subtree hashes
   against recent history. Choose a tracked directory that holds no untracked
   files; untracked files change the subtree hash and hide the match. One matching
   subtree binds the content to an exact commit. That commit is the restore source
   and the recovery anchor.
3. **Run the inverse pull-delta test.** When the bound commit is the previous ref
   position of the branch, compare the path sets of `git diff --name-status
   <previous-head>..HEAD` and the working-tree diff. An exact match, except for
   paths that the current commit deleted and that reappear as untracked files,
   proves that the working tree is the pull reversal. Such a diff has no issue and
   no author. Do not ship it.
4. **Understand the mechanics you see.** A whole-tree restore through
   `git restore --worktree --source=<old> .`, a runner snapshot replay, or a file
   copy leaves the index at `HEAD`. The signature is: only unstaged changes,
   deletions of paths added by the new commit, and untracked paths that the old
   commit tracked. The staged-changes column stays empty.
5. **Verify attribution before the disposition.** Search the issue tracker for a
   removal or revert request. A fingerprint match plus an inverse pull delta plus
   no requesting issue closes the case as mechanical. When the fingerprint matches
   no commit, or the diff is not a pull inverse, treat the state as authored:
   preserve it and use normal triage.
6. **Recover with a local revert, not a pull request.** For the proven mechanical
   case: `git restore --worktree .`, remove the untracked paths that the restore
   re-created, and sync with `git pull --ff-only`. Every byte of the reverted
   state remains recoverable from the bound commit, so the local revert destroys
   nothing. A pull request from this state would re-delete merged work.
7. **Record the evidence.** Keep the bound commit identifier, the two compared
   path sets, and the reflog times in the task record. Later sessions can then
   re-verify the classification.

An agent-runner can replay a stale snapshot into a working tree outside its
recorded tool calls, for example from snapshot state that a concurrent session
holds. Check the runner's snapshot or session records when the git evidence shows
a restore that no recorded command performed. Host schedulers are another source:
check user and system job lists before you conclude.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Read the diff content of changed files to judge intent. | The changed files looked like a coherent revert of several features, which suggested authored work. Only the timeline and the fingerprint showed the pull-delta inversion. | Diff content cannot classify a mechanical restore. Classify the provenance of the tree, not the text. |
| 2 | Match the full working-tree tree hash against history. | Untracked files changed the tree hash, so the full tree matched nothing. | Fingerprint per subtree on tracked directories without untracked files. |

## Results & Parameters

### Configuration

```bash
# Generalized procedure, placeholders only:
#   <previous-head>  the commit the branch held before the sync, from the reflog
#   <sub>            a tracked directory with no untracked files, for example src

export GIT_INDEX_FILE="$(mktemp)"
git add -A
T=$(git write-tree)
unset GIT_INDEX_FILE   # remove the temporary index file afterwards

git rev-list HEAD -n 100 | while read -r c; do
  [ "$(git rev-parse -q --verify "$c:<sub>")" = \
    "$(git rev-parse -q --verify "$T:<sub>")" ] && echo "MATCH $c"
done

diff <(git diff --name-status <previous-head>..HEAD | cut -f2 | sort) \
     <(git diff --name-status | cut -f2 | sort)
```

### Expected Output

- A subtree-hash `MATCH` commits the working-tree content to one historical commit.
- The path-set comparison is empty, except for paths that the current commit
  deleted and that reappear as untracked files.
- `git status` shows only unstaged changes; the index stays at `HEAD`.
- After the local revert: a clean status, no staged or unstaged changes, and the
  branch fast-forwards to the remote tip.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| A multi-agent automation development repository (shared checkout, concurrent agent lanes) | A main checkout showed about 200 reverted paths minutes after an agent session pulled | Subtree fingerprint bound the content to the pre-pull commit; the diff was the exact pull inverse; a local revert plus a fast-forward sync recovered the branch; see [notes](worktree-stale-snapshot-restore.notes.md). |

## References

- [checkout-other-ref-silent-file-clobber](checkout-other-ref-silent-file-clobber.md) — silent state loss from whole-file checkout overlays; a related whole-tree overlay produces this restore signature.
- [dirty-worktree-batch-pr-shipping](dirty-worktree-batch-pr-shipping.md) — the ship-or-skip decision for dirty lane worktrees; this skill is the classify-first step for an unattributed diff on the primary checkout.
- [shared-checkout-unstable-ref-reads](shared-checkout-unstable-ref-reads.md) — bind remote state through a forge API when ambient refs disagree on a shared checkout.
- [probe-mutation-restore-verification](probe-mutation-restore-verification.md) — prove a restore against the object database instead of trusting a copy command.
