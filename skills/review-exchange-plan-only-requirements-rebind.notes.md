# Notes: review-exchange-plan-only-requirements-rebind

Source: one live remediation of an issue-plan review exchange in a workflow
distribution. Identifiers are generalized; no repository, issue, or account
names are recorded.

## Evidence sequence

1. A published plan carrier became permanently unverifiable. The exchange
   inspection returned a withheld result with a human-decision next action,
   although the issue title, body, and acceptance criteria had not changed
   since the publication.
2. Root cause: the corpus skills shipped no snapshot producer. Each agent
   session improvised its own normalizer, and the reducer derived the
   requirements digest from the snapshot bytes. Four independent producers on
   the same immutable content bound four different digests. One producer
   variation was enough: numeric versus node identity for the target, display
   versus raw body text, heading-level match rules, missing-section behavior,
   and stringified versus raw integer identities.
3. The documented remediation ("republish the plan carrier") was not
   executable. The drift inspection dead-ended at human decision, the plan
   preparation returned no operation for a withheld inspection, and every
   reframe and replan verifier required one plan comment and one review
   comment. The stranded epoch was plan-only, so no helper command could
   rebind it.
4. Fix set, all covered by behavior tests in the same change:
   - one canonical snapshot producer with a pinned normalization contract;
   - a reducer-native rebind route gated on the plan-only epoch shape;
   - a distinct rebind diagnostic on the ready inspection;
   - a null provider body mapped to the empty string the reducer accepts.
5. Test evidence recorded at learning time (working tree of the source
   change, source revision pinned in the worktree metadata):
   - two new reducer tests: the plan-only rebind end-to-end path (inspect
     ready with the rebind diagnostic, prepare returns an update of the
     retained comment, readback inspect is ready for the first review) and
     the drift-with-review-carrier case (stays withheld with the drift
     diagnostic);
   - one existing drift subcase moved from the withheld group to the rebind
     group because the plan-only shape now legitimately rebinds;
   - one new producer test: a null body gives exit code zero, an empty body,
     an empty criteria list, and a ready inspection from the reducer;
   - the producer suite already contained the digest-stability property test
     and the historic-producer-variant negative test;
   - focused commands: the producer and reducer test modules (106 passed,
     170 subtests passed), the three new or moved node identifiers (3
     passed), strict type checks over both helper scripts, lint and format
     checks over the changed files, the skill-corpus validator, and the
     Markdown policy scan over the changed documents.
6. A doc-only remediation attempt was rejected in review before any code
   change: the review comment required the route that works, not the route
   that documents intent. That review requirement is the origin of rule 4 in
   the main entry.
7. Delivery outcome (two days after learning): the source remediation is
   merged at the source review after fresh reviewer verification of the
   per-thread replies. The verified-live basis is the delivered change, not
   only the learning-time working tree. No rule, trigger, or failure-mode
   change accompanied the provenance refresh.

## Design parameters observed

- The rebind exchange identifier digests the target, the current requirements
  digest, and the superseded state digest. A fresh initial exchange digests
  only the target and the requirements digest, so the identifier spaces stay
  disjoint.
- The rebind keeps the retained scope and rejects responses and scope-change
  reasons. The visible plan content is republished unchanged; only the
  binding changes.
- The authority and ownership checks of the surrounding reducer still apply
  to the rebind: the actor must own the single plan comment, and foreign
  comments keep the normal marker rules.
- The producer's completeness flag is set only after a short final page, and
  the authority lookups fail closed. The requirements digest does not depend
  on the authority flags, so an authority failure cannot change the identity
  binding.

## Retrieval hints

- requirements digest drift, plan carrier, issue snapshot, rebind, withheld,
  human decision, plan-only epoch, null body, producer normalization,
  digest stability.
