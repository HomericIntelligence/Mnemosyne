# Notes: prematerialize-git-objects-before-fail-closed-verification

Supporting evidence for the main skill. Generalized from one delivery run;
repository names, pull-request numbers, and object identifiers are omitted
under the privacy rules.

## Incident chronology (2026-10-27)

1. A multi-round review exchange spanned one working day. During the day the
   pull-request branch was force-pushed several times, and earlier exchange
   rounds bound the pre-rewrite heads of those pushes.
2. The terminal delivery helper verifies publication evidence against a local
   clone (the anchor source) through immutable git reads with lazy fetch
   disabled. The clone used for delivery was fresh, so it held only the current
   lineage.
3. Standalone verification of the current base-to-head range passed. The
   delivery run then failed closed: `An immutable anchor source Git query
   failed.` for every attempt.
4. Diagnosis: the delivery path re-verifies the publication manifest of every
   annexed carrier in the verified chain, and three of those carriers bound
   pre-rewrite heads. The fresh clone did not hold those objects.
5. Restoration: one `git fetch origin <oid>` per missing head. Each fetch
   restored the head and its full ancestry from the forge.
6. Pre-delivery check: each of the three historical manifests was regenerated
   against the completed source and compared byte-exactly. All three matched,
   so the annex format and diff policy of the installed helper generation were
   compatible with the historical carriers.
7. The delivery then completed: the terminal review published, the state label
   applied exclusively, and no thread stayed open.

## Why the rule generalizes

- The fail-closed design is deliberate: an immutable read must not fetch, so a
  missing object is always a hard failure. Source completeness is therefore a
  precondition of the run, not an error class the run can recover from.
- The gap is invisible to single-range checks. Only an enumeration over the
  whole chain finds identifiers that no branch ref names.
- Forge retention of rewritten objects is time-limited. Restoration becomes
  impossible after pruning, so the fetch belongs early in any delivery plan
  that follows rewrites.

## Limits

- Evidence comes from one helper generation whose verification regenerates
  each bound manifest and compares bytes. Helpers that trust published
  manifests without regeneration would not fail on the same gap, but the
  pre-flight rule still protects them.
- Fetch-by-identifier availability is a forge configuration. The observed
  forge allows it; a forge that refuses it needs an alternative source that
  already holds the objects.
