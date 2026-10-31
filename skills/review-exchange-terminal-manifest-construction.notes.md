# Notes: review-exchange-terminal-manifest-construction

Supporting evidence for the main skill. Generalized from five live
deliveries; identifiers are omitted under the privacy rules.

## Delivery chronology (2026-10-22)

1. A single-file installer fix completed source review as a terminal candidate:
   zero active findings, grade A, exact-head binding, one linked requirement.
   Human authority explicitly waived reviewer independence for this delivery
   (author self-review), and the waiver was recorded in the user-facing report.
2. The first manifest used a detailed prose assessment as the terminal visible
   content. The terminal delivery helper rejected it: the terminal visible
   closure ledger does not match its manifest entries. The published terminal
   body is a deterministic ledger over the binding and the ordered closure
   entries, not reviewer prose. In this round (zero findings, zero entries)
   the deterministic body was a four-line ledger: verdict, reviewed head, and
   one closure-ledger digest.
3. The prose digest had already been written into the reduce event. The event
   was rebuilt with the ledger digest, reduced again, and rendered again.
   The render step requires the carrier's visible-content digest to equal the
   digest bound in the reduce event, so the re-reduce was mandatory, not
   cosmetic.
4. The second manifest was accepted as JSON but rejected in form: the response
   manifest is not canonical JSON. The helper requires the exchange canonical
   byte form — UTF-8, sorted object keys, minimal separators — not only a
   parseable document.
5. Two interface mismatches cost additional submissions before that: a mode
   word passed as the positional argument (the parser consumed it as the
   review identity), and a requirement-issue flag passed in delivery mode
   (valid only in manifest-preparation mode).
6. The third submission was accepted. The helper published one terminal
   COMMENT carrier at the exact head, applied the exclusive terminal-state
   label, and reported zero pending threads. An independent forge readback
   confirmed the published ledger bytes, the label set, and the head binding.
7. Total cost of the rule violation: two rejected submissions and one rebuilt
   state envelope. No forge publication happened before the accepted
   submission, so every retry was safe.

## Reusing the helper's ledger generator in-process

The deterministic visible content must come from the terminal helper itself,
not from an approximation. Two access patterns worked:

- In-process: load the helper module the way its script entry point loads it.
  The helper selects a package-relative import when it believes it runs inside
  a package and a file-location fallback otherwise. An import harness that
  leaves the module's package context non-empty takes the package-relative
  branch and fails; setting the module's package context to empty takes the
  working fallback branch. Then call the helper's ledger generator with the
  binding and an empty entry tuple for a zero-finding round.
- Command line: when the in-process import is not needed, the helper's
  command-line entry point exercises the same generator.

Treat the generated ledger as opaque bytes: the identical byte string is the
hash input for the reduce event, the manifest's terminal visible content, and
the published body.

## Why construction rejection is a distinct class from a delivery wedge

The sole-publisher rule says: never retry the terminal helper. That rule
covers publication-state rejections, where a same-head terminal state already
exists or the chain must not fork. The rejections in this delivery were
input-validation rejections: the helper proved the input malformed before it
touched the forge. The forge readback showed no review and no label change,
so correcting the input and resubmitting could not fork anything. Applying
the no-retry rule to construction rejections would freeze a delivery that was
one input fix away from success. The safe discriminator is the error class,
checked against a forge readback when in doubt: input validation rejects
nothing-published states; wedge errors name existing published state.

## Structural carrier-history incident (2026-10-26)

1. A maintained review thread's round-1 carrier adopted legacy review
   findings as native identities (`native:<provider-identifier>`). Each was
   recorded with a legacy marker of the form `exchange=<record> id=<F-NNN>`.
   The verified derived chain had not been built from that record.
2. The terminal round reached a GO state with all findings resolved. The
   closure manifest was built in the verified order: deterministic ledger,
   visible-content digest, reduce, render, canonical JSON.
3. The terminal delivery helper (version 0.6.0) rejected the manifest at
   preflight: `An adopted native finding has no unique matching review root`.
   The selector in the error was the native identity of an adopted finding.
   The rejection occurred before any forge write, and a forge readback
   confirmed that nothing was published.
4. A full rebuild — deterministic ledger with the adopted findings included
   as native-identity entries, regenerated manifest, and a re-reduce with the
   corrected visible-content digest — repeated the identical preflight error.
   This confirmed that the rejection is structural: it binds to published
   carrier history, not to pending input.
5. With owner approval, the helper's legacy-marker resolution was extended:
   a legacy marker is accepted when its claimed identity is not used by the
   verified derived chain. Strict provenance was kept for every marker that
   the chain claims. The stock helper was preserved byte-exact, with its
   checksum recorded, before the change.
6. The patched helper accepted the rebuilt manifest and published the
   terminal carrier at the exact head with the exclusive terminal-state label
   and zero open threads.
7. An idempotency re-run of the same input against the delivered state
   returned the already-delivered result, which proves no duplicate
   publication.
8. The stock helper at the same version cannot re-verify the delivered
   exchange: it fails the same preflight. The exact divergence is recorded in
   the delivery artifacts, and the extension awaits routing to the helper
   owner. Until the owner accepts the fix, a stock helper reports the
   delivered exchange as unverifiable.

Ordering observation: the structural preflight ran before the input
checks. A structural rejection can mask later input-validation failures, so
repair order matters: resolve the carrier history first, then re-validate
the inputs.

Ledger-mismatch cross-reference: the rebuilt ledger in step 4 bound the
corrected visible-content digest and passed the visible-content checks once
the patched helper reached them. This confirms that the deterministic-ledger
build order in the main skill does not change under the extension.

## Self-referential ledger incident (2026-10-26)

A findings-closure terminal GO delivery exposed a mutual dependency that the
zero-finding and adopted-native deliveries had not shown. Identifiers are
omitted under the privacy rules.

1. A three-finding round reached a complete GO state. The three review threads
   were to close in the same terminal delivery, so the closure manifest
   carried three entries.
2. During construction, each entry's state digest was pointed at the terminal
   state. The helper hashes every entry into the visible ledger and removes a
   digest field only when the field already equals the current terminal
   digest. The terminal state in turn hashes the visible content, and the
   visible content is the ledger.
3. The first submissions failed with the visible-ledger mismatch. The sequence
   of manual repairs was: write a corrected digest, recompute the ledger,
   re-reduce so the state bound the new bytes, then set the entry digests to
   the new terminal digest. Each step changed a value that an earlier step had
   consumed, so every pass produced a new mismatch with a different digest.
   One intermediate digest was stale on arrival and never matched any state.
4. Two related evidence rules surfaced in the same delivery. The terminal
   visible content must equal the ledger exactly: a reviewer report prepended
   above the ledger failed the same mismatch check. Closure evidence for a
   resolved finding must come from the reviewer response, not from the author
   answer, and that evidence is hashed into the entry, so correcting it also
   moves the ledger.
5. The fix was one iterative pass instead of chained edits. With the prior
   state, the event, the entry fields, the closure evidence, and the binding
   held fixed, each pass hashed the current visible content, reduced, set the
   entry digests to the reduced terminal digest, and recomputed the ledger
   with the helper's generator. Pass one changed the ledger; pass two
   reproduced it byte for byte and fixed the point.
6. The helper's own closure validator then accepted the manifest and listed
   all three threads, and delivery published one terminal carrier at the exact
   head with the exclusive terminal label and zero unresolved threads.
7. Cost of the chained approach: several rejected submissions and several
   rebuilt state envelopes. Every rejection was pre-publication, so no retry
   risked a fork.

Convergence observation: the pass that confirms the fixed point usually
reproduces the previous ledger, so stop condition is byte equality of the
ledger, not equality of the digest string alone. Keep the non-derived inputs
frozen across passes; recomputing them inside the loop reintroduces the cycle.

## Terminal-introduced findings and anchor annex incident (2026-10-26)

A terminal GO delivery carried a case the earlier deliveries had not shown:
the terminal review itself raised new findings, and the visible content
carried an anchor annex. Identifiers are omitted under the privacy rules.

1. A findings round reached a complete GO state. During the terminal review,
   the reviewer recorded new nonblocking findings: two inline threads and one
   summary finding. These findings were raised in the terminal round itself;
   the exchange had no prior carrier history for them.
2. The new findings were kept out of the closure entries. The manifest placed
   the per-thread responses in the comments partition and the summary finding
   identity in the summary finding partition. The helper's anchor proofs
   verified the partition before delivery.
3. Two pre-publication rejections occurred during construction. The first
   manifest file was pretty-printed JSON. The second combined reviewer prose
   and anchor content with the deterministic ledger in the terminal visible
   content, without the annex marker structure; the helper rejected it with
   the visible-ledger mismatch, because its equality check compares the
   content up to the annex marker and unmarked extra bytes compare as ledger.
4. The rebuilt visible content placed the deterministic ledger first and the
   anchor annex as the final section after the annex marker line. The combined
   bytes — ledger, marker, annex — were hashed into the reduce event's
   visible-content digest; the envelope was re-reduced and re-rendered. The
   annex source was passed to the delivery helper with its anchor-source
   option. The helper splits the annex before the ledger-equality check but
   binds the annex bytes in the state digest, so the digest must cover both.
5. The canonical manifest was accepted. The helper published one terminal
   comment carrier at the exact head, generated the responses to the two new
   inline threads from the comments partition, resolved both threads, applied
   the exclusive terminal-state label, and reported zero pending threads. An
   independent forge readback confirmed the review identity, the two
   responded and resolved thread identities, the empty pending set, and the
   label set. The reviewed head did not move during delivery.
6. Cost of the two construction rejections: two rejected submissions and one
   rebuilt state envelope. Every rejection was pre-publication, and a forge
   readback confirmed nothing was published, so each retry was safe.

Partition observation: the anchor proofs are the helper's own check of the
terminal-introduced partition. When the proofs pass, the closure entries hold
only findings the exchange already tracked, and every terminal-round finding
has a comments or summary partition record. The partition check runs
pre-publication, so a partition error is an input repair, not a structural
rejection.

Annex placement observation: the annex is the final section. The helper splits
the visible content at the annex marker and compares only the ledger part for
equality, but the state digest binds the full bytes. Annex content before the
marker compares as ledger and fails; annex content omitted from the reduce
digest fails the render check. The delivery helper's anchor-source option
binds the same annex bytes at publication.

## Nonterminal no-go delivery — published-review identity form (2026-10-28)

1. A round-1 source review closed with a nonterminal no-go state: two
   findings, an exact-head binding, one linked requirement. The reviewer
   published one comment review carrier at the exact head, carrying an
   anchor annex after the deterministic annex marker. The same carrier
   acted as the delivery's proof review.
2. Two delivery submissions were withheld at pre-publication input
   validation before the accepted one. The defects they fixed between them:
   the proof review was bound by its decimal database review identifier,
   which the helper rejects — the published-review identity must be the
   GraphQL review node ID — and the annex source was not supplied although
   the proof review carried a published anchor annex. Neither withheld
   attempt published a carrier and neither changed a state label.
3. The accepted submission changed only those two inputs: the GraphQL
   review node ID for the proof review identity and the annex source for
   the published annex. The helper delivered the exclusive nonterminal
   state label and reported the published review identity. An independent
   forge readback confirmed the label set at the exact head. The delivery
   result showed the state label only after the accepted submission, which
   confirms the withheld attempts mutated nothing.
4. Cost: two withheld submissions, zero forge mutations. Every rejection
   was pre-publication, so each resubmission was safe. The exact parameter
   names and value forms for the review identity and the annex source are
   interface witnesses of this helper generation; confirm them against the
   installed helper's signature before relying on them.

## Evidence limits

Five single live cases, one exchange tooling generation each. The invariants
(digest order, deterministic visible body, canonical manifest form,
rejection-class triage, structural carrier-history rejection, fixed-point
convergence, terminal-introduced partition, annex placement, withheld
pre-publication rejection safety) follow from the fail-closed validator design and do not rest on
frequency. Interface details (positional argument, mode flags, import context,
anchor-source option, published-review identity form) are generation-specific witnesses; confirm them against
the installed helper's signature before relying on them.


## Prepare-then-fill and thread flush (2026-10-31)

Sixth live delivery. A two-file change reached a clean zero-finding round-1
assessment at a rebased head. One old-head inline thread remained open. Its
finding was the aggregation-tail assertion, and the rebased head already
carried the corrected assertion.

Findings from this delivery:

1. Answering a fixed legacy thread fails unless the current exchange records
   that finding. The reducer returned a terminal-state rejection first. After a
   clean terminal round was reduced, the same answer was still impossible
   because no carrier owned the finding identity.
2. A direct thread resolution with a linked evidence comment let a clean
   terminal round deliver at the same head. The delivery result reported
   `status=delivered` with the exclusive terminal label, and the readback showed
   zero open threads.
3. The prepare-mode output was a template with a null state and empty visible
   content. Six deliver-mode submissions were withheld before publication: the
   requirement-issue flags, the null state, the bare state record, the empty
   visible content, a visible digest from a ledger built before the reduce, and
   a scope digest captured before a body-text correction. The corrected
   manifest was accepted on the seventh submission.
4. A pull-request body correction moves the live scope digest. The reduce binds
   one scope digest, so collect the scope again and bind the new value before
   delivery.
5. Required checks started only after the terminal label was applied. The two
   earlier failed jobs were label-precondition failures from a run before the
   label existed, and both had a passing re-run at the same head. Auto-merge
   with the squash method merged the pull request when the required checks
   passed.
