---
name: review-exchange-terminal-manifest-construction
description: "Build a terminal-delivery closure manifest in the verified dependency order — deterministic ledger first, visible-content digest before reduce, render, canonical JSON — so the designated terminal delivery helper accepts it. Use when: (1) a review flow routes a terminal-eligible round through a designated terminal delivery helper that consumes a closure manifest, (2) the helper rejects the manifest with an input-validation error such as an uncanonical JSON form, a visible-ledger mismatch, or a published-review identity that is not a GraphQL review node ID, (3) you must decide what belongs in the terminal visible content and which digest to bind in the reduce event, (4) the ledger, the state digest, and the entry set are mutually dependent so each rebuilding pass changes the digest again, or (5) you must distinguish a pre-publication input rejection (fix and resubmit) from a structural carrier-history rejection (no input repair exists) or a publication-state wedge (do not retry). Use also when: (6) the terminal round itself raises new findings that must be partitioned out of the closure entries, or (7) the terminal visible content must carry an anchor annex after the deterministic ledger."
category: tooling
date: 2026-10-28
version: "1.3.0"
user-invocable: false
tags:
  - pr-review
  - review-exchange
  - terminal-delivery
  - closure-manifest
  - deterministic-ledger
  - canonical-json
  - visible-content-digest
  - input-validation
  - carrier-history
  - safe-retry
  - terminal-introduced-findings
  - anchor-annex
  - graphql-review-node-id
  - published-review-identity
---

# Review Exchange Terminal Manifest Construction

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | Deliver a terminal reviewer state through the designated terminal delivery helper on the first accepted submission. |
| **Outcome** | Operational rule derived from one live terminal GO delivery. Hand-written visible prose and a pretty-printed manifest were rejected by fail-closed input guards. Inputs rebuilt in the verified order were accepted, and the helper published the terminal carrier and the exclusive terminal label. A second delivery verified one more rejection class: a structural carrier-history rejection that no input repair can clear. A third delivery verified a self-referential case: the ledger, the state digest, and the entry set are mutually dependent, so the manifest converges by iteration and not by chained manual edits. A fourth delivery verified the terminal-introduced partition and the anchor annex: findings raised in the terminal round itself do not enter the closure entries, and supplementary anchor bytes ride after the ledger in an annex that the helper splits before its equality check. A fifth delivery verified the same class on a nonterminal state carrier: a no-go delivery binding a published proof review and an anchor annex was withheld twice at pre-publication input validation with no forge mutation, then accepted unchanged except for two corrected inputs — the published-review identity must be the GraphQL review node ID, and the anchor source must be supplied when the carrier carries a published annex. |
| **Verification** | verified-live in one zero-finding terminal GO delivery (2026-10-22), one adopted-native terminal GO delivery (2026-10-26), one findings-closure terminal GO delivery with a self-referential manifest (2026-10-26), one terminal GO delivery with terminal-introduced findings and an anchor annex (2026-10-26), and one nonterminal no-go delivery with an anchor annex whose initial submissions used the wrong published-review identity form (2026-10-28). Single-case evidence for each class; the invariants follow from deterministic fail-closed validation. |

## When to Use

Use this skill when these conditions apply:

- A review flow routes a terminal-eligible round (GO state, findings resolved) through a designated terminal delivery helper that consumes a schema-identified closure manifest.
- The helper rejects a manifest before publication with an input-validation error. Examples: the file is not canonical JSON; the terminal visible ledger does not match its manifest entries; a published-review identity is the decimal database review identifier instead of the GraphQL review node ID.
- You must decide what text goes into the manifest's terminal visible content field, and which digest goes into the reduce event's visible-content digest.
- You must classify a rejection: a pre-publication input rejection (fix the input and resubmit), a structural carrier-history rejection (no input repair exists; select a recovery under owner authority), or a publication-state wedge (stop; apply wedge recovery rules).
- A round-1 carrier adopted legacy review findings as `native:<provider-identifier>` identities, and the helper now rejects terminal delivery with an error that names an adopted native finding.
- The manifest has closure entries whose recorded state digest is the terminal digest itself, and every repair pass changes that digest again.
- The terminal review itself raises new findings (for example nonblocking findings on inline threads), and you must decide whether they enter the closure entries or a separate manifest partition.
- The terminal visible content must carry an anchor annex (supplementary anchor content) in addition to the deterministic ledger, and you must decide where the annex goes and which bytes the reduce digest binds.

The publisher-routing decision and wedge recovery are a different rule. See References.

## Verified Workflow

### Quick Reference

```text
1. Compute the deterministic terminal ledger with the terminal helper's own
   generator (binding, ordered closure entries). Never write it by hand.
2. Hash the exact ledger bytes into the reduce event's visible-content digest.
   Then reduce, then render. This order is mandatory: the state binds the digest.
3. Put the same exact ledger bytes in the manifest's terminal visible content.
   It must equal the ledger, not extend it: the helper compares for equality.
4. Serialize the manifest as canonical JSON (sorted keys, minimal separators),
   then deliver.
5. If entries record the terminal digest, steps 1-4 are circular. Iterate to a
   fixed point before delivery; do not chain manual digests.
6. An input-validation rejection is pre-publication: fix the input and
   resubmit. One form of this class is a published-review identity in the
   wrong form: supply the GraphQL review node ID (PRR_...), never the decimal
   database review identifier.
7. A rejection that names an adopted native finding is structural: no input
   repair exists. Hold for an owner-authorized resolution recovery or escalate.
8. Findings raised in the terminal round itself go in the manifest's comments
   and summary finding partitions, not in the closure entries. The helper's
   anchor proofs verify the partition.
9. An anchor annex is the final section after the ledger and its marker line.
   The helper splits the annex before the ledger-equality check, but the reduce
   digest binds the ledger bytes plus the annex bytes.
```

### Suggested Approach

1. Decide the publisher before this rule applies. Once the terminal round is routed to the designated helper, build its inputs in dependency order. The helper derives the visible terminal ledger deterministically from the binding and the ordered closure entries; hand-written prose cannot match it. Call the helper's own ledger generator, treat the output as opaque bytes, and reuse the identical bytes wherever the ledger is required.
2. Respect the digest order. The render step refuses a carrier whose visible-content digest does not equal the digest bound in the reduce event. So: compute the ledger, hash it, write the digest into the reduce event, reduce, render. Any edit to the visible content after reduce invalidates the state; recompute the ledger and reduce again.
3. Serialize the manifest file in the canonical byte form the exchange defines: UTF-8 JSON, sorted object keys, minimal separators. A pretty-printed document parses as JSON but fails the byte-level canonical-form check.
4. Check the helper's interface details against its actual signature. The positional argument is the review identity (number or URL), not a mode word. Requirement-issue flags belong to manifest-preparation mode, not to response-manifest delivery. When importing the helper in-process, reproduce its script entry-point module context so the helper's own module fallback resolves. When a delivery mode asks for the identity of an already-published review — for example the state-carrier proof review that a nonterminal no-go delivery binds — pass the GraphQL review node ID (form `PRR_...`), never the decimal database review identifier. The helper rejects a wrong form at pre-publication input validation and publishes nothing, so the identity fix is the only change a resubmission needs.
5. Triage rejections by class. An input-validation rejection proves nothing was published: correct the input and resubmit; retries are safe. A rejection that names a conflicting terminal review or a nonforking chain is a publication-state wedge: stop and apply the wedge rules; do not fix-and-retry. A rejection that names an adopted native finding is a third class, a structural carrier-history rejection: no input repair exists, and recovery acts on how the helper resolves the published carrier history. See the next subsection.

### Self-referential ledger and fixed-point convergence

The ledger build order becomes circular when the closure entries carry the terminal state digest. The helper hashes every entry into the visible ledger, and it removes a digest field only when that field already equals the current terminal digest. The terminal state, in turn, hashes the visible content, and the visible content is the ledger. Thus each pass over these three values can change the next one:

```text
ledger digest  <-  entries, including their state digest
state digest   <-  visible-content digest, which is the ledger digest
entry digest   <-  state digest
```

Chained manual repair does not converge. If you write a digest by hand, recompute the ledger, then re-reduce to bind the new ledger bytes, the terminal digest changes, so the entries and the ledger change again. Each hand edit starts a new cycle and no edit is final.

Resolve the cycle by iteration to a fixed point:

1. Hold the non-derivable inputs fixed: the prior state envelope, the assessment event with its findings and responses, the entry fields other than the state digest, and the requirements binding. Also fix the closure evidence and the author fields, because they are hashed too. Re-derive them from the verified state, not from memory: for a resolved finding, the closure evidence is the reviewer response evidence, not the author answer evidence.
2. Seed the visible content with the ledger from the current entries.
3. In one pass, hash the visible content into the event, reduce, set every entry's state digest to the reduced terminal digest, and recompute the ledger from those entries with the helper's own generator.
4. Compare the recomputed ledger bytes with the seed. If they are equal, you have the fixed point: write that ledger as the manifest terminal visible content and deliver.
5. If they differ, replace the seed with the recomputed ledger and repeat from step 3. Two passes usually suffice when the entry set is stable: one pass fixes the digests and one confirms them.
6. Confirm acceptance with the helper's own closure validator before delivery. It recomputes the ledger and checks every entry against the verified threads, so its acceptance is the proof of the fixed point.

Do not attempt to break the cycle by excluding an entry or by pasting a digest. Both actions change the hashed entry set, which restarts the cycle.

### Terminal-introduced findings and the anchor annex

The closure entries close findings that the exchange already tracks. A terminal review can also raise new findings in the terminal round itself, for example nonblocking findings recorded as new inline threads. These findings have no prior carrier history to close, so they do not enter the closure entries. They go in the manifest's separate partitions: the comments partition carries the response to each new thread, and the summary finding partition carries the summary finding identities. The helper verifies this partition with its anchor proofs before delivery, so a wrong partition fails pre-publication. At delivery the helper publishes the one terminal comment carrier, generates the responses to the new threads from the comments partition, resolves those threads, and applies the exclusive terminal-state label.

The terminal visible content can also carry an anchor annex: supplementary anchor content after the deterministic ledger. The annex is the final section, separated from the ledger by the annex marker line. The helper splits the annex before its equality check, so the ledger part still compares equal to the deterministic ledger. The reduce-event state digest binds the full bytes, ledger plus annex. Build in this order:

1. Compute the deterministic ledger with the helper's generator.
2. Append the annex as the final section after the marker line. Never place annex bytes before the ledger: the split starts at the marker, so anything before it compares as ledger and fails the equality check.
3. Hash the combined bytes (ledger plus marker plus annex) into the reduce event's visible-content digest. Then reduce, then render.
4. Pass the annex source to the delivery helper with its anchor-source option, so the delivery binds the same annex bytes that the digest binds.

### Structural carrier-history rejection

Round-1 carriers can adopt legacy review findings as `native:<provider-identifier>` identities, recorded with legacy markers of the form `exchange=<record> id=<F-NNN>`. When the helper did not derive the verified chain from that record, it rejects terminal delivery at preflight with an error such as `An adopted native finding has no unique matching review root: <selector>`, where the selector is the native identity. No manifest, digest, ordering, or ledger repair exists, because the rejection binds to published carrier history and not to pending input. Rebuilding and resubmitting the same content only repeats the identical error. A structural rejection can also mask later input-validation failures: only after the history resolution succeeds do the downstream input checks run.

Discriminate before you act:

- Input-validation errors name a malformed or mismatched pending input: JSON form, closure ledger, digest, or event shape. Fix the input and resubmit.
- Structural carrier-history errors name an adopted native finding. The repair extends verified-history resolution.
- Wedge errors name a conflicting terminal publication or a non-forking continuity break. Apply the wedge rules.

With owner authority for a helper extension, recover a claimed-markers case:

1. Preserve the stock helper byte-exact and record its checksum.
2. Extend only the resolution of legacy round-1 markers: accept a marker whose claimed identity is not used by the verified derived chain. Keep strict provenance for every marker the chain claims.
3. Rebuild the deterministic ledger so that it includes the adopted native findings as native-identity entries, regenerate the manifest, and re-reduce with the corrected visible-content digest.
4. Deliver with the patched helper. Then re-run the same input against the delivered state and require the idempotent already-delivered result.
5. Re-verify the delivered exchange with the stock helper. If the stock helper fails preflight, record the exact divergence and route the extension to the helper owner so later exchanges do not need the patch. Keep the byte-exact backup until the owner accepts the fix.

If the extension is not possible, hold the exchange and escalate through the declared surfaces with the error string and the native and claimed selector identities. Use reframe only on a real requirements delta. Never edit the published carrier history, and never retry an unmodified submission.

### If a step is unavailable

- An exchange generation without a deterministic-ledger binding: this rule does not apply. Record which visible-content convention the flow uses before the terminal round.
- No usable in-process import: run the helper's command-line entry point to produce inputs instead of importing its functions.
- A validation error not covered here: treat it as input construction until proven otherwise. Confirm with the forge readback that nothing was published before you resubmit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Hand-written prose as terminal visible content | Composed a detailed assessment report and used it as the manifest's terminal visible content | The helper rejected it: the terminal visible closure ledger does not match its manifest entries. The published body is deterministic over the binding and entries; prose cannot match | Generate the ledger with the helper's own generator. Detailed prose belongs in the user-facing report, never in the terminal visible content |
| Digest bound to prose before the ledger decision | Hashed the prose into the reduce event's visible-content digest, then learned the published body must be the deterministic ledger | The reduce output bound the wrong digest; continuing would fail at render or delivery. The fix required a new reduce with the correct digest | Compute the ledger first and bind its digest; the reduce event is not the place to discover the visible content |
| Prose prefixed to the ledger in the terminal visible content | Appended the deterministic ledger below the reviewer assessment report and used the combination as the terminal visible content | The helper rejected it: the terminal visible closure ledger does not match its manifest entries. The comparison is equality, not a suffix test, so any prose before the ledger fails it | The terminal visible content must be exactly the ledger bytes. The assessment report is a separate publication, not part of this field |
| Chained manual digest repair on a self-referential manifest | Wrote a corrected closure digest, recomputed the ledger, re-reduced to bind the new bytes, then set the entry digests to the new state digest | Every pass changed the terminal digest, so the entries and the ledger changed again. Each submission repeated the ledger-mismatch or evidence-mismatch rejection with a different digest | Iterate to a fixed point: re-derive the ledger from the recomputed entries in one pass and repeat until the bytes stop changing. Do not chain hand edits |
| Pretty-printed manifest JSON | Wrote the closure manifest with indentation for readability | The helper rejected it: the response manifest is not canonical JSON. It enforces the exchange canonical byte form, not JSON parseability | Serialize the manifest with the exchange canonical encoder (sorted keys, minimal separators) before delivery |
| Mode word as positional argument | Passed a mode word as the helper's positional argument | The parser treated the word as the review identity and failed | Read the helper's actual argument signature; the positional argument is the review identity (number or URL) |
| In-process import without entry-point context | Imported the helper module directly to reuse its ledger generator | A package-relative import failed in-process although the script entry point worked | Reproduce the script's module-loading context (empty package context) when importing, or use the command-line entry point |
| Rebuild and resubmit after a rejection that names an adopted native finding | Rebuilt the deterministic ledger with the adopted findings included, regenerated the manifest, and re-reduced with the corrected visible-content digest | The helper repeated the identical unique-review-root error at preflight, before any input check | The rejection binds to published carrier history, not to pending input; classify the rejection before you repair, or the fix-and-resubmit loop never ends |
| Editing the legacy markers on the published round-1 carrier | Considered rewriting the adopted-finding markers so the helper would accept them | Published exchange history is immutable under the exchange integrity rules | Repair verified-history resolution in the helper under owner authority; never rewrite published history |
| Supplementary anchor content merged into the ledger body without the annex marker | Combined reviewer prose and anchor content with the deterministic ledger in the terminal visible content, without the annex marker structure | The helper rejected it: the terminal visible closure ledger does not match its manifest entries. The helper splits an annex only after its marker; unmarked extra bytes compare as a ledger mismatch | Put supplementary anchor content after the annex marker as the final section, hash the combined ledger-plus-annex bytes into the reduce digest, and pass the annex source to the delivery helper |
| Decimal database identifier as the published-review identity | Bound the proof review of a nonterminal no-go delivery by its decimal database review identifier | The helper withheld delivery at pre-publication input validation and published nothing: no carrier, no label. The same submission with the GraphQL review node ID and the annex source supplied was accepted and delivered the exclusive state label | The published-review identity is the GraphQL review node ID (`PRR_...`), never the decimal database identifier; a withheld pre-publication rejection publishes nothing, so it is safe to correct and resubmit |

## Results & Parameters

### Configuration

```text
visible content   = terminal helper ledger generator(binding, ordered entries)  # opaque bytes
                  = the exact ledger bytes, never ledger + prose
reduce digest     = sha256(visible content)   # written into the reduce event before reduce
manifest field    = the same visible content bytes
manifest file     = canonical JSON: UTF-8, sorted object keys, minimal separators
closure evidence  = reviewer response evidence for a resolved finding
                  = author answer evidence when no reviewer response exists
                  = original finding evidence otherwise
self-reference    = entries carry the terminal digest
                  -> one pass: hash visible content, reduce, set entry digests,
                     recompute ledger; repeat until the ledger bytes are stable
retry decision    = input-validation rejection          -> fix input, resubmit (safe: pre-publication)
                  = adopted-native-finding root error   -> structural: hold; owner-authorized
                                                             resolution recovery or escalate
                  = conflicting-terminal / chain error  -> stop; apply wedge recovery rules
terminal-introduced = comments partition + summary finding partition
                  # never closure entries; the anchor proofs verify the partition
annex             = final section after the ledger and the annex marker line
                  # helper splits it before the ledger-equality check
reduce digest     = sha256(visible content)             # ledger only, no annex
                  = sha256(ledger + marker + annex)     # when an annex is used
delivery          = pass the annex source with the delivery anchor-source option
review identity   = pull-request number or URL        # positional argument
                  = GraphQL review node ID (PRR_...)  # published-review identity,
                                                      # e.g. a no-go proof review
```

### Expected Output

- The reduce step accepts the event; the render step produces the state carrier with no digest mismatch.
- The helper publishes exactly one terminal COMMENT carrier at the exact head, applies the exclusive terminal-state label, and closes the authorized fixture set. An independent forge readback shows the published ledger and its closure digest.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal repository review flow | Terminal GO delivery for a single-file installer fix; zero-finding round 1 at the exact head; two manifest submissions rejected on input validation, the third accepted and read back from the forge | [notes](review-exchange-terminal-manifest-construction.notes.md) |
| An internal repository review flow | Terminal GO delivery for a round that adopted legacy findings as native identities; one structural preflight rejection resolved by an owner-authorized helper extension and a rebuilt ledger; delivered at the exact head with the exclusive terminal label and an idempotency re-check (2026-10-26) | [notes](review-exchange-terminal-manifest-construction.notes.md) |
| An internal repository review flow | Terminal GO delivery that closed three findings under the terminal state digest; the manifest converged by fixed-point iteration in two passes after chained manual edits failed; accepted by the helper's closure validator, delivered at the exact head, all threads closed (2026-10-26) | [notes](review-exchange-terminal-manifest-construction.notes.md) |
| An internal repository review flow | Terminal GO delivery carrying findings raised in the terminal round itself: two inline nonblocking threads and one summary finding partitioned into the comments and summary partitions, verified by the anchor proofs; an anchor annex appended after the ledger with the combined bytes bound in the reduce digest; two pre-publication input rejections repaired, delivered with the exclusive terminal label and zero pending threads (2026-10-26) | [notes](review-exchange-terminal-manifest-construction.notes.md) |
| An internal repository review flow | Nonterminal no-go delivery binding a published state-carrier proof review and an anchor annex: two submissions withheld at pre-publication input validation with no carrier or label mutation; the accepted submission corrected only the review-identity form to the GraphQL node ID and supplied the annex source, delivered the exclusive state label, and read back clean (2026-10-28) | [notes](review-exchange-terminal-manifest-construction.notes.md) |

## References

- [review-exchange-terminal-carrier-sole-publisher](review-exchange-terminal-carrier-sole-publisher.md) — the publisher-routing decision and wedge recovery. Apply it before this construction rule, and whenever a rejection is publication-state (conflicting terminal review, nonforking chain) rather than input validation.
