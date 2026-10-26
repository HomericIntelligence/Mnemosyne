# Notes: review-exchange-terminal-manifest-construction

Supporting evidence for the main skill. Generalized from two live deliveries;
identifiers are omitted under the privacy rules.

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

## Evidence limits

Two single live cases, one exchange tooling generation. The invariants (digest
order, deterministic visible body, canonical manifest form, rejection-class
triage, structural carrier-history rejection) follow from the fail-closed
validator design and do not rest on frequency. Interface details (positional
argument, mode flags, import context) are generation-specific witnesses;
confirm them against the installed helper's signature before relying on them.
