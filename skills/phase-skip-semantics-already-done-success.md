---
name: phase-skip-semantics-already-done-success
description: "Distinguish orchestrator-level phase skips (disabled/gated/not-final-loop/shutdown) from worker-internal already-done idempotency, and enforce that 'already done' returns success not failure. Use when: (1) building a multi-phase pipeline driver, (2) a phase's worker has any 'already exists / already done' check, (3) debugging why phase N's downstream phases stopped running, (4) auditing rc semantics across an orchestrator → worker boundary, (5) reviewing whether a worker's success count includes idempotent skips."
category: architecture
date: 2026-05-26
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - orchestrator
  - pipeline
  - idempotency
  - exit-code
  - phase-skip
  - worker-contract
  - already-done
  - rc-semantics
  - multi-phase
  - automation
---

# Phase-Skip Semantics: "Already Done" Is Success, Not Failure

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-26 |
| **Objective** | Prevent the bug class where a multi-phase orchestrator interprets "everything already done" as failure and refuses to advance past phase 1, by keeping orchestrator-level skips and worker-internal idempotency in separate, well-typed layers. |
| **Outcome** | SUCCESS — methodology codified from ProjectHephaestus `scripts/loop_runner.py` + `hephaestus/automation/planner.py` (`_has_existing_plan`) pipeline (plan → review-plans → implement → review-prs → address-review → drive-green). |
| **Verification** | verified-local — observed correct behavior in plan-phase exit `Successfully planned: 0 / Already planned: N / Failed: 0` → rc=0 → pipeline advances to phase 2. |

## When to Use

- You are designing or auditing a multi-phase orchestrator that calls per-issue / per-item workers
- A worker has any "already X — skipping" branch (already-planned, already-implemented, already-reviewed, already-merged)
- Debugging why phase 2..N stopped running after phase 1 completed
- Reviewing whether the orchestrator's "successful" count vs the worker's "successful" count include / exclude idempotent skips
- Adding a new phase to an existing pipeline — verify both skip layers are wired correctly

## Two Distinct Skip Mechanisms — Do Not Conflate

A multi-phase pipeline has **two layers** where work can be "skipped." They are observable as distinct outcomes and MUST stay in separate code paths.

### A) Orchestrator-Level Phase Skips (declarative; "phase did not run this iteration")

The orchestrator decides, before invoking the worker, whether to run the phase at all. Each skip branch has a concrete condition and a logged reason.

| # | Skip Branch | Condition | Logged Reason | Phase RC |
|---|-------------|-----------|---------------|----------|
| 1 | Disabled by `--phases` | Phase name not in user-supplied phase list | `Phase X disabled by --phases (selected: …)` | n/a (not run) |
| 2 | No open issues | Phase requires `--issues`, and `gh issue list --state open` returned empty | `Phase X skipped: no open issues to act on` | n/a (not run) |
| 3 | Not final loop | Phase is final-loop-gated (e.g., `drive-green`) and current iteration < final | `Phase X skipped: only runs on final loop (iteration i/N)` | n/a (not run) |
| 4 | Shutdown requested | `SIGINT` / `SIGTERM` flipped a cooperative shutdown flag | `Shutdown requested; skipping remaining phases` | n/a (not run) |

These produce NO exit code from the worker because the worker is never invoked. The orchestrator logs the skip reason and moves on.

### B) Worker-Internal "Already Done" Idempotency (one invariant)

> **The worker MUST return `success=True` with `rc=0` when the work is already done.** Never count "already done" as failure. The orchestrator's only signal is the worker's exit code, and an idempotent skip is a successful outcome — the work IS done, just not by this invocation.

#### Positive Example (ProjectHephaestus `hephaestus/automation/planner.py`)

```python
# In the per-issue planner branch:
if not self.options.force:
    if self._has_existing_plan(issue_number):
        return PlanResult(
            issue_number=issue_number,
            success=True,                # <-- THE invariant
            plan_already_exists=True,    # informational flag, not a failure signal
        )
```

#### Summary-Print Pattern

The worker's end-of-run summary counts `already_done` separately **within the successful set**, so operators can distinguish "did N new things" from "found N already done" without changing the rc:

```text
Plan phase summary:
  Successfully planned: 0
  Already planned:      7
  Failed:               0
Exit code: 0
```

The orchestrator sees `rc=0` and proceeds to phase 2. The "0 newly planned / 7 already planned" detail is visible in logs but invisible to the orchestrator's control flow — which is exactly what we want.

## The Bug Class This Prevents

An orchestrator that conflates the two layers (or that treats "0 new actions" as failure) will block all subsequent phases when the pipeline reaches a steady state. Concretely:

- Idempotent runs (re-running the loop after everything is already planned) become permanently stuck at phase 1.
- Operators see `rc=1` from phase 1, assume a real failure, and dig into nonexistent bugs.
- Downstream phases (review-plans, implement, review-prs, address-review, drive-green) silently never execute, even though they have useful work to do (reviewing existing plans, advancing existing PRs, etc.).

## Failed Attempts (Anti-Patterns to Avoid)

| Attempt | What Was Tried | Why It Failed | Lesson |
|---|---|---|---|
| Count "already done" as a failure in the worker | Worker returns `rc=1` when every issue is already done, "to signal nothing-to-do" | Orchestrator interprets phase-1 `rc=1` as failure and (in some designs) refuses to advance to phase 2, leaving the pipeline stuck in a no-op loop | Idempotent skip ≡ success at the worker layer. Surface "nothing-to-do" as a log line (`Successfully planned: 0 / Already planned: N`), not via exit code. |
| Build a single "skip" concept covering both orchestrator-gated skips and worker-internal already-done | One unified `PhaseResult(skipped=True)` flag whether the orchestrator declined to run the phase OR the worker found everything already done | Loses the ability to distinguish "user asked us not to run this" from "we ran and there was nothing to do" — operators can't tell from the summary whether the pipeline is healthy or misconfigured | Keep the layers separate: orchestrator skips are visible at the orchestrator log layer with a reason; worker idempotency is visible in the worker's own per-item summary. Both produce phase `rc=0`, but they're observable as distinct outcomes. |
| Treat `rc!=0` from any phase as "stop the pipeline" | Phase 1 fails (e.g., rate limit) → orchestrator marks the run failed and skips phases 2-6 | Loses N-1 phases of useful work per repo. Phase 2 (review previous plans) can still run usefully even if phase 1 (create new plans) hit a rate limit. | Phase failure ≠ pipeline failure. Each phase is independent at the orchestrator layer; continue past phase N's failure to phase N+1, and aggregate per-phase results at the end. |

## Verified Workflow

### Audit Checklist

When designing or reviewing a multi-phase pipeline, walk both layers:

1. **Orchestrator layer** — for each phase, confirm the four skip branches are explicit and each emits a distinct log line:
   - disabled by `--phases`
   - no open issues (only for phases that require `--issues`)
   - not final loop (only for final-loop-gated phases like `drive-green`)
   - shutdown requested (cooperative `SIGINT` / `SIGTERM`)
2. **Worker layer** — for every "already X" branch in the worker:
   - confirm it returns `success=True` (not `False`)
   - confirm it sets an informational flag (e.g., `plan_already_exists=True`) for the summary, not for control flow
   - confirm the end-of-run rc is `0`
3. **Summary print** — confirm the worker's summary counts `already_done` separately within the successful set, so operators can see the steady state without rc churn.
4. **Orchestrator control flow** — confirm the orchestrator's "should we advance to phase N+1" decision uses ONLY the worker's exit code, never the parsed counts.

### Worked Example (ProjectHephaestus, 2026-05-26)

**Files**:
- `scripts/loop_runner.py` — orchestrator; iterates phases, applies skip table (A), invokes per-phase worker, advances only on rc check
- `hephaestus/automation/planner.py:_has_existing_plan` — worker; returns `PlanResult(success=True, plan_already_exists=True)` when an issue already has a plan comment

**Steady-state run** (everything already planned):

```text
[loop 1/1] Phase: plan
  → invoking planner for 7 open issues
  Plan phase summary: Successfully planned: 0 / Already planned: 7 / Failed: 0
  Exit code: 0
[loop 1/1] Phase: review-plans
  → invoking plan reviewer for 7 issues with plans
  ...
```

Phase 1 returned `rc=0` despite doing zero new work. Phase 2 ran. The pipeline is healthy and observable.

## Results & Parameters

- **Source pipeline**: ProjectHephaestus `scripts/loop_runner.py` (plan → review-plans → implement → review-prs → address-review → drive-green)
- **Worker reference**: `hephaestus/automation/planner.py::_has_existing_plan` — returns `PlanResult(success=True, plan_already_exists=True)` on idempotent skip
- **Final-loop-gated phase**: `drive-green` (only runs on final iteration of the outer `--loops N` counter)
- **Cooperative shutdown**: `SIGINT` / `SIGTERM` flip a module-level flag checked between phases
- **RC contract**: orchestrator advances to phase N+1 iff worker `rc=0`; per-phase failures do NOT abort the pipeline (each phase is independent)
