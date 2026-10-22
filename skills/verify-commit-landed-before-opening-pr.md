---
name: verify-commit-landed-before-opening-pr
description: "Check that a commit exists before you create a pull request. Use when a commit command prints several hook lines but no confirmation, and the subsequent pull-request creation fails with a message that the branch has no commits relative to the base."
category: tooling
date: 2026-10-22
version: "1.0.0"
user-invocable: false
tags: [git, pre-commit, commit-abort, hook-modifies-files, pull-request, ruff-format, rolled-back-fixes, exit-code]
---

# Verify That the Commit Landed Before You Open a Pull Request

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Recognize that a commit command aborted although its output looks like normal hook progress, then re-stage and re-commit before a pull request. |
| **Outcome** | Successful. Identified the cause from complete hook output, re-staged the formatter edits, and the pull request was created. |

A commit hook that reformats a file aborts the commit, but this abort is easy
to miss. The hook reports `Failed - files were modified by this hook`. When the
same run also carries an unstaged change, the hook framework stashes it,
cannot re-apply the formatter edit, and rolls back its own fix. The working tree
then looks unchanged, the trailing hook suite can report `Passed`, and a
truncated output view shows no error. The commit does not exist. The next
branch push succeeds, and pull-request creation fails with a message such as
"No commits between \<base\> and \<head\>".

## When to Use

- A commit command printed hook results but no commit summary line, and the
  exit status was not checked.
- Pull-request creation fails with "No commits between \<base\> and \<head\>".
- A branch push appears successful but the remote branch equals the base.
- The output ends at a passing hook with no failure visible near the end.

## Verified Workflow

### Quick Reference

```bash
# 1. Test whether the commit exists, before any pull request.
git log --oneline origin/main..HEAD

# 2. If empty: inspect the complete hook output for the aborting hook.
git commit -m "<message>" 2>&1 | grep -vE "^check .*Passed$" | head -20

# 3. Apply the formatter yourself, then stage and commit.
<formatter> format <edited files>
git add <edited files> && git commit -m "<message>"
git log --oneline origin/main..HEAD   # required: one commit
```

### Suggested Approach

1. Treat `git log --oneline <base>..HEAD` as the completion check for a commit.
   A push is not the proof that a commit exists.
2. Read the complete hook output. A hook framework buffers output and can place
   a failure above later passing hooks, so a tail view hides it. Filter passing
   hooks instead of truncating the stream.
3. Recognize the rollback signature: `[WARNING] Stashed changes conflicted
   with hook auto-fixes... Rolling back fixes...`. This proves that the commit
   aborted even when the tree shows no change.
4. Apply the formatter to the edited files and stage the result before you
   commit. This removes the hook's edit and its stash conflict.
5. Repeat the existence check after the commit and before the pull request.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the tail of the commit output | Piped the commit through `tail -2` and treated "Passed" as success | The failing hook report was above the last passing hooks, so the abort was invisible | Read the complete output and filter passing lines out |
| Re-commit without changing the tree | Repeated the same command after a pull-request failure | The hook rewrote the file again, so the same abort repeated | Fix the input to the hook instead of repeating the command |
| Trust the push result | Pushed, then created the pull request | The push moved the base commit to the base branch; the pull request had no commits | Check `git log` between base and head before the push and before the pull request |

## Results & Parameters

### Configuration

```bash
# Abort signature to search for in the complete commit output.
grep -nE "files were modified by this hook|Rolling back fixes" <commit output>

# Required existence check: one line of output means the commit exists.
git log --oneline <base>..HEAD
```

### Expected Output

- The failure signature appears before the re-staging step and is absent after it.
- `git log --oneline <base>..HEAD` prints the new commit.
- Pull-request creation succeeds.
- Safety bound: apply the formatter to the files that this change edits. Do not
  reformat unrelated files only to make the hook pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An automation repository with a formatter hook in a pre-commit suite | Three consecutive commit attempts across one session | See [notes](./verify-commit-landed-before-opening-pr.notes.md). |

## References

- [Related skill: formatter edits to pre-existing files](./ruff-format-preexisting-files-precommit.md)
- [Related skill: complete hook output instead of a tail slice](./worktree-phantom-dirs-block-validated-commit.md)