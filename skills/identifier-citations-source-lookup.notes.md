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

## Real-but-wrong identifier case (generalized)

A session audited its own already-published, digest-bound JSON deliverable.
The audit found one token that was a one-character variant of the standard
term for a path-name convention. Both the variant and the correct term are
real tokens in adjacent software vocabulary, so the string was not absent.

Why the existing gates did not catch it:

- schema validation accepted a free-form prose field, because no schema can
  bound natural-language term choice;
- exact readback confirmed the published bytes equal the prepared bytes, so
  fidelity passed while correctness did not;
- the author's self-review used the same vocabulary as the draft.

Recovery applied: the defect was reported as a correction, not a silent
rewrite, because the artifact was already published and could have been
quoted downstream. The correction named the wrong term and the correct term.

The audit rule that found it: extract every token that carries technical
meaning from the delivered text, then compare that set against the source
vocabulary. Run the comparison on the exact revision the text was derived
from. Do not compare against the author's memory of the domain.

This case is not a duplicate of the absent-identifier case. The absent case
needs removal plus a coverage-limit sentence. The real-but-wrong case needs
explicit revocation with both terms named.
