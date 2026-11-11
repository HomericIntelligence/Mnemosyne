# serving-idle-baseline-per-model-opt-out — Evidence Notes

Privacy-safe supporting evidence for the main skill. Repository, model, issue,
and pull-request identifiers are generalized.

## Source Context

A model-serving control plane stored a protected floor per model in a recipe
layer and a slot cost plus autoscale bounds in a deployment policy. A
deployment-wide baseline added one or more replicas above the protected floor
on a preemptible tier. The owner selected five model families to revert to a
fully cold idle state.

## Evidence Chain Behind the Decision Rules

- **Baseline versus floor.** The baseline was additional to the protected
  floor. Two selected models had protected floors above zero (5 and 24
  replicas). An operator drain was therefore not equivalent: it zeroed the
  whole pool and waited for an operator restart.
- **Consumer inventory.** The per-model value was read in 12 places: the
  steady-state autoscale loop, event-recovery eligibility, pool reconcile,
  tier status, fleet report, mandatory footprint, QoS envelope, and the
  operator CLI note, plus tests and context checks.
- **Identity.** The nullable field used an exclusion-declared default. A dump
  probe confirmed that an unset value is absent from the serialized form.
  Unedited records kept their digest. The record that set the override rotated
  and was registered again.
- **Capacity.** The bounded-deployment footprint used the larger of the
  declared and resolved floors. Lowering two recipe floors also lowered the
  conservative footprint and repaired an existing shortfall in a small
  deployment.
- **Scale.** The selected opt-outs removed 44 slots (about 5.5 nodes) from the
  idle target. The remaining models kept 55 slots (about 7 nodes) of baseline.

## Test Evidence

- Resolver: inheritance, zero, a positive override, and an unknown model.
- Identity: an unset per-model value does not change the serialized digest.
- Capacity: a zero override is not charged; the inheriting model is charged.
- Runtime: the opt-out pool converges to zero while a sibling keeps one
  replica.
- CLI: the convergence-floor note uses the per-model value.
- Checked-in contexts: every registered context fits its mandatory footprint.

## Boundary

This entry covers an additive idle baseline. It does not cover demoting a lane
by changing its protected floor, and it does not cover the operator start path
for a pool that has no desired-state record.