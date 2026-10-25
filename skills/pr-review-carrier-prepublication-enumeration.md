---
name: pr-review-carrier-prepublication-enumeration
description: "Before automation publishes a machine-readable review record (state carrier, exchange round, or authority event) onto a pull request, enumerate the artifact's existing review records even when automation owns the authenticated identity. Use when: (1) multiple automation lanes or sessions share one forge identity and can review the same pull request, (2) a chain-verified review exchange exists on the artifact, (3) a second state carrier on one artifact would fork a bounded review exchange, (4) a branch head moved while publication was in flight."
category: tooling
date: 2026-10-25
version: "1.0.0"
user-invocable: false
tags:
  - pr-review
  - review-exchange
  - carrier
  - coordinator-ownership
  - multi-lane-automation
  - forge-records
  - enumeration
---

# PR Review Carrier Pre-publication Enumeration

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Keep exactly one live review-exchange chain per pull request by enumerating the artifact's existing machine records before publishing a chain's first carrier. |
| **Outcome** | Operational. A second coordinator's round-1 carrier landed minutes behind a first coordinator's chain on the same pull request under one authenticated identity; the second coordinator stopped its own exchange and contributed its findings to the live chain as admissible additions instead of forking a second one. |

## When to Use

- Automation under one forge identity can run several independent coordinator lanes (separate sessions, machines, or schedules) that can touch the same pull request.
- The review workflow publishes state carriers that chain-validate predecessor links, ordering, and per-artifact exclusivity.
- A branch head can move during evidence collection, reduction, rendering, or publication.
- Before delivery operations that a fail-closed helper gates on an exact head and a complete carrier chain.

## Verified Workflow

### Quick Reference

```bash
# Enumerate BEFORE reduce/render/publish on any artifact:
gh api repos/<OWNER>/<REPO>/pulls/<N>/reviews --paginate \
  --jq '.[] | {id, state, commit_id, submitted_at, head: (.body[0:80])}'
# Then scan the bodies whose previews look structural for carrier markers or exchange
# identities before composing anything. A live chain found -> stop your own chain here.
```

### Suggested Approach

1. Enumerate the artifact's review records first and scan bodies for existing carriers or exchange identities. Do not infer exclusivity from labels, merge state, or "this session has not published".
2. Remember that the authenticated identity does not identify the coordinator: identity binds to the token, and ownership binds to the coordinator session that published the chain.
3. When a live chain exists on the artifact, publish nothing. Stop the would-be second coordinator. Contribute its review output to the live chain as admissible round additions under that exchange's later-finding rules (for example missed-correctness classes), and let the live chain's author-refresh mechanics settle any head moves.
4. Publish a new chain only when enumeration shows none: reduce, render, publish once at the exact current head, then read back byte-exactly. Wrong call forms and their record repair are covered by the void-repair skill.
5. A head move between binding and publication is not permission to reuse the stale binding: withhold, re-enumerate, and follow the head-refresh repair skill.
6. Immutable history stays immutable: an already-published carrier cannot be deleted (see the void-repair skill). Stop writes immediately and record the disposition in the session report instead of stacking further recoveries on the artifact.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Assume one lane owns the artifact | Composed and published a full round-1 carrier without enumerating existing records | An earlier lane's carrier and author-response had landed minutes before under the same identity; both carriers are immutable, so the artifact carried two chains until the second coordinator stopped | Enumeration before first publication is the only fork prevention; after the fact the complete recovery is stop-and-contribute |
| Re-deliver into a moved head | Ran a rendered NO-GO label delivery after the branch had advanced | The fail-closed helper withheld delivery on the stale head binding | Recheck the remote head immediately before each publication and each label operation |

## Results & Parameters

### Configuration

```yaml
record_set: pull-request reviews (immutable machine carriers)
enumeration_call: gh api repos/<owner>/<repo>/pulls/<n>/reviews --paginate
live_chain_signals:
  - a carrier marker fence in a review body
  - an exchange identity string inside a carrier
on_existing_chain: stop-coordinator, publish-nothing, contribute-findings-to-live-chain
ownership_boundary: one coordinator session owns publication, labels, and threads per artifact
head_recheck: immediately before every publication and every label operation
```

### Expected Output

- Exactly one live chain per artifact; later coordinators contribute findings without publishing.
- No out-of-order or forked carriers; any immutable stray records are reported, voided where the void-repair rules apply, and otherwise left as history with a recorded disposition.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A private repository pull-request review drive | One fork incident across two same-identity coordinator lanes | Generalized identifiers; details in [notes.md](../skills/pr-review-carrier-prepublication-enumeration.notes.md) |

## References

- [GitHub pull request reviews API](https://docs.github.com/en/rest/pulls/reviews)
- [github-pr-review-record-void-repair.md](github-pr-review-record-void-repair.md)
- [review-exchange-head-refresh-carrier-repair.md](review-exchange-head-refresh-carrier-repair.md)
- [review-exchange-terminal-carrier-sole-publisher.md](review-exchange-terminal-carrier-sole-publisher.md)
