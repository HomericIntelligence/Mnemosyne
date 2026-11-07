---
name: opencode-goal-lane-revival
license: BSD-3-Clause
description: "Revive a goal-bearing OpenCode V2 lane whose goal record and session state disagree: goal active with a dead session, or an idle lane waiting on a self-resume that never fires. Use when a monitor or coordinator must decide wait versus revive for another owner's lane, the nudge must not redo delivered work, or a completion ceremony orders learn and a marker prefix."
category: tooling
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - opencode
  - goal-mode
  - session-store
  - goal-store-divergence
  - coordinator-nudge
  - lane-revival
  - audit-not-redo
  - model-availability
  - completion-ceremony
---

# OpenCode Goal-Lane Revival

**Supporting detail:** [notes](./opencode-goal-lane-revival.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Steer goal-bearing lanes to closure when the goal store and the session store disagree, without redoing work that a lane already delivered |
| **Outcome** | Successful — three lanes closed their own goals with evidence in one sweep: one session dead for twelve days finished in less than thirty minutes after one nudge; one session dead for five days closed with an audit; one idle lane whose checks were all green merged its artifact six minutes after one nudge. One plan-mode lane was correctly escalated as an owner step |
| **Verification** | verified-live — one coordinator sweep against twenty goal records, observed end to end from nudge to closure |

## When to Use

- A goal record reads `active` while its bound session has not updated for days, so the goal store and the session store disagree about liveness.
- A goal lane parks idle after the condition it waits on is already true. Example: a self-resume watcher on review checks that stopped polling after every check went green.
- You monitor or coordinate lanes that another session owns, and you must decide between wait, one revive nudge, or owner escalation.
- A lane completion requires a ceremony order: durable learning first, then a marker or title prefix.

## Verified Workflow

### Quick Reference

```bash
# 1. Classify liveness from the session store, read-only. Busy means the
#    row moved across two snapshots ~20 s apart or is fresher than ~120 s.
T1=$(sqlite3 "file:~/.local/share/opencode/opencode.db?mode=ro" \
  "SELECT time_updated FROM session_v2 WHERE id='<lane>';")
T2=...same query after 20 s...
# Divergent means: goal record says active AND the row is days stale.

# 2. Probe the owned log, then send ONE bounded nudge, detached, own session excluded.
: > "<owned-dir>/<lane>.log" || stop
nohup opencode run --session <lane> --model <provably-served-model> \
  "<facts you verified, and the audit-not-redo instruction>" \
  > "<owned-dir>/<lane>.log" 2>&1 &

# 3. Classify the outcome from the owned log per the ladder below.

# 4. Let the lane close its own goal record with evidence. Verify the
#    closure in the goal store. Then run learning, then the marker prefix.
```

### Suggested Approach

1. **Map the fleet from two stores, not one.** The goal store records lifecycle (`active`, `paused`, `complete`, `unmet`, `usageLimited`); the session store records publishing (title, `time_updated`). Neither is sufficient alone. A goal can read `active` while its session has been silent for days after a host restart; conversely a goal can read stopped while its session title self-declares the task done. Take both reads before any action.
2. **Classify before you touch.** Sample `time_updated` twice about twenty seconds apart. A lane is busy when the row moved or is fresher than about two minutes; skip busy lanes, a message competes with a live generation path. A lane is idle-detail when its goal status is recent or its tokens are still moving in the goal store; give it one bounded wait. A lane is divergent when the goal record reads active and the session row is days stale; only divergent lanes get one revive nudge. Terminal lanes (`usageLimited`, `unmet`, `paused`) from a superseded era get no nudge: resurrecting old-scope work risks duplicate lanes, and the goal policy does not treat those statuses as continuable.
3. **Do not nudge a live silent lane.** An alive lane with zero output for tens of minutes is usually load-slowed, not wedged. That wait-versus-replace decision is a different branch with its own observed budgets; see the references. Your branch starts only when the session itself is dead or the wait condition is already true and the resume did not fire.
4. **Nudge with proven served capacity, once.** Pass `--model` with a model that has a live worker now. The strongest local proof is the model your own session runs on; the fleet-standard model can sit at zero floor while a release is in flight. One parameter correction per failure class, then stop: `Model unavailable: <entry>` means the lane's stored entry is unserved (one retry on a proven entry); `no worker available for model <entry>; retry when a replica is ready` is a transient capacity state, not a delivery failure, and the fix is a different served entry rather than a follow-up loop.
5. **Give the lane audited facts and an audit-not-redo instruction.** Put the outside facts you verified into the message, for example "all checks green, zero pending, automerge not armed, session idle thirty minutes". Then require: re-read the live forge state before any mutation; if the outcome is already delivered, close the goal with evidence and stop instead of redoing the work; if the mode blocks action, say so. Delivered revivals observed so far close their own goal records, do their own housekeeping, and some deliver outstanding learning before they stop.
6. **Classify the outcome from the owned log, never from the launcher output.** Confirm the run attached through process state and log growth. A reply that names a mode block (for example plan mode) means only the owner can resume that lane; record it and move on. Do not send a second nudge to the same lane on the same condition; redeliver only after a new material fact appears.
7. **Verify closure in the goal store, then run the ceremony.** New goal status plus a closure timestamp is the completion proof; log text is a claim. When the sweep's lanes are closed or escalated, run durable learning on the episode, then apply the marker prefix with the host rename tool against titles discovered read-only from the session store. A title already marked `Done:` upgrades by replacing that prefix, not by stacking a second one.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Nudge with the lane's stored model | `opencode run --session <lane>` with no model override | The run died at once: the stored model entry was unserved on this host, and the lane could never have continued on it | Pass an explicitly served model; a stored entry is a declaration, not a proof of service |
| Retry on the fleet-standard model | One retry against the serving entry other lanes name in their objectives | The run answered `no worker available ...; retry when a replica is ready`: a transient zero-floor capacity state, not a delivery failure | A zero-floor entry is the same unserved class for delivery purposes; switch to any entry that has a worker now, do not loop on capacity |
| Treat the goal record as proof of liveness | Read `active` in the goal store and act as if the lane were running | The bound session had been dead for twelve days; the goal record was a divergent claim, not state | Cross-check the goal store against the session store before every decision; cross-store divergence is a normal failure mode after host churn |

## Results & Parameters

### Configuration

```yaml
liveness:
  snapshot_gap_s: 20
  fresh_threshold_s: 120
  divergent_age: "days of silence while the goal record stays active"
nudge:
  model: "an entry with a live worker; prefer the model your own session proves served"
  message_contract: ["outside facts you verified", "fresh forge read before mutation", "close with evidence, do not redo", "say so if the mode blocks action"]
  retries: "one parameter correction per failure class; then escalate, never loop"
delete_candidates:
  exclude: ["your own session", "busy lanes", "terminal lanes from a superseded era"]
ceremony:
  order: ["durable learning", "marker or title prefix"]
```

### Expected Output

- A divergent lane wakes on the nudge, audits live state, closes its goal record with evidence, and does its own cleanup.
- A parked idle lane whose condition is already true concludes in minutes (merge or final report), because the missing input was a completed turn, not more compute.
- A mode-blocked lane replies with the blocker; the coordinator records an owner action instead of looping.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode V2 goal-mode fleet (Linux), twenty goal records | One coordinator sweep across two release eras | Timing table, verbatim failure strings, and closure classes in [notes.md](../skills/opencode-goal-lane-revival.notes.md) |

## References

- Delivery mechanics for one message to many sessions: [tooling-opencode-v2-batch-session-messages](tooling-opencode-v2-batch-session-messages.md)
- Live silent lane, wait versus replace: [background-agent-silent-lane-wait-or-replace](background-agent-silent-lane-wait-or-replace.md)
- Audit-not-redo against live forge state: [mid-drive-peer-completion-audit](mid-drive-peer-completion-audit.md)
- Status misread as premature exit: [swarm-agent-status-misread-as-premature-exit](swarm-agent-status-misread-as-premature-exit.md)
- Marker prefix against a discovered title: [tooling-opencode-v2-current-session-rename](tooling-opencode-v2-current-session-rename.md) and [session-rename-unreadable-remainder](session-rename-unreadable-remainder.md)
