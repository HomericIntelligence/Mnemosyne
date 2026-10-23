# Notes: Git Worktree sys.path Precedence Issue

Supporting evidence for `git-worktree-sys-path-precedence-issue.md`. Project
names, hosts, virtualenv paths, and account identifiers are generalized on
purpose; the main skill carries the decision rules.

## Verified session evidence addendum (2026-10-23)

### Runner poisoning by an ambient production-venv PYTHONPATH

Context: a regression suite for a key-cache fix ran in a clean git worktree of
an internal model-serving gateway repository. The team runs tests through a
fixture interpreter (`<fixture-venv>/bin/python`) prepared per assembly.

Symptom: the three fix-adjacent test files reported `404 passed, 1 failed`,
including a "pre-existing" coordinator failure, plus earlier syntax-level
import errors that contradicted the diff.

Detection:

- `python3 <fixture-venv>/bin/python -c "import <pkg>; print(<pkg>.__file__)"`
  resolved modules into the production release virtualenv's site-packages —
  not the worktree. The ambient shell exported
  `PYTHONPATH=<production venv>/lib/python3.12/site-packages`, and child
  interpreters prepend that variable over the fixture's own `.pth` paths.
- Sanitized runner:

  ```bash
  cd <worktree> && PYTHONPATH=$PWD/src <fixture-venv>/bin/python -s -m pytest <tests>
  ```

  The variable is replaced (not prepended), and `-s` drops user
  site-packages. After sanitation, the same `__file__` probe printed paths
  inside the worktree, and the evidently-affected 13-test subset passed in
  ~3 s.

Outcome: the full related-file suite at the fix head — 359 passed, 0 failed
(~5 minutes). The flagged "[missing]" parameter of the coordinator test also
passed under a sanitized checkout of the PRE-fix revision, so the reported
"pre-existing failure" never existed in code; it was a pure runner artifact.

Rule of thumb this evidence supports: when a suite baseline is implausible for
the diff (untouched modules failing at import, or a "pre-existing" failure no
teammate can reproduce), treat the runner environment as the first suspect —
prove the loaded module path before reading any failure text as code
evidence. Replacing `PYTHONPATH` and adding `-s` is cheap enough to be the
default probe for automation-dispatched test runs.
