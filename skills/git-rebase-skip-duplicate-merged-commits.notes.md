# Notes: git-rebase-skip-duplicate-merged-commits

Supporting evidence for the v1.2.0 amendment. All identifiers are generalized; the source
was a proprietary large Python monorepo session.

## Session context

A long-lived PR branch had accumulated eleven cherry-picked copies of commits that later
reached the default branch as squash merges (same subjects with `(#NNNN)` suffixes,
different SHAs), plus one merge commit and a small number of branch-unique commits. The
task was an authorized rebase onto the default branch, an interactive drop of one unwanted
commit, and a force-with-lease push.

## Patch-id skip list

Ten of the eleven suspect pairs had equal `git patch-id --stable` identifiers:

```bash
for pair in "<branch-sha> <upstream-sha>"; do
  set -- $pair
  a=$(git show $1 | git patch-id --stable | cut -d' ' -f1)
  b=$(git show $2 | git patch-id --stable | cut -d' ' -f1)
  [ "$a" = "$b" ] && echo "$1 == $2 SKIP-SAFE" || echo "$1 != $2 NEEDS-MANUAL"
done
```

The eleventh pair differed. Inspection showed the upstream squash merge had also folded in
a stacked prerequisite change, so the two patches were different shapes of the same intent.
The deciding evidence was the result, not the patch:

```bash
git show $branch_sha --stat                              # files the commit touches
git diff <(git show $branch_sha) <(git show $upstream_sha)  # both produce the same final blob
```

Both diffs named the same target blob for the touched file
(`index <base>..<same-result>`), and during the rebase stop the worktree blob already
equaled `REBASE_HEAD`'s target blob:

```bash
wt=$(git hash-object <path>); tgt=$(git show REBASE_HEAD:<path> | git hash-object --stdin)
[ "$wt" = "$tgt" ]   # true → applying the commit is a no-op → skip is safe
```

All four branch-unique commits (the real payload) applied without conflicts.

## Automation failure modes observed

1. **Silent no-op loop.** A skip loop guarded by `[ -d .git/rebase-merge ]` inside a
   linked worktree exited on the first check and printed "rebase complete", while ten
   picks still waited. In linked worktrees `.git` is a file that points at the real
   gitdir (`<main-checkout>/.git/worktrees/<name>`), so directory probes never match.

2. **Short-SHA pattern miss.** `git rev-parse --short REBASE_HEAD` returned eight digits
   for one commit and seven for another; an exact `case` pattern written for seven digits
   routed a verified duplicate into the manual-review branch.

3. **Guarded ref-update failure at the last step.** After the final pick,
   `error: could not update refs/heads/<branch>` / `"cannot lock ref ... is at <A> but
   expected <B>"`. A second worktree still had the branch checked out (attached earlier
   with an ignore-other-worktrees switch), and the other worktree's tip held one unique
   fixup commit. Recovery: inspected and cherry-picked the fixup commit onto the rebased
   result, removed the stale (clean) worktree, then finished by hand with
   `git rebase --quit`, `git branch -f <branch> <rebased-tip>`, `git switch <branch>`.
   `--continue` alone still failed after the removal because its guarded update kept the
   original expected value.

4. **Pre-rebase debris.** Unrelated staged changes from a prior session blocked the
   rebase. They were moved aside with a named `git stash push -m "<reason>"` rather than
   discarded, which kept them recoverable without dirtying the result.

## Outcome

Rebase completed with eleven skips and zero manual conflict resolutions. The final branch
contained only the unique commits; the PR diff shrank to the true payload because part of
the branch's earlier work had already landed upstream through a stacked PR merge. CI on
the new head passed.
