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

## Incident chronology (2026-10-28)

A documentation program ran under fleet automation: several automation
sessions under one account published on the same pull requests.

1. One pull request carried a foreign round-1 exchange whose only finding had
   been adjudicated and resolved in-tree. During branch maintenance, a
   sibling session posted two distinct terminal GO state carriers over one
   parent state, accompanied by empty carrier bodies. The persisted chain
   forked: one state had multiple derived successors.
2. Helper terminal delivery at the refreshed head failed closed: the guards
   require one nonforking chain and reject any state with multiple derived
   successors. Review dismissal is rejected as an invalid carrier, and the
   forge exposes no review deletion, so no carrier-level repair existed. A
   reframe was not available either: the exchange requirements had not
   changed.
3. A cross-session coordination note prescribed the same recovery that the
   graph analysis had indicated: close the pull request as superseded and
   open one replacement from the same branch and head with one publisher.
   The closure comment and the replacement body carried the fork record, the
   per-finding in-tree resolution table of the old exchange, and the
   unchanged verification results.
4. On the replacement pull request, a sibling session's delivery landed
   seconds before this session's prepared delivery. Replaying the persisted
   carriers classified the rejection as preemption, not a wedge: exactly one
   terminal GO envelope bound the exact live head. This session extracted
   the sibling carrier and audited it byte-for-byte against its own prepared
   manifest — requirement digest, reviewed-scope digest, artifact revision,
   anchor annex base and head, and the single-round complete-GO event
   structure. Every value matched, so this session posted a handoff note,
   applied the terminal state label exactly once, and armed auto-merge.
5. On a later, clean pull request with no foreign carriers, the same
   manifest-construction route delivered on the first attempt: the helper
   published the terminal review and applied the terminal state label
   itself, and auto-merge completed.

## Why the fork classification matters

The fork is a property of the persisted carrier set, not of the delivery
input. No manifest repair exists, so every retry fails identically, and the
standard exits do not apply: a void repair edits one's own carrier, but the
duplicate carriers here were a sibling's records, and voiding one successor
of a forked parent leaves the chain forked by definition; a reframe requires
a real requirements change, which did not exist. Closing the pull request as
superseded resets the persisted carrier set because a new pull request
starts an empty chain, while the branch and head — and therefore every
in-tree finding resolution — carry over unchanged.

## Additional limits

- The close-and-replace recovery was exercised once, under an explicit
  cross-session coordination note and a sole-publisher agreement. Without
  that agreement, two sessions can open competing replacements and re-fork.
- The audit-acceptance path applies only when the sibling uses identical
  tooling and the audit covers every binding field. A partial audit turns
  acceptance into trust.
- The empty carrier bodies that accompanied the duplicate carriers were
  immutable and stayed in place as part of the fork record.

## Incident: read-blind state carrier on a reopened artifact (2026-10-31)

### Shape

A terminal delivery on a reopened artifact. An earlier round had published
three inline finding roots, each with a machine marker that named an exchange
identity, plus one state-carrier review that owned those findings. The forge's
REST record listing still showed that carrier review at its original head.

The terminal delivery helper reads carriers through one GraphQL-only read
path. That path could not resolve the carrier review's record. The helper's
read-only preparation therefore returned a fresh-exchange result: no prior
state, zero carriers, and the three published roots listed as plain open
threads with conversation digests.

### The mask

The fresh-exchange result invites a reconstruction: build a reducer-derived
genesis state (initial review that adopts the findings, author answers, one
terminal GO assessment), then deliver. This session built that genesis and
traced the delivery preflight against the live helper code before any write.
The preflight binds every manifest entry whose inline root carries a marker to
the reviewer-state review that introduced the finding, inside the verified
chain. Because the read-blind carrier never enters the chain, that origin
record resolves to nothing, and the binding fails for every manifest. The
failure is structural, not transient: no genesis construction can satisfy it,
because the required record is invisible to the reader by construction.

### Distinguishing sign

- A genuinely fresh exchange: no carrier review in any forge listing, and no
  finding markers that name an exchange identity.
- A read-blind carrier: the preparation reports zero carriers while another
  forge listing shows the carrier review, and the open threads' roots carry
  exchange-identity markers.

Confirm with two reads before any reconstruction: the helper's read-only
preparation, and the forge's record listing over the other API.

### Delivery that worked

The owner-override path of this entry, executed completely:

1. A terminal statement review pinned to the exact head, with a per-finding
   ledger whose evidence was re-verified at that head, not inherited from the
   invisible exchange.
2. One evidence-naming reply per published thread, then thread resolution.
3. The terminal state label applied and the opposed label removed, so exactly
   one state label remained.
4. A public audit note that names the verified blocker (the unresolvable
   carrier record and the origin-binding rule it defeats) and the reason the
   helper path is unsatisfiable.

Required checks ran on the labeled head, and the artifact merged by squash.

### Evidence quality rule

The override inherits no review evidence from the invisible exchange. Each
finding's closure cites evidence read at the delivery head (current file
contents, a full-file local test run, and the clean formatting checks). This
keeps the override honest when the invisible exchange's findings are stale.

## Incident: adoption-incompatible terminal carrier (2026-10-31)

### Shape

An automation flow ran the issue-to-merge route on one artifact: round 1 of
the review produced a terminal GO verdict, and the round publisher released
the GO review body through the general reviewer-round publisher as a plain
triple-backtick `json` report fence. No further rounds existed. Every review
thread was already resolved at that head, and no state labels were present.

### The blocker chain

1. The terminal delivery helper has an adoption path for a delivered same-head
   terminal review. Its acceptance set is narrow: the review body must equal
   the exact prepared body bytes, or it must carry the versioned compressed
   carrier fence (a `<scope>-json-zlib-base64` marker form). A plain report
   fence holds the same content, but it is outside the acceptance set, so
   adoption failed closed.
2. A second same-head terminal carrier could not clear the block. The
   duplicate-state guard forbids a second terminal state at one head.
3. The carrier-recovery route requires an exact suffix-byte reconstruction of
   the published bodies plus an authoritative requirements reframe. The
   exchange requirements had not changed, so the reframe had no requirements
   identity to bind and would fabricate protocol state.
4. Every in-band exit was therefore unavailable: adoption (format), second
   carrier (duplicate-state guard), and recovery reframe (no requirements
   delta). The remaining exits were the owner override and hold.

### Gate-state readback

The override authority recorded the gate-state readback in the work item's
public coordination thread before any write:

- the artifact open at the exact head;
- zero open review threads;
- exactly one delivered GO review bound to that head, in a commented state;
- no state labels present.

### Delivery that worked

The owner authority applied the terminal state label on the recorded gate.
The repository starts its required checks from the state label, so the label
write started the checks on the labeled head, and automerge delivery followed
the normal policy. The decision record in the coordination thread carries the
readback and the authority basis.

### Why the classification matters

A lane that reaches this state without a classification spends budget on
non-exits: re-running adoption against the same format, preparing a second
carrier that the duplicate-state guard will reject, or evaluating a reframe
that cannot bind a requirements identity. The classification is one check
against the carrier body format and one read of the requirements digest; both
are cheaper than each non-exit.

## Toolchain-version drift over unchanged requirement content (2026-11-01)

### What happened

A two-round exchange had a clean history: the round-1 state carrier returned
NO-GO with four required findings, one author response resolved all four, and
round 2 returned GO with complete coverage. Terminal delivery then withheld
with three independent blockers:

1. **Requirements-digest inequality.** The exchange bound the digest that the
   snapshot producer computed at exchange genesis. The installed producer
   computed a different digest from the same content, and the delivery helper
   requires equality.
2. **Anchor-manifest mismatch.** The delivery adapter re-verifies each
   published carrier's anchor annex against immutable source. The current
   producer emits summary and outside-bound entries for findings that the
   earlier producer recorded as inline only. The round-1 annex therefore could
   not re-verify.
3. **Terminal-carrier shape.** The round carrier was published by the general
   round publisher with reviewer resolution prose. The helper expects the
   terminal carrier to carry its deterministic closure ledger as visible
   content, and the published carrier is immutable.

### How the cause was confirmed

- The linked issues showed no comment created after the exchange start.
- The linked issues showed no update after the exchange start, so no body,
  title, or criterion changed.
- The installed review toolchain files had modification times later than the
  exchange start, and the installed version manifest reported a new version.
- The two digests were reproduced directly: the current producer gave one
  value, and the exchange retained the earlier value. The difference was
  attributed to the producer change, not to content.

This separated the drift from the requirements-edit branch that the main entry
already covered. The recovery follows the requirements-edit branch in one
respect only: both use the owner override. It differs in a way that changes
the decision: a reframe is never valid for a derivation change, because no
material requirement changed.

### Blockers that were not repaired

- A reframe was not used. It needs a material requirement change, and the
  content was byte-identical. Using it would fabricate protocol state and
  restart a full exchange over unchanged reviewed content.
- The installed toolchain was not edited or downgraded. That would rewrite the
  verifier for one exchange and leave other sessions on a different
  derivation, which is the same defect in a new place.
- No manual label write was made. The label was left as the reviewer round
  delivered it, and no guessed write touched the forge.

### The rule this case adds

Classify the drift cause before you select a recovery: content edit versus
toolchain-version change. The evidence that separates them is the issue
update time, the comment history after the exchange start, and the installed
toolchain's modification time against its version manifest. Only the content
edit can route to a reframe, and only when it is material.

## Case: void-then-rebuild recovery of a same-requirements wedge (2026-11-01)

### Situation

A two-sided review exchange over an internal pull request completed its round-2
reviewer assessment with verdict GO. The terminal round's state carrier was
published through the general reviewer-round path first, with narrative prose as
its visible content. The envelope, its digests, and the carrier fence were all
well-formed, so the record parsed cleanly and readbacks verified. Requirements
and the installed toolchain were unchanged since the exchange start.

The designated terminal delivery helper could not deliver a version-1 closure
manifest against that exchange: the prepared terminal visible content must equal
the deterministic closure ledger generated from the binding and the closure
entries, and the already-published carrier bound the prose, not the ledger. An
owner override would have left the finding threads, the state labels, and the
gate record to manual bookkeeping; a reframe would fabricate protocol state
over unchanged requirements.

### Decision taken

Void the own-session carrier in place with a PUT body edit (plain-text void
note, exact state digests, no exchange markers; record repair mechanics in
github-pr-review-record-void-repair). The record stops being parseable, so the
persisted carrier chain replays to the pre-terminal state (round-1 NO-GO plus
the author-event answers, awaiting the reviewer round). Then rebuild the
terminal state as a plain next transition:

1. Regenerate the deterministic terminal ledger from the unchanged prepared
   closure entries through the delivery helper's own ledger generator, with
   the completed author-event and disposition fields.
2. Bind the new ledger digest as the reviewer-assessment event's
   visible-content digest. Reduce: accepted, terminal state, verdict GO.
3. Serialize the manifest in canonical JSON: state envelope equals the new
   terminal envelope, terminal visible content equals the exact ledger bytes,
   each entry's recorded terminal digest equals the new terminal digest.
   Convergence took one pass: the ledger generator drops each entry's recorded
   terminal digest from the hashed visible entries when the entry has no
   reframe successor, so the ledger bytes do not depend on the new digest.
4. Deliver. The helper published one terminal carrier, generated a structured
   closure response on each of the three inline finding threads, resolved all
   three, applied the exclusive terminal state label, and removed the opposed
   label. Delivery result: delivered; zero pending threads.

### Refused alternatives

- Owner override: available but heavier; it records the prose review as the
  merge gate and leaves thread closure, label exclusivity, and the audit note
  to manual execution. Void-then-rebuild delivers the same head through the
  primary path with a deterministic ledger as the gate record.
- Reframe: requirements were unchanged, so a reframe would fabricate protocol
  state and restart a full exchange over unchanged reviewed content.
- Iterating the prose-bound envelope: its visible-content digest can never
  equal the deterministic ledger over the entries, so every repair edit starts
  a new cycle. The envelope was discarded, not iterated.
- Close and replace: the chain was not forked by duplicate terminal carriers;
  no fork existed once the own-session carrier was voided.

### Delivery-input failures during the same run

Pre-publication input rejections, each corrected once without a forge mutation;
the classes and remedies follow review-exchange-terminal-manifest-construction:

- A GO-mode delivery passed a state-carrier file argument. That argument is
  valid only for a NO-GO delivery; the terminal GO envelope rides in the
  manifest state field.
- The author-event review identity was first supplied as the decimal review
  identifier. The correct form is the GraphQL review node ID.
- The delivery rejected with "publication anchor proof failed: publication
  anchor verification requires immutable source": the round-1 state carrier
  carried a published anchor annex that binds the original head commit, so
  final delivery needs the anchor-source option whenever such an annex exists,
  not only for annex-bearing terminal visible content.

### Anchor source with orphaned objects

After a rebase and force-push, the head that the round-1 anchor annex binds is
orphaned: no branch or tag references it, and a plain fresh clone cannot
materialize it. The recovery used a bare repository whose objects/info/alternates
file points at a long-lived checkout whose object store still retains the
orphan. Verify the source before delivery: regenerate the annex byte-identically
with the helper's manifest preparation function (same base, same head, same
finding set) and compare against the published annex bytes. Note the two-digit
trap: the source directory must resolve objects through normal git plumbing
(the helper runs git commands in it), and it must contain every commit the
annex or the binding names: base, head, merge base, and the current delivery
head.

### Readback discipline

Carrier and review readbacks through the forge API append one trailing line
feed; strip exactly one final LF before byte comparisons and before strict
carrier extraction (the same rule as github-pr-review-record-void-repair and
review-exchange-head-refresh-carrier-repair record).

### The rule this case adds

A wedge from your own same-round report-bound terminal carrier, with unchanged
requirements and toolchain, has an in-band exit that is cheaper and more
auditable than the owner override: void your own record, restore the chain,
and rebuild the terminal state through the helper as a plain next transition.
The owner override stays for records you cannot void: foreign carriers,
adopt-as-gate records, and read-blind carriers.
