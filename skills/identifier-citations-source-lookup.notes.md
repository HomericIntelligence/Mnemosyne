# Notes: identifier-citations-source-lookup

Supporting detail for the main entry. Nothing here is required for operation.

## Incident detail (generalized)

While preparing a terminal code-review round whose carrier binds the exact
published text by digest, the reviewer drafted a coverage-limit paragraph
that cited a registry seal by name:

> "...is marked broken by the registry
> (`disallow_lanes_that_overlap_public` seals overlapping lane roots at bind
> time)..."

The sentence leaned on that seal to justify a narrower boundary check. A
single pre-publication lookup (grep for the identifier and its key words over
the exact reviewed tree) returned nothing: the concept did not exist at any
name. The name had been assembled from the codebase's own vocabulary —
plausible prefix, plausible subject, plausible suffix — which is exactly why
it read as true.

Correction applied before publication:

- the fabricated citation was removed from the paragraph;
- the paragraph was rewritten to state what the review actually established
  and what it did not establish ("whether a nested binding can be constructed
  at all is not established by this review (coverage limit)");
- the corrected text was then reduced, bound, published, and merged.

## Why the recovery differs from a missing number

A missing measurement has an honest placeholder form ("occurrences: TBD until
the build metrics job lands"). A nonexistent seal has no honest placeholder:
"the registry seals X (unverified)" still teaches the reader a false
architecture. Removal plus an explicit coverage-limit sentence is the only
correct form, because the carrier does not get a cheap correction channel
once its digest is bound and consumed by later workflow steps.

## Lookup recipe used

```bash
grep -n "disallow_lanes_that_overlap_public\|overlap_public" <tree>/src/<pkg>/*.py
# (no output) -> the concept does not exist; remove the claim
```

Run the lookup on the exact revision the deliverable binds; on a base with
heavy merge traffic, an older worktree can hide or invent structure relative
to the reviewed head.
