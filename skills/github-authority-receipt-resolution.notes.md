# Notes: github-authority-receipt-resolution

Supporting evidence for the main skill. Generalized from one live delivery;
identifiers are omitted under the privacy rules.

## Delivery chronology (2026-10-31)

1. A review exchange on a pull-request artifact had reached a delivered
   terminal state. A materially changed requirement authorized a reframe, so a
   new exchange identity started at round 1 and needed a fresh authority
   record.
2. The authority record was prepared and published, but the delivery helper
   rejected the receipt reference with the literal "The authority receipt does
   not resolve to one forge record."
3. Two causes were identified in the same delivery: the record lived on the
   pull-request conversation stream (an issue comment), and a reference
   variant used a decimal REST identifier. Both are outside the helper's
   resolution key space; the same rejection message covers both.
4. The helper's resolution rule, read from its interface: it scans review
   objects and review-thread comments on the pull request and matches GraphQL
   node identifiers. Issue comments and decimal REST identifiers never
   resolve.
5. Relocation: the identical canonical record was published again as a pull
   request review, in one exact-byte write, inside the bound ordering window —
   after the superseded carrier and before the terminal carrier. The reference
   used the new review's GraphQL node identifier in the `review:` form.
6. Readback verification compared the republished review's body with the
   original prepared record. The digests matched, which confirmed that the
   forge stored the submitted body byte-exactly and that the record digest was
   preserved across relocation. The delivery then passed receipt validation
   and completed: terminal review published, threads closed, exclusive state
   label applied.
7. The original record on the conversation stream stayed in place, documented
   as relocated. Publication channels are append-only; nothing was edited or
   withdrawn.

## Byte-format observations

- The forge stores submitted review and comment bodies byte-exactly. Digest
  comparisons must parse the raw JSON body of the readback. Common CLI JSON
  formatters append one trailing newline to their output, which changes the
  byte count and breaks an equality check that uses formatted output.
- Empty COMMENTED review records can appear after a terminal review as forge
  wrapper records for GraphQL thread replies. Chain validation ignored them in
  the observed delivery; they are not carriers and not receipts.

## Limits

- Evidence comes from one delivery on one helper generation. A helper that
  accepts other receipt surfaces or reference forms may exist; read the
  installed helper's resolution rule before you generalize in the other
  direction.
- Relocation by republication adds a second record. It keeps every digest and
  the ordering window, but the receipt now has two published copies; the
  resolvable one is the record of authority, and the original is documentation.
- The ordering window in this delivery bound the receipt between two carriers.
  Other exchanges may bind no position; the window rule then does not apply.

## Privacy note

Source identifiers (organization, repository, pull request, review and comment
identifiers, digests) are deliberately omitted. The rules are stated against
the general mechanism.
