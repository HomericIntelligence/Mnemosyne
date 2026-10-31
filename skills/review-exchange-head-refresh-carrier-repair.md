---
name: review-exchange-head-refresh-carrier-repair
description: "Recover and rebind a chain-verified review-exchange carrier chain in the field: repair a forge-published carrier that the strict parser rejects, recompute the artifact and visible-content binding digests when the evidence collector cannot materialize the snapshot, rebind the exchange to a changed head with an author-response refresh before the next reviewer round, and re-derive a delivery payload when a moved head makes every bound digest stale. Use when: (1) extraction rejects a published carrier with a malformed-or-not-final JSON fence, (2) the artifact head changed while the reduced state awaits the reviewer, (3) the collector fails on a private remote because its isolated fetch cannot authenticate, (4) the reduce request rejects a stored author event for retained state-level fields, (5) the reduced state is decision_required after a head move and the in-place recovery events are reducer-rejected, (6) a pause precedes a forge write and you must re-read live state, which includes whether a concurrent authorized actor already delivered the goal, (7) the reducer rejects a fix answer at the constant head because a pull-request fix must bind a new head revision and the pending correction changed only forge metadata., or (8) the head must change after the exchange reached a terminal delivered state, for example a CI-mandated refresh while auto-merge is armed: the reducer accepts only a reframe after terminal delivery, so archive the completed exchange by its terminal reply, disarm auto-merge before any push, open a fresh round-1 exchange with an independent reviewer at the live head, and re-arm only after the new terminal delivery binds the pushed head. Also use when (9) a bug-fix commit moves the head after the terminal GO delivery already completed (carrier, threads, and exclusive label) and the delivery contract may keep that GO. Also use when (10) an already-published carrier embeds a receipt reference that resolves in one forge identifier space but not the reader's (a numeric REST review id where the reader needs the GraphQL node identifier): the exchange is dead, so stop and supersede it."
category: tooling
date: 2026-10-21
version: "1.5.0"
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
  - metadata-only-fix
  - empty-signed-commit
  - commit-text-hygiene
  - post-delivery-head-change
  - reference-space-fault
  - authority-receipt-resolution
  - immutable-carrier
  - dead-exchange-diagnosis
  - superseded-artifact
---

# Review Exchange Head Refresh and Carrier Repair

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-21 |
| **Objective** | Keep a chain-verified review-exchange carrier chain publishable when the strict parser rejects a forge-published carrier, the artifact head changes mid-round, or the evidence collector cannot materialize the immutable snapshot. |
| **Outcome** | Operational rule set derived from five live exchanges. First: a mid-round force-push left the reduced state awaiting the reviewer at a stale head. Four published carriers needed a parser repair before extraction; the collector's snapshot materialization failed on the private remote; the author-response refresh carrier was computed by hand, published, readback-verified, and the owner merged the pull request minutes later. Second: a terminal-delivery preparation in which the reduced state was `decision_required`, the head moved twice, and a concurrent authorized actor delivered the goal; a fully offline-validated closure manifest died at preflight and was discarded with zero forge writes. Third: a correction that touched only forge metadata could not be answered at the constant head; the author advanced the head with one empty signed commit whose tree was byte-identical, the refresh bound the new head, terminal delivery completed, and the artifact merged with an explicitly set squash body. Fourth: two CI-mandated head refreshes after a terminal GO delivery; each refresh archived the completed exchange by its terminal reply and opened a fresh round-1 exchange, auto-merge was disarmed before every push and re-armed after the final delivery bound the pushed head, and the squash merge followed. Fifth: a complete terminal GO delivery (carrier, threads, and exclusive label) was followed by a CI-found repair commit that moved the head; the completed exchange accepted no rebind event, the reframe path required a requirements delta that did not exist, and the delivered GO survived per the delivery contract — the artifact merged on green required checks. Sixth: a published reframe carrier embedded a numeric REST review id as its receipt reference, but the reader resolves only GraphQL node identifiers. The carrier is immutable, so its event can never verify, and its derived state holds the predecessor's single successor slot, which makes every later transition invalid. No GO was reachable; the artifact stopped with one blocker comment and was referred for supersession. |
| **Verification** | verified-live in five exchanges: one two-round exchange (2026-10-21), where the trailing-line-feed repair recovered all four published carriers, the manual digest formulas reproduced a published carrier's digests, and the refresh carrier reduced, rendered, published, and readback-verified; one terminal-delivery preparation (2026-10-24), where the decision-required branch analysis, the re-derive-not-patch rule, and the concurrent-actor goal-met stop were each verified against the reducer rules and live forge state; and one two-round exchange (2026-10-26), where the constant-head fix rejection, the deliberate empty-commit head advance, and the squash-hygiene verification were each confirmed against the reducer and the post-merge forge state; and one post-terminal refresh (2026-10-26), where the terminal law ("A terminal review state cannot accept another event") and the armed-auto-merge stale-head hazard were verified empirically against the reducer and the live forge; and one terminal GO exchange (2026-10-26), where the complete-phase reducer rejection and the reframe requirements-digest gate were observed, and the delivery-contract survival rule was confirmed by the subsequent merge with the exclusive label intact; and one dead-exchange diagnosis (2026-10-31), where a published carrier's embedded numeric REST review id was confirmed to resolve to zero records in the reader's GraphQL identifier space against the live review node identifier, the single-successor and single-chain rules were each traced against the live state, and the stop-and-supersede branch was executed with zero carrier writes. |

## When to Use

- `review_exchange.py extract` rejects a carrier with "The review-exchange JSON fence is malformed or not final", and the body came from a forge API.
- The artifact head changed after the last author answers, and the reduced logical state is `awaiting_reviewer` at the stale head revision.
- The changed-path set of the artifact changed since the last binding (for example, a base branch deleted review files that the resolution then kept byte-identical), so the scope set and the artifact digest changed.
- The evidence collector cannot bind the reviewed scope because its isolated fetch fails on a private remote (exit 128, "could not read Username").
- The reduce request fails with "author response has invalid fields: unknown requirements_sha256, target" because a stored envelope state was passed as the event.
- The reduced state is `decision_required` and the head, the scope set, or the requirements digest changed while the exchange waited. The in-place recovery events are reducer-rejected in this state; select a reframe under reframe authority, or hold and escalate.
- The reduce request rejects an author `fix` or `fix_with_tradeoff` answer with "A pull-request fix must bind a new head revision", and the correction changed only forge metadata (for example the pull-request body). The artifact head is unchanged, so no tree delta exists to push.
- A head-chain commit message carries linkage text (for example a closing keyword) that a squash merge can copy into the merge commit on the default branch, even when the pull-request body is clean.
- A delivery payload was prepared and validated offline, and the artifact changed before the first forge write. Re-derive the payload from the live snapshot; do not patch bound fields.
- A pause precedes a forge write. Re-read the live forge state (head, labels, open threads, the latest carrier). A concurrent authorized actor can deliver the goal while the exchange waits.
- The head changed, or must change, after terminal delivery (the reduced state is complete). The reducer accepts only a reframe in this state; every other event is rejected with "A terminal review state cannot accept another event". Archive the completed exchange by its terminal reply and open a fresh round-1 exchange at the live head with an independent reviewer.
- Auto-merge is armed on the artifact and a push is necessary. An armed request survives pushes and is not head-pinned: the forge merges whichever head first passes branch protections. Disarm auto-merge before the push; re-arm only after terminal delivery binds the pushed head.
- A bug-fix commit (for example, a CI-found repair) moves the head after the terminal GO delivery already completed: the terminal carrier is published and readback-verified, every exchange thread is resolved, and the exclusive terminal-state label is applied. Do not try to extend the completed exchange.
- An already-published carrier embeds a receipt reference that resolves in one forge identifier space and not the other: it extracts and verifies, but no delivery can resolve its event. Confirm the mismatch in both spaces first.
- You must publish or readback-verify one carrier without inventing a new digest convention.

## Verified Workflow

### Quick Reference

```text
Forge-published carrier: remove exactly one final line feed, then extract.
All other carrier damage: reject; do not repair.
Head changed while reduced state is awaiting_reviewer:
  publish an author-response refresh carrier (one fresh evidence-backed answer
  per required finding) before the next reviewer assessment. The round stays.
Fix answer rejected at the constant head ("must bind a new head revision")
  and the correction is metadata-only:
  land the metadata fix, then advance the head with one empty signed commit
  (byte-identical tree). Refresh at the new head.
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
Head changed after complete terminal delivery (label + zero open threads):
  the delivered GO survives (already_delivered). No exchange event exists:
  a complete state accepts only reframe, and reframe needs a changed
  requirements digest. Merge on green required checks.
  Re-review is author judgement, not an exchange obligation.
After any pause before a forge write:
  re-read head, labels, open threads, latest carrier. Goal already met -> stop.
  Otherwise re-derive every bound digest from the live snapshot; never patch a
  validated payload.
Carrier event names an authority receipt that resolves in one forge identifier
  space but not the reader's -> the exchange is dead. Do not repair or probe.
  Confirm the delivered NO-GO label, post one blocker comment, supersede.
Digests: recompute from the forge API with the canonical recipes below.
  Verify each recipe against an already-published carrier before binding a new one.
Publish one COMMENT review per carrier, then readback-verify digest, author, position.
Keep closing keywords out of every head-chain commit message. At merge, set the
  squash title and body explicitly; verify the merge commit and each linked
  requirement's state afterward.
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

   The same refresh path applies when the author must change the head deliberately. The reducer rejects a `fix` or `fix_with_tradeoff` answer at the constant head ("A pull-request fix must bind a new head revision"). A correction that changed only forge metadata (for example the pull-request body) has no tree delta to push, so advance the head deliberately: land the metadata correction first, recompute the scope digest (the corrected metadata changes it; the changed-path manifest and the requirements digest stay), then create one empty signed commit on the review branch whose tree is byte-identical to the tested head. Verify `git diff` between the tested head and the new head is empty and that both tree object identifiers match. Give the commit an honest message: the exchange records author corrections only on a new head revision, the commit is empty, and a squash merge carries none of its identity. Push, confirm the forge head moved, then build the refresh exactly as above at the new revision. Because the reviewed-scope digest binds mutable metadata (branch names, not the head object identifier), the digest that bound the corrected metadata survives the head advance. Coverage was still invalidated, but the next full-coverage round proves tree identity and re-affirms the unchanged source coverage instead of re-executing it.
6. Publish one carrier atomically. Submit exactly one COMMENT review with `commit_id` = the bound head and an empty inline-comment list. Do not post other pull-request comments in the same round.
7. Readback-verify the published carrier. Re-fetch the review by id, repair per step 1, extract, and compare: the envelope digest equals the accepted digest; the review author is the expected publisher; the carrier is the last carrier in chain order on the pull request. Only after this gate, hand off to the reviewer round.
8. Rebind a decision-required exchange to a moved head. Preconditions: the reduced logical state is `decision_required`, and the head, the scope set, or the requirements digest differs from the bound value. In this state the reducer rejects both in-place events: an author-response refresh is admissible only when the exchange's own derived stop-reason is the literal `replacement_blocker`, and a `human_decision` event must carry the prior state's artifact binding unchanged, so it cannot rebind a moved head. The remaining transitions are:
   - **Reframe**: start a new exchange at round 1 at the current head. This needs reframe authority: the owner's approval for a new exchange, or a real requirements delta. A reframe without one fabricates protocol state (the sole-publisher rule records this failure). Publish the authority record once, then derive every round-1 binding from the live snapshot.
   - **Hold**: stop and escalate when no reframe authority exists. Do not probe the reducer with a patched head binding in an event schema that cannot carry it.
9. Re-derive, never patch, after any mid-flight change. Treat each bound value — head revision, artifact-binding digest, scope set and scope digest, requirements digest, finding-thread digests — as perishable between the harvest and each forge write. Immediately before the write, recompute each digest from the live immutable inputs and validate the complete payload offline again. A field-by-field patch keeps the dependent digests stale. In the second source incident a fully validated closure manifest died at preflight because the head, the scope set, the requirements source, and the open threads had all changed since harvest. Rebuild from intent; discard the derived parts.
10. Stop when the goal is already met. A concurrent authorized actor — another session, the owner, or automation — can deliver the terminal state while the exchange waits. After each pause, and again before each forge write, read the current head and base, the open review threads, the state labels, and the latest published carrier from the forge. If the target terminal state is already published or the artifact is merged, stop; discard the prepared unpublished artifacts. Carriers that are already published stay in place: delivery channels are append-only, so a stale authority record is documented and left, never retracted or overwritten.
11. External closure stops the ceremony. If the owner merges the artifact before terminal delivery, record the merge as the exchange's external closure and publish no further carriers to the merged artifact.
12. Treat a delivered terminal GO as surviving a later bug-fix head change. Preconditions: the terminal carrier is published and readback-verified, every exchange thread is resolved, and the exclusive terminal-state label is applied. A later commit — a CI-found repair or any other bug fix — moves the head, but the exchange is complete: the reducer accepts only a reframe event on a complete state, and a reframe requires a changed requirements digest, which an unchanged requirements source does not supply. The delivery contract records the outcome directly: an exclusive terminal-state label with zero open threads and a verified completed history is `already_delivered`; the label does not lapse when a later commit changes the head, and a rebase, a base merge, or a later bug fix does not remove it. Confirm the label and thread state from the live forge, then merge when the required checks pass at the new head. The label lapses only when a reviewer delivers the exclusive NO-GO label or when the target carries no state label. Re-review is the author's judgement — for example, when the repair changes behavior that a reviewed finding covered — and never an exchange obligation; a real re-review starts a full fresh exchange under new authority instead of extending the completed one.
13. Rebind a post-terminal head move by exchange replacement. Preconditions: the reduced state is terminal (delivery complete), and the head must change afterwards, for example a CI-mandated container refresh. In a terminal state the reducer rejects every event kind except `reframe` with "A terminal review state cannot accept another event"; do not attempt an author refresh, a second assessment, or a second delivery on the completed exchange. The completed exchange stays archived by its terminal reply — the reply is its closure record and publication channels are append-only. Open a fresh round-1 exchange at the live head: derive every binding from the live snapshot, and give the new head an independent full-coverage reviewer round from a fresh context. A GO delivered against a stale head does not transfer. Several completed exchanges can coexist on one artifact; each archives by its own terminal reply. Repeat the same branch for each post-terminal refresh.
14. Sequence auto-merge around every head push. An armed auto-merge request survives pushes and is not head-pinned: the forge merges whichever head first satisfies branch protections, so an armed request can merge a stale or intermediate head before terminal delivery binds it. Before any push to the artifact, disable auto-merge (`gh pr merge --disable-auto`); run the refresh and the fresh exchange; re-arm (method per branch policy) only after the new terminal delivery binds the pushed head. Apply the arm-time gating checklist from the auto-merge entry at every re-arm.
15. Keep closing keywords out of head-chain commit text. A terminal reviewer round can attach a finding to any head-chain commit message: a merge that composes its default title or body from branch commit messages can re-introduce a closing keyword even when the pull-request body is clean. This applies in both directions: a policy-required reference must live in the pull-request body fields, not only in commit text. Defenses: keep closing keywords and other harmful linkage text out of every head-chain commit message from the start, including a deliberate empty commit; set the final squash title and body explicitly at merge arm time (do not rely on the default); and after merge verify that the merge commit carries no closing keyword and that each linked requirement stayed in its intended state (a requirement that the artifact deliberately does not complete keeps its issue open).
16. Treat an unresolvable identifier inside an immutable carrier as a dead exchange, not a repairable one. Detect it when the carrier extracts and its standalone state verifies, but a reference string inside its accepted event does not resolve in the reader's identifier space; prove that by resolving the same reference in both spaces. No route exists: the carrier is immutable, so an edit or dismissal invalidates every delivery; its state occupies the predecessor's single successor slot, so any later event creates two successors; and with no terminal GO, every later delivery fails the single-chain check at any head. Do not repair or probe the reducer. Confirm the delivered NO-GO label, post one comment naming the failing reference, both identifier values, and the two chain rules, and stop. Recompose the work into a fresh artifact. This differs from steps 1, 5, 8, and 13: step 1 repairs a read-side parse artifact, steps 5 and 8 rebind a head, and step 13 replaces an exchange that reached terminal delivery.

### If a step is unavailable

- No local reducer or extractor available: hold the publication. A delayed carrier is recoverable; a carrier with unverified digests is not.
- No reframe authority for a decision-required wedge (no requirements delta, no owner-approved new exchange): hold and escalate. A `human_decision` or author-response event with a patched head binding cannot reduce; do not probe the reducer with it.
- The requirements source changed since the last binding: the refresh path does not rebind requirements; stop and route through the exchange workflow's own rebind path instead of reusing the retained digest.
- The forge body differs in damage beyond one trailing line feed: reject the carrier; do not generalize the repair.
- No fresh-context reviewer is available for the next round: hold the exchange; the refresh carrier alone does not advance the round.
- A head change after complete terminal delivery, with a review-workflow text that appears to accept a pre-round-5 complete GO as a head-refresh precondition: the current reducer gate accepts no non-reframe event on a complete state. Treat the delivered GO as terminal, apply the survival rule, and do not probe the reducer to confirm. See the notes for the exact gate and the observed text tension.

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
| Repair an immutable carrier whose event reference will not resolve | A carrier named its receipt by numeric REST review id while the reader resolves only GraphQL node identifiers; considered editing or dismissing the carrier to republish a corrected reference | A published carrier is immutable, so an edit or dismissal invalidates every delivery. Its state also held the single successor slot, so each later event created two successors, and the missing terminal GO failed the single-chain check at any head | Treat it as a dead exchange: confirm the mismatch in both spaces, keep the delivered NO-GO label, post one blocker comment, and supersede with a clean exchange |
| Continue an exchange after terminal delivery | Attempted further round events on an exchange whose terminal GO had already reduced to the complete state, after CI required a head refresh | The reducer rejected every event except reframe: "A terminal review state cannot accept another event"; the exchange state machine is closed | A terminal delivered state is final. Archive the completed exchange by its terminal reply, open a fresh round-1 exchange at the live head, and give the new head an independent reviewer round |
| Auto-merge kept armed across a head refresh | Considered pushing a CI-mandated head refresh while the armed auto-merge request was live; inspected the live forge state first | The armed request survived the previous push and was not head-pinned: the forge would merge whichever head first passed branch protections, so an intermediate head could merge before terminal delivery bound it | Disarm auto-merge before every push; re-arm only after terminal delivery binds the pushed head. Branch protections gate checks, not head identity |
| Answer a forge-metadata-only fix at the constant head | Submitted the `fix` answer with the revised scope digest and the unchanged head revision after the pull-request body was corrected | The reducer rejected the answer: "A pull-request fix must bind a new head revision"; the rule is absolute, and no event field carries a metadata-only fix | Land the metadata correction, then advance the head deliberately with one empty signed commit (byte-identical tree) and bind the author-response refresh to the new head |
| Rely on the merge-time default message | Followed the repository's `Closes #N` convention inside a head-chain commit message while the pull-request body itself held the required non-closing linkage | A terminal reviewer round flagged the commit text as a follow-up finding: a squash merge that composes its default message from branch commit messages can copy the closing keyword into the default branch | Keep closing keywords out of every head-chain commit message; set the squash title and body explicitly at merge arm time; verify the merge commit and each issue state after merge |
| Probe a completed GO exchange with a continued author or reviewer event after a CI-found repair | A CI gate found a configuration defect after the terminal GO delivery; the repair commit moved the head, and a continued author-response event and a round-increment reviewer assessment were prepared to rebind the completed exchange | The reducer rejected the event: "A terminal review state cannot accept another event." A complete state accepts only a reframe, and a reframe requires a changed requirements digest, which an unchanged requirements source cannot supply | A delivered GO survives a later bug-fix head change by contract; do not rebind or extend the completed exchange. Confirm the `already_delivered` state from the live forge and merge on green required checks |

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
fix rejected at constant head AND correction
  is forge-metadata-only                           -> land the metadata fix; recompute the
                                                          scope digest; advance the head with one
                                                          empty signed commit (byte-identical tree);
                                                          refresh at the new head
head-chain commit text carries linkage text      -> keep it clean from the start; set the
                                                          squash title and body explicitly at merge;
                                                          verify the merge commit and the issue states
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
head changed after complete terminal delivery
  (carrier + threads + exclusive label)                -> already_delivered: the GO
                                                          survives; no exchange event;
                                                          merge on green required checks;
                                                          re-review = author judgement only
carrier event reference resolves in one forge
  identifier space but not the reader's                -> dead exchange: no repair, no
                                                          probe; keep the delivered
                                                          NO-GO label; one blocker
                                                          comment; supersede the artifact
                                                          with a clean round-1 exchange
```

### Expected Output

- A repaired extraction yields the same envelope digest as before the repair.
- A refresh carrier reduces to `awaiting_reviewer / review_assessment` at the new head with the round unchanged, renders, publishes as one COMMENT review, and readback-verifies as the last carrier of the exchange.
- A decision-required reframe starts a round-1 exchange at the current head with every binding recomputed from the live snapshot; without reframe authority, the exchange holds with zero forge writes.
- A pre-write recheck after a pause returns `goal met`: the prepared payload is discarded with no publication, and already-published carriers are left in place and documented.
- A merged artifact carries the refresh carrier as its published record, and the exchange closes externally without further carriers.
- A post-terminal head refresh leaves the completed exchange archived by its terminal reply, opens a fresh round-1 exchange at the live head with an independent reviewer GO, and ends with auto-merge armed only against the head that terminal delivery bound; several completed exchanges can coexist on one artifact, each archived by its own terminal reply.
- A deliberate head advance produces an empty signed commit whose tree is byte-identical to the tested head; the author-response refresh binds the new revision; the next full-coverage round proves tree identity and re-affirms source coverage.
- A merge with an explicitly set squash title and body leaves the merge commit free of closing keywords and each linked requirement in its intended state.
- Diagnosing an unresolvable receipt reference ends with the delivered NO-GO label intact, exactly one blocker comment carrying both identifier values and the two chain rules, zero carrier edits, and zero reducer probes; the reusable work moves to a fresh artifact.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Chain-verified pull-request review exchange (v1 carriers) | Mid-round force-push of a qualification-artifact pull request; carrier repair on four published carriers, manual digest recomputation, author-response refresh published and readback-verified; owner merged before terminal delivery | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |
| Chain-verified pull-request review exchange (v1 carriers) | Terminal-delivery preparation against a twice-moved head with a concurrent authorized actor; the decision-required branch reduced to reframe-only, the fully validated manifest was discarded at preflight with zero forge writes, and the goal was verified met by the concurrent exchange before the discard | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |
| Chain-verified pull-request review exchange (v1 carriers) | Two CI-mandated head refreshes after a terminal GO delivery on a worker-agent pull request; terminal-law rejection verified empirically, three exchanges archived by terminal reply on one artifact, auto-merge disarmed before every push and re-armed after the final delivery bound the pushed head, followed by a guarded squash merge | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |
| Chain-verified pull-request review exchange (v1 carriers) | Forge-metadata-only policy correction at the constant head: the reducer-rejected fix answer, the deliberate empty-commit head advance (byte-identical tree), the author-response refresh at the new head, terminal delivery, and the explicitly set squash body at merge with post-merge verification of the merge commit and the issue state | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |
| Chain-verified pull-request review exchange (v1 carriers) | Post-delivery repair after a complete terminal GO: a CI gate found a configuration defect, the repair commit moved the head, the completed exchange rejected rebind probes (complete-phase gate, reframe requirements-digest gate), and the delivered GO survived per contract; the artifact merged on green required checks with the exclusive label intact | [notes](review-exchange-head-refresh-carrier-repair.notes.md) |

## References

- [review-exchange-assessment-canonical-response-order](review-exchange-assessment-canonical-response-order.md) — the response-order rule inside published assessment events; the same reduce-before-publish gate applies.
- [review-exchange-terminal-carrier-sole-publisher](review-exchange-terminal-carrier-sole-publisher.md) — the publisher-routing rule for the terminal round; route carrier counts and channels accordingly. Its reframe-authority condition binds the reframe branch of this entry.
- [review-exchange-terminal-manifest-construction](review-exchange-terminal-manifest-construction.md) — the construction-order rule for a terminal closure manifest. Apply this entry's rebind rules first, so the manifest is built on live bindings.
- [github-pr-review-head-bound-check-evidence](github-pr-review-head-bound-check-evidence.md) — binds CI evidence to a moved head; this entry binds exchange carriers to the same moved head.
- [github-auto-merge-ci-gating-merge-method](github-auto-merge-ci-gating-merge-method.md) — the arm-time gating checklist for auto-merge; apply it at every re-arm after terminal delivery binds the pushed head.
