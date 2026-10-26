---
name: review-exchange-head-refresh-carrier-repair
description: "Recover and rebind a chain-verified review-exchange carrier chain in the field: repair a forge-published carrier that the strict parser rejects, recompute the artifact and visible-content binding digests when the evidence collector cannot materialize the snapshot, rebind the exchange to a changed head with an author-response refresh before the next reviewer round, and re-derive a delivery payload when a moved head makes every bound digest stale. Use when: (1) extraction rejects a published carrier with a malformed-or-not-final JSON fence, (2) the artifact head changed while the reduced state awaits the reviewer, (3) the collector fails on a private remote because its isolated fetch cannot authenticate, (4) the reduce request rejects a stored author event for retained state-level fields, (5) the reduced state is decision_required after a head move and the in-place recovery events are reducer-rejected, or (6) a pause precedes a forge write and you must re-read live state, which includes whether a concurrent authorized actor already delivered the goal, or (7) the head must change after the exchange reached a terminal delivered state, for example a CI-mandated refresh while auto-merge is armed: the reducer accepts only a reframe after terminal delivery, so archive the completed exchange by its terminal reply, disarm auto-merge before any push, open a fresh round-1 exchange with an independent reviewer at the live head, and re-arm only after the new terminal delivery binds the pushed head."
category: tooling
date: 2026-10-21
version: "1.2.0"
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
  - decision-required
  - reframe
  - rebind-not-patch
  - concurrent-actor
  - post-terminal-refresh
  - terminal-law
  - auto-merge-disarm
---

# Review Exchange Head Refresh and Carrier Repair

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-21 |
| **Objective** | Keep a chain-verified review-exchange carrier chain publishable when the strict parser rejects a forge-published carrier, the artifact head changes mid-round, or the evidence collector cannot materialize the immutable snapshot. |
| **Outcome** | Operational rule set derived from three live exchanges. First: a mid-round force-push left the reduced state awaiting the reviewer at a stale head. Four published carriers needed a parser repair before extraction; the collector's snapshot materialization failed on the private remote; the author-response refresh carrier was computed by hand, published, readback-verified, and the owner merged the pull request minutes later. Second: a terminal-delivery preparation in which the reduced state was `decision_required`, the head moved twice, and a concurrent authorized actor delivered the goal; a fully offline-validated closure manifest died at preflight and was discarded with zero forge writes. Third: two CI-mandated head refreshes after a terminal GO delivery; each refresh archived the completed exchange by its terminal reply and opened a fresh round-1 exchange, auto-merge was disarmed before every push and re-armed after the final delivery bound the pushed head, and the squash merge followed. |
| **Verification** | verified-live in three exchanges: one two-round exchange (2026-10-21), where the trailing-line-feed repair recovered all four published carriers, the manual digest formulas reproduced a published carrier's digests, and the refresh carrier reduced, rendered, published, and readback-verified; one terminal-delivery preparation (2026-10-24), where the decision-required branch analysis, the re-derive-not-patch rule, and the concurrent-actor goal-met stop were each verified against the reducer rules and live forge state; and one post-terminal refresh (2026-10-26), where the terminal law ("A terminal review state cannot accept another event") and the armed-auto-merge stale-head hazard were verified empirically against the reducer and the live forge, and three exchanges archived correctly on one pull request. |

## When to Use

- `review_exchange.py extract` rejects a carrier with "The review-exchange JSON fence is malformed or not final", and the body came from a forge API.
- The artifact head changed after the last author answers, and the reduced logical state is `awaiting_reviewer` at the stale head revision.
- The changed-path set of the artifact changed since the last binding (for example, a base branch deleted review files that the resolution then kept byte-identical), so the scope set and the artifact digest changed.
- The evidence collector cannot bind the reviewed scope because its isolated fetch fails on a private remote (exit 128, "could not read Username").
- The reduce request fails with "author response has invalid fields: unknown requirements_sha256, target" because a stored envelope state was passed as the event.
- The reduced state is `decision_required` and the head, the scope set, or the requirements digest changed while the exchange waited. The in-place recovery events are reducer-rejected in this state; select a reframe under reframe authority, or hold and escalate.
- A delivery payload was prepared and validated offline, and the artifact changed before the first forge write. Re-derive the payload from the live snapshot; do not patch bound fields.
- A pause precedes a forge write. Re-read the live forge state (head, labels, open threads, the latest carrier). A concurrent authorized actor can deliver the goal while the exchange waits.
- The head changed, or must change, after terminal delivery (the reduced state is complete). The reducer accepts only a reframe in this state; every other event is rejected with "A terminal review state cannot accept another event". Archive the completed exchange by its terminal reply and open a fresh round-1 exchange at the live head with an independent reviewer.
- Auto-merge is armed on the artifact and a push is necessary. An armed request survives pushes and is not head-pinned: the forge merges whichever head first passes branch protections. Disarm auto-merge before the push; re-arm only after terminal delivery binds the pushed head.
- You must publish or readback-verify one carrier without inventing a new digest convention.

## Verified Workflow

### Quick Reference

```text
Forge-published carrier: remove exactly one final line feed, then extract.
All other carrier damage: reject; do not repair.
Head changed while reduced state is awaiting_reviewer:
  publish an author-response refresh carrier (one fresh evidence-backed answer
  per required finding) before the next reviewer assessment. The round stays.
Head changed while reduced state is decision_required:
  author-refresh and human_decision are both reducer-rejected. Reframe with
  authority (an owner-approved new exchange or a real requirements delta), or hold.
Head changed after terminal delivery (state complete):
  reducer accepts only reframe. The completed exchange stays archived by its
  terminal reply; open a fresh round-1 exchange at the live head with an
  independent reviewer. A stale-head GO does not carry to the new head.
Auto-merge armed and a push is necessary:
  disarm before the push; the armed request is not head-pinned and merges the
  first head that passes protections. Re-arm only after terminal delivery
  binds the pushed head.
After any pause before a forge write:
  re-read head, labels, open threads, latest carrier. Goal already met -> stop.
  Otherwise re-derive every bound digest from the live snapshot; never patch a
  validated payload.
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
8. Rebind a decision-required exchange to a moved head. Preconditions: the reduced logical state is `decision_required`, and the head, the scope set, or the requirements digest differs from the bound value. In this state the reducer rejects both in-place events: an author-response refresh is admissible only when the exchange's own derived stop-reason is the literal `replacement_blocker`, and a `human_decision` event must carry the prior state's artifact binding unchanged, so it cannot rebind a moved head. The remaining transitions are:
   - **Reframe**: start a new exchange at round 1 at the current head. This needs reframe authority: the owner's approval for a new exchange, or a real requirements delta. A reframe without one fabricates protocol state (the sole-publisher rule records this failure). Publish the authority record once, then derive every round-1 binding from the live snapshot.
   - **Hold**: stop and escalate when no reframe authority exists. Do not probe the reducer with a patched head binding in an event schema that cannot carry it.
9. Re-derive, never patch, after any mid-flight change. Treat each bound value — head revision, artifact-binding digest, scope set and scope digest, requirements digest, finding-thread digests — as perishable between the harvest and each forge write. Immediately before the write, recompute each digest from the live immutable inputs and validate the complete payload offline again. A field-by-field patch keeps the dependent digests stale. In the second source incident a fully validated closure manifest died at preflight because the head, the scope set, the requirements source, and the open threads had all changed since harvest. Rebuild from intent; discard the derived parts.
10. Stop when the goal is already met. A concurrent authorized actor — another session, the owner, or automation — can deliver the terminal state while the exchange waits. After each pause, and again before each forge write, read the current head and base, the open review threads, the state labels, and the latest published carrier from the forge. If the target terminal state is already published or the artifact is merged, stop; discard the prepared unpublished artifacts. Carriers that are already published stay in place: delivery channels are append-only, so a stale authority record is documented and left, never retracted or overwritten.
11. External closure stops the ceremony. If the owner merges the artifact before terminal delivery, record the merge as the exchange's external closure and publish no further carriers to the merged artifact.
12. Rebind a post-terminal head move by exchange replacement. Preconditions: the reduced state is terminal (delivery complete), and the head must change afterwards, for example a CI-mandated container refresh. In a terminal state the reducer rejects every event kind except `reframe` with "A terminal review state cannot accept another event"; do not attempt an author refresh, a second assessment, or a second delivery on the completed exchange. The completed exchange stays archived by its terminal reply — the reply is its closure record and publication channels are append-only. Open a fresh round-1 exchange at the live head: derive every binding from the live snapshot, and give the new head an independent full-coverage reviewer round from a fresh context. A GO delivered against a stale head does not transfer. Several completed exchanges can coexist on one artifact; each archives by its own terminal reply. Repeat the same branch for each post-terminal refresh.
13. Sequence auto-merge around every head push. An armed auto-merge request survives pushes and is not head-pinned: the forge merges whichever head first satisfies branch protections, so an armed request can merge a stale or intermediate head before terminal delivery binds it. Before any push to the artifact, disable auto-merge (`gh pr merge --disable-auto`); run the refresh and the fresh exchange; re-arm (method per branch policy) only after the new terminal delivery binds the pushed head. Apply the arm-time gating checklist from the auto-merge entry at every re-arm.

### If a step is unavailable

- No local reducer or extractor available: hold the publication. A delayed carrier is recoverable; a carrier with unverified digests is not.
- No reframe authority for a decision-required wedge (no requirements delta, no owner-approved new exchange): hold and escalate. A `human_decision` or author-response event with a patched head binding cannot reduce; do not probe the reducer with it.
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
| In-place event for a decision-required wedge | Evaluated an author-response refresh and a `human_decision` event for a `decision_required` state with a moved head | Both are reducer-rejected: the refresh hatch requires the literal derived stop-reason `replacement_blocker`, and `human_decision` must carry the prior state's artifact binding unchanged, so it cannot carry a new head | In `decision_required` state, reframe under reframe authority is the only legal transition to a new head; without authority, hold and escalate |
| Patch a stale delivery manifest | Considered updating only the moved fields of an offline-validated closure manifest after the head, scope, requirements, and thread states all changed | Each bound value is a digest of a snapshot that no longer existed; a field-by-field patch keeps the dependent digests stale, and the payload fails at the first pre-publication gate or carries inconsistent bindings | Discard the derived parts and re-derive the complete payload from the live snapshot; validate it offline before any forge write |
| Deliver from a harvested snapshot without a forge-state recheck | Prepared a complete terminal-delivery set (fresh reviewer GO, thread closures, authority record, validated manifest) against a harvested snapshot | During the pause a concurrent authorized actor moved the head twice, resolved the last open threads, and published the complete terminal exchange; the prepared set was dead on arrival and was discarded with zero forge writes | After each pause and before each forge write, re-read head, labels, open threads, and the latest carrier from the forge; when the goal is already met, stop |
| Continue an exchange after terminal delivery | Attempted further round events on an exchange whose terminal GO had already reduced to the complete state, after CI required a head refresh | The reducer rejected every event except reframe: "A terminal review state cannot accept another event"; the exchange state machine is closed | A terminal delivered state is final. Archive the completed exchange by its terminal reply, open a fresh round-1 exchange at the live head, and give the new head an independent reviewer round |
| Auto-merge kept armed across a head refresh | Considered pushing a CI-mandated head refresh while the armed auto-merge request was live; inspected the live forge state first | The armed request survived the previous push and was not head-pinned: the forge would merge whichever head first passed branch protections, so an intermediate head could merge before terminal delivery bound it | Disarm auto-merge before every push; re-arm only after terminal delivery binds the pushed head. Branch protections gate checks, not head identity |

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
state decision_required AND any binding moved       -> reframe with authority, or hold;
                                                         in-place events are reducer-rejected
pause before any forge write                        -> re-read head, labels, open threads,
                                                         latest carrier; goal met -> stop
mid-flight change to any bound value                -> discard the derived payload;
                                                         re-derive all bindings from the
                                                         live snapshot; validate offline
owner merges before terminal delivery                  -> record external closure;
                                                         publish no further carriers
state terminal (complete) AND head changed           -> reframe-only; completed
                                                         exchange stays archived by
                                                         its terminal reply; fresh
                                                         round-1 exchange at live
                                                         head, independent reviewer
reviewer GO on a stale head                          -> does not transfer; new head
                                                         needs its own full-coverage
                                                         fresh-context round
auto-merge armed AND push required                   -> disarm before the push;
                                                         re-arm after the terminal
                                                         delivery binds the pushed
                                                         head
```

### Expected Output

- A repaired extraction yields the same envelope digest as before the repair.
- A refresh carrier reduces to `awaiting_reviewer / review_assessment` at the new head with the round unchanged, renders, publishes as one COMMENT review, and readback-verifies as the last carrier of the exchange.
- A decision-required reframe starts a round-1 exchange at the current head with every binding recomputed from the live snapshot; without reframe authority, the exchange holds with zero forge writes.
- A pre-write recheck after a pause returns `goal met`: the prepared payload is discarded with no publication, and already-published carriers are left in place and documented.
- A merged artifact carries the refresh carrier as its published record, and the exchange closes externally without further carriers.
- A post-terminal head refresh leaves the completed exchange archived by its terminal reply, opens a fresh round-1 exchange at the live head with an independent reviewer GO, and ends with auto-merge armed only against the head that terminal delivery bound; several completed exchanges can coexist on one artifact, each archived by its own terminal reply.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Chain-verified pull-request review exchange (v1 carriers) | Mid-round force-push of a qualification-artifact pull request; carrier repair on four published carriers, manual digest recomputation, author-response refresh published and readback-verified; owner merged before terminal delivery | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |
| Chain-verified pull-request review exchange (v1 carriers) | Terminal-delivery preparation against a twice-moved head with a concurrent authorized actor; the decision-required branch reduced to reframe-only, the fully validated manifest was discarded at preflight with zero forge writes, and the goal was verified met by the concurrent exchange before the discard | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |
| Chain-verified pull-request review exchange (v1 carriers) | Two CI-mandated head refreshes after a terminal GO delivery on a worker-agent pull request; terminal-law rejection verified empirically, three exchanges archived by terminal reply on one artifact, auto-merge disarmed before every push and re-armed after the final delivery bound the pushed head, followed by a guarded squash merge | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |

## References

- [review-exchange-assessment-canonical-response-order](review-exchange-assessment-canonical-response-order.md) — the response-order rule inside published assessment events; the same reduce-before-publish gate applies.
- [review-exchange-terminal-carrier-sole-publisher](review-exchange-terminal-carrier-sole-publisher.md) — the publisher-routing rule for the terminal round; route carrier counts and channels accordingly. Its reframe-authority condition binds the reframe branch of this entry.
- [review-exchange-terminal-manifest-construction](review-exchange-terminal-manifest-construction.md) — the construction-order rule for a terminal closure manifest. Apply this entry's rebind rules first, so the manifest is built on live bindings.
- [github-pr-review-head-bound-check-evidence](github-pr-review-head-bound-check-evidence.md) — binds CI evidence to a moved head; this entry binds exchange carriers to the same moved head.
- [github-auto-merge-ci-gating-merge-method](github-auto-merge-ci-gating-merge-method.md) — the arm-time gating checklist for auto-merge; apply it at every re-arm after terminal delivery binds the pushed head.
