---
name: merged-content-verify
description: "Confirm that merged work reached the target branch before you report completion. Use when a pull request merges before all intended commits land, when you add a follow-up commit after opening a PR, or when a reviewer must confirm that specific content is on the base branch."
category: tooling
date: 2026-10-26
version: "1.0.0"
user-invocable: false
tags: [pull-request, merge, verification, autosquash, follow-up-commit, base-branch, completion-evidence, race]
---

# Verify the merged content, not the merged state

**Supporting cases:** [notes](./merged-content-verify.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Prevent a report that claims delivered content when the target branch holds an earlier version of the pull request. |
| **Outcome** | Successful. The missing content was found on the base branch, and a follow-up pull request delivered it. |

A pull request can merge while you are still working on it. This is common when
a repository has auto-merge, a merge queue, or a reviewer who merges on first
sight. The merged result then contains the **head commit at merge time**, not
your later commits.

A green check, a `MERGED` state, and a merge commit all prove that *something*
merged. None of them proves that your intended content merged.

## When to Use

- You opened a pull request and then made one or more commits to the same branch.
- The repository has auto-merge, a merge queue, or a fast reviewer.
- You must report delivered work, and the evidence includes a pull request URL.
- A reviewer or auditor asks whether a specific change is on the base branch.
- A previous task claims completion, and you must confirm the claim.

Do not use this for a pull request that is still open. Use the normal review
and merge-readiness checks for that state.

## Verified Workflow

### Quick Reference

```bash
# 1. Bind the branch and the base.
git fetch origin <base> --quiet
git rev-parse origin/<base>

# 2. Test whether YOUR commit is an ancestor of the base branch.
git merge-base --is-ancestor <your-commit> origin/<base> \
  && echo "content on base" || echo "content MISSING from base"

# 3. Confirm the actual file content, not only the commit graph.
git show origin/<base>:<path> | grep -c "<a distinctive marker from your change>"
```

### Suggested Approach

1. **Record the commit, not only the PR number.** A pull request is an
   identity that can merge an earlier head. The commit is the content.
2. **Test ancestry on the base branch.** `git merge-base --is-ancestor` gives a
   direct answer. Do not use the pull request state as a substitute.
3. **Check one distinctive marker in the file.** Read the merged file from the
   base branch and count a string that exists only in your change. A count of
   zero proves that the content is absent even when the commit is on the base.
4. **Compare the local diff against the base.** Run `git diff origin/<base>
   --stat` in your branch. A small or empty diff after a large change shows that
   the base already contains the work, or that the work never landed.
5. **Act on the result.**
   - Content is on the base: report delivery. You can remove the worktree.
   - Content is missing: your commit is not on the base. Rebase your branch onto
     the current base and open a follow-up pull request. Do not force-push an
     already-merged branch and expect a second merge.
6. **Do not close an already-merged pull request.** A pull request that already
   merged cannot close again. Use follow-up wording that does not add a
   closing keyword for it.
7. **Report the two states separately.** Say what merged and what did not. Do
   not collapse them into one success statement.

### When the pull request merges from a queue

A merge queue tests and merges the queue entry, not your live branch. A commit
you push after the queue accepts your entry does not join that entry. Select the
same verification: read the base branch and test your commit.

### Recover missing content

```bash
# Rebasing drops the commit the base already has and keeps the rest.
git fetch origin <base> --quiet
git rebase origin/<base>
git log --oneline origin/<base>..HEAD   # required: the missing commits

git push --force-with-lease              # your own unmerged branch only
```

The rebase can skip a commit that the base already contains. That skip is
correct. Confirm that the remaining commit carries the content that the base
lacks.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust the pull request state | Read `state: MERGED` and the green checks, then reported the full change as delivered | The merge used the first head. A later commit never reached the base branch. | A merged state proves a merge, not your content |
| Trust the check results | Saw the documentation check pass and treated it as evidence for the later content | The check ran against the earlier head | Check results bind to a head commit, not to your intent |
| Read the commit list only | Listed the commits on the pull request | The list can show a single commit while your branch holds more | Compare the base branch content against your branch |

## Results & Parameters

### Configuration

| Item | Value |
| ------- | ------- |
| Ancestry test | `git merge-base --is-ancestor <commit> origin/<base>` |
| Content test | `git show origin/<base>:<path>` and grep for a marker |
| Diff test | `git diff origin/<base> --stat` |
| Recovery | `git rebase origin/<base>`, then a new pull request |

### Expected Output

- `content on base` when the commit is an ancestor of the base branch
- A non-zero marker count when the file content is present
- A small `git diff origin/<base> --stat` that contains only the new work
- A follow-up pull request URL when content was missing

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| HomericIntelligence/comet | A documentation pull request merged before its second commit landed | See [notes](./merged-content-verify.notes.md) for the full sequence and the recovery. |

## References

- [Related: verify the commit exists before the pull request](verify-commit-landed-before-opening-pr.md)
- [Related: assess merged pull requests end to end](ci-cd-verify-merged-prs-end-to-end.md)
- [Related: unpushed fixes that never reach the PR](automation-review-loop-unpushed-fix-oscillates.md)