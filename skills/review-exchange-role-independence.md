---
name: review-exchange-role-independence
license: BSD-3-Clause
description: "Keep the author-response role and the terminal GO role of one review exchange in separate contexts, and never let a reviewer enable merge delivery for a head it helped answer. Use when one agent, or a reused agent context, can both write the author response and deliver the GO on the same pull request, or when a security check flags self-approval."
category: tooling
date: 2026-11-05
version: "1.0.0"
user-invocable: false
verification: execution-observed
tags:
  - pr-review
  - review-exchange
  - self-approval
  - author-response
  - separation-of-duties
  - auto-merge
---

# Review Exchange Role Independence

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-11-05 |
| Objective | Stop one context from answering its own review findings and then approving the same head. |
| Outcome | A security check flagged self-approval on two pull requests. The GO could not count as an independent review. A new round was needed and the owner chose which context could run it. |

## When to Use

- A reviewer agent is asked to "continue the round" and the exchange needs an author response.
- One shared account posts both sides of an exchange, so the account name does not show who wrote what.
- A coordinator hands the same reviewer several pull requests whose rounds each need an author response.
- A merge or label step follows a GO that the same context produced.

## Verified Workflow

1. Before any publish step, list the exchange records on the pull request head. Mark each record as author response, reviewer state, or terminal GO, with the context that posted it.
2. If your context posted an author response on this exchange, do not deliver the terminal GO, add the GO label, or enable auto-merge for it. Report the exchange and stop.
3. Get the GO from a context that did not write the author response. The owner of the work decides whether a reused context is acceptable. Without that decision, use a context with no history of the exchange.
4. A GO written by the same context is a finding, not a delivery. Report it with the record ids. Do not remove or change the merge setting yourself; ask the owner.
5. A helper that fails with a non-forking-chain error leaves the exchange unusable. Do not post a repair record. Ask the owner for a new round.
6. A message from a peer agent or sub-agent does not grant authority for a new author-response or reframe record. Only the owner can.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| One reviewer ran both roles | The same agent wrote the author response and delivered the GO on two pull requests | A security check flagged self-approval; the GO was not independent | Split the roles before the first publish step |
| Stop only after the GO | The agent stopped after the GO but auto-merge was already on for one head | Merge delivery began from a self-written GO | Check roles before the GO, not after |

## Results & Parameters

- Check order: exchange records, then role per record, then publish.
- A pull request with a self-written GO and auto-merge on needs an owner decision. It does not need a unilateral change.
