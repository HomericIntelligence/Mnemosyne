# Notes: worktree-stale-snapshot-restore

Privacy-safe supporting evidence for `skills/worktree-stale-snapshot-restore.md`.
All repository names, commit prefixes, issue numbers, paths, and timestamps are
generalized. The git commands and observed values are the reusable part.

## Case: primary checkout reverted to the pre-pull snapshot

### Observed state

- Shared development checkout on a network filesystem. Several agent-runner
  sessions use the checkout concurrently. Branch: the default branch.
- `git status`: about 200 paths with unstaged modifications and deletions,
  including the removal of a feature directory that several merged pull requests
  had added. Nothing staged.
- A small set of paths appeared as *untracked* although their content was old:
  exactly the paths that merged work had deleted from the current commit.
- Local default branch also lagged the remote by about 100 visible commits.
  (Fetch state in a shared checkout can be stale in either direction.)

### Timeline correlation

| Evidence | Value |
| --- | --- |
| Reflog: previous fast-forward | `T-1 day 23:00`, branch moved to `<old>` |
| Reflog: `pull --ff-only` | `T 21:42:39`, branch moved `<old>` to `<new>` |
| Modification times of all changed files | `T 21:42:40`, one second, uniform |
| Session records | An agent session ran `git pull --ff-only` at that second |

A uniform one-second modification time across about 200 files is a bulk machine
write. Authored work spreads over minutes.

### Fingerprint transcript

```bash
export GIT_INDEX_FILE="$(mktemp)"; git add -A; T=$(git write-tree); unset GIT_INDEX_FILE
for c in $(git rev-list HEAD -n 400); do
  [ "$(git rev-parse -q --verify "$c:src")" = "$(git rev-parse -q --verify "$T:src")" ] && echo "MATCH $c"
done
# MATCH <old>          <- the commit the branch held before the pull
# MATCH <old>~1        <- identical src subtree by chance on one ancestor; the
#                         topmost match at the reflog position is the binding
```

`src` held no untracked files, so its subtree hash was a clean fingerprint.
Directories with untracked files (`docs`, `.github`) did not match any commit;
that mismatch itself confirmed which paths the restore had re-created.

### Inverse pull-delta transcript

```bash
git diff --name-status <old>..<new> | cut -f2 | sort > /tmp/pull-delta   # 198 paths
git diff --name-status            | cut -f2 | sort > /tmp/worktree-diff  # 194 paths
comm -3 /tmp/pull-delta /tmp/worktree-diff
# output: exactly the 4 paths that <new> deleted and that reappeared as untracked
```

The working-tree diff was the exact inverse of the pull delta. Authored reverts
do not reproduce a pull delta byte-for-byte across 198 paths, including report
artifacts and an ADR file marked immutable.

### Restore signature (mechanics)

- Index stayed at `<new>` (`HEAD`): only unstaged changes, no staged entries.
- Paths added by `<new>` were deleted from disk.
- Paths deleted by `<new>` reappeared on disk as untracked files.

This signature matches a whole-tree content write that bypasses the index, for
example `git restore --worktree --source=<old> .`, a runner snapshot replay, or
a recursive copy from an older checkout. The whole-tree dot form of
`git checkout <old> -- .` also stages an overlay, so a clean staged column rules
that form out.

### Attribution and disposition

- Runner session records proved an agent pulled at the sync second; the runner's
  own snapshot hashes recorded the tree change `<old-tree> to <new-tree>` and,
  in the next recorded state, `<old-tree>` again, with no tool call in between.
  The replay source was not identified further: no cron table and no user
  system jobs existed on the host. The lesson does not depend on naming the
  source.
- Issue-tracker search for the affected feature names found no removal request.
- Disposition: `git restore --worktree .`, delete the 4 re-created untracked
  paths, `git pull --ff-only`. The branch fast-forwarded about 100 commits to
  the remote tip. Nothing was lost: all reverted content exists at `<old>`.

### Hypotheses rejected during classification

| Hypothesis | Test | Result |
| --- | --- | --- |
| skip-worktree or assume-unchanged bits blocked the pull's file writes | `git ls-files -v`; the pull reflog printed create/delete lines; content equals `<old>`, not mixed | Rejected: bits were normal; the pull completed, then content was rewritten |
| Partial checkout left the tree half-updated | Pull exit status 0; HEAD moved; all changed paths uniform at restore second | Rejected: the pull applied fully before the overwrite |
| Authored mega-revert by another session | Subtree fingerprint; pull-delta inversion; issue search | Rejected: byte-exact old tree, exact pull inverse, no requesting issue |

## Sanitization

The released evidence withholds the repository identity, the session
identifiers, the commit prefixes for `<old>` and `<new>`, the issue numbers of
the affected features, and the absolute checkout path. The commands, the path
counts, the one-second modification-time cluster, and the signature analysis
carry the reusable value.
