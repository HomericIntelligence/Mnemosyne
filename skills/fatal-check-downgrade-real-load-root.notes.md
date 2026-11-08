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

## Evidence for the authentication branch (added 2026-11-08)

A reviewed implementation of a digest-downgrade removed the content-digest
comparison from a frozen receipt model. The model described itself as verified,
but the loader no longer proved that. Two consequences were measured:

- An existing security test suite that asserted tampering raised an error lost
  four tests. The same suite passed at the base commit.
- A later guard compared a live audit prefix against a digest field read from
  the receipt. With the model no longer self-verifying, that comparison checked
  the live data against a value the caller supplied.

The full review also found the ordering defect that the plan had forbidden: a
drift event claimed that the operation continued, and the next statement raised.
A drift event must be emitted only after the enforcement points that can still
stop the operation.

Reviewer check that found it: search the tree for the error text that the
converted check used to raise. Each remaining test that asserts that text is a
required outcome that the change must preserve or must name as converted.
