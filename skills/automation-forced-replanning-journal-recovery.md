---
name: automation-forced-replanning-journal-recovery
license: BSD-3-Clause
description: "Teach a fail-closed forced-replanning workflow for queue pipelines with durable GitHub plan journals. Use when: (1) a force flag must bypass approved-plan and open-PR shortcuts, (2) an approved canonical plan must become a new reviewed revision, (3) partial archive or canonical writes must recover without duplicate planner jobs, or (4) stale hydrated state could republish an old plan after an agent failure."
category: architecture
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - automation
  - forced-replanning
  - durable-journal
  - plan-revision
  - crash-recovery
  - fail-closed
  - state-labels
  - queue-pipeline
  - idempotency
  - behavior-first-testing
---

# Forced Replanning With Durable Journal Recovery

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Make an operator force flag reopen an approved plan, publish exactly one fresh canonical revision, and route it through plan review even when an open PR exists. |
| **Outcome** | Proposed state-classification, label-transition, publication, retry, and restart-test pattern for ProjectHephaestus's queue pipeline. |
| **Verification** | unverified — the design and acceptance tests were specified, but the Hephaestus implementation and CI were not executed in the learning session. |

The core rule is that force changes only two planning shortcuts: approved-plan
fast-forward and open-PR skip. Closed issues, operator `state:skip`, and
`state:plan-blocked` remain higher-priority stops. Replanning continues to use
the existing canonical-plan journal, archive records, pending-review sentinel,
and mutually exclusive state-label helpers; force does not introduce another
state owner.

## When to Use

- A planning CLI exposes `--force`, but the stage-facing configuration silently
  drops the value before `PlanningStage` evaluates its shortcuts.
- An issue has `state:plan-go` and an approved canonical plan, and the operator
  needs a new revision even though an open PR already exists.
- A forced run restarts after some, but not all, archive/canonical journal writes
  completed and must resume review without invoking the planner again.
- `state:plan-go` exists without a canonical plan and force must repair the
  inconsistent state by publishing an initial plan rather than inventing a
  revision.
- A failed planner job leaves an older canonical plan visible in GitHub and the
  stage must not mistake that old plan for the new candidate.
- A label mutation can partially succeed or its readback can be inconclusive;
  no planner request should be scheduled until the exclusive state is confirmed.
- Restart tests currently fabricate labels or comments instead of driving the
  real `PlanningStage` and `PlanReviewStage` interfaces.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a
> proposed implementation and test pattern until the focused ProjectHephaestus
> tests and CI pass. Mnemosyne skill validation proves document structure only.

### Quick Reference

```python
# 1. Preserve the operator decision across the coordinator boundary.
self._stage_config = _StageRunConfig(
    enable_advise=not config.no_advise,
    force=config.force,
    # ...existing fields...
)

# 2. Force bypasses only the two normal shortcuts.
if is_exclusive_plan_state(labels, STATE_PLAN_GO) and not ctx.config.force:
    return StageOutcome(Disposition.ADVANCE, "plan already approved")

open_pr = ctx.github.find_pr_for_issue(item.issue)
if open_pr and not ctx.config.force:
    return StageOutcome(Disposition.SKIP, f"open PR #{open_pr} exists")

# 3. Reconcile the durable journal before classifying forced entry.
comments = reconcile_plan_journal(item.issue, ctx.github)
snapshot = journal_snapshot(comments)

# 4. Never retain the old canonical plan as a new-revision candidate.
if is_replan_entry:
    item.payload["requires_plan_revision"] = True
    item.payload.pop("plan_text", None)

# 5. A failed revision candidate retries the planner budget.
awaiting_revision_candidate = (
    item.payload.get("requires_plan_revision", False)
    and item.payload.get("plan_text") is None
)
```

### Detailed Steps

1. **Propagate force into the stage-facing configuration.** A CLI/parser test
   that proves `PipelineConfig.force` is true is insufficient if the coordinator
   constructs a separate `_StageRunConfig`. Pass `force=config.force` at that
   boundary and assert `coordinator._ctx_for_repo(...).config.force is True`.

2. **Keep the stop-order contract intact.** Evaluate closed issue,
   `state:skip`, and `state:plan-blocked` guards before force-specific behavior.
   Gate only the normal `state:plan-go` fast-forward and open-PR skip with
   `not ctx.config.force`. This preserves non-forced behavior while allowing an
   explicit operator request to reopen planning.

3. **Reconcile the durable journal before classifying entry.** The journal is
   the recovery authority. Hydrate `plan_text` and `plan_revision` from the
   reconciled canonical plan, then distinguish these cases:

   | Durable entry state | Classification | Required entry label | Planner job? |
   |---------------------|----------------|----------------------|--------------|
   | Approved canonical plan, no matching pending review for its next revision | Forced revision | `state:plan-no-go` | Yes |
   | Newly published canonical revision with matching pending-review sentinel | Recovered published revision | `state:needs-plan` | No; resume verification/review |
   | `state:plan-go` but no canonical plan | Forced initial plan | `state:needs-plan` | Yes, as revision 1 |
   | Ordinary non-forced initial planning | Initial plan | `state:needs-plan` | Yes |

   A revision is already published only when a canonical plan exists and the
   current review is a pending-review sentinel for the exact same revision.
   Revision-number equality is essential: a stale sentinel from revision 1 must
   not authorize revision 2.

4. **Establish one exclusive state label before agent work.** For a new forced
   revision, atomically replace the approved state with `state:plan-no-go` and
   keep that label until the new journal publication is durable. For a recovered
   published revision or a forced initial plan, enter `state:needs-plan`.
   Re-read labels through the existing transition helper and confirm the expected
   exclusive state. If readback is not exclusive, return `Disposition.RETRY`
   before scheduling an agent. Let GitHub mutation/read exceptions cross the
   existing coordinator poisoned-item boundary; do not catch them and continue.

5. **Separate the old canonical plan from the new candidate.** Reconciliation
   must hydrate the old plan so the stage can classify recovery, but a genuine
   replan entry must then set `requires_plan_revision=True` and remove
   `item.payload["plan_text"]`. Otherwise a failed planner job can fall through
   verification, see the old canonical plan, and republish or advance stale
   content.

6. **Publish before routing.** When the planner produces a candidate, use the
   existing journal publisher. A revision publication must archive the old plan
   and review, write the new canonical plan, and write its matching pending-review
   sentinel before the stage advances. Only after those durable artifacts exist
   may the state label move to `state:needs-plan` and the item route to plan
   review. Do not add a database, local state file, or second revision counter.

7. **Treat the journal reconciler as the restart transaction coordinator.** If
   a write fails after one or more archive/canonical mutations, a fresh work item
   should call `reconcile_plan_journal()` first. The reconciler must converge the
   partial mutation set to one revision-2 canonical plan, one matching
   pending-review sentinel, and immutable revision-1 plan/review archives. That
   recovered classification skips a second planner job and resumes verification.

8. **Retry planner failure within the existing plan budget.** In verification,
   compute `awaiting_revision_candidate` before testing whether GitHub still has
   a plan. If a required revision has no candidate, do not use
   `has_existing_plan()` as success evidence. Increment the existing `plan`
   attempt counter, return to `PLAN_WAIT` while budget remains, and finish-fail
   only when that budget is exhausted.

9. **Test behavior through real stage interfaces.** Drive `PlanningStage` from
   `ENTER` through its real planner `JobRequest`, feed a `JobResult`, publish,
   restart with a fresh `WorkItem`, and then drive `PlanReviewStage` until its
   real review `JobRequest`. Assert artifacts and routing, not only a returned
   `ADVANCE` disposition.

10. **Keep documentation synchronized with the state machine.** The planning
    stage docstring should state that force bypasses approved-plan/open-PR
    shortcuts, new revisions remain `state:plan-no-go` until durable publication,
    and recovered pending revisions resume review without another planner call.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Prove force only at CLI parsing or scope seeding | The top-level config was true, but `Coordinator` omitted it when constructing `_StageRunConfig`. | `PlanningStage` still observed the default false value and took normal shortcuts. | Assert force at the `StageContext` boundary and pass it explicitly through every config projection. |
| Let force bypass every early stop | Force was treated as a general override for closed, skipped, or plan-blocked issues. | This weakened operator and safety states unrelated to stale-plan/open-PR shortcuts. | Force should bypass only `state:plan-go` fast-forward and open-PR skip. Preserve higher-priority stops. |
| Replace `state:plan-go` with `state:needs-plan` immediately for every forced revision | The transition erased the durable signal that the old approved plan was being superseded before a new revision existed. | A crash could make an unpublished revision look like ordinary planning or review-ready work. | Keep new revisions at `state:plan-no-go` until publication; use `state:needs-plan` only for recovered published or initial plans. |
| Trust a successful label edit call without readback | A partial mutation added the new label but failed to remove the old one. | Two mutually exclusive states remained, yet the planner could still be scheduled. | Re-read and confirm exactly one expected state; otherwise retry before agent work. |
| Leave hydrated `plan_text` in the payload while requesting a revision | The old canonical plan remained a plausible candidate after the planner failed. | Verification could publish or advance stale revision-1 content. | Clear `plan_text` on new-revision entry and distinguish `awaiting_revision_candidate` from an existing canonical plan. |
| Invoke the planner again after a partial journal write | Restart logic classified only from in-memory state or the label. | It duplicated expensive work and risked a second revision publication. | Reconcile journal artifacts first; a canonical revision with a matching pending sentinel resumes review without replanning. |
| Assert only that restart returns `ADVANCE` | The test did not inspect canonical revision, pending sentinel, archive immutability, or actual review scheduling. | A broken recovery path could pass while losing history or never requesting review. | Assert revision 2, exact current content, matching pending review, immutable revision-1 archives, and a real `PlanReviewStage` `JobRequest`. |
| Treat `state:plan-go` without a canonical plan as a revision | Revision logic assumed an old plan body existed. | Publication could create revision 2 with no revision-1 artifact or archive meaningless content. | Classify it as forced initial planning, transition to `state:needs-plan`, and publish revision 1. |

## Results & Parameters

### Required State Invariants

```text
normal + state:plan-go       -> ADVANCE (unchanged)
normal + open PR             -> SKIP (unchanged)
force + approved plan        -> state:plan-no-go -> planner -> publish R(n+1)
force + open PR              -> do not skip; same forced classification applies
force + published pending Rn -> state:needs-plan -> no planner -> plan review
force + plan-go/no canonical -> state:needs-plan -> planner -> publish R1
unconfirmed exclusive label  -> RETRY before JobRequest
failed revision planner      -> PLAN_WAIT retry; old canonical remains untouched
partial publication restart  -> reconcile -> exactly one canonical/pending pair
```

### Behavior-First Assertions

```python
snapshot = journal_snapshot(github.issue_comments(issue))
assert snapshot.revision == 2
assert snapshot.current_plan == "Plan v2"
assert is_pending_review(snapshot.current_review, revision=2)

history = {
    (artifact.revision, artifact.kind): artifact.body
    for artifact in snapshot.history
}
assert set(history) == {(1, "plan"), (1, "review")}
assert archived_old_plan(history[(1, "plan")]) == "Plan v1"
assert archived_new_plan(history[(1, "plan")]) == "Plan v2"

review_request = PlanReviewStage().step(item, ctx)
assert isinstance(review_request, JobRequest)
assert review_request.job.descr == "review"
assert review_request.job.prompt_kwargs["plan_text"] == "Plan v2"
```

### Proposed Validation Commands

```bash
# Focused forced replan, normal open-PR behavior, and recovery paths
uv run pytest \
  tests/unit/automation/pipeline/stages/test_stage_planning.py \
  tests/unit/automation/pipeline/stages/test_stage_plan_review.py \
  tests/unit/automation/pipeline/test_plan_journal.py \
  tests/unit/automation/pipeline/test_coordinator.py -v

# Modified Python surface
uv run ruff check \
  hephaestus/automation/pipeline/coordinator.py \
  hephaestus/automation/pipeline/stages/planning.py \
  tests/unit/automation/pipeline/stages/test_stage_planning.py \
  tests/unit/automation/pipeline/test_coordinator.py
```

### Verification Promotion

Promote this skill to `verified-local` only after the focused stage, journal,
coordinator, and lint commands pass against the implementation. Promote it to
`verified-ci` only after the corresponding Hephaestus PR's required CI passes.
When promoting, archive this version in a `.history` file and record the exact
test counts, PR, and commit SHA.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Proposed `hephaestus-plan-issues --force` planning-stage revision and recovery design | Not implemented or run during capture; CI validation pending. |
