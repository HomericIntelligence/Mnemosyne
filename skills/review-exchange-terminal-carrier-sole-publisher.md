---
name: review-exchange-terminal-carrier-sole-publisher
description: "Route a review-exchange terminal carrier only through the designated terminal delivery helper. Use when: (1) an exchange binds a deterministic closure ledger as the visible digest of the terminal review body, (2) a round that can be terminal (findings resolved, GO state) needs a state-carrier publication, (3) fail-closed guards reject helper delivery with a conflicting-terminal or nonforking-chain error although the evidence is complete at the exact head, (4) a wedged exchange needs an owner-override, reframe, or hold decision, (5) a delivery rejection must be classified as a fleet preemption — a sibling publisher already delivered the terminal GO at the exact head — before it is treated as a wedge, or (6) a forked carrier chain with multiple derived successors needs a close-and-replace recovery. Prevents a permanent terminal-delivery wedge that a same-round state carrier released through a general publisher first creates."
category: tooling
date: 2026-10-09
version: "1.1.0"
user-invocable: false
verification: verified
tags:
  - pr-review
  - review-exchange
  - terminal-delivery
  - sole-publisher
  - state-carrier
  - closure-ledger
  - fail-closed
  - wedge
  - owner-override
  - reframe
  - forked-chain
  - close-and-replace
  - fleet-preemption
  - escalate-not-retry
---

# Review Exchange Terminal Carrier Sole Publisher

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-09 |
| **Objective** | Keep terminal delivery of a multi-round review exchange unblocked: route the terminal round's state carrier only through the designated terminal delivery helper. |
| **Outcome** | Operational rule derived from one live wedge. In the source incident, the terminal round's GO carrier was published through the general publisher first; the helper then rejected terminal delivery for the exchange and could never accept it. An owner override completed the publication with the published exact-head GO review recorded as the merge gate. |
| **Verification** | verified-live in one two-round exchange (2026-10-09): the fail-closed rejections were observed against the helper, and the override path merged at the recorded gate. Single-case evidence; the invariant follows from the fail-closed design. |

## When to Use

- A review flow uses a designated terminal delivery helper as the sole terminal publisher: it binds a deterministic closure ledger as the visible digest of the terminal review body.
- A round can be terminal: every finding is resolved and the state to publish is GO.
- You must select the publisher for that round's state carrier.
- A general publisher already released the terminal round's carrier, and the helper now rejects terminal delivery with a conflicting-terminal-review or nonforking-chain error.
- More than one automation session under the same account can publish carriers on the same pull request, so a delivery rejection can be a fleet preemption instead of a wedge.
- A publisher can post duplicate terminal states over one parent state, which forks the carrier chain, and no carrier-level repair exists.
- Delivery is blocked although the evidence is complete and verified at the exact head, and you must choose owner override, full protocol recovery (reframe), or hold.

## Verified Workflow

### Quick Reference

```text
Decide the terminal publisher before the terminal round.
A designated terminal delivery helper is the sole terminal publisher
of the terminal round's state carrier.
Publish the terminal carrier through it, or not at all.
A same-round carrier released by a general publisher first wedges the
helper for the exchange; fail-closed guards reject every retry.
```

### Suggested Approach

1. Before you publish any round carrier, decide whether the round can be terminal. A round with resolved findings and a GO state is terminal-eligible. A round with open findings (NO-GO) is not.
2. If the round is not terminal-eligible, a general publication channel for the state carrier does not conflict with the helper. The terminal publisher decision stays open.
3. If the round is terminal-eligible, route the carrier through the designated terminal delivery helper. Do not publish the same state through a general publisher first. The helper binds the closure ledger as the visible digest of the review body; a carrier that already exists at the same head makes the helper input invalid.
4. If the wedge already exists, do not retry the helper. The guards (conflicting-terminal review, nonforking chain) are deterministic fail-closed checks; a retry reproduces the same rejection.
5. Classify the rejection before you recover. Extract every persisted carrier on the pull request and replay the chain. Two distinct causes read as the same error:
   - **Fleet preemption**: exactly one terminal GO envelope binds the exact live head, posted by a sibling automation session between your preparation and your delivery. Audit that carrier byte-for-byte against your own prepared manifest: requirement digest, reviewed-scope digest, artifact revision, anchor annex base and head, and a single-round complete-GO event structure. When every value matches, accept the carrier: post a handoff note that records the audit digests and your own verification result, apply the terminal state label exactly once, and follow the recorded gate. A second delivery violates the one-live-terminal invariant and fails by design.
   - **Forked chain**: one parent state has multiple derived successors, which duplicate terminal carriers create. No carrier-level repair exists: review dismissal is rejected as an invalid immutable carrier, and the forge exposes no review deletion.
6. Select a recovery from the wedge or the fork:
   - **Sanctioned supersession**: if the exchange tooling supports an opt-in overriding terminal report, use it first. It binds the foreign carrier, declares it superseded, and carries the closure ledger as the authoritative state, so the helper's bookkeeping closes for the exchange.
   - **Close and replace the pull request**: for a forked chain from duplicate terminal carriers, close the pull request as superseded with an explanatory record, open one replacement from the same branch and head, and run exactly one reviewer round with one publisher. Carry the issue linkage and the in-tree resolution state of the old exchange's findings into the replacement body.
   - **Owner override**: record the published exact-head GO review as the merge gate. Post an explanatory note on the pull request, apply the state labels directly, and run the merge on that recorded gate. Keep the override decision and the evidence pointers in the note.
   - **Full protocol recovery (reframe)**: use only when the exchange requirements genuinely changed. A reframe is the only complete-state carrier the chain accepts after a wedge; a reframe without a real requirements delta fabricates protocol state.
   - **Hold**: stop the publication, keep the exchange open, and escalate to the owner when no other exit applies.
7. After recovery or acceptance, close the loops that the helper would normally close (finding threads, labels, notes) explicitly, with references to the recorded gate.

### If a step is unavailable

- No ledger-binding helper on the flow (older exchange tooling): this rule does not bind; record which publisher convention the flow uses before the terminal round.
- Before you declare a wedge permanent, check whether the installed tooling supports a sanctioned opt-in supersession report. Tooling generations differ: later helpers can recover in-band from a foreign-published carrier.
- No override authority and no supersession support: hold and escalate; do not weaken the guard, and do not publish more carriers to probe the guard.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Publish the terminal carrier first, deliver through the helper after | The terminal round's GO state carrier was released through the general publisher; the helper then ran terminal delivery for the same head | Fail-closed guards rejected the delivery: a terminal state already existed at that head (conflicting-terminal review), and the exchange chain must not fork | Publish order fixes the outcome: the helper is the sole terminal publisher; decide the publisher before the terminal round is published |
| Reframe as an unblock path | Evaluating a reframe carrier for the wedged complete state | The chain accepts a reframe for a complete state only when requirements changed; the exchange requirements were unchanged, so a reframe would fabricate protocol state | Reframe is not a mechanical unblock; without a real requirements delta, the remaining exits are owner override or hold |
| Repair a forked carrier chain in place | Dismissal of one duplicate terminal carrier, and a retry of helper delivery, for one parent state with multiple derived successors | Dismissal is rejected as an invalid immutable carrier, the forge has no review deletion, and a retry re-derives the same fork from the persisted carriers | A forked chain has no in-band repair; close the pull request as superseded and cut one replacement from the same branch and head |
| Race a sibling's terminal delivery | Delivered a prepared terminal GO after a sibling session had already published a terminal carrier at the exact live head | The one-live-terminal guard rejected the second delivery as a nonforking-chain violation | Classify the rejection first: a valid sibling carrier at the exact head is a preemption to audit and accept, not a wedge to repair |

## Results & Parameters

### Configuration

```text
round has open findings (NO-GO)      -> general state-carrier publication does not wedge the helper
round is terminal-eligible (GO)      -> terminal carrier through the designated helper ONLY
wedge exists, supersession available -> opt-in overriding terminal report (in-band recovery)
wedge exists, requirements unchanged -> owner override (recorded gate) or hold; never retry the helper
wedge exists, requirements changed   -> reframe carrier through the exchange flow
helper rejects nonforking-chain      -> extract and replay every persisted carrier; classify
or multiple derived successors          preemption versus fork before any recovery
sibling terminal GO binds the        -> audit byte-for-byte against your prepared manifest;
exact live head                         accept with a handoff note; never deliver twice
forked chain from duplicate          -> close the pull request as superseded; one replacement
terminal carriers                       from the same branch and head, one round, one publisher
```

### Expected Output

- Correct routing: exactly one terminal review body at the exact head, published by the helper; the helper applies the state labels and the flow closes the finding threads.
- Override path: the pull request carries an explanatory note that names the published exact-head GO review as the merge gate; the labels show the terminal state; the merge record references the recorded gate.
- Preemption path: one sibling-delivered exact-head terminal GO carrier stands as the merge gate, the handoff note records the digest audit, and the terminal state label is applied exactly once.
- Replacement path: the superseded pull request carries the fork record and the in-tree finding resolutions; the replacement binds the same branch and head with exactly one terminal carrier and one reviewer round.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Benchmark-report pull request reviewed with v1 exchange tooling | Two-round exchange; the terminal round's GO carrier was published through the general publisher, which wedged helper terminal delivery; an owner override recorded the published exact-head GO review as the merge gate, and the pull request merged | [notes](review-exchange-terminal-carrier-sole-publisher.notes.md) |
| Production-documentation pull requests under multi-session fleet automation | A duplicate-carrier fork on one exchange recovered by close-and-replace at the same head; a preempted delivery on the replacement exchange accepted after a byte-for-byte digest audit; a later clean exchange delivered first try through the same route | [notes](review-exchange-terminal-carrier-sole-publisher.notes.md) |

## References

- [pr-review-threadless-nogo-verdict-retry-wedge](pr-review-threadless-nogo-verdict-retry-wedge.md) — the queue-automation retry-wedge variant: the same escalate-not-retry pattern with a different trigger (threadless NO-GO findings under deterministic retry).
- [mid-drive-peer-completion-audit](mid-drive-peer-completion-audit.md) — the queue-level sibling: audit a peer completion and finish the leftover bookkeeping; this entry adds the exchange-protocol classification when the peer completion is a terminal carrier that raced your delivery.
