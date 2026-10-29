---
name: github-pr-review-record-void-repair
license: BSD-3-Clause
description: "Repair a submitted GitHub pull-request review record without deletion. Automation cannot delete a submitted review, so void it in place with a PUT body edit that removes its machine-parseable carrier, then repost the replacement review byte-identically in one call. Use when: (1) an automation-published review holds a malformed, superseded, or junk machine carrier that a body-scanning toolchain must stop seeing, (2) a delete of a submitted review fails on every transport, (3) a review body must be reposted with byte identity so recorded content digests still bind, (4) a same-head duplicate or malformed terminal carrier wedges a fail-closed delivery gate, or (5) a racing lane re-posts a byte-identical copy of an older state carrier and the fail-closed whole-history duplicate-state scan wedges terminal and non-terminal delivery with a duplicate reviewer state message error."
category: tooling
date: 2026-10-25
version: "1.2.0"
user-invocable: false
verification: verified-live
tags:
  - github
  - pull-request-reviews
  - forge-api
  - record-repair
  - tombstone
  - carrier
  - gh-api
  - automation
  - immutable-records
---

# GitHub PR Review Record Void Repair

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Remove a malformed, superseded, duplicate, or junk machine carrier from a submitted GitHub pull-request review without deleting the forge record, and repost a replacement that byte-identical toolchain digests still bind. |
| **Outcome** | Successful across three record repairs in one fleet run, plus a second-run whole-history duplicate-state design: both delete transports refused (REST 422, GraphQL UNPROCESSABLE); a PUT body edit removed each carrier from the machine-visible chain; byte-identical single-call reposts kept every recorded content digest valid. |
| **Verification** | verified-live on three executions (one long authority event, one junk review, one wedge-remedy design validated against a fail-closed helper's skip rules), plus a whole-history duplicate-state variant design-validated against the same helper's observed duplicate-scan error text and skip rules — the variant is diagnosed on live forge state, not yet executed. Single-session evidence per run; each primitive was observed on the live forge before use. |

## When to Use

- An automation stack publishes pull-request **reviews** (not issue comments) whose bodies carry a structured machine carrier (JSON fence, marker comment), and a body scanner consumes them.
- A published review must be superseded, migrated, or removed from that machine-visible chain: malformed carrier, race-posted duplicate, superseded authority event, or junk review from a wrong API call form.
- A delete on the review fails: review deletion is not available to automation once the review is submitted (see Failed Attempts).
- A fail-closed delivery gate rejects a second publication while a same-head, same-round carrier already exists and cannot be finalized (for example, a well-formed carrier whose visible body is not the deterministic terminal form).
- **A whole-history duplicate-state scan wedges an artifact's delivery lane**: a racing automation lane re-posted a byte-identical copy of an older review record, two parseable copies of one state digest now exist in the full review history, and the fail-closed scanner rejects every later delivery attempt with a duplicate-state error — including attempts whose own digests are unique. Only a full-history enumeration (not a same-head filtered list) surfaces this failure class.
- A replacement must keep recorded content digests valid (chains that bind `sha256` of the visible body).

Do not use this for: issue comments (deletable and editable without these constraints), unsubmitted pending review drafts (the UI and API can discard those), or rewriting a foreign record's content (authority required; see Suggested Approach step 5).

## Verified Workflow

### Quick Reference

```bash
# 1. Void in place (PUT, not PATCH). The tombstone body removes every
#    machine-parseable fence/marker and adds a short human void note.
gh api repos/<OWNER>/<REPO>/pulls/<PR>/reviews/<REVIEW_ID> -X PUT -F body=@tombstone.md

# 2. Repost the replacement in ONE call. -F expands the file; --raw-field sends literal text.
gh api repos/<OWNER>/<REPO>/pulls/<PR>/reviews -X POST \
  -F commit_id=<HEAD_SHA> -F event=COMMENT -F body=@carrier.md -f comments='[]'
```

### Suggested Approach

1. **Confirm the primitive before you rely on it.** Do not attempt delete as the primary path and do not retry delete variants: for a submitted review, REST `DELETE` returns 422 and GraphQL `deletePullRequestReview` returns UNPROCESSABLE even with an admin-scoped token. Body edit is the only available mutation: REST `PUT /repos/{owner}/{repo}/pulls/{n}/reviews/{id}` with a JSON `body` field. The review state (`COMMENTED`/`APPROVED`/`CHANGES_REQUESTED`), commit binding, timestamps, author, and attached threads persist.
2. **Compose the tombstone minimally.** Remove every byte sequence the consuming toolchain scans for (carrier fence, marker comment). Keep a short human-readable void note: what was voided, why, and the identifier of any replacement record. The tombstone keeps the human audit trail; the toolchain's scanner skips bodies without the fence (verify the scanner's documented skip rule before you rely on this).
3. **Repost byte-identically, once, when digests bind the content.** Compose the full replacement body first. `-F body=@file` expands file content; `--raw-field` sends the literal string. Post with the complete body in the single create call: a later edit marks the record edited, and chain verifiers that recompute visible-content digests reject edited or divergent carriers. When nothing machine-visible must survive (a junk review), skip the repost.
4. **Verify the repair.** Read back: the tombstone body is live, the replacement appears exactly once, the scanner skips the void and parses the replacement, and all other review fields are unchanged. When you compare body bytes, remember that `gh api --jq .body > file` appends one trailing LF; strip exactly one final LF before byte-identity checks against a strict parser.
5. **Keep authority explicit.** Voiding a record published by a different automation session is a record repair, not an assessment: bind an explicit owner or task decision before the PUT. Never rewrite foreign content; tombstone only, and let the repost carry the replacement.
6. **Wedge-remedy branch.** When a fail-closed helper refuses terminal delivery because a same-head, same-round carrier exists but cannot be finalized, and chain history forbids a second carrier, void-tombstone plus canonical re-delivery is the only non-forking record repair. The alternative is to park the artifact for an owner disposition; do not post a second carrier and do not falsify a non-terminal carrier to force a label.
7. **Whole-history duplicate-state variant.** When the wedge is two parseable copies of one state digest (a racing lane re-post, or a second copy of a record that an earlier void failed to cover), no repost is needed for that state: its content is already on the artifact. Tombstone every duplicate copy so exactly one parseable record per digest remains. Voiding a racing lane's copy is a foreign-record repair and requires explicit owner or task authority first (step 5). Do not repost the duplicated state again — a third copy re-arms the same scan. Verify by replaying the scanner over the full review history: one parseable record per digest, zero duplicate-state errors, and later unique-digest deliveries accepted.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Delete a submitted review over REST | `DELETE /repos/{o}/{r}/pulls/{n}/reviews/{id}` with admin-scoped token | 422 Unprocessable Entity | Submitted reviews are immutable to deletion over automation; plan the PUT edit |
| Delete over GraphQL | `deletePullRequestReview` mutation | UNPROCESSABLE | The limit is the record state, not the transport; do not retry delete variants |
| Edit the original carrier body to fix it in place | PUT a corrected carrier over the established one | Chain verification rejects edited carriers when recorded digests bind the original bytes | Void + byte-identical repost preserves digests; in-place edits do not |
| PUT the body-edit endpoint with a `/body` path suffix | `gh api -X PUT repos/<o>/<r>/pulls/<n>/reviews/<id>/body -F body=@tombstone.md` | HTTP 404; the operator then classified the review as uneditable and left a junk record in place | The reviewed edit endpoint has no `/body` suffix; a 404 from the suffix form is a wrong-path signal, not evidence that review bodies are immutable |
| Report a duplicate-state wedge as permanently blocked | Classified the artifact's delivery as unwedgable without enumerating full review history, assuming only a same-head scan ran | The duplicate-state scan covers the artifact's full review history; a racing lane's byte-identical re-post of an older digest wedges every later delivery, and parked record pairs survive carrier enumeration tombstones | Enumerate the full history, identify the duplicate-digest pair, and tombstone the copies: the repair needs no new carrier and no fork |

## Results & Parameters

### Configuration

```yaml
record_class: submitted pull-request review (COMMENT / APPROVE / CHANGES_REQUESTED state)
delete_available: false            # REST 422, GraphQL UNPROCESSABLE
body_edit:
  method: PUT                      # not PATCH
  endpoint: /repos/{owner}/{repo}/pulls/{n}/reviews/{id}
  suffix_form: "/reviews/{id}/body returns 404 on the observed surface; not the reviewed edit endpoint"
  preserves: [state, commit_id, submitted_at, author, threads]
tombstone:
  contains: [human void note, replacement-pointer]
  must_not_contain: [carrier fence, marker comment]
repost:
  body_flag: -F body=@file         # expands file content
  literal_flag: --raw-field        # sends literal text; wrong for bodies from files
  call_count: 1                    # compose fully; a later edit triggers edited-carrier rejection
readback_artifact: gh api --jq .body appends one trailing LF; strip exactly one LF for byte checks
```

### Expected Output

- The tombstone is live on the voided review identifier, fence-less, and is skipped by the body scanner.
- The replacement review exists exactly once, binds the intended head, and parses under the strict rules.
- No review field other than the tombstone body changed; authority for the repair is on record.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A private GitHub monorepo pull-request fleet | Three record repairs in one run during a multi-artifact review drive | Session evidence with counts and receptor behavior in [notes.md](../skills/github-pr-review-record-void-repair.notes.md) |

## References

- [GitHub REST API: pull request reviews](https://docs.github.com/en/rest/pulls/reviews)
- [review-exchange-terminal-carrier-sole-publisher.md](review-exchange-terminal-carrier-sole-publisher.md) — terminal-publisher routing and the wedge decision family this repair serves
- [review-exchange-assessment-canonical-response-order.md](review-exchange-assessment-canonical-response-order.md) — canonical carrier construction that prevents malformed carriers
- [pr-review-carrier-prepublication-enumeration.md](pr-review-carrier-prepublication-enumeration.md) — full artifact record enumeration; the scan class that surfaces a whole-history duplicate-state pair
