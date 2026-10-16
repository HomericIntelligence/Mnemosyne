# Notes: Review Exchange Assessment Canonical Response Order

Privacy-safe supporting detail for `review-exchange-assessment-canonical-response-order`.
Identifiers from the source incident (repository, pull request, review, and digest values)
stay out of this record. Git provenance keeps the authoring context.

## Source case (2026-10)

A three-round, chain-verified pull-request review exchange with 31 ledger findings
reached a verified terminal GO state. The terminal delivery helper rejected the exchange:

> The terminal state does not have one complete persisted event chain.

Local replication of the delivery helper's chain replay showed:

- The genesis link replay was clean.
- The terminal link replay was clean: exactly one accepted candidate, no stop reason.
- The round-2 link failed under every accepted stop-reason variant of canonical event
  inference (all six variants produced the same canonical digest, which differed from
  the published link digest).

Root cause: the round-2 reviewer assessment event was submitted with its finding
responses in completion order. One partially resolved finding had its response appended
after the responses that follow it in the ledger. The exchange tooling serializes the
assessment event exactly as submitted; canonical inference normalizes the same content
into ledger order. The two orders produce different state digests, so the published
link is unreachable from canonical replay. The ledger content of the event was correct;
only its serialization order was wrong.

## Eliminated repair paths (all checked against the installed tooling)

| Path | Result |
| ---- | ------ |
| Retry terminal delivery with the same manifest | Deterministic fail-closed rejection at the round-2 link; no state change between attempts |
| Supersession (override terminal report) | Collides with the multiple-derived-successors guard: a successor state already exists for the terminal parent |
| Reframe | The exchange requirements were unchanged; a reframe for a complete state without a requirements delta fabricates protocol state |
| Replacement exchange id | Fails the foreign-thread gate (threads belong to the original exchange) and the closure-source-digest gate |
| Legacy override that skips chain verification | Category violation: the defect is a publication defect, not a legacy-format artifact |
| Batch/stream republication | The broken link is upstream of any new tip; adding links cannot repair it |
| Deleting the published round reviews | Violates review immutability; not an authorized operation |

## Completed recovery (owner-directed)

1. Root-cause report to the owner with the per-link replay evidence and the choices
   (human completion or hold).
2. On the owner's direction, the terminal review carrier was verified against its
   envelope digest and published as a COMMENT review at the exact head.
3. One closure reply per finding thread (31), generated from the same deterministic
   closure-ledger manifest the helper would have used, then all threads resolved.
4. The stale exclusive NO-GO label was replaced with the terminal GO label.
5. One disclosure comment recorded the defect, the unreachable link, the evidence
   that the review rounds were complete, and the human authority for the completion.
6. The documented merge gates (signed commits, green required checks at the exact
   head, the recorded exact-head review chain) were left as the owner's merge record.

## Durable checks worth repeating

- The digest gate at step 3 of the workflow needs only the delivery helper's canonical
  inference and the candidate event; it costs seconds and prevents the permanent wedge.
- An artifact revision change refreshes the whole ledger: a correction commit requires
  revalidation responses for every terminal required finding, in ledger order, not only
  for the findings that the correction touched.
- Per-link replay is the fastest diagnosis for an incomplete-chain error: clean
  terminal + unreachable mid-chain link with correct content is the signature of a
  publication-order defect.
