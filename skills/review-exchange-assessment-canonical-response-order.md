---
name: review-exchange-assessment-canonical-response-order
description: "Publish review-exchange assessment events with their finding responses in canonical ledger order, and verify the reduced state digest before publication. Use when: (1) an author or reviewer relayer assembles an assessment event for a chain-verified review exchange, (2) terminal delivery fails with an incomplete persisted event chain although every round review exists and the terminal link replays cleanly, or (3) a post-publication mid-chain digest mismatch forces a choice between repair attempts and owner completion. A published mid-chain event with non-canonical response order is unreachable from canonical event inference and permanently blocks mechanical exclusive terminal delivery for the exchange."
category: tooling
date: 2026-10-15
version: "1.0.0"
user-invocable: false
tags:
  - pr-review
  - review-exchange
  - assessment-event
  - canonical-order
  - ledger-order
  - state-digest
  - chain-replay
  - fail-closed
  - terminal-delivery
  - wedge
  - owner-override
  - escalate-not-retry
  - publish-order
---

# Review Exchange Assessment Canonical Response Order

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-15 |
| **Objective** | Keep every published link of a review-exchange event chain replayable: submit finding responses in canonical ledger order and verify the reduced digest before publication. |
| **Outcome** | Operational rule derived from one live three-round exchange. The round-2 assessment event was published with its finding responses in completion order instead of canonical ledger order. The published link became unreachable from canonical event inference, and terminal delivery failed with an incomplete persisted event chain. An owner-directed human completion closed the exchange. |
| **Verification** | verified-live in one three-round exchange (2026-10): every published round review was present, the terminal link replayed cleanly, and the mid-chain link was unreachable under every accepted inference variant. Single-case evidence; the invariant follows from the fail-closed design. |

## When to Use

- You assemble a reviewer or author assessment event for a chain-verified review exchange. The event carries one response for each ledger finding.
- An artifact revision change requires you to revalidate earlier findings, and you are tempted to append the late responses after the current ones.
- Terminal delivery rejects the exchange with an incomplete-chain error. Every round review exists on the pull request, and replaying the terminal link alone succeeds.
- You must select a recovery for a published order defect: helper retry, supersession or reframe, a replacement exchange, a legacy override, deletion of published carriers, or owner human completion.

## Verified Workflow

### Quick Reference

```text
Response order in an assessment event == the exchange ledger order of the findings.
Never submit completion order, review order, or hand-assembled order.
Before publication, reduce the event with the delivery helper's canonical inference.
Publish only when the reduced state digest equals the digest you will publish.
```

### Suggested Approach

1. Derive the response order from the ledger, not from the response set. The canonical order is the order in which the exchange ledger lists the findings: each finding at its introduction position. Late revalidation responses take the ledger position of their finding, not the end of the list.
2. Generate, do not assemble. Build the response set with the exchange tooling's own ledger or manifest builder. Do not append late responses to an earlier list. An artifact revision change refreshes the whole ledger; regenerate the complete ordered set.
3. Gate publication on the digest. Reduce the event with the same canonical inference that terminal delivery uses. Publish only when the produced state digest equals the digest that the publication binds. A mismatch means the serialized event is not the canonical one.
4. Diagnose an incomplete-chain failure by link. Replay each chain link separately. A mid-chain link whose published digest is unreachable under every inference variant, while its ledger content is correct, marks a non-canonical publication order. A terminal link that replays cleanly confirms that the defect is mid-chain, not in the terminal state.
5. Do not retry or fabricate a repair after publication. Published reviews are immutable. A supersession or reframe carrier collides with the multiple-derived-successors guard. A replacement exchange id fails the foreign-thread and closure-source-digest gates. A legacy override that skips chain verification changes its failure category. Deleting carriers violates review immutability. None of these paths restores mechanical delivery.
6. Complete under owner authority. Record the defect, the unreachable link, and the evidence that the terminal state is correct: fresh-context verifier rounds and green required checks at the exact head. With explicit owner direction, publish the terminal review, close the finding threads, and set the exclusive state label directly. Publish one disclosure note as the provenance. The merge stays an owner decision on the documented gates.

### If a step is unavailable

- No local reducer before publication: hold the publication. A delayed round is recoverable; a non-canonical published link is not.
- No owner authority for human completion: hold the exchange open and escalate with the per-link replay evidence. Do not test the remaining exit paths one by one; the guards are deterministic.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Append the late response | The round-2 assessment responses were submitted in completion order: the response for one partially resolved finding was appended after the responses that follow it in the ledger | The published link digest differed from the digest of canonical event inference; terminal delivery rejected the exchange with an incomplete persisted event chain | The serializer does not normalize response order. Publication order is replay semantics. |
| Retry the helper | Re-ran terminal delivery with the same manifest after the wedge was known | The chain replay is deterministic; every stop-reason variant failed at the same mid-chain link | Do not loop a deterministic fail-closed guard. Diagnose the link, then act once. |
| Supersession or reframe | Looked for an in-band carrier that binds and supersedes the defective link | A new derived state on the same parent collides with the multiple-derived-successors guard; the requirements were unchanged, so a reframe would fabricate protocol state | In-band exits exist only for their designed cases. A publication-order defect is not one of them. |

## Results & Parameters

### Configuration

```text
event covers every ledger finding
  AND responses are in ledger introduction order  -> publish after the digest gate passes
event order != ledger order                       -> regenerate the ordered set; do not publish
delivery fails at a mid-chain link, terminal clean -> publication-order defect; owner completion or hold
delivery fails at the terminal link               -> different defect class; see the terminal-carrier rules
```

### Expected Output

- Correct order: the reduced digest of the event equals the published digest. Terminal delivery replays every link and applies the terminal state, labels, and thread closures.
- Recovery: the pull request carries the terminal review at the exact head, closed finding threads, the exclusive terminal label, and one disclosure note with the defect provenance and the merge-gate record.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Chain-verified pull-request review exchange (v1 carriers) | A three-round exchange; the round-2 assessment event was published with non-canonical response order and blocked mechanical exclusive terminal delivery; owner human completion closed the exchange on the recorded gates | [notes](review-exchange-assessment-canonical-response-order.notes.md) |

## References

- [review-exchange-terminal-carrier-sole-publisher](review-exchange-terminal-carrier-sole-publisher.md) — the publisher-routing rule for the terminal round; this entry covers the order rule inside the published events.
- [pr-review-threadless-nogo-verdict-retry-wedge](pr-review-threadless-nogo-verdict-retry-wedge.md) — the deterministic-retry wedge pattern; do not loop a fail-closed guard whose input cannot change.
