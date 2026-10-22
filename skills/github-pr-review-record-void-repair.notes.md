# Notes: github-pr-review-record-void-repair

Supporting session evidence (privacy-safe summary; identifiers, digests, repository
names, and account names withheld). All observations are from one live fleet run on
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
