# Notes: Fatal Check Downgrade on Its Real Load Root

## Source

A read-only plan review of one refactor. The refactor converted blocking
configuration consistency checks into logged drift events and continued.

## Evidence collected (generalized)

- Two loaders parse one config module. The profile loader embeds the quota,
  scheduling, identity, and retry-retention models. The cookbook loader
  constructs the workload, topology, mount, and image-layout models.
- About half of the checks that the first plan listed were on models that the
  profile loader does not embed. The first plan wired only one pass point.
- One validator group had no production construction path. Only tests built
  those models. The live surface for the same settings was a different model
  owned by another issue.
- One validator mixed two classes: one sub-check was conditional on a declared
  kind (cross-field consistency), and one sub-check checked an absolute path
  (format). The plan moved only the first.

## Review sequence that found the defect

1. List each validator that the plan converts.
2. For each validator, name the model that owns the field.
3. Walk the embedding chain to a loader root.
4. Compare the set of loader roots with the number of pass points in the plan.
5. Search the package for each model name. A model that appears only in the
   config module and in tests has no production path.

## Follow-up that the plan recorded

Supervisor and validation call sites kept the standard-error branch in the
same change. Supplying a per-deployment log directory to those call sites was a
separate mechanical change.
