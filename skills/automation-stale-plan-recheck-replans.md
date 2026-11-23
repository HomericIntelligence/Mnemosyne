---
name: automation-stale-plan-recheck-replans
license: BSD-3-Clause
description: "Re-plan an accepted plan when a freshness recheck returns NOGO. Use when: (1) an automation queue rechecks an accepted plan older than a staleness threshold, (2) the recheck returns NOGO because the tree moved, (3) plan-go items finish as blocked for human intervention after a wave, or (4) a design must choose between blocking and re-planning on proven plan drift."
category: architecture
date: 2026-11-23
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - automation-loop
  - plan-review
  - stale-plan
  - replanning
  - state-labels
  - no-progress
  - liveness
---

# Stale-Plan Recheck: Re-Plan the NOGO

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-23 |
| **Objective** | Keep a queue moving when an accepted plan no longer applies to the current tree. |
| **Outcome** | The freshness recheck NOGO routes through the ordinary amendment path. Items stop finishing with a human-intervention block for tree drift. |
| **Verification** | verified-local: focused stage and journal tests passed, the change PR passed required CI, and a live rerun logged the re-plan path on its first rechecked item. |

## When to Use

- An automation queue rechecks an accepted plan when the plan is older than a staleness threshold.
- The recheck returns NOGO because the tree moved after the plan was approved.
- Items finish as blocked for human intervention while the plan is still published on the issue.
- A wave blocks many `plan-go` items days after the plans were approved.
- A design must choose between a terminal block and a re-plan when a recheck proves drift.

## Verified Workflow

### Quick Reference

```text
recheck GO   -> keep the accepted plan; clear the one-shot flag; advance
recheck NOGO -> proven drift: re-plan through the ordinary review NOGO path
                retract the approved label
                publish the durable NOGO record
                amend within the review budget
                budget exhausted -> route back to planning

Never: finish the item with a human-intervention block for tree drift.
```

### Suggested Approach

1. Make the recheck one-shot. Arm it when the accepted plan is stale, and keep a durable flag so
   a restart does not arm it again. One recheck answers "does the plan still apply?".

2. On GO, clear the flag, keep the plan, and advance. The approval stays valid because the
   recheck just re-verified it against the current tree.

3. On NOGO, treat the verdict as an ordinary review NOGO. Log the decision (for example
   `stale-plan recheck failed (NOGO); re-planning the accepted plan against the current tree`),
   then clear the flag.

4. Reuse the existing amendment path. Retract the approved label, write the durable NOGO
   record, and continue into the amendment state while the review budget remains. Do not add a
   special terminal state for drift.

5. When the review budget is exhausted, fail back to planning. The plan no longer applies, so
   planning is the correct recovery owner.

6. Keep one state owner. The recheck does not add a label, a marker comment, or a second
   revision counter. The label vocabulary already routes re-planning.

7. Delete the retired block path. When the routing changes, remove the block marker, its
   renderer, and its tests together. A reader that finds the marker can revive the old behavior.

8. Test behavior through the real stage interface. Drive the review step with a stale-plan flag
   and a NOGO verdict. Assert the continuation state (`AMEND_WAIT`), the label set
   (`plan-no-go`), the popped flag, and the absence of a block comment.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Finish with a human-intervention block | A recheck NOGO proved the plan no longer applied, then the item wrote a block marker and finished for human intervention. The plan stayed unchanged. | Across one wave, 43 of 57 `plan-go` items ended this way and no PR was opened. Nothing in the run could clear the block. | Proven drift is amendable work, not a terminal state. The recheck exists to detect drift, so its NOGO must feed the amendment path. |
| Re-plan every old plan without a recheck | Plans past the staleness threshold went straight to a new planning budget. | Plans that still apply pay a full planner and review budget for no gain. | Recheck first: GO keeps the accepted plan, NOGO re-plans. |
| Keep the approved label during the amendment | The item stayed `plan-go` while its plan was under revision. | Two exclusive states described the item at once. The queue could fast-forward to implementation on a plan it had just rejected. | Move the item to the NOGO state before the amendment starts. |
| Leave the block marker and renderer in place | The routing changed, but the marker constant, renderer, and comment text remained. | A later reader can find the marker and restore the old block behavior. Dead paths are instructions that no longer apply. | Remove the block artifact set in the same change that changes the routing. |

## Results & Parameters

### Configuration

```text
stale_plan_recheck_age_days: 7    # arm the one-shot recheck after this age
stale_plan_recheck_budget: 1      # one recheck per accepted plan
review_amendment_budget: 3        # ordinary NOGO amendment budget
on_GO: clear flag, keep plan, advance
on_NOGO: retract plan-go, write NOGO record, amend; on budget exhaustion route to planning
```

### Expected Output

- Log line on the NOGO path: `stale-plan recheck failed (NOGO); re-planning the accepted plan
  against the current tree`.
- Labels during amendment: `state:plan-no-go`; the approved label is absent.
- No `hephaestus-stale-plan-block` comment and no human-intervention block on the issue.
- On amendment budget exhaustion: the item routes to planning, not to a blocked state.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Routing change with focused stage tests | [notes.md](automation-stale-plan-recheck-replans.notes.md) — test counts and the live rerun evidence. |

## References

- [Automation plan-review journal: canonical comments and liveness](automation-plan-review-journal-bounded-liveness.md)
- [Forced replanning with durable journal recovery](automation-forced-replanning-journal-recovery.md)
- [Never pass --update-plan to an automation-loop wave](automation-loop-no-update-plan.md)