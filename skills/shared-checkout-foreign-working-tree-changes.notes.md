# Notes — Shared Checkout Foreign Working-Tree Changes

Supporting evidence for `shared-checkout-foreign-working-tree-changes.md`.

## Why the working tree is the dangerous surface

Every other foreign-state surface in a git checkout keeps a second copy inside git:

| Surface | git-held recovery |
| ------- | ----------------- |
| stash entry | reflog plus unreachable objects |
| local branch | reflog, remote tracking ref |
| staged index | object store blobs |

The working tree has none. An uncommitted modification or an untracked file exists once, on the
filesystem. Any step that overwrites, restores, switches over, or deletes it destroys the only
copy. That asymmetry is the whole reason the snapshot comes first, before the git operation, not
in parallel with it.

## The parked-checkout failure modes

Running `git checkout` or `git switch` inside a checkout that holds foreign uncommitted changes
has three observable outcomes, all bad:

1. **Refusal.** The change conflicts with a file the target ref would touch. The tree stays dirty
   and the branch never switches; the operator may misread the refusal as a git error and retry
   with `-f`, which discards the foreign change.
2. **Stranding.** The switch succeeds because the dirty files do not conflict, and the changes
   now sit on a ref they were never written against. Provenance is lost; the next agent finds
   "their" branch modified.
3. **Silent carry.** Same as stranding, but the carried changes look intentional in a later diff
   and get reviewed or committed as part of unrelated work.

`git fetch`, `git pull` on a clean tracked set, and `git push` of named refs do not touch the
working tree's uncommitted content. They are safe to run from the parked checkout. The boundary
is exactly the commands that write the working tree.

## Verification evidence

The destruction gate used in the verified session, run immediately before the destructive step
rather than at plan time:

```bash
for br in fix/a fix/b fix/c; do
  l=$(git rev-parse "$br"); r=$(git rev-parse "fork/$br" 2>/dev/null)
  if [ "$l" = "$r" ]; then echo "  OK  $br"; else echo "  ABORT $br drifted"; exit 1; fi
done
```

Drift can only be caught at execution time: a remote tip can move between planning and execution,
and in a shared checkout another actor can move local refs too. The gate cost is three
`rev-parse` calls; the failure it prevents is unrecoverable.

## "Open is not durable"

The verified session shipped its recovery through fork-based PRs. The head fork had already been
deleted once that week, auto-closing the original PRs permanently (see the fork-deletion branch
of `git-branch-state-triage-and-recovery`). An open PR number is therefore evidence that work is
*submitted*, not that it is *safe*: the head branch can live on a repository the PR author does
not control the lifetime of, or can delete themselves.

Backups were accordingly held after cleanup, and removed only when the owner gave an explicit
instruction after being told what would become unrecoverable. One combined tree state — the three
fixes stacked together in the parked checkout — existed in no branch, and the owner accepted its
loss. That asymmetry is worth stating to an owner plainly: keeping costs kilobytes, deleting is
irrevocable, and the decision belongs to them.
