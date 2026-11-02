# Notes: Peer Rewrote the PR Head

Supporting evidence for the main entry. These notes are not retrieved as guidance.

## Observed sequence (three rewrites, one session)

All three cases came from one shared repository with several review and
implementation agents that push the same branches under one forge credential.

| Case | What the remote showed | My local state | Chosen action |
| --- | --- | --- | --- |
| A | The branch that received my merge was rewritten; my commit was absent from the remote | A later, reviewed commit that was never pushed | New pull request from the same feature branch to the default branch |
| B | The pull request merged from an older head; the merged tree lacked one fix | A rebased commit with the fix and its tests | New follow-up issue and pull request on the current default head |
| C | The branch was rewritten again and the pull request carried a blocking state label plus a peer claim | A rebased commit with a protected test | Review comment with the patch and the test, no push |

Case B is the clearest evidence for the merged-head check. A pull request into
a feature branch merged a commit whose content matched an intermediate head.
The newest reviewed commit was never an ancestor of the merge. Source
inspection of the merged tree showed the missing behavior directly: a gate
still compared a release-scoped field.

## Why a claim stops the push

In case C the peer posted a short comment that claimed the findings at an
exact head. A push from a second actor would rewrite that head and invalidate
the peer's review round. The honest delivery was the delta: one function
change and one test, with the note that the record path already used the same
form. The peer could apply it in its own round.

## Checks that found the drift

```bash
# Branch present or gone
git ls-remote origin 'refs/heads/*<keyword>*'

# Commit missing from a rewritten branch
git merge-base --is-ancestor <sha> origin/<branch>

# Merge took an older head
git show <merge-commit> --stat
git diff --stat <reviewed-sha> <merge-commit> -- <changed-paths>

# Lease outcome
git push --force-with-lease=<branch>:<expected-sha> origin HEAD:<branch>
#  ! [rejected] ... (stale info)
```

## Replay onto a new default head

The recovery used an `--onto` replay so only the orphaned commit moved:

```bash
git branch <rescue> <orphaned-sha>
git checkout -B <rescue> <orphaned-sha>
git rebase --onto origin/main <old-base-sha> <rescue>
```

One conflict appeared in a test file, where a peer had already renamed the
same test and added the same case removal in different words. Resolution was
to keep the merged form of that hunk and re-apply only the new test.

## Verification after the replay

- The digest-refusal test set gave the same failure count on the branch and on
  the default head. `comm` on the sorted failure lists showed no branch-only
  failure.
- The new stop test failed with the guard removed and passed with it.
- Signature check: `git log --show-signature -1` reported a good signature for
  every replayed commit.
- The linter passed on the changed sources and tests.

## Measure the base, do not guess

The host could not build a trusted service root below a shared temporary
directory. The affected CLI tests failed on every base, including the default
tree. A separate detached worktree at the base commit, never a stash in the
working worktree, gave the comparison:

```bash
git worktree add --detach <tmp>/base-<n> <base-sha>
# run the same selection in both trees, sort the failure lines, compare
comm -23 <mine>.txt <base>.txt   # empty means no regression
```

A stash-based comparison once ended a long run mid-way with the changes still
stashed. The separate worktree removes that risk.