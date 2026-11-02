---
name: audit-milestone-sweep-attachments
description: "Audit a release milestone for items that a bulk sweep attached, but that the release plan never named. Use when: (1) a milestone holds items that no epic or plan lists, (2) many unrelated items share one milestone with near-identical attach timestamps, (3) a tracker or capability item of multi-release size sits in a short patch cut, or (4) the release is near its due date and its member count is far above the plan's roster."
category: tooling
date: 2026-11-02
version: "1.0.0"
user-invocable: false
tags: [github, milestone, release-plan, sweep, timeline-events, triage, scope, epic, due-date, gh-api]
---

# Audit Milestone Sweep Attachments

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Find the items in a release milestone that a bulk sweep attached and the release plan never named, then move only those to a milestone that matches their size. |
| **Outcome** | Operational. Two audits separated eight swept trackers and two oversized design epics from real release work, with zero unintended moves. |

A milestone's member list is not a scope decision. A board sweep assigns
membership by bucket rule, so a short patch cut can hold capabilities that
need many releases. Membership alone never proves that an item was planned.
The attach event is the evidence that separates a planned assignment from a
sweep assignment.

## When to Use

- A release milestone holds items that no epic, tracker, or plan body lists.
- Many unrelated items in one milestone carry near-identical attach times.
- A tracker, capability, or design program with a multi-release horizon sits
  in a short patch cut.
- The milestone due date is near and the member count is far above the
  roster in its plan.

Do not use this skill to undo a reported accidental bulk move. That is a
different intent with a different recovery rule; use the dedicated undo
entry for it.

## Verified Workflow

### Quick Reference

```bash
# 1. Singular vs clustered attach times. A tight cluster is a sweep signature.
gh issue list --repo O/R --milestone "TARGET" --state open --limit 500 \
  --json number --jq '.[].number' | while read n; do
  echo -n "$n: "
  gh api "repos/O/R/issues/$n/timeline?per_page=100" \
    --jq '[.[] | select(.event=="milestoned") | .created_at] | join(", ")'
done

# 2. Cross-check each member against the release plan roster.
gh issue view PLAN --repo O/R --json body --jq .body | grep -cE '#<num>\b'   # 0 = not named
```

### Suggested Approach

1. **Get the plan roster first.** Read the milestone's epic or tracker body.
   Its checklist is the declared scope. Record it before you read members.
2. **Extract attach events, not membership.** For each open member, read the
   issue timeline and keep only `milestoned` events. Sort the results by
   timestamp.
3. **Look for a cluster.** Attach events within seconds or one minute of each
   other, across unrelated items, are the signature of one bulk operation.
   Singular or hour-separated events are individual decisions.
4. **Intersect cluster with absence from the plan.** An item is a sweep
   artifact only when both hold: it entered inside the cluster, and no epic or
   plan body names it. Either signal alone is not sufficient.
5. **Test each candidate against the cut horizon.** The cut is a duration, not
   a date. Compare the work inside the item with the days the cut still has.
   An item whose own body says a later stage, a decision gate, or a separate
   release does not fit.
6. **Propose, do not move.** Report the evidence and a destination per item.
   Get owner confirmation, because a milestone assignment is a scope decision
   that belongs to the release owner.
7. **Move and verify counts.** Move each confirmed item, then compare every
   milestone's open count with the recorded before state. The source must lose
   exactly the moved count and each destination must gain exactly its share.

Do not move every cluster member without step 4. Planned tracker epics can
carry the same timestamp shape when a plan is authored in one pass.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Title-token scan | Grep the milestone titles for one version token to find misplaced work | The title token named a past version on many items that were correctly deferred forward, so the scan found history, not misplacement | Detect by attach event inside the cluster plus absence from the plan; the title is only a hint |
| Title suffix read as a milestone | Move an item whose title said "rebuild on vX.Y.Z" | That token was a dependency engine version inside one product line, not a release milestone | Confirm what a version-shaped token refers to before you treat it as a milestone |
| Judgment by age alone | Move items because they were created before the milestone | Old age does not prove wrong scope; correctly planned backlog is often old | Time of creation is not evidence; time of attachment is |

## Results & Parameters

### Configuration

```yaml
sweep_signature:
  window: "<= 60s across unrelated items"
  required_signals: 2   # inside-cluster attach AND absent from plan roster
horizon_test: "work in the item vs days the cut has left"
excluded: "created_at recency, title version tokens"
verification: "per-milestone open counts before and after"
```

### Expected Output

- Every moved item carries both signals, with its timestamp in the report.
- Source and destination counts change by the exact proposed numbers.
- Items with one signal only are listed and left in place, with the reason.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Large internal inference-platform repository | Two audits of a patch-cut milestone; ten items re-homed, zero unintended moves | Evidence in [audit-milestone-sweep-attachments.notes.md](audit-milestone-sweep-attachments.notes.md) |

## References

- [github-accidental-bulk-milestone-undo](github-accidental-bulk-milestone-undo.md) — the same timeline technique for a reported accidental move; that entry restores, this entry audits wrong scope.
- [github-release-board-realignment](github-release-board-realignment.md) — the sweep that creates this condition; bucket rules place members without a plan.
- [automation-loop-exclude-epic-roadmap-issues](automation-loop-exclude-epic-roadmap-issues.md) — tracking issues are checklists, so they cannot satisfy a leaf-work cut.