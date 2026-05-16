---
name: liza-planning-handoff-partial-resume
description: "Diagnose and repair Liza planning-to-implementation handoff starvation. Use when merged architecture or code-planning tasks have outputs but no implementation children, coders are idle despite completed planning work, PLANNING_COMPLETE is absent, or liza resume/checkpoint does not execute transitions."
category: debugging
date: 2026-05-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - liza
  - planning-complete
  - handoff
  - resume
  - orchestration
---

# Liza Planning Handoff Partial Resume

## Overview

Objective: unblock Liza when completed planning tasks do not hand off to implementation because `PLANNING_COMPLETE` is gated behind the whole planned sprint becoming terminal.

Outcome verified locally: a patched Liza binary created 13 implementation children from previously merged planning outputs in Radiance after `liza sprint-checkpoint` and `liza resume`; `liza validate --json` then passed.

## When to Use

- Liza shows merged architecture or code-planning tasks with `output[]`, but no coding children exist.
- `liza repair-agent-pool --dry-run` says there are no missing roles with claimable work, while coders are idle.
- The TUI reports stalled progress even though planning tasks are merged.
- `liza resume` after a checkpoint does not move a mid-sprint planning handoff into implementation.
- `PLANNING_COMPLETE` only appears after every planned task is terminal, so one unrelated active planning task starves unrelated merged outputs.

## Verified Workflow

### Quick Reference

```bash
liza status --json
liza sprint-checkpoint
liza resume
liza validate --json
```

When changing Liza source, use a writable Go cache and refresh embedded assets before building or testing:

```bash
make sync-embedded
GOCACHE=/tmp/liza-go-build-cache go test ./internal/ops ./internal/agent ./internal/commands
```

### 1. Confirm handoff starvation

Inspect `liza status --json` and separate three facts:

- Planning tasks that are `MERGED` and have non-empty `output[]`.
- Implementation children that should have been created from those outputs.
- Other non-terminal planned tasks that are unrelated to those completed outputs.

If merged planning outputs exist and no implementation children were created, treat the problem as handoff starvation rather than an agent pool shortage.

### 2. Add diagnostics before changing behavior

Expose a status diagnostic such as `phase_handoff` with:

- ready planning outputs that have not been consumed,
- non-terminal planned tasks that are still blocking whole-sprint terminal detection,
- stale assigned agents with expired leases.

This makes the failure visible from `liza status --json` without requiring direct state-file inspection.

### 3. Fix wake detection

In Liza source, ensure `DetectOrchestratorWakeTriggers` emits `PLANNING_COMPLETE` as soon as merged planning outputs with unconsumed `output[]` exist.

Important behavior:

- Do not require every planned task in the sprint to be terminal before emitting `PLANNING_COMPLETE`.
- Suppress duplicate wakeups for `CHECKPOINT` and `COMPLETED` states.
- Keep whole-sprint terminal detection for true completion, but do not use it as the only path to planning handoff.

### 4. Fix resume behavior for mid-sprint checkpoints

When `liza resume` resumes from a checkpoint whose trigger is `PLANNING_COMPLETE`, execute available transitions directly during resume.

Expected behavior:

- Call transition execution immediately instead of waiting for a separate orchestrator PreWork cycle.
- Clear the checkpoint trigger once transitions are executed successfully.
- Print transition counts and errors even if the sprint did not advance to a new lifecycle phase.

This is necessary when no orchestrator process is actively running after a manual checkpoint/resume.

### 5. Validate against the stuck project

After installing the patched binary in the affected project:

```bash
liza sprint-checkpoint
liza resume
liza status --json
liza validate --json
```

Expected result: implementation children appear for every ready planning output that has concrete emitted work.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Attempt 1 | Repaired the agent pool first | The implementation tasks had not been generated yet, so no coder work was claimable | Diagnose planning output handoff before changing the pool |
| Attempt 2 | Added status diagnostics only | Observability made the problem visible but did not create transitions | Add wake detection and resume transition execution |
| Attempt 3 | Waited for all planned tasks to become terminal | One unrelated active `CODE_PLANNING` task blocked unrelated merged outputs | Emit `PLANNING_COMPLETE` when any merged planning output is ready |
| Attempt 4 | Relied on an orchestrator PreWork cycle after checkpoint/resume | Manual resume did not execute transitions if no orchestrator was running | Execute available transitions during `liza resume` for `PLANNING_COMPLETE` |
| Attempt 5 | Treated an empty `output[]` warning as fatal | Empty planning outputs can be skipped while valid outputs proceed | Continue processing other ready outputs and report the warning |

## Results & Parameters

Observed downstream state after applying the fix in Radiance:

- Liza binary installed from commit `7649c45`; previous binary saved at `~/.local/bin/liza.backup-before-partial-handoff-fix`.
- `liza resume` after `liza sprint-checkpoint` created 13 implementation children.
- Final observed task mix: 50 tasks total, 31 `MERGED`, 5 `SUPERSEDED`, 1 `CODE_PLANNING`, 10 `DRAFT_CODE`, and 3 `IMPLEMENTING_CODE`.
- `liza validate --json` returned success after the handoff.

Liza source changes that fixed the behavior:

- `internal/agent/workdetection.go`: detect ready planning outputs before all-planned-tasks-terminal logic.
- `internal/ops/mode_change.go`: execute transitions on resume from `PLANNING_COMPLETE` checkpoints and clear the checkpoint trigger.
- `internal/commands/status.go`: include `phase_handoff` diagnostics.
- `internal/commands/resume.go`: print transition counts/errors even without a sprint advance.

## Verified On

| Project | Evidence |
| --- | --- |
| `liza-mas/liza` | Fix published as PR `https://github.com/liza-mas/liza/pull/70`; bug tracked as `https://github.com/liza-mas/liza/issues/69` |
| `LLM360/Radiance` | Patched local binary unblocked stalled planning handoff and created implementation children; `liza validate --json` passed |
