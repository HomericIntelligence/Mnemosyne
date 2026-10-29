# Notes: github-pr-review-record-void-repair

Supporting session evidence (privacy-safe summary; identifiers, digests, repository
names, and account names withheld). Observations are from two live fleet runs on
GitHub against submitted pull-request reviews authored by the automation account.

## Case 1 — superseded long authority event (void + byte-identical repost)

- A ~17 KB review body carried a superseded machine authority event whose visible-content
  digest was recorded in a verified chain. The chain required the original bytes back under
  a new record identity.
- REST `DELETE`: HTTP 422, twice (different call forms), admin-scoped token.
- GraphQL `deletePullRequestReview`: UNPROCESSABLE.
- PUT body edit: accepted; only the body changed (state, commit binding, timestamps,
  author, threads persisted). The chain-scanning helper was observed to skip the
  fence-less tombstone.
- Byte-identical repost posted in one call: chain verify passed; the new record bound the
  same head and digest set. No edit flag present.

## Case 2 — junk review (void, no repost)

- A ~25-byte carrier-less body was posted by a wrong flag form (`--raw-field` instead of
  `-F body=@file`). Nothing machine-visible had to survive, so a single PUT tombstone was
  the complete repair. Zero downstream references.

## Case 3 — wedge-remedy design (validated, withheld pending owner decision)

- A well-formed state carrier at the exact review head was well-formed for the parser but
  non-canonical for the fail-closed terminal helper (visible body not the deterministic
  closure ledger). The helper's nonforking-chain guard rejected a second same-head carrier.
- The validated remedy design: PUT-tombstone the carrier (scanner skip), then deliver the
  canonical terminal carrier as the chain's only visible state record. Alternative branch:
  park for an owner disposition. Executed branch: parked (owner decision withheld in that
  instance).

## Transport and client facts observed

- `gh api -F body=@file` expands the file into the field; `--raw-field body=...` sends the
  literal characters. A literal `@file` under `--raw-field` was the Case-2 root cause.
- `gh api --jq .body > file` appends one trailing LF. A strict parser that requires the
  carrier fence to be the final body element then reports `malformed or not final`.
  Removing exactly one final LF restores strict acceptance — a readback artifact, not a
  forge mutation.
- The review body edit endpoint is `PUT /repos/{owner}/{repo}/pulls/{n}/reviews/{id}`.
  `PATCH` on the same path is not the documented form and was not used.

## Related in-flight corpus work at discovery time (2026-10-22)

This lesson's duplicate discovery enumerated every open knowledge PR. Two adjacent
open PRs cover carrier *parser* recovery, digest recomputation, head-refresh rebind, and
closure-manifest construction. Neither covers the forge record primitives here
(delete-unavailability, PUT body edit, void tombstone, byte-identical repost). One
existing entry covers terminal-publisher routing and wedge disposition decisions; this
entry supplies the record-repair mechanics that serve a repair-oriented disposition.

## Case 4 — suffix-form PUT 404 read as immutability (observed 2026-10-25)

- A coordinator repairing a wrong-form junk review (a `-f body=@path` post that stored
  the literal path as the review body; same root-cause family as Case 2) issued the PUT
  against `/pulls/{n}/reviews/{id}/body` and received HTTP 404.
- Deletion was already known unavailable, so the operator concluded that no mutation path
  existed and left the junk record in place, recording it as permanent noise.
- Recheck against this entry produced the correct diagnosis: the suffix form is not the
  endpoint. The reviewed body edit uses the review resource path itself; the 404 was a
  wrong-path signal, not immutability evidence.
- The transport note in this entry already gives the correct path; this case records
  the operator trap (doc-memory of a suffix form) so it is not repeated.

## Case 5 — whole-history duplicate-state wedge (diagnosed 2026-10-28; remedy withheld for authority)

- A fail-closed delivery helper rejected a terminal record whose own digest was unique,
  citing a duplicate reviewer state in the round history. A same-head, same-round
  enumeration showed no duplicate carriers.
- Enumerating the artifact's *full* review history surfaced the cause: a racing
  automation lane under the same shared identity had re-posted byte-identical copies of
  each of two older round records. Every one of those older digests then had exactly two
  parseable copies, and the whole-history duplicate-state scan rejected all later
  delivery attempts regardless of their own digest uniqueness.
- Earlier enumeration tombstones in the same history (fence-less junk records, Case-4
  class) did not trigger the scan — confirming that the scan keys on parseable carrier
  bodies, and that a fence-less record is invisible to it.
- Validated remedy design: tombstone every duplicate copy (no repost — each duplicated
  state's content is already on the artifact, and any new copy would re-arm the scan as
  a third identical record). After the repair the history holds one parseable record
  per digest and the fail-closed gate re-opens. No exchange fork: later rounds consume
  the latest accepted reviewer state, which the repair does not remove.
- Not executed: the duplicate copies are foreign-lane records and explicit owner or
  task authority for their repair was not held. The wedge was reported per
  stop-and-report and parked for an owner disposition.
- Operator trap recorded: the wedge was first classified as permanently blocked with
  "repair unresolved". Full-history enumeration plus this entry's skip rule shows it is
  remediable with tombstones alone — no new carrier, no fork, and no helper change.
