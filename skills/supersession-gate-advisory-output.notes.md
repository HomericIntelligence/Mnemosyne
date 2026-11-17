# Notes: supersession-gate-advisory-output

## Source

Observed during one automation-pipeline feature in the shared tooling
repository (late 2026). A plan-review stage gained a final planner pass for
accepted-with-findings reviews. The first design published the integrated plan
as a new journal revision on the accepted path. The plan journal's publication
helper rejected the write at runtime: a plan revision may be superseded only
under an authoritative exclusive rejection label, and the item held acceptance.

## Verification evidence

- The corrected design kept the reviewed plan artifact untouched and delivered
  the integration output as a payload key rendered into the implementation
  prompt as a fenced untrusted block beside the findings.
- Behavior tests covered: one pass per item lifetime (guard set before the job
  is requested), unchanged-output skip, failed-pass continuation, and the
  accepted-verdict label write surviving all outcomes. The full stage suites
  passed with ruff and mypy clean.
- The feature merged through the repository's normal review and CI path.

## Design detail worth keeping

The guard flag must be set in the same transition that routes to the pass
state, not in the completion handler. Setting it later would let a restart
between routing and completion mint a second pass.

## Related entries

- automation-forced-replanning-journal-recovery: covers the rejection-state
  path where supersession is authorized; this entry covers the acceptance-state
  path where it is not.
- architecture-github-labels-as-state-vocabulary: the exclusive-state label
  mechanics that the ownership gate builds on.
