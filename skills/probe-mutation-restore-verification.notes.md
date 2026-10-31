# Notes: probe-mutation-restore-verification

Privacy-safe session evidence. Names of repositories, hosts, accounts, and
issue identifiers are generalized.

## Session context

- Date: 2026-10-23 to 2026-10-30.
- Task: remediate review threads on an automation-fleet pull request. The
  reviewer required a test that fails on the reviewed base commit and a
  base-bound reproduction for an already-implemented behavior.
- The delivery channel was uncommitted worktree state; an automation
  orchestrator created the signed commit and pushed.

## Probe evidence

Sequence actually run in the session, in order:

1. Premise check first: the production behavior already existed on the base
   commit. A standalone probe test confirmed the database path rendered both
   an active row and a revoked row (`PROBE OUT` showed both rows).
2. In-tree mutation probe, first attempt:
   - Backup command: `cp src/<changed>.py <tmp>/aa.orig 2>/dev/null || (mkdir -p <tmp>/v513 && cp ... )`.
   - The fallback branch failed: `cp: cannot create regular file '<tmp>/v513/aa.orig': No such file or directory`.
   - The probe itself succeeded: the focused run reported
     `Failed: DB mode opened the offline key snapshot` and `1 failed, 1 passed`.
   - The restore step then failed (`cp: cannot stat ...`), and
     `git status` showed the source file still mutated.
3. Repair: restore from the first-branch backup copy that did exist
   (`<tmp>/aa.orig`), then prove restoration:
   - `git show HEAD:src/<changed>.py` compared with the file through a small
     Python byte comparison printed `matches HEAD: True`.
   - `git status --short --untracked-files=all` listed only the test file.
4. Second probe run later in the session used a backup created before the
   mutation with `cmp` confirmation. Probe result: `1 failed, 1 passed`.
   Restoration proven with the same object-database comparison; the temporary
   copy was removed afterward.

## Environment note

The worktree's `uv`-managed virtual environment lost its development extras
between session turns (external resynchronization). Focused runs required
`uv sync --extra dev` first and used `.venv/bin/python -m pytest` with
`--override-ini="addopts="` to keep the invocation locked and explicit. See
`uv-offline-validation-sync-first`.

## Why this is a separate lesson

The adjacent entries cover different triggers:

- `checkout-other-ref-silent-file-clobber`: whole-file clobber from
  `git checkout <ref> -- <path>` during change porting.
- `automation-clean-checkout-intermediate-artifacts`: cleanliness gate for
  generated and ignored artifacts, not tracked-source mutation.
- `ci-cd-git-boundary-merge-conflict-staged-handoff`: staged handoff of merge
  resolution under the orchestrator commit boundary.
- `verify-delegated-agent-claims-run-full-suite`: re-verification of delegated
  claims by execution, not probe cleanup.

None of them gives the backup-before-mutation contract or the
object-database restore proof for deliberate probe mutations.
