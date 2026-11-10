# serving-replica-floor-enablement — Evidence Notes

Privacy-safe supporting evidence for the main skill. Repository, organization,
model, issue, and pull-request identifiers are generalized per the privacy rules.

## Source Context

A production model-serving control plane stored each model's replica floor in
two layers: a per-model recipe with per-cluster overrides, and a deployment
policy with a slot cost and autoscale bounds for every allowed model. A change
set the default floors for model diversity: one warm replica for several model
families and two replicas for the family that carried most traffic.

## Evidence Chain Behind the Decision Rules

- **Runtime authority.** The deployment policy was unbounded, so the runtime
  resolver returned the per-cluster recipe floor. The policy floor was inert at
  runtime. The mandatory-cost check read the larger of the policy and recipe
  floors. A repository test allowed the policy floor to be zero or the recipe
  floor, but not a third value.
- **Pool existence.** The supervisor iterated only pools that had a
  desired-state record. A floor did not create that record. The live status
  showed several pools at zero replicas even though their recipe floors were
  above zero, which showed that a floor is a property of an enabled pool, not a
  start trigger.
- **Start path.** The on-demand load path rejected a model whose resolved floor
  was above zero with a protected-tier code and changed no state. A zero-floor
  model used the same path to create the pool and a time-bounded hold. The load
  path was therefore not a substitute for the operator pool start after a
  floor increase.
- **Sealed record.** The pool runtime contract hashed the resolved recipe,
  including the floor. The change rotated the records for the models whose
  floors changed. The existing release-prep re-authoring issues covered only
  some of the rotated records. A follow-up was necessary for the uncovered
  model.
- **Capacity check.** The grant check charged every declared recipe floor,
  including pools with no desired record. Its reported footprint was much
  larger than the sum of the policy floors, and much larger than the recorded
  scheduler grant. The supervisor caught the shortfall as a warning and started
  anyway. The exact counts are withheld.
- **Identity rotation.** The deployment-policy edit changed the deployment
  context identity. Requests and holds bound to the old identity need reissue.

## Review Corrections

The first plan said that the on-demand load path would become a protected
base-tier request. The source showed that it is refused. The first plan also
did not state that a floor does not create a pool. An independent source review
found both gaps and withheld a GO until the plan and the change description
stated the refusal code and the one-time operator start. The corrected head
passed a second review.

## Validation Record

- Targeted capacity, configuration, and deployment-context test modules:
  passed. The exact command and count are withheld because they identify the
  source repository.
- Autoscale capacity check: passed against the deployment node budget.
- Scheduler-grant capacity check: reported a pre-existing shortfall as a
  warning, not a refusal.
- Pull-request CI: all required checks passed. No failure was caused by the
  floor change.
- The live operator tree was not writable from the working account, so the
  source change could not apply the live floors. The change ships in the next
  release, with the one-time operator pool start for the pools that had no
  desired-state record.

## Provenance

Lesson extracted at the end of a floor-policy change on 2026-11-10. The change
merged with full CI. The source repositories, model names, issue numbers, and
fleet counts are withheld; the decision rules and the failure modes are the
durable content.