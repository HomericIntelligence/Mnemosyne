---
name: automation-loop-no-update-plan
license: BSD-3-Clause
description: "Never pass `--update-plan` to a Hephaestus automation-loop wave. Use when you launch `hephaestus-automation-loop` over issues that already have plans, and you wonder whether to refresh every plan from origin/main first. The durable state-label vocabulary already routes re-planning; the flag forces a fresh revision on every selected plan-go issue and, on the v0.12 queue pipeline, turns the wave into first-publication blocks with zero merges."
category: tooling
date: 2026-10-15
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - hephaestus-automation
  - automation-loop
  - update-plan
  - forced-replanning
  - first-publication
  - state-labels
  - wave-sizing
  - launch
---

# Never Pass --update-plan to an Automation-Loop Wave

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-15 |
| **Objective** | Launch an issue wave without re-opening approved plans or losing the wave to forced-revision failure. |
| **Outcome** | Rule established from one 19-issue wave launched with `--update-plan` (v0.12.1.dev queue pipeline): the coordinator forced a new revision on every already-approved issue, 11 of 19 items ended blocked (9 with `BLOCKED:first_publication_discovery_failed`), 8 failed, and zero PRs merged after approximately 102 agent jobs and 54 agent-hours. Waves launched without the flag on the same host made merges the same week. |
| **Verification** | verified-live: the failure wave and follow-up waves without the flag ran on one multi-tenant automation host against one target repository. |

## When to Use

- You launch `hephaestus-automation-loop` and consider `--update-plan` (its help text says
  "Update each selected issue plan from current origin/main, then continue the queue") because
  origin/main moved since the plans were written.
- The selected issues already carry approved plans (`state:plan-go`), and some have published
  branches or open PRs.
- A previous wave blocked many items at planning with `BLOCKED:first_publication_discovery_failed`
  or failed them with `plan not found`, and you must decide how to relaunch.

## Core rule

The durable state labels are the plan-refresh mechanism. There is no ambient "stale plan"
problem to fix at launch:

- `state:needs-plan` issues enter the planner normally.
- `state:plan-no-go` issues re-plan on the next loop.
- `state:plan-go` issues fast-forward to implementation; the approved plan is the asset.
- `state:plan-blocked` and `state:skip` are stronger stops that a refresh flag does not and
  must not bypass.

`--update-plan` overrides that routing. For every selected issue it forces a new plan revision:
the coordinator logs `forced revision entry; add ['state:plan-no-go'], remove ['state:plan-go', 'state:needs-plan']`
and re-runs the full planner-and-review budget for an approval the issue already had. On the
v0.12 queue pipeline the forced entry then re-binds durable source-workspace records. An item
with no open PR re-binds to a branch that carries a fresh run nonce, while its existing records
bind the old one; the first-publication pre-intent check fails closed and the item ends
`BLOCKED:first_publication_discovery_failed` at planning, one budget cycle at a time, for hours.

Refresh a plan only as a deliberate per-issue act. Label one issue back to `state:needs-plan`, or
run a small single-issue pass with `--force`. Never refresh a wave.

## Verified Workflow

### Quick Reference

```bash
# Launch the wave WITHOUT any plan-refresh flag. Trust the labels.
cd <clean scratch checkout>
hephaestus-automation-loop \
  --issues <comma list> \
  --stages planning,plan_review,implementation,pr_review,merge_wait \
  --agent <agent> --planner-model <m> --implementer-model <m> --reviewer-model <m> \
  --max-workers 4 \
  --gh-extra-path-root <real-gh-dir> -v --log-file <run>.log

# Do NOT add: --update-plan  (never)
# Do NOT add: --force        (reserved for a deliberate single-issue re-plan)

# To refresh ONE plan: move that issue back, or run a small one-issue pass.
gh issue edit <n> --add-label state:needs-plan --remove-label state:plan-go
hephaestus-automation-loop --issues <n> --force ...   # single issue only
```

### Suggested Approach

1. Size the wave and the worker count from telemetry instead of refreshing plans up front.
   Follow the batch and worker guidance in
   [automation-loop-backlog-cost-scaling](automation-loop-backlog-cost-scaling.md): small,
   homogeneous batches make a bad plan cheap to re-drive, and they keep one bad revision from
   consuming the wave budget.
2. Let required checks and exact-head review catch integration drift. A plan written before
   origin/main moved is still an acceptance asset; the fast-forward carried it for a reason.
   Rebase conflicts are implementation-stage evidence, not a launch-time problem.
3. If a wave did run with the flag, do not relaunch the same selection with the flag removed
   and expect convergence. Previously approved issues now hold `state:plan-no-go` with no new
   revision, and blocked items have stale durable records. Drive the `plan-no-go` issues through
   one small re-plan pass first; for the first-publication blocks, follow the record-disposition
   sequence in
   [hephaestus-interrupted-implementation-lane-recovery](hephaestus-interrupted-implementation-lane-recovery.md).
4. Launch from a clean, dedicated checkout of the target repository. An unrelated dirty linked
   worktree anywhere in the source checkout makes the intake fail before any issue work starts
   (`repository-intake requires a clean tracked tree`), which hides the plan-routing behavior
   this rule protects.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Wave-wide plan refresh | A 19-issue wave launched with `--update-plan`, `--stages planning,plan_review,implementation,pr_review,merge_wait`, `--max-workers 20`, against issues that mostly held `state:plan-go` | The coordinator forced a revision on every approved issue; 9 items blocked in first-publication discovery (roughly 1 to 5.5 hours of agent budget each), 2 blocked with "planning made no progress", 5 failed with "plan not found", 1 failed with `plan_cycles_exhausted`, 2 failed on pretest paths; zero PRs merged in ~5.7 wall hours | Every failure class occurred only on issues the flag forced to re-plan. The flag converts an approved plan from an asset into a fresh liability at wave scale |
| Refresh as safety before merge | Same wave reasoning: "origin/main moved, so refresh every plan first" | Forced revisions re-entered publication binding; on direct pre-PR items the new run nonce conflicted with the durable records of the interrupted prior run | Integration drift belongs to the implementation lane and its guards (rebase evidence, required checks, exact-head review). It is not a reason to reopen approvals |
| Flag-neighbor assumption | `--update-plan` treated as a lighter form of `--force` that would only touch stale plans | The forced entry does not inspect plan staleness; it rewrites state for every selected issue, including `plan-go` items with open PRs | The flag is unconditional. The select-the-stale-issues judgment you wanted does not exist at the flag level; make it per issue with labels or `--force` |

## Results & Parameters

### Configuration

```bash
# Wave launch contract that routes through the label vocabulary
hephaestus-automation-loop \
  --issues <explicit list> \
  --stages planning,plan_review,implementation,pr_review,merge_wait \
  --agent <agent> \
  --planner-model <model> --implementer-model <model> --reviewer-model <model> \
  --max-workers 4 \
  --gh-extra-path-root <dir-with-the-real-gh-binary> \
  -v --log-file <run>.log
```

- `--max-workers 4`, not 20: a large wave of forced revisions self-contends on the shared
  intake, and each blocked item still consumes its full agent budget.
- No `--fallback-model` is required by this rule; size planner and reviewer timeouts for the
  chosen models as usual.

### Expected Output

- Items at `state:needs-plan` and `state:plan-no-go` move through planning; items at
  `state:plan-go` fast-forward past the planner (`plan already approved` path) toward
  implementation.
- No log line of the form `forced revision entry; add ['state:plan-no-go']` appears, and no
  item blocks with `first_publication_discovery_failed` that was not already carrying an
  interrupted implementation record.
- Follow-up waves without the flag can implement; merged PRs and closed issues accumulate
  instead of plan-review minutes.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Hephaestus automation loop + one target repository | v0.12.1.dev6 queue pipeline; one 19-issue wave with `--update-plan` (11 blocked, 8 fail, 0 merges, ~102 agent jobs) against follow-up waves without the flag on the same host and backlog | Aggregate counts in this skill; session evidence held by the learning run |

## References

- [hephaestus-interrupted-implementation-lane-recovery](hephaestus-interrupted-implementation-lane-recovery.md) —
  why a fresh run nonce plus stale durable records produces `BLOCKED:first_publication_discovery_failed`,
  and the record-disposition recovery that this skill deliberately avoids needing.
- [automation-loop-backlog-cost-scaling](automation-loop-backlog-cost-scaling.md) — batch and
  worker sizing that replaces the temptation to de-risk a large wave by refreshing its plans.
- [automation-forced-replanning-journal-recovery](automation-forced-replanning-journal-recovery.md) —
  the proposed durable-journal semantics of a forced revision; this skill is the operator-side
  rule that such revisions belong to deliberate single-issue acts, not waves.
- [hephaestus-loop-unconfigured-host-operation](hephaestus-loop-unconfigured-host-operation.md) —
  host bring-up and launch mechanics for a first loop on a new machine.
