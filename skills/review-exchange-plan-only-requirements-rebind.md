---
name: review-exchange-plan-only-requirements-rebind
description: "Rebind an issue-plan review exchange whose plan carrier binds a stale requirements digest, and keep one canonical producer for a content-derived requirements identity. Use when: (1) a plan-only exchange reports a requirements-drift diagnostic with a human-decision next action although the issue content did not change and no reviewer comment exists, (2) different agent sessions improvised their own issue snapshot and identical issue content gives different requirements digests, (3) a documented republish migration route cannot run because every reframe verifier requires one plan comment and one review comment, or (4) an issue snapshot producer rejects a provider value that the reducer accepts."
category: tooling
date: 2026-10-28
version: "1.0.1"
user-invocable: false
verification: verified-live
tags:
  - review-exchange
  - issue-plan
  - requirements-digest
  - snapshot-producer
  - requirements-drift
  - rebind
  - plan-only-epoch
  - withheld
  - human-decision
  - null-body
  - producer-reducer-symmetry
  - digest-stability
---

# Review Exchange Plan-Only Requirements Rebind

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-28 |
| **Objective** | Keep a published issue-plan carrier reviewable when the requirements digest that a historic snapshot producer bound no longer matches the canonical producer, and stop ad-hoc producers from creating that divergence. |
| **Outcome** | Successful. The reducer gained one bounded rebind route for the plan-only epoch shape: the inspection reports a ready rebind state, and the plan preparation returns an update of the retained plan comment that binds the current digest. Every other drift shape stays withheld. The canonical snapshot producer is now the only valid snapshot source, and it maps a null provider body to the empty string that the reducer accepts. |
| **Verification** | verified-live in one remediation: behavior tests prove the rebind route end to end (inspect, prepare, publish, readback inspect), prove that drift with a review carrier stays withheld, and prove that two independent producer builds of one fixture give the identical digest. The producer and reducer accept a null issue body as an empty body. The remediation is delivered: the reducer route, the producer null-body acceptance, and the contract documentation are merged at the source review after fresh reviewer verification of the replies. |

## When to Use

- A two-sided review exchange derives a requirements identity digest from an issue snapshot, and a published plan carrier reports a requirements-drift diagnostic although the title, body, and acceptance criteria did not change.
- The exchange has one plan comment and no review comment (a plan-only epoch), and the drift diagnostic routes to a human decision with no executable operation.
- Each agent session builds its own issue snapshot with different normalization rules, and the same issue content gives different digests on different sessions.
- A documented migration or rebind route must be checked against the reducer before you publish or trust it.
- You design or review a snapshot producer whose output feeds a digest that a reducer verifies.

## Verified Workflow

### Quick Reference

```text
Drift shape check (plan-only rebind):
  exactly one actor-owned plan comment
  + the carrier binds the current target
  + the carrier is an initial event (no prior state, no answers)
  + no review comment on the issue
    -> inspection is ready with a rebind diagnostic, next action prepare-plan
    -> prepare-plan returns one update of the retained plan comment
    -> publish, read back, verify publication
  a review comment is present
    -> the drift stays withheld; the review binds the old digest
Producer rules:
  one canonical producer; every hand-built snapshot is invalid input
  pin the identity fields, endpoint family, body handling, and pagination
  map provider nulls to the values the reducer accepts
```

1. Pin exactly one canonical producer for every snapshot that feeds a content-derived identity digest. Give the producer a pinned module contract: the identity fields, the endpoint family, the body handling, the heading and item rules, the pagination bound, and the failure mode. Declare every hand-built or hand-edited snapshot an invalid input. Two sessions that run the producer on the same content must produce byte-identical snapshots.

2. Check the drift shape before you select a remediation. The rebind route applies only when the epoch has exactly one actor-owned plan carrier, that carrier is an initial event bound to the current target, and the issue has no review comment. If a review comment is present, the review state binds the old digest; a plan-only rebind would orphan that state. Keep that shape withheld.

3. Make the rebind route reducer-native. When a wedge class has no legal transition at all, correct the reducer; do not correct only the documentation. Give the route strict preconditions, derive the new exchange identifier from the superseded state digest so a replay cannot collide with a fresh initial exchange, keep the retained scope, and reject any carry-over of prior answers. Emit a distinct diagnostic code so agents can identify the route from the inspection result alone.

4. Prove each documented route against the reducer before you publish the documentation. Run the inspection for every epoch shape: no carrier, plan-only carrier with a matching digest, plan-only carrier with drift, plan and review with drift. Record the returned next action for each shape. A migration paragraph that the reducer dead-ends is a defect, not a remediation.

5. Keep producer acceptance a superset of reducer acceptance. The provider can return a null body for an issue without a description. If the reducer accepts an empty body, the producer maps the null to the empty string and continues; it does not fail. Add a test that runs the producer output through the reducer and asserts a ready result.

6. Prove digest stability with a property test. Build the snapshot twice from the same fixture through the producer path and assert one identical digest. Add negative tests that show two different normalization conventions bind different digests, so the test suite keeps the reason for the single-producer mandate visible.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Document-only migration text | Stated that the author republishes the plan carrier to rebind it, and pointed each skill at that route. | The reducer could not execute the route. The inspection returned withheld with a human-decision next action, the plan preparation returned no operation, and every reframe and replan verifier required one plan comment and one review comment. A plan-only epoch has no review comment, so no helper command could rebind the carrier. | Verify each diagnostic code path before you document a remediation. State the route that the reducer can actually execute for the exact epoch shape. |
| Reuse the reframe verifier | Tried to treat the rebind as a requirements reframe under existing reframe authority. | A reframe requires changed requirements and a prior review state, plus one actor-owned plan comment and one review comment. The plan-only epoch fails the comment-count precondition by construction. | Separate wedge classes need separate bounded routes. Do not force one verifier to cover epoch shapes that its preconditions exclude. |
| Rebind every drifted plan carrier | Made the rebind route apply to any plan carrier with a stale digest. | A drift with a review carrier present must stay withheld. The review state binds the old requirements digest, and a silently rebound plan would orphan that review state and break the exchange chain. | Gate the route on the complete epoch shape. Withholding is the correct result for every shape that the route does not prove. |
| Fail the producer on a null body | Treated a missing issue description as an incomplete provider record and stopped the run. | The reducer accepts an empty body, so the only valid producer could not build a snapshot that the reducer accepts. An issue without a description became impossible to plan. | Keep producer acceptance a superset of reducer acceptance. Map provider nulls to the accepted values and test the boundary through the reducer. |

## Results & Parameters

- Rebind preconditions: exactly one actor-owned plan comment; the carrier state binds the current target; the carrier is an initial event with no prior state and no answers; the issue has no review comment. The requested plan scope must equal the retained scope. Prior answers and scope-change reasons are rejected.
- Rebind result: the inspection is ready with a distinct rebind diagnostic and next action `prepare_plan`. The plan preparation returns one `update` operation for the retained plan comment. The update keeps the visible plan content and binds the current requirements digest. After publication and readback, the inspection is ready for the first review.
- Identity derivation: the rebind exchange identifier is a digest over the target, the current requirements digest, and the superseded state digest. A fresh initial exchange derives its identifier without the superseded value, so the two cannot collide.
- Producer contract: one endpoint family; one identity representation for the target and for every actor and comment identity; bodies passed through without edits, with provider nulls mapped to reducer-accepted values; one pinned heading and item rule set with a missing section yielding an empty list; exhaustive bounded pagination with a completeness flag set only after the short final page; authority lookups that fail closed.
- Digest-stability property: two independent builds of the same fixture produce one identical digest. Different normalization conventions produce different digests for the same content; the suite keeps one such negative case.
- Boundary tests: a null body gives exit code zero, an empty body, an empty criteria list, and a ready inspection; a drift with a review carrier gives withheld with the drift diagnostic; a drift without a review carrier gives the ready rebind state.
