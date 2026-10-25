---
name: background-agent-silent-lane-wait-or-replace
license: BSD-3-Clause
description: "Decide whether a zero-output background agent lane is load-slowed or wedged before replacing it. Use when an autonomous lane shows no file edits, commits, or processes for tens of minutes on a loaded agent host."
category: tooling
date: 2026-10-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - background-agent
  - agent-orchestration
  - silence-threshold
  - wait-or-replace
  - load-slowed
  - duplicate-lane
---

# Background Agent Silent Lane — Wait or Replace

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Decide wait vs replace for a background implementation lane that shows zero visible output after its setup phase, without producing duplicate racing lanes. |
| **Outcome** | Successful — two lanes that each showed ≥45 minutes of zero output and were nearly declared wedged both completed normally in ≈5.5 hours with merge-grade pull requests; a third lane repeated the same signature (≈2h silence, then steady production). The one premature replacement produced a duplicate pull request that had to be closed as superseded. |
| **Verification** | verified-local — three sequential lanes on one loaded agent host measured end to end. |

## When to Use

- A dispatched background agent lane created its worktree or branch and then shows no file edits, no commits, and no spawned processes for tens of minutes.
- The agent host shows a load signal, for example sustained high CPU on the agent daemon and a load average near or above the processor count.
- You must decide to wait, to replace the lane, or to escalate.
- Several lanes run in parallel and a replacement would race the same plan as the lane it replaces.

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm that lane setup succeeded: the worktree and the branch exist.
git worktree list | grep <lane>
# 2. Sample for activity at long intervals (10-15 min), do not poll each minute.
find <lane-worktree> -type f -newermt "<last-signal-time>" ! -path "*/.git/*" -printf '%T+ %p\n' | sort -r | head -6
# 3. Check for a pushed head before any duplicate-PR decision.
git ls-remote --heads origin <lane-branch>
# 4. Only after the silence budget expires AND no host generation is visible:
#    replace with a NEW branch and worktree. Add an anti-collision instruction
#    to the replacement: run a PR search for the issue before any PR creation
#    and stop-and-report if one exists.
```

### Suggested Approach

Zero output is not a wedge when the host is loaded. Generation stalls inside the host can hold a lane for up to ≈2 hours before its first file artifact, and the lane then runs steadily to completion. Measure the budget from completed sibling lanes that run under the same load:

- longest measured zero-output phase of a completed lane: ≈2 hours
- typical background implementation runtime under the same load: ≈5.5 hours
- silence budget = 2× the longest measured phase; escalate after that, with evidence

Decision rules:

- **Sample passively.** Use file mtimes, `git status`, `git ls-remote`, and the process table. Do not message a live agent session to ask for status; the message competes with the same loaded generation path.
- **Wait below the budget.** Do not replace a lane inside the silence budget.
- **Beyond the budget with no host-side generation, escalate first** when an external decision is valid; replace only as a last action, never push over the old lane, and give the replacement a duplicate-PR guard.
- **A held lane can wake on its own background shell.** A self-driving lane can park on its own long-running shell (for example a test suite) and auto-resume on the native shell-completion notification. A completion notification that carries an interim structured status and a pending shell is flow, not failure.
- **After a completion notification, trust but verify.** Check the pull request file set, the review trail, the labels, and the merge state against the plan. Do not trust report text alone.

When this skill does not apply: a completion notification whose result field reports an API or connection error is a silent failure that looks like completion; recover per [agent-background-task-failure-recovery](agent-background-task-failure-recovery.md). Orchestration of the full lane set stays with [clear-open-issue-backlog-myrmidon-swarm](clear-open-issue-backlog-myrmidon-swarm.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Replace after ≈45 min of zero output | Two implementation lanes each showed ≥45 minutes with no edits, no commits, and no processes; replacement was prepared and started | Both lanes were load-slowed, not wedged: each completed normally in ≈5.5 hours and delivered a merge-grade pull request; the replacement produced a duplicate pull request against the same plan, closed as superseded, and doubled the review effort | Zero output close to the host load noise level is normal, not a stall; measure the silence budget from completed siblings before any replacement |
| Frequent active polling of the lane | Status probes each 1-2 minutes | Each probe confirms only the last state and costs a full orchestration turn; it never accelerates the lane | Sample at 10-15 minute intervals; act only at a material state change (new artifact, commit, PR, or completion notification) |

## Results & Parameters

### Configuration

| Parameter | Measured Value | Use |
| --------- | ---------------- | ---------------- |
| Longest zero-output phase of a completed lane | ≈2 hours (first visible artifact ≈1h59m after lane start) | Silence budget = 2× this value under the same load |
| Full runtime of a load-slowed lane, worktree to merged-grade PR | ≈5.5 hours | Expected total run time; plan the serial queue around it |
| Host load signal during the window | Sustained ≈46% CPU on the agent daemon; load average ≈7 on a comparable core count | If the host shows no load signal, shorten the budget; a silent lane on an idle host is a different failure |
| Duplicate-lane failure signature | Original lane completes anyway; a second PR races the same plan; one PR closes as superseded | Cost of premature replacement |

### Expected Output

- Lane progression pattern: worktree or branch creation → ≤2 hours of silence → first file edits → focused test cycles → atomic commits → pull request → review exchange → merge.
- No duplicate pull requests for one issue.
- Escalations have measurements, not guesses: sampled mtimes, process-table checks, and remote-branch reads.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Issue-backlog orchestration drive | Three sequential background implementation lanes on one loaded agent host; two lanes fully measured from dispatch to merged pull request, one lane measured through its silent phase and first artifacts | Measured values and probe commands in [notes](background-agent-silent-lane-wait-or-replace.notes.md) |

## References

- [agent-background-task-failure-recovery](agent-background-task-failure-recovery.md) — the sibling case: a *completed* background agent that carries an API-error result is a silent failure, not a silent-but-alive lane. Recover; do not wait.
- [clear-open-issue-backlog-myrmidon-swarm](clear-open-issue-backlog-myrmidon-swarm.md) — the orchestration recipe this wait-or-replace judgment operates inside.
