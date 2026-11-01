---
name: coordinator-owned-terminal-review-lanes
description: "Keep terminal-stage lane launches (for example, independent review) with the coordinator, gated on forge-verified artifact existence. Use when: (1) a background implementation lane proposes to self-launch its own review or gate lane, (2) a parent lane's background session can end while its spawned children still run, (3) a stalled terminal stage tempts a replacement launch, or (4) several review lanes race on the same pull request."
category: tooling
date: 2026-11-01
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags:
  - background-agent
  - agent-orchestration
  - review-lane
  - terminal-stage
  - orphan-children
  - race-avoidance
  - notification-ownership
  - capacity
---

# Coordinator-Owned Terminal Review Lanes

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Keep the notification owner of a terminal-stage lane (independent review, gate, release check) alive for the lane's full run, so its completion always reaches a live decision-maker and no replacement lane races it. |
| **Outcome** | Operational. Orphaned child lanes (notification lost with the ended parent) and reviewer races (several same-head reviews from different reporters) both came from the same root cause: background lanes spawning background children. Coordinator-owned launches and pre-launch enumeration remove both. |

A background lane's completion notification goes to the session that spawned
it. When an implementation lane runs in the background and self-launches its
own background review child, the parent's session can end while the child
still runs. The child's completion then has no live receiver: the coordinator
sees nothing, assumes the stage is covered or lost, and the review stalls —
or the coordinator launches a replacement and two reviewers race the same
head. Terminal stages decide merges; their ownership belongs with the lane
that holds the long-lived notification channel: the coordinator.

## When to Use

- A background implementation lane's brief includes "launch the independent
  review yourself" or the lane proposes it in a completion report.
- A lane must delegate and the delegated child can run longer than the
  parent's session stays alive.
- A terminal stage shows no completion signal and you must decide between
  waiting, auditing, or launching a replacement.
- You find two or more review publications for the same pull request at the
  same head from different reporters — the symptom of a race the pre-launch
  enumeration would have prevented.

## Verified Workflow

1. **Implement the no-grandchildren rule.** A background lane does not spawn
   background child lanes. Put this in the implementation brief: deliver the
   artifact, report, stop. Review and gate stages are not part of the
   implementation lane's authority. A foreground child that the parent
   awaits before reporting is inside the parent's notification lifetime and
   is permitted.
2. **Let the coordinator launch the terminal stage.** After an
   implementation lane's completion report passes forge readback (the pull
   request resolves; the reported head binds), the coordinator launches the
   independent review lane itself, in a fresh context. Central launch keeps
   the review's completion with a live owner and preserves the independence
   the stage exists for — a reviewer that the author spawned is not
   independent of the author's session tree.
3. **Enumerate before every terminal launch.** Before a first launch and
   before every replacement, read the artifact's current state: reviews
   listed, open threads, recent head commits, and the coordination record
   for existing claims. Launch only when the state confirms the gap — for
   example, zero reviews at a stable head. A stalled signal is not a gap;
   only enumeration turns it into one.
4. **Hand off delegation that is truly unavoidable.** If a lane must spawn a
   child that can outlive it, the lane records the child's session and shell
   identifiers in a durable, cheap forge comment before its own report ends,
   so the coordinator can subscribe to the child directly. A child without a
   durable identifier record does not exist for coordination purposes.
5. **Classify orphans by artifact state, not by silence.** When the parent
   is gone and child state is unknown, re-read the artifact:
   - *Orphan-completed:* the publication is present (review posted at the
     bound head). Accept it with the usual audit; no replacement.
   - *Orphan-stalled:* nothing appeared and the head is stable for hours.
     Run step 3's enumeration; if it still shows a gap, launch one fresh
     replacement.
   - *Ambiguous:* partial signals (a claim comment, no publication). Treat
     as stalled after one bounded wait; record the classification.
6. **Count live children as their own work items.** Capacity bookkeeping
   tracks each child under its own durable identifier, never under the dead
   parent's entry. A parent end-of-life never removes a live child from the
   in-flight count.

### Quick Reference

| Situation | Action |
| --------- | ------ |
| Lane brief says "self-launch the review" | Strike it; coordinator launches after forge readback |
| Implementation report verified, no review yet | Enumerate, then coordinator launches one fresh-context reviewer |
| Parent session ended, child signal lost | Classify by artifact state; replace only after enumeration shows a gap |
| Two same-head reviews already racing | Do not launch a third; reconcile the pair and record the race |
| Unavoidable delegation | Durable forge comment with child session/shell IDs before parent reports |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Self-launched background reviewers | Two implementation lanes each spawned their own background review child and then ended | Both parent sessions ended; one child's completion notification was lost entirely (the stage stalled for hours at a stable head), the other child's report only surfaced through manual artifact reads | A background child's completion reaches only its spawner; terminal-stage launches belong with the coordinator who holds the long-lived channel |
| Replacement on the lost-signal alone | On a parent-dead review lane's silence, launched a fresh reviewer without re-reading the artifact | Three independent reviewers published round-1 reviews for the same pull request at the same head from different reporters; the verdicts converged but tripled the review spend and complicated verdict reconciliation | Silence is not a gap; enumerate reviews, threads, head, and claims before any replacement launch |
| Child shells under the parent's capacity entry | Counted a lane's background children as part of the parent's in-flight slot | The parent's end hid live children from the count; admission decisions assumed free capacity that did not exist | Each child is its own work item with its own durable identifier; a parent end never decrements a live child |

## Results & Parameters

```yaml
delegation_rule: no-grandchildren-in-background
foreground_child: permitted          # parent awaits it before reporting
unavoidable_delegation_handoff:
  medium: durable forge comment
  content: [child session id, child shell id, target artifact, bound head]
  timing: before the parent's own report ends
terminal_stage_launch:
  owner: coordinator
  gate: forge-verified artifact existence (PR resolves, head bound)
  context: fresh
pre_launch_enumeration:
  - artifact reviews
  - open threads
  - recent head commits
  - coordination-record claims
  launch_condition: enumeration confirms the gap
orphan_classification:
  orphan-completed: accept with audit
  orphan-stalled: one bounded wait, enumerate, single fresh replacement
  ambiguous: treat as stalled after the bounded wait; record the class
capacity_accounting: each child is its own work item with a durable identifier
race_symptom: concurrent same-head reviews from different reporters
```

### Expected Output

- Every terminal-stage lane has a live notification owner from launch to
  completion.
- No review lane is author-spawned; independence holds by construction.
- Replacement launches happen only after enumeration confirms a gap, so
  same-head reviewer races do not start.
- Orphaned children are classified by artifact state and recovered with at
  most one fresh replacement.

### Explanation

The two observed failure modes — the lost-completion orphan and the
three-reviewer race — have one root cause: a terminal stage whose launch and
ownership sat with a session that could not outlive it. Moving the launch to
the coordinator and gating it on forge readback fixes ownership and timing
together; enumerating before replacement fixes the race. The rules are cheap:
an enumeration is a handful of read calls, and a handoff comment is a single
write.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Multi-lane backlog program on a shared delivery forge | 2026-11-01: orphaned background review children observed in both modes (one completed and published, one stalled silently); one three-reviewer same-head race after a replacement launched without enumeration; all decisions held after coordinator-owned launches replaced the pattern | Generalized evidence in [notes](coordinator-owned-terminal-review-lanes.notes.md) |

## Related Skills

- `verify-completion-report-against-forge`: the forge readback that gates the
  coordinator's terminal launch.
- `agent-background-task-failure-recovery`: capacity ceilings and relaunch
  discipline that terminal launches must respect.
- `background-agent-silent-lane-wait-or-replace`: the wait-or-replace decision
  for a lane whose signal stops; this entry supplies the enumeration that
  makes the replace half safe for review lanes.
- `mid-drive-peer-completion-audit`: reconciling stale snapshots when
  parallel lanes move the same artifact.
- `pr-review-loop-orchestration-agent-patterns`: reviewer, fixer, and
  merge-owner role separation inside the review loop itself.
