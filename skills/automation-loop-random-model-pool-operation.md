---
name: automation-loop-random-model-pool-operation
license: BSD-3-Clause
description: "Operate an issue-automation loop whose planner, reviewer, implementer, and fallback models are drawn at random for each run from a pool of served deployments. Use when: (1) role models come from a provider catalog where a listed deployment can be down or cold, (2) the agent CLI can exit 0 even when the provider request fails, so an exit code cannot prove liveness, (3) a resumed item has an in-flight plan-review session whose bound reviewer model must stay stable, or (4) a run admitted zero items after a BLOCKED disposition swapped the issue's seeding label."
category: tooling
date: 2026-10-24
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - automation-loop
  - random-model-draw
  - model-pool
  - health-probe
  - exit-status
  - plan-review-session
  - session-pinning
  - session-reset
  - label-restore
  - seeding-labels
  - hephaestus-automation
  - opencode
---

# Random Model Pools for Automation Loops: Probe, Pin, Restore

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-24 |
| **Objective** | Run an issue-automation loop (planner, reviewer, implementer jobs) that draws each role's model at random per run, without the draw itself causing agent-job failures or lost review cycles. |
| **Outcome** | Operational. A planning item that had failed four relaunches mechanically reached a recorded GO verdict (3 review rounds, 62 minutes, 5 agent jobs) with a content-verified pool probe, a reset review session, and restored seeding labels. |
| **Verification** | verified-live: evidence comes from supervised live loop runs on a multi-item issue campaign against a self-hosted model gateway. See [notes](automation-loop-random-model-pool-operation.notes.md). |

## When to Use

- A runner draws the planner, reviewer, implementer, or fallback model at random for each run, instead of pinning a fixed model per role.
- The pool comes from a model catalog in which a listed entry can be unserved or cold.
- The agent CLI can exit with status 0 while the provider request failed, so an exit code cannot prove liveness.
- The loop resumes items stopped at a plan-review stage, where the review journal binds the reviewer tool and model.
- A BLOCKED disposition applies a blocked label to the issue, and the loop seeds its work list from a needs-work label.

## Verified Workflow

### Quick Reference

```bash
# Liveness = expected token in the output. Never the exit code.
probe() { timeout 75 <agent-cli> run --model "<provider>/$1" \
  "Reply with exactly: OK" 2>&1 | grep -q OK; }
POOL=(); for m in model-a model-b model-c; do
  probe "$m" && POOL+=("$m") || echo "EXCLUDED: $m"; done
# Draw every role (planner, implementer, reviewer, fallback) from POOL only.
# If POOL has fewer entries than roles, allow repeats.

# An item that resumes at the plan-review stage:
#   - keep the bound reviewer model for that item's reviewer slot, OR
#   - relaunch with --reset-plan-review-session (fresh cycle; the plan survives).

# Recovery after BLOCKED:review-session-lost:
gh issue edit <n> --remove-label state:plan-blocked --add-label state:needs-plan
```

### Suggested Approach

1. Probe each candidate by output content before the draw. A catalog listing is not liveness: one observed deployment answered every request with `No worker available` while the agent CLI still exited 0. Launch a minimal reply probe with a timeout and require the expected token in the output. Apply the same rule to every health check around the loop: judge by output, never by exit status.
2. Keep a review session's reviewer model stable across runs. The review journal fail-closes on a reviewer tool or model change (`review-session-lost`), so a random re-draw almost always breaks a resumed plan-review item. Either constrain that item's reviewer slot to the model recorded in its review record, or pass `--reset-plan-review-session` to start a fresh cycle. Prefer reset at round 0, or when the bound model has left the allowed pool; prefer pinning when the item has review rounds whose NOGO citations the amend cycle must keep.
3. Restore seeding labels after a `BLOCKED:review-session-lost`. The fail-closed path replaces the item's `state:needs-plan` label with `state:plan-blocked`, and the loop seeds candidates from the needs-plan label — the next run then admits zero items and exits cleanly with no jobs, a silent no-op that reads as success in the summary. Remove the blocked label and re-add the needs-plan label together with the reset or pin.
4. Probe the fallback role too. An unprobed fallback fails at the same stage as an unprobed primary, only later in the run, after more agent time is spent.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trust the catalog and exit code | Treated a catalog-listed deployment as drawable; the agent CLI exited 0 on probe-shaped requests | The deployment was down; the CLI prints the provider error and exits 0. The drawn reviewer died with `reviewer error retries exhausted` after real agent jobs had run (≈90 s, 3 jobs) | Require the expected token in probe output; exit status is not a probe signal |
| Fresh draw into a live review | Re-drew all roles on a relaunch; the resumed plan-review item received a different reviewer than its session record | The journal fail-closed with `review-session-lost: reviewer tool or model changed` and the run BLOCKED in under a minute with zero agent jobs. A parallel run without the reset flag reproduced the same block | Pin the reviewer slot to the session's bound model, or relaunch with `--reset-plan-review-session` |
| Relaunch without label restore | Reran the loop after the BLOCKED disposition | The block had swapped `state:needs-plan` for `state:plan-blocked`; seeding selects on the needs-plan label, so the run admitted zero items and exited in seconds with no error | Restore the seeding label as part of the reset, before the next run |

## Results & Parameters

### Configuration

```yaml
pool_probe:
  prompt: "Reply with exactly: OK"
  success: expected token in combined output
  timeout_seconds: 75          # 45–90 observed range
  draw: every role from the probed pool; allow repeats when pool < roles
review_session:
  pin_rule: constrain the resumed item's reviewer slot to the bound model
  reset_flag: --reset-plan-review-session   # fresh cycle; published plan is kept
  prefer_reset_when: round 0, or bound model removed from the allowed pool
  prefer_pin_when: review rounds exist whose citations the amend cycle needs
labels:
  after_blocked: remove state:plan-blocked, add state:needs-plan
```

### Expected Output

- The run header classifies each candidate (`probe OK` / `EXCLUDED`) before the draw and records each role's drawn model.
- A reset plan-review starts at round 0 with a fresh session id; NOGO rounds cite code locations; a GO applies the done label to the issue.
- A restored item is admitted by the next run instead of a zero-item summary.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Issue-automation loop with a self-hosted model gateway | Seven supervised relaunches of one planning item behind a randomly drawn two-model pool: four mechanical failures (session mismatch, lost seeding label, dead deployment, operator interrupt), then GO after three review rounds | [notes.md](automation-loop-random-model-pool-operation.notes.md) |

## References

- [hephaestus-loop-unconfigured-host-operation](hephaestus-loop-unconfigured-host-operation.md) — canonical layered repair table for the same loop family, including the general probe-before-choosing rule and the session-reset plus label-restore repair; this skill adds the preventive policy for randomly drawn pools.
- [automation-plan-review-journal-bounded-liveness](automation-plan-review-journal-bounded-liveness.md) — review-cycle mechanics (canonical plan/review comments, amendment handling) behind the pin-or-reset decision.
