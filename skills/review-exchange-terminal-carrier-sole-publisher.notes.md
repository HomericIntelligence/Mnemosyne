# Notes: review-exchange-terminal-carrier-sole-publisher

Supporting evidence for the main skill. Generalized from one live incident;
identifiers are omitted under the privacy rules.

## Incident chronology (2026-10-09)

1. A two-round review exchange covered a benchmark-report pull request with a
   large generated-evidence diff.
2. Round 1 returned NO-GO with two root-cause findings; the author fixed both
   at a new head with a regression test, and round 2 verified closure at the
   exact head, resulting in a GO state.
3. The round-2 GO state carrier was published through the general publisher
   instead of the designated terminal delivery helper.
4. Terminal helper delivery then failed closed: the guards reported a
   conflicting terminal review for the head and required a nonforking exchange
   chain. A same-head terminal state already existed, so the helper input was
   permanently invalid for that exchange.
5. Recovery options were enumerated: full protocol recovery, owner override, or
   hold. The complete-state chain accepts a reframe only when requirements
   changed; the exchange requirements were unchanged, so that path did not
   apply. The owner selected the override.
6. The override record: an explanatory note on the pull request names the
   published exact-head GO review as the merge gate; the state labels were
   applied directly; both finding threads received replies and were resolved;
   the pull request merged as a merge commit with the branch retained.

## Second incident chronology (2026-10-27)

1. A one-day multi-round exchange on a research-monorepo pull request ended in
   a complete GO state whose requirements binding had gone stale after base
   drift.
2. The coordinator reframe superseded that stale terminal state and reset the
   requirements identity to the live binding. The reframe round was
   terminal-eligible at round one.
3. The coordinator published the round's state carrier through the general
   publisher, with the narrative review report as the visible content. The
   intent was a verdict report in the style of the earlier non-terminal
   rounds.
4. Helper delivery rejected the closure manifest: `The carrier does not bind
   the visible content`. The terminal state envelope must bind the digest of
   the deterministic closure ledger as its visible content; the published
   carrier bound the report instead.
5. A chained reframe with unchanged requirements was also rejected: `A reframe
   must bind a new requirements identity.`
6. Recovery: the report-bound carrier was voided in place with a PUT body edit
   that removed the carrier marker (the record-repair primitive). A corrective
   reframe was then built from the last ancestor whose requirements binding
   differed from the live requirements, with a fresh authority receipt.
7. The corrective reframe reduced to a terminal state that bound the
   deterministic ledger, and the helper delivered it cleanly: the terminal
   review published, the state label applied exclusively, and no thread stayed
   open.
8. Byte-format facts observed during the same delivery: an anchor annex must
   sit in its own section (one blank line before the marker), and the terminal
   visible content ends exactly at the annex closing fence with no trailing
   newline when an annex is present.

## Why the second case refines the rule

- The publish-order constraint alone did not prevent this wedge: the carrier
  was published before helper delivery, which is the correct order, but the
  round was terminal-eligible and its visible content was a report. The
  binding rule and the publisher rule must both hold.
- The void-then-reframe exit completes the decision table for a carrier that
  your own session published in error: void in place, then reframe from the
  last different-requirements ancestor. It avoids the owner override and
  keeps the helper's bookkeeping complete.

## Third incident chronology (2026-10-27)

1. A multi-round exchange on an endpoint-consumer pull request ended with an
   independent exact-head GO review. The terminal round's state carrier had
   been published through the general publisher, per-round, before the helper
   ran.
2. Terminal-delivery preparation surfaced two further ledger blockers beyond
   the foreign carrier. First, the live requirements digest no longer equaled
   the value the exchange bound at round 1: the requirements source had been
   edited mid-exchange. The terminal state, the manifest, and the live
   binding must agree, so the helper would reject. Second, seven open review
   threads predated the exchange and carried no envelope in any published
   chain carrier (their era has no marker envelopes), so the closure manifest
   could not close them and they stayed foreign-open.
3. The seven pre-exchange threads were re-audited at the recorded head: five
   fixed or obsolete with source evidence; two residual nits, both recorded
   nonblocking. Current-exchange threads already carried their round
   answers.
4. Recovery selection: void-then-reframe did not apply, because no
   same-requirements carrier needed voiding and the blockers were
   ledger-side, where voiding repairs nothing. A requirements-drift reframe
   was legally possible but would restart a full exchange over unchanged
   reviewed content, and the current-head reviewer had verified the edits
   content-compatible. The owner selected the override.
5. Execution: a gate note named the published exact-head GO review identity,
   its state digest, the reviewed head and base, and each verified blocker.
   Every open thread received an evidence-referenced reply and was resolved,
   leaving zero open. The terminal state label applied and the opposed state
   label was removed.
6. Later head change: the base branch merged into the artifact branch, with
   one conflict at a site where both sides had added distinct handlers. The
   resolution kept both. An independent reviewer verified that the merged
   tree equals the union of both parents' change sets (byte-identical
   outside the overlapped paths), and the gate was re-bound by an
   addendum that named the new head and that verification. The full local
   suite result was recorded as merge-gate evidence; the exact-head CI run,
   suppressed organization-side, stayed a separate merge condition and never
   fed the review verdict.

## Why the third case refines the rule

- The wedge diagnosis must go beyond the foreign carrier: drift equality and
  no-envelope pre-exchange threads are independent fail-closed blockers, and
  each must be named in the override note.
- A requirements edit is not automatically a reframe trigger. When the
  current-head reviewer verifies the change content-compatible, the recorded
  GO stays semantically valid; the reframe cost (a full exchange over
  unchanged content) buys nothing, so the override records the drift instead.
  A material requirements change still routes to reframe.
- The override's execution surface is enumerable: gate note, per-thread
  evidence closure to zero open, exclusive state label, evidence separation
  from CI, and a re-bind addendum after any later head change with
  independent verification that the delta preserves the reviewed content.

## Why the rule is safe to generalize from one case

The invariant does not rest on frequency. The helper's terminal-delivery path
is fail-closed by design: it must be the sole writer of the terminal review
body, and it binds the deterministic closure ledger as the visible digest. Any
same-head prior publication makes that binding unachievable, so a retry cannot
succeed. The decision value is the publish-order constraint, which one
observed rejection proves.

## Recovery outlook

After the incident, an upstream change request was filed for the exchange
tooling: an opt-in mode in which the terminal helper, instead of refusing a
foreign-published same-head terminal carrier, publishes a superseding terminal
report. The report binds the foreign carrier by review identity and state
digest, declares it superseded, and carries the canonical closure ledger as
the authoritative state. The default stays fail-closed; supersession requires
explicit operator opt-in and a single parseable, attributable foreign carrier.

If such a mechanism lands, prefer it over an owner override: it closes the
helper's bookkeeping for the exchange instead of leaving it permanently
incomplete. Reassess the permanence of this wedge class against the installed
tooling generation before you select a recovery.

## Limits

- Evidence comes from three exchanges: one on v1-era exchange tooling
  (override path), one on a ledger-binding helper generation
  (void-then-reframe path), and one on v1-era tooling with requirements
  drift and no-envelope pre-exchange threads (override path with gate
  re-binding). Helper versions that do not bind a closure ledger may not
  enforce sole publication.
- The reframe path was evaluated against the protocol contract; it was not
  executed. The supersession path is a filed proposal, not yet implemented or
  verified.
- The owner override is a governance decision, not a protocol mechanism. It
  requires owner authority and leaves the helper's bookkeeping incomplete for
  the exchange; the notes, labels, and thread closures must then be done
  explicitly.
