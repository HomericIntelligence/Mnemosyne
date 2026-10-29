---
name: pr-review-legacy-thread-authorized-closure
description: "Close legacy out-of-band review findings under explicit authority, then read the terminal-delivery preflight honestly. Use when: (1) a fail-closed review-delivery helper prepares a closure manifest whose required entries are unanswered legacy findings, (2) old review threads carry only legacy severity markers and no version-1 finding marker, (3) an assessment was produced outside the exchange publisher and never became a version-1 state carrier, or (4) after every thread closes, the prepared manifest still has no terminal state."
category: tooling
date: 2026-10-26
version: "1.0.0"
user-invocable: false
tags:
  - pr-review
  - review-exchange
  - legacy-carrier
  - authorized-actor
  - thread-closure
  - closure-manifest
  - preflight
  - terminal-delivery
  - state-null
  - fail-closed
---

# PR Review Legacy Thread Authorized Closure

**Supporting detail:** [notes](./pr-review-legacy-thread-authorized-closure.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Deliver or withhold a terminal GO on a pull request whose review history contains legacy findings that out-of-band automation published, without inventing protocol state. |
| **Outcome** | Operational decision procedure. One live wave of four pull requests verified it: preflight classification, one authorized thread closure, and the state-null branch each reproduced by direct helper probes and forge reads. |

## When to Use

- A review-delivery helper consumes a schema closure manifest and gates a terminal GO on
  ordered closure entries.
- The prepared manifest contains required entries with legacy `native:` identities, no author
  answer, and no terminal-ledger disposition. The threads carry only legacy severity markers.
- The pull request has a legacy findings-ledger comment or an empty-body review at an old head,
  published outside the exchange publisher.
- A review assessment exists only as session output. No version-1 carrier carries its state.
- After authorized closure of the legacy threads, the prepared manifest still has an empty
  terminal state, and you must select the deliverable path.

## Verified Workflow

### Quick Reference

```text
# Preflight first. The manifest preparation is read-only. Run it before any
# reviewer round and classify every entry.
<delivery-helper> --prepare-manifest ...

# Classification:
#   entry is native:* + required + unanswered   -> legacy finding, authority needed
#   every entry closed + state is null          -> no version-1 terminal state exists

# Authorized closure order, per legacy thread:
#   1. publish one author-response review on the exact current head that cites
#      the resolving change for each finding
#   2. verify the response is visible
#   3. resolve only the threads whose evidence provably closes their finding
#   4. re-run the preflight; report each thread that stays open

# Terminal path:
#   state present      -> continue normal terminal manifest construction
#   state null         -> publish a real version-1 round, or stop report-only
```

### Suggested Approach

1. Run the helper's read-only manifest preparation before you spend a reviewer round. Do not
   infer the blocker from prose reports. Classify each prepared entry as a legacy adoption or a
   current-round finding.
2. A legacy thread without a version-1 finding marker can never gain a terminal-ledger
   disposition. Closure needs explicit authority for the actor and the scope.
3. Under that authority, close in the verified order: publish one author-response review on the
   exact current head that cites the resolving change for each finding, verify the response is
   visible, then resolve exactly the threads whose evidence provably closes their finding. Keep
   every unproven thread open and report it. Never resolve a foreign thread, and never write a
   disposition field by hand.
4. Re-run the preflight. When the manifest has an empty entry list and a null terminal state, no
   version-1 terminal reviewer state exists at all. A summary assessment that was never published
   as a version-1 carrier is not a deliverable state.
5. Never hand-write the terminal state envelope or the terminal visible content to fill that
   gap. Hand-authored protocol state is fabrication, and the fail-closed guards catch it.
6. Select the path explicitly. Publish a real reviewer round through the exchange publisher
   under the sole-publisher rules, then deliver normally. Or record a report-only assessment and
   leave the artifact open. Do not guess past the gate.
7. A merge queue can supersede the remaining lattice later. Re-read the forge before you spend
   the round, and record which path delivered the artifact.

### If a step is unavailable

- No explicit authority for thread closure: withhold closure and report the exact thread
  identities and evidence state. Do not close threads under implied authority.
- The exchange publisher cannot run on this flow: the state-null rule still binds. Stop
  report-only instead of manufacturing protocol state.
- The helper offers no read-only preflight: enumerate the review records and threads directly on
  the forge. Classify from the markers before you spend a reviewer round.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treat a completed in-session review assessment as deliverable | A reviewer round reached a GO verdict inside a delegated session, but no version-1 carrier was ever published | The prepared manifest showed the state field null with an empty entry list after authorized closure; there was no terminal state to deliver | An assessment is not protocol state. Verify that a version-1 carrier exists before you plan any terminal delivery |
| Resolve legacy threads before verified author-response evidence | Considered resolving threads whose findings the current head addressed, without a published author response | The flow's closure rules require the exact response to be visible before resolution, and forbid resolutions without a terminal-ledger disposition | Order is load-bearing: author-response review, verify visible, then resolve with cited evidence |
| Repost a corrected review body after an in-place body edit | An actor edited a published review body, then reposted the identical body as a new review | The edited record failed the chain's immutability check, and the duplicate spawned duplicated inline finding threads | Review bodies are immutable from first publication; repair an established record only through the void-repair procedure, never by edit or unvoided repost |
| Treat one blocked pull request as one defect | Three pull requests blocked in the same wave with the same manifest signature | The cause was one systemic defect: out-of-band automation published legacy carriers without version-1 finding markers | Run the preflight across the wave before you assess. Systemic blockers need one authorized procedure, not per-item improvisation |

## Results & Parameters

### Configuration

```yaml
preflight:
  mode: read-only
  classify_entries:
    legacy: "identity matches native:* and author_answer is null and disposition is required"
    current_round: "identity carries a version-1 finding marker"
closure:
  authority: explicit, actor-bound, thread-scoped
  order: [author_response_review, verify_visible, resolve_proven_threads, re_preflight]
  preserve: "each unproven thread stays open and reported"
terminal_state:
  null_means: "no published version-1 terminal state exists"
  forbidden: "hand-authored state envelope or hand-authored visible content"
  paths: [publish_real_v1_round, report_only]
```

### Expected Output

- A preflight classification that names each legacy entry and each current-round entry.
- Authorized closure receipts: the author-response review identity, the resolved thread
  identities, and the cited resolving change for each.
- An explicit terminal decision: deliver through a real version-1 round, or report-only.
- Zero hand-written protocol state fields.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal repository review flow | A four-pull-request wave blocked on legacy out-of-band carriers | Preflight classification ran on each artifact; one authorized closure resolved three threads with cited changes; the state-null branch reproduced on all four artifacts; the wave completed later through the repository merge queue — verified-live by direct helper probes and forge reads; see [notes](./pr-review-legacy-thread-authorized-closure.notes.md) |

## References

- [review-exchange-terminal-carrier-sole-publisher](review-exchange-terminal-carrier-sole-publisher.md) — publisher routing and wedge recovery for the terminal round.
- [review-exchange-terminal-manifest-construction](review-exchange-terminal-manifest-construction.md) — manifest inputs once a real terminal state exists; its hand-written-content rejection is the manifest-side counterpart of the state-null rule here.
- [github-pr-review-record-void-repair](github-pr-review-record-void-repair.md) — the sanctioned repair for edited or duplicated review records.
- [review-exchange-head-refresh-carrier-repair](review-exchange-head-refresh-carrier-repair.md) — head moves between evidence and delivery.
