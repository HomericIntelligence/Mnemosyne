# Notes: union-containment-vacuous-pass

Single-case evidence recorded 2026-10-26. Project, repository, identifiers,
and internal paths are withheld per the privacy policy; the set-relation
invariants below are the reusable content.

## Source engagement shape

- A view presented model aliases to a reporting layer. An earlier migration
  rebuilt the view as a projection of the live configuration rows only and
  silently dropped a UNION with the audit-history table.
- The repair migration restored `configuration UNION history UNION fleet
  projection`, with a `NOT EXISTS` filter against the union of the two known
  sources for the fleet branch.
- The seed migration inserts the same alias pairs into the configuration
  table and into the history table. On a fresh database, history rows are
  therefore a subset of configuration rows.

## Vacuity measurement

- First containment design: assert every history row appears in the view.
  On a fresh pre-fix database the assertion is `history ∖ view = ∅` and
  passes, because the configuration branch alone already covers the seeds.
  The same assertion passes post-fix: empty difference in both revisions,
  zero signal. The defect was invisible to the test that was meant to
  capture it.
- Fix to the test: insert one probe row with a unique key into history only
  (a retired model absent from configuration). Three assertions:
  1. shipped seeds are visible in the view (guards a different regression),
  2. the probe is visible in the view (the defect branch),
  3. one model present in both history and the fleet projection contributes
     exactly one row (overlap dedupe branch).
- Proof runs: pre-fix revision → test fails, probe missing (RED). Fixed
  revision → pass (GREEN). Owning suite: 30 passed, executed at the authored
  base and again at the rebased base before delivery. Lint clean.

## Why a fresh database matters

Production databases accumulate retired rows: configuration deletes leave
history rows that belong to exactly one side of the union. That asymmetry is
the real trigger for the defect and is exactly what a fresh seeded database
hides. A fixture strategy that reproduces only the shipped seeds misses the
production data shape.

## Boundaries of the rule

- Not the exact-list drift class: assertions that enumerate a growing
  register fail loudly from parallel merges, a different trigger; see
  `enumerated-registry-assertion-drift.md`.
- The probe technique generalizes past SQL: any assertion of X ⊆ Y, set
  equality, or empty-difference over two derived collections is vacuous
  while X ∖ Y is empty in every tested revision.
- One engagement of evidence; the decision rule follows from set algebra,
  and the probe construction is the portable part.
