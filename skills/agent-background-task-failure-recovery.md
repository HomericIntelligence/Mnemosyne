---
name: agent-background-task-failure-recovery
license: BSD-3-Clause
description: "Recover unfinished agent work when completion messages contain API failures or expected edits are missing. Also use when skill-bearing subagent spawns fail repeatedly with infrastructure errors while a minimal probe succeeds, and the failed lane carries a verdict that gates a merge."
category: tooling
date: 2026-04-17
version: "1.3.0"
user-invocable: false
verification: verified-local
tags: [background-agent, run_in_background, api-error, connection-refused, recovery, foreground-agent, spawn-failure, inline-degradation, operator-escalation]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/agent-background-task-failure-recovery.history"
history-cleanup-date: "2026-09-20"
---

# Background Agent Failure Detection and Recovery

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-04-17 |
| **Objective** | Detect and recover from silent background agent failures that report `status: completed` but contain `result: API Error` |
| **Outcome** | Successful — pattern identified and recovery workflow confirmed |
| **Verification** | verified-local |

## When to Use

- A background agent's completion notification shows `result: API Error: Unable to connect to API (ConnectionRefused)`
- Files that the background agent was supposed to modify appear untouched or only partially edited
- A background agent consumed many tokens (~12K–26K) and tool uses (~50–77) over 20–40 minutes before "completing"
- Deciding whether a multi-file task should use `run_in_background: true` or run in the foreground
- The user changes requirements while a background agent is already running

## Verified Workflow

### Quick Reference

```bash
# Step 1: When notification arrives with "API Error", do NOT assume work is done
# Step 2: Re-check what the agent actually changed
grep -rn "<pattern-agent-was-fixing>" <target-directory>/

# Step 3: Launch a fresh foreground agent scoped to remaining unfixed files
# (No run_in_background — use default foreground execution)
```

### Detailed Steps

1. **Recognize the failure signature**: The notification arrives with `status: completed` but the `result` field contains `API Error: Unable to connect to API (ConnectionRefused)` rather than a task summary. This is a silent failure — it looks like completion.

2. **Do NOT assume the work was done.** The agent may have partially edited files or left them entirely untouched.

3. **Audit what was actually changed**: Re-run the grep or search pattern the agent was supposed to fix to see which files it touched vs. which remain unchanged.

4. **Continue the unfinished work** directly or with a fresh agent scoped to the remaining files. Consider foreground execution when background connectivity has failed.

5. **For changed requirements**, use available agent messaging or interruption controls. If those controls are unavailable, reconcile the returned work with the latest request before integration. Continue independent work while waiting.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trusting `status: completed` | Assumed the task was done when the notification arrived with `completed` status | `status: completed` only means the agent process exited — it does not mean the task succeeded | Always check `result` field content, not just `status` |
| Waiting for background agent on large multi-file task | Used `run_in_background: true` for a task requiring 50–77 tool uses across many files | Background agents can hit connection timeouts after ~20–40 minutes, silently failing with ConnectionRefused | Use foreground for tasks estimated >5 minutes or requiring many sequential tool calls |
| Attempting to redirect running background agent | Tried to send updated instructions mid-flight | `SendMessage` is not available in the main conversation context | Plan for immutable instructions when using background agents; prefer foreground when requirements may evolve |

## Results & Parameters

**Failure signature to watch for:**
```
status: completed
result: API Error: Unable to connect to API (ConnectionRefused)
```

**Second failure signature — host-wide credential wave (added 2026-10-26):**
```
state: error
result: Failed to drain Session: invalid or missing API key
```

This signature behaves differently from ConnectionRefused, and the recovery changes with it:

- **Zero footprint.** The agent dies before its first tool call. No edits, no commits, no pushes.
  Recovery starts from re-verification, not from partial-work reconciliation. Check for output
  before assuming any exists.
- **Host-wide, not task-specific.** Many agents on the same host die in the same window with the
  same message. Treat one such death as a signal to stop launching: run a short, cheap probe
  first. If the probe dies the same way, the wave is still active. Do not spawn replacements
  until a probe completes end to end.
- **Short probes can pass during a wave.** A completed probe does not prove a long background task
  will survive. Rotate, re-verify gateway health, then re-dispatch the real work.
- **Early-push defense.** For any background task whose product is a branch, instruct the agent
  to commit and push incrementally as it goes, not once at the end. A wave death then costs
  only the unsaved tail instead of the whole run.
- **Independent completion happens.** A review or merge that the dead agent was dispatched to
  drive may still complete through another route. Before relaunching, read the forge state:
  pull request state, labels, reviews, and merge record. Resume only the gap, never the whole
  assignment from memory.

**Third failure signature — verdict-lane spawn wave (added 2026-10-30):**

```text
spawn fails at dispatch, repeated across replacements:
result: Failed to drain Session: invalid or missing API key
also observed: Timed out waiting for response headers
(while a minimal no-skill probe spawn succeeds)
```

This signature lands at dispatch time and adds a deliverable dimension to the
wave behavior:

- **Spawn-time death.** The failure surfaces at or near the spawn call, before
  any work starts. The footprint is zero, as in the credential-wave signature.
- **Probe with a matching profile.** A minimal no-skill probe proves only that
  minimal spawns survive. In the recorded session, one trivial probe passed
  while five skill-bearing review spawns failed in the same window. Probe with
  the same profile as the failing work before you trust a recovery signal.
- **Bound the retries.** Probe, then retry the real dispatch once. The same
  failure means the path is unavailable for this session; each further
  replacement spends budget and adds no evidence.
- **Degrade the deliverable, not the standard.** When the dead lane carried an
  independent verdict that the author cannot issue, such as a review GO that
  gates a merge, complete the review inline, publish it labeled as an author
  evidence record — never as the independent verdict — and move the merge
  decision to the operator. The independence requirement stays; only the
  reviewer changes.
- **Record the infrastructure failure.** Put the spawn error text, the retry
  count, and the probe result in the evidence record, so that the operator can
  judge the degradation.

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Relaunching verdict-lane spawns without a bound | Re-dispatched a dead review spawn as soon as each failure arrived | Every replacement failed with the same infrastructure error while the gated merge decision waited | Probe with a matching profile, retry once, then degrade inline |
| Treating a minimal probe as recovery proof | Read one trivial no-skill probe success as clearance to re-dispatch skill-bearing spawns | The probe exercised a different spawn profile; the skill-bearing spawns kept failing | Match the probe profile to the failing work before you trust the signal |
| Relaunching replacements during the wave | Spawned new agents as soon as deaths were noticed | The credential failure was still active host-wide; each replacement died the same way | Probe first; re-dispatch only after a probe completes |
| Assuming a dead agent left partial work | Searched for its edits and commits | The wave killed agents before their first tool call; the footprint was zero | Verify the footprint before reconciling; zero-footprint deaths need only a fresh dispatch after the wave |
| Waiting to push until the branch was finished | Held all commits locally for a final push | A death would have lost the whole product | Push incrementally during long background runs |

**Typical failure profile:**
- Token consumption: ~12,000–26,000 tokens
- Tool uses: ~50–77 tool calls
- Wall-clock time: ~20–40 minutes

**Background vs. foreground decision guide:**

| Condition | Use |
| ----------- | ----- |
| Short task (<5 min estimated) | `run_in_background: true` |
| Truly independent — don't need result before proceeding | `run_in_background: true` |
| Many file edits or sequential tool calls | Foreground (default) |
| Instructions might need refinement based on what the agent finds | Foreground (default) |
| User may change requirements mid-task | Foreground (default) |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ArchIdeas | Background agent launched to fix patterns across many research files; failed silently with ConnectionRefused after ~26K tokens and 77 tool uses | Session 2026-04-17 |
| LLM360/comet | Five skill-bearing review-dispatch spawns failed (four times `invalid or missing API key`, once a response-header timeout) while one trivial probe passed; the review completed inline as a labeled author evidence record on pull request #3239 and the operator took the merge decision | [notes](agent-background-task-failure-recovery.notes.md) |
