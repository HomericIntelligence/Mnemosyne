---
name: coordinator-owned-terminal-review-lanes
description: "Keep terminal-stage lane launches (for example, independent review) with the coordinator, gated on forge-verified artifact existence. Use when: (1) a background implementation lane proposes to self-launch its own review or gate lane, (2) a parent lane's background session can end while its spawned children still run, (3) a stalled terminal stage tempts a replacement launch, or (4) several review lanes race on the same pull request. Also use when a reviewer starts in a shared checkout and finds a second live reviewer process, or uncommitted edits it did not make, already in that checkout."
category: tooling
date: 2026-11-01
version: "1.1.0"
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
  - shared-checkout
  - foreign-uncommitted-edits
  - reviewer-verdict-ownership
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
- You start a review in a shared checkout and find a second live process with
  the same task, or uncommitted edits that you did not make, already in it.

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
   If enumeration instead finds a race already running — concurrent
   same-head reviews from different reporters — do not launch another
   reviewer. Reconcile the existing review set, bind one canonical verdict
   to the head, and record the race in the coordination record.
6. **Count live children as their own work items.** Capacity bookkeeping
   tracks each child under its own durable identifier, never under the dead
   parent's entry. A parent end-of-life never removes a live child from the
   in-flight count.

### When the Race Starts After the Launch

Pre-launch enumeration cannot stop a race that the launcher never saw. Apply
this branch when you are a reviewer and the checkout already holds a second
writer.

1. **Prove the second writer before you decide.** Check for a live process
   with the same task command bound to the checkout, a claim record that
   names one owner, file modification times that no command of yours
   produced, and untracked files you did not create. Record the process and
   claim identifiers in your report.
2. **Do not push while the ownership is split.** A commit or push from either
   process gives the branch no single author, and the reviewed head becomes
   ambiguous. Post one verdict and one ownership note instead.
3. **Screen in-flight foreign edits before you treat them as a fix.** Read the
   foreign diff as review evidence, not as a cleared repair. An edit that
   skips one validation can produce an artifact that claims the value of set
   A while it carries set B, and the artefact passes the edited check and
   fails a later consumer. Do not report such an edit as a fix.
4. **Restore only tracked files you did not change.** Restore them to the
   head, so a later push cannot carry a half-applied repair. Leave untracked
   files that the other process created in place; they are its work.
5. **Leave the gate labels off.** A split ownership is not a clean review
   state. Post the verdict with the evidence you have, and keep any
   implementation gate unset.
6. **Ask the coordinator to stop one process.** Name both process identifiers
   and the claim owner. Put a decision request on the artifact when the repair
   needs a product choice rather than a reviewer edit.

### Quick Reference

| Situation | Action |
| --------- | ------ |
| Lane brief says "self-launch the review" | Strike it; coordinator launches after forge readback |
| Implementation report verified, no review yet | Enumerate, then coordinator launches one fresh-context reviewer |
| Parent session ended, child signal lost | Classify by artifact state; replace only after enumeration shows a gap |
| Two same-head reviews already racing | Do not launch a third; reconcile the pair and record the race |
| Second reviewer process already in your shared checkout | Post one verdict and an ownership note; do not push; restore foreign tracked edits |
| Foreign uncommitted edit looks like a fix | Screen it as evidence; a skipped validation can make a draft claim a value it does not carry |
| Foreign untracked file in the checkout | Leave it in place; it belongs to the other process |
| Unavoidable delegation | Durable forge comment with child session/shell IDs before parent reports |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Self-launched background reviewers | Two implementation lanes each spawned their own background review child and then ended | Both parent sessions ended; one child's completion notification was lost entirely (the stage stalled for hours at a stable head), the other child's report only surfaced through manual artifact reads | A background child's completion reaches only its spawner; terminal-stage launches belong with the coordinator who holds the long-lived channel |
| Replacement on the lost-signal alone | On a parent-dead review lane's silence, launched a fresh reviewer without re-reading the artifact | Three independent reviewers published round-1 reviews for the same pull request at the same head from different reporters; the verdicts converged but tripled the review spend and complicated verdict reconciliation | Silence is not a gap; enumerate reviews, threads, head, and claims before any replacement launch |
| Child shells under the parent's capacity entry | Counted a lane's background children as part of the parent's in-flight slot | The parent's end hid live children from the count; admission decisions assumed free capacity that did not exist | Each child is its own work item with its own durable identifier; a parent end never decrements a live child |
| Two reviewer processes launched into one shared checkout | A launcher started a second review of the same artifact while the first review still ran, and both edited the same files | The second process left uncommitted edits mid-review, so the checkbox state stopped being a single reviewed head; the edits also carried an incomplete repair that would have passed the edited check and failed a later consumer | A shared checkout needs one writer. A reviewer that finds a second writer posts one verdict and an ownership note, and does not push. |

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
  enumerate:
    - artifact reviews
    - open threads
    - recent head commits
    - coordination-record claims
  launch_condition: enumeration confirms the gap
orphan_classification:
  orphan-completed: accept with audit
  orphan-stalled: enumerate; single fresh replacement if the gap stands
  ambiguous: one bounded wait, then treat as stalled; record the class
capacity_accounting: each child is its own work item with a durable identifier
race_symptom: concurrent same-head reviews from different reporters
shared_checkout_race:
  detect: [same-command process, claim owner, foreign mtimes, foreign untracked files]
  write_rule: one owner pushes; the other posts one verdict and one ownership note
  foreign_tracked_edits: restore to head
  foreign_untracked_files: leave in place
  gate_labels: unset while ownership is split
  escalation: name both process ids and the claim owner
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
| Multi-lane backlog program on a shared delivery forge | 2026-11-07: a second reviewer process was launched into a checkout that a live reviewer already used, minutes after the first start; the second process left uncommitted edits mid-review, including a repair that skipped a validation and produced an artifact that claimed a digest for one value set while it carried another; the first reviewer posted one verdict and an ownership note, restored the tracked edits, and set no gate label | Generalized evidence in [notes](coordinator-owned-terminal-review-lanes.notes.md) |

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
