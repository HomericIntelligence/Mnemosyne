# Notes: background lane timeout artifact reconcile

Supporting evidence for `background-lane-timeout-artifact-reconcile.md`. The
session-level identifiers are deliberately generalized.

## Context

A multi-item planning and review wave used several background lanes. Some lanes
timed out. For at least one item, the coordinator could not tell from the worker
message alone whether the lane had already written to the shared delivery
surface.

## What worked

- The coordinator froze the saved evidence for the failed item: the prepared
  artifact bytes, the expected target identity, and the original brief.
- It read the live target state and compared it with the prepared bytes by exact
  identity and digest before retrying.
- It classified the result as already delivered, partial, drifted, or unsafe.
- For a later attempt, it resumed one item per replacement lane, with one bounded
  evidence set and one write target.
- It did not re-run broad discovery and did not create a duplicate artifact.
- It recorded that the original terminal status was unobserved and that the
  delivery was proven by live state rather than worker prose.

## Failure mode the rules prevent

A replacement lane that repeats the original broad brief can duplicate the
already-delivered artifact. A replacement lane that rebuilds the whole context
can reproduce the same timeout. A coordinator that trusts worker prose alone can
misclassify unknown write state.

## Limits

The exact probe set depends on the delivery surface. The invariant is broader:
read the live effect surface, compare it with the prepared evidence, then resume
only the gap.
