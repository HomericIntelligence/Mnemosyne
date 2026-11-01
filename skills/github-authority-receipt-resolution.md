---
name: github-authority-receipt-resolution
description: "Make an authority receipt resolve to exactly one forge record during exchange delivery. Use when: (1) a reframe, rebind, or terminal delivery must reference a published authority record and the delivery helper rejects the reference, (2) the helper reports that the authority receipt does not resolve to one forge record, (3) the record was published as an issue comment on the pull-request conversation stream, (4) the record is referenced by a decimal REST identifier instead of a GraphQL node identifier, or (5) a record already published on a non-resolving surface must move to a resolvable surface with its bytes unchanged."
category: tooling
date: 2026-10-31
version: "1.0.0"
user-invocable: false
tags:
  - github
  - review-exchange
  - authority-receipt
  - reframe-authority
  - graphql-node-id
  - byte-exact
  - append-only
  - publication-ordering
---

# Resolve an Authority Receipt to One Forge Record

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-31 |
| **Objective** | Publish an authority record on a forge surface that delivery tooling can resolve, and reference it so the reference names exactly that record. |
| **Outcome** | Operational rule from one live authority-transition delivery. A receipt that failed resolution from the conversation stream and by decimal identifier resolved after republication as a review with identical bytes and a GraphQL node-identifier reference. Byte identity kept the record digest unchanged, and the receipt kept its bound position in the carrier chain. |

An authority receipt is the published record of the authority for an exchange
action: an owner's approval of a new exchange, or the record of a real
requirements change. Downstream delivery helpers do not read prose. They resolve
the receipt to a forge record by identity, and they fail closed when the
reference does not name exactly one record on a scanned surface.

## When to Use

- A reframe, rebind, or terminal delivery needs an authority receipt, and the
  receipt reference must resolve at delivery time.
- The delivery helper rejects the receipt with a resolution diagnostic, for
  example "The authority receipt does not resolve to one forge record."
- The record was published as an issue comment on the pull-request
  conversation stream.
- The reference names the record by a decimal REST identifier.
- A record already published on a non-resolving surface must become resolvable
  without changing its content.

## Verified Workflow

### Quick Reference

```text
Receipt surface:     a pull-request review, or a reply on a review thread.
                     Issue comments on the conversation stream are not scanned.
Receipt reference:   review:<GraphQL node identifier>
                     comment:<GraphQL node identifier>
                     Decimal REST identifiers do not resolve.
Resolution failure:  "The authority receipt does not resolve to one forge record."
Relocation:          one exact-byte write of the prepared canonical body as a review;
                     compare digests computed from raw JSON bodies
Ordering:            keep the receipt inside its bound window (after the superseded
                     carrier, before the terminal carrier)
Append-only:         a record on a non-resolving surface stays in place, documented;
                     relocation adds a record, it does not move or edit one
```

### Suggested Approach

1. Publish the receipt on a scanned surface the first time. On a pull-request
   artifact, the receipt resolver reads review objects and review-thread
   comments. A review with the record as its body always resolves; a reply on a
   review thread also resolves. The conversation stream outside review objects
   (issue comments) is outside the scan, however visible it is to people.
2. Reference the record by its GraphQL node identifier. Read the node
   identifier from the forge API response for the write that published the
   record. The form is `review:<node identifier>` for a review and
   `comment:<node identifier>` for a review-thread comment. Decimal REST
   identifiers are a different key space; the resolver does not match them.
3. Diagnose a resolution failure in this order: surface first, then identifier
   form. The same rejection message covers both causes, so check where the
   record lives before you check how the reference spells its identity.
4. Relocate a published record by republication, never by edit. Publication
   channels are append-only: the original record stays in place and is
   documented, and the relocation adds one new review. Write the prepared
   canonical body in one exact-byte call. The forge stores submitted review
   bodies byte-exactly, so identical input bytes give an identical record
   digest, and every downstream digest comparison still passes. Compute the
   readback digest from the raw JSON body, not from a formatter's output:
   common CLI JSON formatters append one trailing newline and change the byte
   count.
5. Satisfy the ordering window. When the exchange binds the receipt's position,
   publish the resolvable copy inside the same window; a typical window is
   after the superseded carrier and before the terminal carrier. A receipt
   outside its window can resolve and still fail a chain-order check.
6. If the write capability is unavailable, hold the delivery and keep the
   prepared exact bytes as the retry artifact. Do not approximate the body by
   retyping it; a changed byte changes the digest and breaks the receipt's
   digest binding.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Receipt on the conversation stream | Published the authority record as an issue comment on the pull request, and referenced it from the delivery input | The delivery helper's receipt resolver scans reviews and review-thread comments only; resolution failed with "The authority receipt does not resolve to one forge record" | Publish the receipt as a review or a review-thread reply; visibility to people is not resolution by tooling |
| Decimal identifier in the reference | Referenced the receipt record by its decimal REST identifier | The resolver matches GraphQL node identifiers; the decimal form is a different key space and did not resolve | Use the GraphQL node identifier of the published record, read from the forge API response of the publishing write |

## Results & Parameters

### Configuration

```text
receipt surface        -> pull-request review | review-thread reply
rejected surfaces      -> issue comment on the conversation stream
receipt reference      -> review:<GraphQL node id> | comment:<GraphQL node id>
rejected references    -> decimal REST identifier
resolution diagnostic  -> "The authority receipt does not resolve to one forge record."
relocation             -> one exact-byte write as a review; original record stays in place
digest verification    -> raw JSON body on both sides; formatters append a newline
ordering window        -> after the superseded carrier, before the terminal carrier
```

### Expected Output

- The receipt reference resolves to exactly one forge record, and the delivery
  proceeds past receipt validation.
- The readback digest of the republished record equals the digest of the
  original record.
- The original record on the non-resolving surface stays in place, documented
  as relocated; no published record is edited or withdrawn.
- The receipt holds its bound position: after the superseded carrier and
  before the terminal carrier.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Internal review-exchange delivery | Authority transition to a new exchange after a delivered terminal state: the receipt first failed resolution from the conversation stream and by decimal identifier, then resolved after byte-exact republication as a review with a node-identifier reference; digest preserved, ordering held | [notes](github-authority-receipt-resolution.notes.md) |

## References

- [review-exchange-terminal-manifest-construction](review-exchange-terminal-manifest-construction.md) — binds a published review's identity inside a delivery manifest field. That rule governs a manifest input; this entry governs the receipt record's own surface, reference, and relocation.
- [review-exchange-head-refresh-carrier-repair](review-exchange-head-refresh-carrier-repair.md) — the reframe-authority prerequisites and the publish-the-record-once rule that this entry's surface and reference forms make executable.
- [review-exchange-terminal-carrier-sole-publisher](review-exchange-terminal-carrier-sole-publisher.md) — sole-publisher and publish-order constraints around terminal rounds; the ordering window in this entry inherits them.
- [forge-exact-byte-comment-publication](forge-exact-byte-comment-publication.md) — the exact-byte write and readback discipline for issue comments. Apply the same byte discipline to reviews when relocating a receipt.
