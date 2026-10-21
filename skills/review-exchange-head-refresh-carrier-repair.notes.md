# Notes: Review Exchange Head Refresh and Carrier Repair

Privacy-safe supporting detail for `review-exchange-head-refresh-carrier-repair`.
Identifiers from the source incident (repository, pull request, review, account, and
digest values) stay out of this record. Git provenance keeps the authoring context.

## Source case (2026-10-21)

A chain-verified review exchange on a qualification-artifact pull request (eight
changed paths, seven required findings plus two nonblocking findings) reached round 2
`NO-GO`, then received author answers at one head, then a conflict-resolution
force-push moved the head. The reduced logical state after the author answers was
`awaiting_reviewer`, round 2, coverage invalidated by the refresh convention.

The reviewer-side next step required rebinding the exchange to the new head. Three
tooling obstacles appeared in sequence; each was resolved and verified in the same
session.

## Obstacle 1: strict parser versus forge bodies

`review_exchange.py extract` rejected every published carrier body as returned by the
forge review API with "The review-exchange JSON fence is malformed or not final". Byte
inspection showed each body ended with the closing fence, one line feed, and one
additional line feed. Removing exactly one final `"\n"` made the strict parser accept
every carrier (four of four, including the round-1 state, the round-2 state, and two
author-response carriers). The repaired documents produced the same envelope digests as
the ones referenced inside the chain, confirming that the trailing delta is a delivery
artifact, not carrier damage. The skill's own contract already anticipates exactly this
delta for one delivery path; the session extended the same recovery to readback
verification of freshly published carriers.

## Obstacle 2: reduce-request schema width

Replaying a published author event through the reducer with the extracted envelope
state as the event failed: "author response has invalid fields: unknown
requirements_sha256, target." The stored envelope state retains two state-level fields
that the event schema does not admit. Removing exactly those two fields made the
original round-2 author event reduce cleanly (`status: accepted`), which also served as
a live verification of the replay path before any new event was prepared.

## Obstacle 3: snapshot materialization on a private remote

The evidence collector's materialization tier ran `git fetch` with an isolated
environment (global and system git configuration redirected to `/dev/null`, terminal
prompts disabled). On a private remote this yields exit 128: "could not read Username
for 'https://...'". An ambient fetch of the same refs succeeded because it used the
configured credential helper. The collector also mounts quota volumes; on hosts without
that capability earlier tiers fall back, so the auth boundary is the one that binds in
practice. Mitigation used in the session: recompute each binding digest directly from
the forge API under the documented canonical recipes, then reproduce a published
carrier's digests with the same code before trusting it for a new event.

## Digest conventions verified in the session

- Visible content: SHA-256 of the visible carrier text with every trailing line-feed
  byte stripped. Verified by reproducing the visible-content digest inside a published
  author-response carrier (exact match); two alternate normalizations (as-is bytes up
  to the marker, single-trailing-line-feed) did not match.
- Reviewed scope: SHA-256 of the canonical JSON serialization (sorted keys,
  `(",", ":")` separators, `ensure_ascii=false`, `allow_nan=false`) of the
  pull-request scope fields, with `closingIssuesReferences` items each canonical-JSON
  serialized and the item strings then sorted. Verified by computing the digest for the
  live pull-request metadata twice (before prepare and before publication) with
  identical results.
- Failed candidates for the scope digest (listed to prevent re-derivation):
  concatenation of sorted scope-file bytes; concatenation of per-file SHA-256 digests;
  canonical JSON of per-file digest map; sorted `path\0blob-sha1\n` records; sorted
  `git ls-tree` output; and the head tree object identifier.
- Requirements digest: retained from the earlier binding because the bound requirements
  issue was closed and unmodified since nine days before the last binding
  (last-modified time compared against binding time).

## Head-refresh event construction

The refresh preserved: exchange identity, round number, finding identifiers, and the
fix/contest dispositions of all seven required findings. It replaced: the head
revision (new force-pushed head), the artifact and visible digests (recomputed), the
changed-path set (eight paths -> five paths, because the merged base had deleted three
test files that the resolution then kept byte-identical to the base, so they left the
author-intent diff), with a non-empty `scope_change_reason`, and every finding's
evidence list (each re-stated against the new head). The reducer accepted the event;
the new logical state was `awaiting_reviewer / review_assessment`, round 2, at the new
head, with all seven required findings re-answered (5 fix, 2 contest) and both
nonblocking findings untouched.

One clarification on contested findings: a refresh revalidation of a contest re-verifies
the enforcement evidence at the new head (render-boundary context gate and
replica-ceiling enforcement, both unchanged by the force-push because the force-push
touched no source file). The contest disposition stands; the reviewer round evaluates it
on that evidence.

## Publication and readback

The refresh carrier was published as exactly one COMMENT review, `commit_id` = the new
head, empty inline-comment list. Readback followed the same rule set: re-fetch the
review by id, remove exactly one final line feed, extract, and compare the envelope
digest with the accepted digest (match), the review author (expected publisher), and
the carrier's chain position (last carrier on the pull request). Full revalidation
ran immediately before publication: pull-request state/head/base from the API and a
fresh scope-digest recomputation, both matching the event's bindings.

## External closure

Two minutes after the refresh carrier was published, the owner merged the pull
request. No terminal round-3 carrier was prepared or published; the exchange closed
externally through the merge. The prepared reviewer-round task instructions were
discarded without execution (they were drafted but never dispatched). This incident
shape is the basis for the "owner merges before terminal delivery" rule row; the
session did not attempt any post-merge carrier, so that row is a stop rule derived
from protocol design (carriers bind live artifact state), not from an observed
rejection.

## Verification record

- Repaired extraction: four published carriers, all accepted after exactly one-line-feed
  removal; envelope digests matched their in-chain references.
- Replay verification: original round-2 author event reduced `accepted` after stripping
  the two state-level fields.
- Refresh: reducer output `status: accepted`, decision `awaiting_reviewer /
  review_assessment`, round 2; rendered carrier round-tripped through the extractor
  with an identical digest; published carrier readback-verified.
- Pull-request preconditions at publication: `OPEN`, exact head and base oids matched,
  scope digest recomputed fresh and matched.
