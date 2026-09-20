---
name: agent-background-task-failure-recovery
license: BSD-3-Clause
description: "Recover unfinished agent work when completion messages contain API failures or expected edits are missing."
category: tooling
date: 2026-04-17
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [background-agent, run_in_background, api-error, connection-refused, recovery, foreground-agent]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/ed1bd4f54fd4aaba446af92c8b3ab9aff2589ae3/skills/agent-background-task-failure-recovery.history"
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
