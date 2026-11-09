# Notes: union-fixture-registry-divergence

Supporting evidence for the 2026-11-09 entry. Generalized; no source-project
identifiers, paths, host names, or issue numbers.

## Evidence record

- **Rule added.** A resolution boundary gained a check: the entries of an
  artifact must equal the entries the scope declares. The opposite direction
  (a declared entry with no artifact entry) already existed.
- **Pre-change baseline.** The focused module ran 63 tests green. The new rule
  then failed 55 of them in one pass.
- **Failure message shape.** Each failure named the same five extra entries,
  all of which the shared builder adds for cross-scope use.
- **First classification.** The failing scopes declared none of those five
  entries. The rule was correct; the double was not a production shape.
- **After the projection fix.** 55 failures fell to 7.
- **Second family.** All 7 remaining failures were identity mismatches at the
  comparison helper, not rule failures. Cause: the restricted artifact kept
  the identity fields of the full artifact.
- **After the identity rebind.** 7 failures fell to 0; a targeted rerun of the
  10 affected tests passed in about 2.5 minutes.

## Two-phase diagnosis detail

The first phase (projection) changed what each scope resolves against. The
second phase (identity) was invisible until the first was fixed, because every
comparison failed on the extra entries before it could reach the identity
check. This ordering is why the count delta matters: 55 to 7 told us the first
cause was resolved, and 7 to 0 named the second.

A helper that only read the artifact for a comparison also had to project.
Restricting at the construction site alone was not enough, because that helper
re-validated the shared artifact against a per-scope context.

## Wrong-reason passes

Two tests in the module asserted only that a validation error occurred. While
the fixtures were inconsistent, those tests passed because the identity check
raised first. After the projection and rebind, the same tests still passed but
reached their intended branch. The only way to tell the difference was to read
the raised diagnostic after the change. Treat a rejection test that passes
both before and after a fixture change as unverified until you confirm its
branch.

## Verification record

- Focused module reruns at each phase, with the counts above.
- Neighbour modules that share the builders were run after the change.
- Static checks (formatter, linter, type checker) clean on the changed paths.
- The delivered change passed the full repository CI, including the
  database-backed suite that could not run on the development host.

## Generalization map

| Source detail | Generalized form |
| --- | --- |
| One artifact built for every scope at once | Shared fixture that supplies a superset |
| Derived identity fields invalidated by subsetting | Content-addressed artifact whose identities must be recomputed |
| A rejection test that passed on another branch | Rejection with no attribution assertion |
| 55 then 7 then 0 failures | The count delta as the classification evidence |