---
name: hephaestus-random-model-draw-launch-safety
license: BSD-3-Clause
description: "Keep repeated Hephaestus plan/implement loop launches healthy when a wrapper draws planner, implementer, reviewer, and fallback models randomly per run from a pool. Use when: (1) a run dies in seconds with BLOCKED:review-session-lost and zero agent jobs, (2) a relaunch admits zero items after a failed run, (3) an agent job dies late on a provider that answers No worker available, or (4) a one-loop-at-a-time launch guard must coexist with several clones of one repository."
category: tooling
date: 2026-10-24
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - hephaestus-automation
  - automation-loop
  - model-pool
  - random-draw
  - review-session
  - plan-blocked
  - health-probe
  - launch-guard
  - opencode
---

# Hephaestus Random-Model-Draw Launch Safety

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-10-24 |
| **Objective** | Run repeated Hephaestus loop waves through a wrapper that draws models randomly for each run from a pool, without self-inflicted launch failures. |
| **Outcome** | After four rules were applied (reviewer-model pin, label restore, content probe, clone-scoped guard), the blocked wave passed end to end: plan GO in 3725 s wall time, 5 agent jobs, three review rounds with amend cycles, `state:plan-go` applied by the loop. |
| **Verification** | verified-live — six refused or failed launches diagnosed one signature at a time on a live four-issue epic; the seventh attempt completed with no wrapper change beyond the four rules. Evidence in [notes](hephaestus-random-model-draw-launch-safety.notes.md). |

## When to Use

- A wrapper script launches `hephaestus-plan-issues` or `hephaestus-implement-issue` repeatedly and draws planner, implementer, reviewer, and fallback models randomly for each run from a pool.
- A run dies within seconds with `BLOCKED:review-session-lost` and `agent jobs: 0`.
- The relaunch after a failed run admits zero items even though the issue is ready.
- An agent job fails late with `reviewer error retries exhausted`, and a direct probe of the drawn provider answers `No worker available`.
- You design a launch guard that refuses a second loop, on a host where several clones of the same target repository run loops in parallel.

## Verified Workflow

### Quick Reference

1. An in-flight plan-review session pins its reviewer model. A fresh draw that differs fail-closes the new run. For an issue with an in-flight review session, constrain the next draw to the bound reviewer model, or relaunch with `--reset-plan-review-session`.
2. A review-session-lost block publishes `state:plan-blocked` on the issue, and loop seeding excludes that label. Restore `state:needs-plan` before any relaunch, or the next run admits zero items.
3. Probe every pool member by output content, never by exit status: `opencode` exits 0 even when the provider call fails. Probe success is the expected answer token in the output. Exclude non-responders from the pool for the run.
4. Scope a one-loop-at-a-time launch guard to the shared intake clone, never to the repository. Parallel intake clones of one repository are a legitimate operating pattern.

### Suggested approach

Record the pool policy in the wave plan document: allowed models, excluded models with the evidence (deployment outage, probe failure), and the draw for each run in the first lines of the run log (planner, implementer, reviewer, fallback). A log that starts with the probed pool and the draw makes every later failure unambiguous.

For every issue whose plan-review cycle is in flight, bind the reviewer slot of the draw to the recorded bound reviewer model instead of drawing fresh. Pass `--reset-plan-review-session` only when the mismatch is intentional: a reset starts the review cycle at round 0 with revision 1, so earlier rounds are lost. After any `BLOCKED:review-session-lost`, repair the issue label first (`state:plan-blocked` back to `state:needs-plan`), then relaunch. The reset flag and the label restore are two different repairs; the flag addresses the session binding, the label restores seeding eligibility.

Probe each pool member before the draw with a short prompt and a small token budget:

```bash
# Exit status is not evidence: opencode exits 0 on provider failure.
# Success = the expected token appears in the output.
answer=$(opencode run --model <provider/model> "Reply with exactly: OK" 2>/dev/null)
[ "$answer" = "OK" ] || echo "exclude <provider/model> from this run's pool"
```

A catalog listing, a health endpoint, and an exit status of 0 are all insufficient: a served-but-dead deployment passes all three and then burns a full run of planner and review jobs before the loop reports `reviewer error retries exhausted`.

Write the launch guard as a same-clone check: refuse a new launch only when a live loop shares this run's intake clone path. A repository-wide guard blocks legitimate queued waves on a multi-clone host and adds no protection, because lane state is per-clone.

If a step is unavailable:

- No reset flag on an older loop build: constrain the draw to bound reviewer models for in-flight issues. Do not relaunch into a known mismatch.
- No probe budget: run with a pinned pool of models proven in earlier runs. An unprobed random draw is the failure source, not the loop.
- No label authority: stop and report. A relaunch without the label restore produces a silent zero-item run that looks like an intake defect.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Relaunch with a fresh random draw while a review session was in flight | The new draw chose a different reviewer model than the session was bound to | The review journal fail-closes on a reviewer tool or model change mid-session: `BLOCKED:review-session-lost` in 17.8 s with zero agent jobs | An in-flight review session pins its reviewer model; the wrapper must pin the draw to the bound model or pass `--reset-plan-review-session` |
| Immediate relaunch after the fail-close | Relaunched the wave after the review-session-lost block | The failure path had published `state:plan-blocked`, and seeding excludes that label; the run admitted zero items and looked like an intake problem | A review-session-lost block always costs a manual `state:needs-plan` restore before the next relaunch |
| Random draw from an unprobed pool | Included a catalog-listed provider in the pool without a liveness probe | The deployment was down (`No worker available`); `opencode` exits 0 on provider failure, so exit-status checks had passed; the run spent 3 agent jobs and died with `reviewer error retries exhausted` | Probe by output content (expected token in output); neither catalog membership nor exit status 0 is evidence of provider liveness |
| Blanket one-loop-per-repository guard | Refused every launch while any loop on the repository was live | Parallel intake clones of one repository are an established operating pattern, so the queued wave could never start while a sibling clone's loop ran | Scope the concurrency guard to the shared intake clone; repository-wide refusal blocks legitimate waves without adding protection |

## Results & Parameters

### Configuration

- Launch contract that passed: probed pool of two models, draw recorded in the first lines of the run log, `--reset-plan-review-session` on the affected item, label restored to `state:needs-plan`, same-clone guard.
- Label repair before relaunch:

```bash
gh issue edit <issue-number> --repo <owner/repo> \
  --remove-label state:plan-blocked --add-label state:needs-plan
```

### Expected output

- The run log opens with the probed pool (each member answered the probe token) and the drawn planner, implementer, reviewer, and fallback.
- No `BLOCKED:review-session-lost` at startup; the first agent job starts within the first minutes of the run.
- Review rounds show amend cycles that converge, and a GO applies `state:plan-go` to the issue.
- A relaunch after failures admits the expected items (`agent jobs` above zero), not a silent zero-item run.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Hephaestus plan/review loop on repository comet | Epic wave-0, four child issues driven to `state:plan-go`; six refused or failed launches, then a clean pass (2026-10-22 to 2026-10-24) | [notes.md](hephaestus-random-model-draw-launch-safety.notes.md) |

## References

- [hephaestus-loop-unconfigured-host-operation](hephaestus-loop-unconfigured-host-operation.md) — host bring-up signature table; its session-reset row is the single-model predecessor of the draw-pin rule here.
- [interrupted-automation-loop-relaunch-salvage](interrupted-automation-loop-relaunch-salvage.md) — salvages in-flight work after a crashed loop; this skill prevents the launch-time failure classes instead.
- [hephaestus-interrupted-implementation-lane-recovery](hephaestus-interrupted-implementation-lane-recovery.md) — implementation-lane recovery after timeouts; the adjacent phase after plan review.
