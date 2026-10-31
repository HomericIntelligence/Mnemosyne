# merged-content-verify — supporting notes

These notes hold the evidence for
[`merged-content-verify.md`](./merged-content-verify.md). They are not part of
normal retrieval.

## Source sequence

The source was a documentation task in an internal repository. The sequence:

1. A branch with one documentation commit opened a pull request.
2. The pull request reported `MERGED` quickly. The local branch held one more
   commit that added substantial content to the same file.
3. The completion report described the full change.
4. A later check read the merged file from the base branch and found **zero**
   occurrences of the sections from the second commit.
5. `git merge-base --is-ancestor <second-commit> origin/<base>` returned
   non-zero, which confirmed that the commit was absent from the base.
6. The branch was rebased onto the current base. The rebase reported
   `skipped previously applied commit` for the first commit, because the base
   already contained it. Only the second commit remained.
7. The rebased branch opened a follow-up pull request. The diff against the base
   was the single changed file.

## Why the first signal was misleading

| Signal | What it actually proves |
| --- | --- |
| `state: MERGED` | A pull request merged. It does not name the content. |
| Required check passed | The check ran on some head of that pull request. |
| Merge commit exists | The base history contains a merge. It does not contain your later commit. |
| Commit list shows one commit | The list reflects the pull request head at the time of merge. |

## The check that worked

```bash
git fetch origin <base> --quiet
git merge-base --is-ancestor <commit> origin/<base> \
  && echo "content on base" || echo "content MISSING from base"
git show origin/<base>:<path> | grep -c "<distinctive marker>"
```

The marker test is the stronger check. A commit can be an ancestor of the base
and still fail to contain a specific file change after a later revert,
superseding change, or partial replay.

## Rebase skipped-commit message

The rebase printed:

```
warning: skipped previously applied commit <sha>
hint: use --reapply-cherry-picks to include skipped commits
```

This warning is correct and expected. Do not use `--reapply-cherry-picks` here.
It would replay the commit that the base already contains.

## Follow-up pull request wording

Do not write `Closes #<n>` for a pull request that already merged. The number
is already closed, and the keyword does not add a useful link. State that the
follow-up supersedes the content that the earlier pull request merged without.

## Boundaries

- This lesson does not apply to a pull request that is still open. Use normal
  merge-readiness checks for that state.
- A merge queue changes the timing, not the rule. Verify the base branch
  content.
- A force-push to an already-merged branch cannot create a second merge. Open a
  new branch and a new pull request instead.

## Privacy review

This note keeps the generalized pattern only. It removes repository paths,
branch names, commit identifiers, pull request numbers, and the internal content
of the documentation change.