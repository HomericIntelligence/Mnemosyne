# Notes: Retired Runtime-Lever Inertness Guard

Privacy-screened delivery record for `testing-retired-lever-inertness-guard`.
Organization, repository, issue, PR, CI-run, and environment identifiers are
intentionally omitted; the decision facts are preserved.

## Source session (generalized)

- A single-issue worker was dispatched on an issue titled "Remove
  `<DEPLOY_RELAX_HATCH>` once `<env>` E2E is green". The issue body carried
  three documented removal-acceptance criteria.
- Premise check: `git log --all -S '<HATCH_IDENTIFIER>' -- src/` returned zero
  hits; the hatch branches had been deleted by a recorded earlier change. The
  removal ask was overtaken by events; the residual asks were the guards.

## Acceptance-criteria binding (the decision record)

| Criterion | Evidence bound | Result |
|-----------|----------------|--------|
| Runbook audits and repairs existing-tree modes before staging | A closed prerequisite issue; the runbook step cited by file and line and re-verified present on the branch base | Satisfied |
| Promotion succeeds end to end with the hatch unset | A CI run on a head that descends from the removal commit, with the required provenance step `success` | Satisfied |
| — rejected candidate for the same row | An earlier green run whose provenance step concluded `skipped` | Not qualified: a skipped step never exercised the configuration |
| Hatch branches and their tests deleted; strict behavior kept | Zero source hits for both retired identifiers; two existing inverse guards still rejecting with each variable set; this delivery added the missing loader-gate guard and the source scan | Satisfied |

Step granularity was the operative rule: overall `conclusion: success` was
present on both the rejected and the accepted run; only the per-step
conclusion differed.

## Test evidence shape

Pinned environment (`umask 022`, `TMPDIR=/tmp`, locked dependency resolver):

- Baseline at the branch start commit, detached worktree, same pin, both
  touched modules: `N passed, 3 failed, 1 skipped`.
- Branch: `(N+5) passed, 3 failed (the same three), 1 skipped`. Delta:
  +5 passed (4 inertness parametrizations + 1 resurrection scan), zero new
  failures.
- Family run (both existing inverse guards + both new guards): 11 passed.
- Tier-inventory test passed unchanged: both modules were already members of
  the nightly-only tier, so no tier edit was needed.
- Format and lint on both edited files: clean.

## Fixture design that made the guard non-vacuous

- The service-directory fixture passed the observed device, owner, and group
  through unchanged and forced `mode=None`, so only the permission-bit branch
  could reject. A fixture that lets identity/ownership branches reject as well
  would let a resurrected lever hide behind a passing test.
- The clean-fixture control used mode `0o755` under the same retired lever:
  it must not raise. With the lever set, the dirty fixture raised and the
  clean fixture did not, so each rejection is attributable to the permission
  bits rather than the environment.

## Scope discipline

The same 3 pre-existing failures reproduced identically on a clean worktree
at the base commit; they belonged to a manifest-policy family tracked by a
separate issue and were deliberately left untouched (no drive-by fixes).
Existing inverse guards for the validation layer were left unchanged.
