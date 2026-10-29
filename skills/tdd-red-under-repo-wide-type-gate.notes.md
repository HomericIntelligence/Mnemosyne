# Notes: Red-Phase Tests Under a Repo-Wide Type Gate

Supporting evidence for
[tdd-red-under-repo-wide-type-gate](tdd-red-under-repo-wide-type-gate.md).
Measured case from one Python monorepo delivery on 2026-10-28; all
identifiers generalized.

## Measured case

- Setup: a type-check hook (`entry: uv run <typechecker> check`,
  `pass_filenames: false`) gates every commit. An interrupted implementation
  lane had left salvaged work in an isolated worktree: one red spec file
  (about 1100 lines) that imports a not-yet-implemented package module, plus
  clean deliverables (two source extensions with their tests, a suite
  fixture package, and an operator runner script).
- Attempt 1: staged everything including the red file. The type check
  reported 28 diagnostics, all in the red file (7 unresolved-import, the rest
  consequences), and the commit aborted.
- Attempt 2: kept the red file in the worktree but out of the index and
  staged only the clean files. The identical 28 diagnostics returned; the
  whole-tree scan reads the working tree, so the index was irrelevant.
- Recovery: moved the red file to a staging directory outside the repository,
  committed the clean set. The type check passed; one mechanical import-style
  finding in a fixture file needed a one-line fix, then the commit landed
  signed. The red file was restored to its original path immediately after.
- The truncated-tail trap: one earlier commit attempt showed several `Passed`
  hook lines yet `git log` proved no commit existed; the failing hook line
  (an import-style rule) sat past the visible output window.
- Final delivery: a later lane commit paired the red spec with the
  implementation module in one commit; the gate passed with zero
  unresolved-import diagnostics, and the pull request later merged after
  review and CI.

## Diagnostic cues

- Diagnostics confined to an unstaged or untracked file mark a whole-tree
  scan (`pass_filenames: false`): the hook ignores the index.
- To see exactly which files a failing gate read, run the hook's own type
  command and extract the `--> file:line` markers; compare the set against
  `git status`.
- The paired red-plus-implementation commit is the structural fix. Every
  weaker shortcut (stub the module, guard the import, mark the test
  expected-fail) makes the red begin green and removes its evidence value.
