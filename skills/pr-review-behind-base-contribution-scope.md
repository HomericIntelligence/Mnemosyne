---
name: pr-review-behind-base-contribution-scope
description: "Split a pull request contribution into its own commits and work that the target branch already contains. Use when a pull request is behind its target branch, an unrequested change appears beside an in-scope fix, or a reviewer reports an unrelated change in scope. Compare against the merge base, then rebase onto the target before you answer a scope finding."
category: tooling
date: 2026-11-01
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: [pr-review, scope, stale-branch, merge-base, rebase, stacked-branches, review-threads]
---

# Pull Request Behind Its Base: Contribution and Scope

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Tell the real contribution of a branch from work that the target already contains, so a scope finding gets a correct answer and the narrowest fix. |
| **Outcome** | Operational. A scope finding was answered by a rebase instead of code edits, the contribution stayed unchanged, and the pull request diff became the reviewed scope. |

## When to Use

Use this skill when:

- a pull request is behind its target branch, or its diff shows files that the requested work does not touch;
- an unrequested change appears beside an in-scope fix, such as a helper that a parallel pull request also needs;
- a review thread reports an unrelated change, or asks to split the change or to state its requirement link;
- a branch stacked on another feature branch stays open after the base pull request merges;
- you must decide whether a scope finding needs a code edit, a rebase, or an answer with evidence.

Do not use this skill to decide whether a change is correct. Use a change review for that.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the real contribution: merge base to head.
git merge-base origin/main HEAD          # MB
git log --oneline "$MB..HEAD"            # commits unique to the branch
git diff "$MB...HEAD" --stat             # files this branch adds

# 2. Find the work the target already contains.
git diff origin/main HEAD --stat         # differences between the two trees
gh api "repos/<owner>/<repo>/compare/main...<head>" \
  --jq '{ahead_by, behind_by, files: [.files[].filename]}'

# 3. Classify each commit. Then rebase to drop what the target already carries.
git branch -f backup/pre-rebase-<n> "$(git rev-parse HEAD)"
GIT_EDITOR=true git rebase origin/main

# 4. Confirm the result is the reviewed scope.
git log --oneline -3
git diff --stat origin/main HEAD
```

### Suggested Approach

1. **Bind the revisions.** Record the exact target commit and head commit before you compare. Use a
   moving branch name only to find the bound commit.
2. **Read the contribution through the merge base.** A two-endpoint diff shows target-only work in
   reverse, and it shows stacked or already merged base work as if the branch added it. Use the
   merge-base diff to state what the pull request contributes.
3. **Match each commit to its pull request.** A squash merge rewrites the commit identifier, so a
   merged helper commit can still sit on a stale feature branch. Search the target history for the
   change by subject and by the files it touches, and check for a closed or merged pull request that
   names the same scope.
4. **Choose the narrowest action for a scope finding.**
   - If the extra change is only stale base history, rebase onto the target. The commit drops when
     the target already carries it. Then answer the finding with the commit list and the diff stat.
   - If the extra change is unique work that the target does not carry, split it into its own pull
     request, or record the requirement link in the pull request description.
   - Do not delete the change only to make the diff look small. Preserve unique work.
5. **Resolve rebase conflicts by keeping both sides.** A conflict where the target added a function
   and the branch added a different function near the same line needs both. Read the markers; do not
   pick a side by default.
6. **Re-sign and re-validate after the rebase.** A rebase rewrites the commits. Check the signature
   state of every new commit. Run the tests that cover the remaining changes. A large target advance
   can move those test dependencies.
7. **Push with a lease.** Use `git push --force-with-lease origin HEAD:refs/heads/<branch>` after a
   rebase. Never use `git push --force`.
8. **Answer the scope thread with the new diff.** Name the removed commit, where it landed, and the
   file list that now matches the requested scope. Then resolve the thread.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Read the pull request file list as the branch contribution and treated every extra file as scope creep in the session. | The extra files came from the branch base, not from the pull request commit. The branch was cut from another feature branch that merged separately. | Compare the merge base to the head first. A stale base shows another branch's work as if this pull request added it. |
| Attempt 2 | Considered code edits to remove the unrelated helper from the scope. | The helper was already merged through its own pull request, and other callers used it. Deletion would have broken the target. | Remove stale base work by rebase, not by deleting code. |

## Results & Parameters

### Configuration

```bash
# Rebases that would open an editor must not wait for input.
export GIT_EDITOR=true

# Use a lease, not a force push, after a rebase.
git push --force-with-lease origin HEAD:refs/heads/<branch>
```

### Expected Output

- The branch log holds only commits that the target does not carry.
- The endpoint diff between the target and the head lists only the requested scope.
- Every new commit has a valid signature.
- The scope thread has an answer with the removed commit and its landing point.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| private repository | Review round on one pull request with a scope finding | General pattern only. Do not record internal identifiers. |

## References

- [PR Review: Two-Dot and Three-Dot Diffs](pr-review-two-dot-vs-three-dot-diff.md)
- [Git Rebase Skip for Duplicate Merged Commits](git-rebase-skip-duplicate-merged-commits.md)
- [Git Stacked PRs Rebase, Merge, and Worktree Orchestration](git-stacked-prs-rebase-merge-worktree-orchestration.md)