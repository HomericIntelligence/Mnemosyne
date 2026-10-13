# Notes: worktree-phantom-dirs-block-validated-commit

Supporting evidence for the main skill. All paths, repository names, and issue
identifiers are generalized per the privacy rules.

## Incident timeline (generalized)

1. An agent session created three feature worktrees from the primary checkout of
   an automation-pipeline repository and implemented changes in each.
2. The main branch advanced. One merge deleted several hundred test files,
   including the entire contents of five directories under `tests/unit/`.
3. A worktree branch moved to a commit that contained that deletion. Git removed
   the tracked test files. Five directories remained on disk, each containing
   only interpreter cache (`__pycache__` trees of `*.pyc`).
4. Every git status mode reported the worktree as clean except three intended
   staged files: porcelain empty, `--untracked-files=all` showed nothing, and
   `git ls-files --others --exclude-standard` was empty.
5. A commit of the three intended files ran the pre-commit suite, which runs a
   fast repository test suite. The suite (more than 3,000 tests passed, run
   time about 2.5 minutes) failed exactly two tests:
   - a guard that rejects content-free ("phantom") directories under
     `tests/unit/`;
   - a layout-gate self-check that requires the shipped checkout to satisfy
     every retained layout rule.
6. The visible hook output ended at the last listed hook marked Passed. Exit
   code was 1 with no error near the end of the stream. Only a complete log
   capture (over 3,200 lines) showed the two failed tests and the failed layout
   hook earlier in the stream.
7. Evidence that the branch had moved: the branch reflog showed a recent
   checkout move; `git log` showed the head contained the deletion commit;
   `git ls-tree HEAD tests/unit/` confirmed the five directories were absent
   from the tracked tree while present on disk.
8. Safety check before removal: `find <dir> -type f` with cache patterns
   excluded printed no files for all five directories, and
   `git ls-files <dir>` was empty.
9. Removal of the `__pycache__` subtrees plus `rmdir` of the five directories
   cleared both validator failures. The re-run commit passed the full hook
   suite and landed. `git status` stayed clean.

## Diagnostic signatures

- `git commit` exit 1; visible hook output ends at a Passed line; no error in
  the stream tail.
- Validator complaint names directories that do not exist in
  `git ls-files` or `git ls-tree HEAD` output.
- Directories exist on disk only because ignored cache files survived a
  file-deleting checkout move.

## Boundaries

- The admission-side cleanliness rule (expected generated artifacts must sit
  under a reviewed ignore rule or outside the checkout, and porcelain
  `--untracked-files=all` must be empty) does not cover this case: these
  leftovers are invisible to every status mode, yet visible to whole-tree
  validators. See `automation-clean-checkout-intermediate-artifacts` for the
  admission-side rule.
- Do not generalize removal to all ignored directories. Limit deletion to
  directories whose every remaining file matches an ignored cache pattern and
  that Git does not track. `rmdir` as the final step enforces that bound.
- If another session may still write the worktree (recent mtimes, processes
  with their working directory inside, fresh reflog entries), coordinate or
  wait before cleanup.
