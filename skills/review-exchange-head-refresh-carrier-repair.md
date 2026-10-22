---
name: review-exchange-head-refresh-carrier-repair
description: "Recover and rebind a chain-verified review-exchange carrier chain in the field: repair a forge-published carrier that the strict parser rejects, recompute the artifact and visible-content binding digests when the evidence collector cannot materialize the snapshot, and rebind the exchange to a changed head with an author-response refresh before the next reviewer round. Use when: (1) extraction rejects a published carrier with a malformed-or-not-final JSON fence, (2) the artifact head changed while the reduced state awaits the reviewer, (3) the collector fails on a private remote because its isolated fetch cannot authenticate, or (4) the reduce request rejects a stored author event for retained state-level fields."
category: tooling
date: 2026-10-21
version: "1.0.0"
user-invocable: false
tags:
  - pr-review
  - review-exchange
  - carrier
  - trailing-newline
  - fence-mismatch
  - head-refresh
  - artifact-binding
  - scope-digest
  - visible-content-digest
  - digest-recomputation
  - readback-verification
---

# Review Exchange Head Refresh and Carrier Repair

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-21 |
| **Objective** | Keep a chain-verified review-exchange carrier chain publishable when the strict parser rejects a forge-published carrier, the artifact head changes mid-round, or the evidence collector cannot materialize the immutable snapshot. |
| **Outcome** | Operational rule set derived from one live exchange. A mid-round force-push left the reduced state awaiting the reviewer at a stale head. Four published carriers needed a parser repair before extraction; the collector's snapshot materialization failed on the private remote; the author-response refresh carrier was computed by hand, published, readback-verified, and the owner merged the pull request minutes later. |
| **Verification** | verified-live in one two-round exchange (2026-10-21): the trailing-line-feed repair recovered all four published carriers, the manual digest formulas reproduced a published carrier's digests and matched a live recomputation, and the refresh carrier reduced, rendered, published, and readback-verified at the accepted digest. Single-case evidence; each rule was also gated by an independent verification in the same session. |

## When to Use

- `review_exchange.py extract` rejects a carrier with "The review-exchange JSON fence is malformed or not final", and the body came from a forge API.
- The artifact head changed after the last author answers, and the reduced logical state is `awaiting_reviewer` at the stale head revision.
- The changed-path set of the artifact changed since the last binding (for example, a base branch deleted review files that the resolution then kept byte-identical), so the scope set and the artifact digest changed.
- The evidence collector cannot bind the reviewed scope because its isolated fetch fails on a private remote (exit 128, "could not read Username").
- The reduce request fails with "author response has invalid fields: unknown requirements_sha256, target" because a stored envelope state was passed as the event.
- You must publish or readback-verify one carrier without inventing a new digest convention.

## Verified Workflow

### Quick Reference

```text
Forge-published carrier: remove exactly one final line feed, then extract.
All other carrier damage: reject; do not repair.
Head changed while reduced state is awaiting_reviewer:
  publish an author-response refresh carrier (one fresh evidence-backed answer
  per required finding) before the next reviewer assessment. The round stays.
Digests: recompute from the forge API with the canonical recipes below.
  Verify each recipe against an already-published carrier before binding a new one.
Publish one COMMENT review per carrier, then readback-verify digest, author, position.
```

### Suggested Approach

1. Repair only the known forge line-feed delta. A carrier body that a forge API returns can carry one additional trailing line feed after the closing fence; the strict parser requires the final fence. Remove exactly one final `"\n"` and extract again. The inner envelope and its digests do not change, so a repaired document still verifies. For every other parse or verification failure, reject the carrier. Publication channels are append-only; a repaired read is a convenience, a rewritten carrier is not.
2. Make the reduce request schema-clean. Build the request with `previous` = the current state envelope and `event` = only the event-schema fields. A stored envelope state retains state-level fields (`requirements_sha256`, `target`) that the event schema rejects; strip them before the submit.
3. Reproduce the digest conventions against a published carrier before you reuse them:
   - `visible_content_sha256` = SHA-256 of the visible text with every trailing line-feed byte removed.
   - `artifact_binding.sha256` (reviewed scope) = SHA-256 of the canonical JSON (sorted keys; `(",", ":")` separators; `ensure_ascii=false`; no NaN) of the pull-request scope fields: `title`, `body`, `closingIssuesReferences` (each item canonical-serialized and the items then sorted as strings), `state`, `isDraft`, `baseRefName`, `headRefName`. Fetch the fields from the forge API at bind time.
   - The requirements digest stays valid while the bound requirements source is unchanged; compare the source's last-modified time with the binding time.
   - The reviewed-scope digest binds mutable metadata, not file content. Content formulas (file bytes, per-file digest lists, blob identifiers, tree output) do not reproduce it. Verify each formula against a published carrier first; do not trial formulas on a new event.
4. When the collector cannot bind the reviewed scope (isolated fetch without credentials on a private remote), recompute the digests from the forge API under the same recipes and revalidate them immediately before publication (mutable fields can drift).
5. Rebind a changed head with an author-response refresh. Preconditions: the reduced state is `awaiting_reviewer`, and the artifact head revision differs from the state's bound revision. Prepare an `author_response` event with: the current state digest as `prior_state_sha256`; `artifact_binding` with the new head revision and the recomputed digests; `scope` = the current changed-path set; `scope_change_reason` non-empty exactly when the path set changed; and one fresh evidence-backed answer for every required finding (a fix answer stays a fix; a contest answer stays a contest with the enforcement evidence re-verified at the new head). The refresh keeps the round number and moves finding states back to the answered/contested set. Coverage was invalidated: the next reviewer assessment is a full-coverage round, from a fresh context that did not author or author-respond to the artifact.
6. Publish one carrier atomically. Submit exactly one COMMENT review with `commit_id` = the bound head and an empty inline-comment list. Do not post other pull-request comments in the same round.
7. Readback-verify the published carrier. Re-fetch the review by id, repair per step 1, extract, and compare: the envelope digest equals the accepted digest; the review author is the expected publisher; the carrier is the last carrier in chain order on the pull request. Only after this gate, hand off to the reviewer round.
8. External closure stops the ceremony. If the owner merges the artifact before terminal delivery, record the merge as the exchange's external closure and publish no further carriers to the merged artifact.

### If a step is unavailable

- No local reducer or extractor available: hold the publication. A delayed carrier is recoverable; a carrier with unverified digests is not.
- The requirements source changed since the last binding: the refresh path does not rebind requirements; stop and route through the exchange workflow's own rebind path instead of reusing the retained digest.
- The forge body differs in damage beyond one trailing line feed: reject the carrier; do not generalize the repair.
- No fresh-context reviewer is available for the next round: hold the exchange; the refresh carrier alone does not advance the round.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Guess the scope-digest formula | Six content-based candidates (concatenated file bytes, concatenated per-file digests, JSON of per-file digests, paths with blob identifiers, sorted tree listing, head tree hash) against the published reviewed-scope digest | None matched: the published digest is computed over forge metadata fields, not tree content | The reviewed-scope digest binds the pull request's mutable scope metadata. Reproduce it from the forge API with the canonical-JSON recipe; verify the recipe on a published carrier first. |
| Pass the extracted event verbatim | Used the stored author-event state (with its retained `requirements_sha256` and `target`) as the reduce event | The reducer rejected the request: "author response has invalid fields: unknown requirements_sha256, target" | The event schema is narrower than the stored envelope state. Strip to event-schema fields in every reduce request. |
| Strict extraction of forge bodies | Ran `review_exchange.py extract` on review bodies exactly as the forge API returned them | "The review-exchange JSON fence is malformed or not final" | The delivery channel adds one trailing line feed after the closing fence. Remove exactly one final line feed and re-extract; anything else stays a rejection. |
| Collector on a private remote | Ran the evidence collector to bind the reviewed scope; its snapshot materialization failed | The isolated fetch environment strips git configuration (no credential helper) and disables terminal prompts: exit 128, "could not read Username" | When the collector cannot materialize, recompute each binding digest from the forge API under the published conventions and revalidate immediately before publication. |

## Results & Parameters

### Configuration

```text
extract fails, body has exactly one extra trailing LF -> strip one "\n"; extract again
extract fails for any other reason                   -> reject carrier; no repair
state awaiting_reviewer AND head != bound revision    -> author-response refresh first;
                                                         round unchanged; next assessment
                                                         is full-coverage, fresh context
path set unchanged                                     -> scope_change_reason stays empty
path set changed                                       -> non-empty scope_change_reason
collector cannot materialize (private remote auth)     -> manual digest recomputation;
                                                         verify on a published carrier;
                                                         revalidate just before publish
owner merges before terminal delivery                  -> record external closure;
                                                         publish no further carriers
```

### Expected Output

- A repaired extraction yields the same envelope digest as before the repair.
- A refresh carrier reduces to `awaiting_reviewer / review_assessment` at the new head with the round unchanged, renders, publishes as one COMMENT review, and readback-verifies as the last carrier of the exchange.
- A merged artifact carries the refresh carrier as its published record, and the exchange closes externally without further carriers.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Chain-verified pull-request review exchange (v1 carriers) | Mid-round force-push of a qualification-artifact pull request; carrier repair on four published carriers, manual digest recomputation, author-response refresh published and readback-verified; owner merged before terminal delivery | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |

## References

- [review-exchange-assessment-canonical-response-order](review-exchange-assessment-canonical-response-order.md) — the response-order rule inside published assessment events; the same reduce-before-publish gate applies.
- [review-exchange-terminal-carrier-sole-publisher](review-exchange-terminal-carrier-sole-publisher.md) — the publisher-routing rule for the terminal round; route carrier counts and channels accordingly.
- [github-pr-review-head-bound-check-evidence](github-pr-review-head-bound-check-evidence.md) — binds CI evidence to a moved head; this entry binds exchange carriers to the same moved head.
