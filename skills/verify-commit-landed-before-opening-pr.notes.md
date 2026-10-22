# Notes: verify-commit-landed-before-opening-pr

Supporting evidence for
[verify-commit-landed-before-opening-pr.md](./verify-commit-landed-before-opening-pr.md).
This file is outside normal retrieval. The main skill holds the rules that the
workflow requires.

## Incident shape

Three commits in one session aborted without a visible error. Each time the
next step was a branch push followed by a pull-request create, which failed with
"No commits between \<base\> and \<head\>".

The repeated pattern was:

1. A source edit added a line longer than the configured formatter line length.
2. The commit command ran the pre-commit suite.
3. The formatter hook reported `Failed` with `files were modified by this hook`.
4. An unstaged change in the same tree triggered the stash warning:
   `[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes...`
5. The hook framework restored the tree. No commit was created.
6. The later `tail` slice of the output showed only passing hooks.

## Observed abort output

```
[WARNING] Unstaged files detected.
[INFO] Stashing unstaged files to <cache path>.
ruff format..............................................................Failed
- hook id: ruff-format
- files were modified by this hook
1 file reformatted, 1 file left unchanged
[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
```

A `tail -2` view of the same run shows the preceding hook lines and no error.

## Why the tree looked clean afterwards

The rollback restores the pre-commit content. `git status` then shows only the
staged changes that the author intended, so no working-tree evidence of the
abort remains. Only the commit graph shows it.

## Fix that worked

Format the edited files explicitly, stage them, and commit again:

```bash
<formatter> format <edited source files> <edited test files>
git add <edited source files> <edited test files>
git commit -m "<message>"
git log --oneline origin/main..HEAD
```

The hook then has nothing to change and the commit lands on the first run.

## Cost of not making the check

Each miss produced an extra push (creating or moving a remote branch that
pointed at the base commit), one failed pull-request create, and one re-commit.
In one case the commit was retried three times before the cause was read from
the complete output.

## Generalization decisions

- The skill states the command shape, not a fixed branch name or tool name, so
  it applies to any base reference and any formatter hook.
- The abort signature is quoted because it is the only evidence that survives
  the rollback. Match it by text.
- The safety bound forbids reformatting unrelated files. This prevents the
  cheaper but wider repair from becoming the habit and keeps the change reviewable.

## Verification limits

- Evidence comes from one repository and one hook suite.
- The exact hook names and formatter are generalized. The decision rule does
  not depend on them.
- No CI evidence was collected for the related skills. The commit-graph check
  is local and deterministic.