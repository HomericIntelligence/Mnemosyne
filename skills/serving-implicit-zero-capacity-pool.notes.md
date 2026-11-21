# Notes: serving-implicit-zero-capacity-pool

Supporting evidence for the main entry. Generalized; specific project names,
paths, identifiers, and counts omitted by the privacy rules.

## Source change

- A control-plane change that removed the operator pool start as a
  prerequisite for demand-start serving.
- Before: the reconcile loop and the autoscaler listed desired-state records
  and skipped every model without one; the request proxy wrote demand records
  for declared models, but no verdict was ever published for a record-less
  model, so the model-starting answer never went positive.
- After: a supervisor-side overlay resolver synthesizes an implicit in-service
  zero-replica pool for each candidate that passes the context gates and has
  no real record. Real records always win; a corrupt or untrusted existing
  record still counts as a record so its blocked state survives.

## Key implementation facts

- Admission gates reused from the explicit creation path: the model is
  declared in the deployment policy (the same source the proxy uses for demand
  records), the bring-up recipe is complete, and the model is not on the
  absence list. The gate set is cached per reconcile pass.
- The record lister itself is unchanged, so consumers outside the supervisor
  keep the real-record contract. Deliberate real-record-only consumers: the
  recycling toggle and the host restore path (restores never materialize
  implicit pools), recorded as an accepted deviation in the change review.
- The first real write creates the record through the existing
  exclusive-claim, generation-zero semantics. Both apply paths (direct scale
  and compare-and-swap scale) handle the record-less case.
- Effective floor for an implicit pool is zero at every read site: the
  autoscale default, the eligibility branch, the footprint-deficit scan, and
  the tier accounting. A queued-floor recovery branch keeps the conservative
  behavior and does not exceed this rule.
- Status reporting: a boolean implicit marker on the supervisor roll-up, on
  the control-plane and operator-service status views, on the public model
  row, and in the operator CLI. The strict public model contract ignores
  unknown fields; older clients read the roll-up key-wise. A pinned
  older-client parse test proves the compatibility branch.
- The operator drain writes a real out-of-service record; demand never starts
  a drained pool, and the real record beats the overlay.

## Test evidence (authoring time)

- Focused pool test file: all tests passed.
- Combined multi-file run across supervisor, autoscale, demand, pool, proxy
  admission, control-plane, and operator-service suites: one failure,
  verified pre-existing and environmental on the base commit (a unix-socket
  path-bound failure on the host); it passes in isolation or on other hosts.
- Review: approved with the implementation-go verdict; the two follow-up
  coverage gaps (status overlays for the control-plane and operator service,
  and the proxy consumption path) were closed with new tests before merge.
- Merge state at authoring time: pull request open, awaiting required checks.

## Design decisions worth remembering

- The overlay shape beat two alternatives considered in planning: writing a
  real record eagerly for every declared model (storage churn and identity
  rotation for pools nobody asked for) and adding implicit branches to each
  consumer (the missed-consumer failure mode the idle-baseline entry
  documents).
- A dirty or untrusted record counting as "record exists" was a review
  finding: without it, the overlay would mask a blocked state as an available
  implicit pool.
