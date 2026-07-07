---
name: testing-pipeline-crash-matrix-real-stage-durability
description: "Use when: (1) strengthening ProjectHephaestus pipeline crash-matrix or restart/re-seeding tests, (2) replacing hand-fabricated GitHub journal labels or PR records with real PlanReviewStage / ImplementationStage transitions, (3) making fake GitHub PR creation durable enough for classifier lookup paths, (4) testing crash recovery from durable state:plan-go or PR_CREATE boundaries."
category: testing
date: 2026-07-07
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - projecthephaestus
  - crash-matrix
  - durable-journal
  - pipeline-tests
  - restart
  - re-seeding
  - plan-review-stage
  - implementation-stage
  - fake-github
  - classifier
---

# Pipeline Crash-Matrix Tests With Real Durable Stage Transitions

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-07 |
| **Objective** | Strengthen ProjectHephaestus issue #1900 crash-matrix coverage by replacing hand-fabricated S3/S4 journal states with real `PlanReviewStage` and `ImplementationStage` transitions. |
| **Outcome** | Proposed test-only durability pattern: drive the actual stage methods until they emit durable `state:plan-go` and PR creation records, then simulate crash/re-seeding and classify from the fake GitHub state that production-style lookup paths read. |
| **Verification** | unverified - captured from implementation learning. Do not claim verified-local or verified-ci unless the ProjectHephaestus crash-matrix tests themselves are run. |

## When to Use

- A crash-matrix, restart, or re-seeding test currently fabricates GitHub journal state directly instead of driving the real stage boundary that should have written that state.
- A pipeline classifier should decide from durable fake GitHub facts, but the test helper still reads in-memory `WorkItem` fields or explicit override arguments.
- A fake GitHub implementation records created PRs in a side channel that `find_pr_for_issue()` does not read, so restart classification cannot see PRs created by the stage under test.
- You need coverage for the crash window after `state:plan-go` is durable but before implementation is re-seeded, or after PR creation is durable but before PR review is re-seeded.

## Verified Workflow

<!-- The validator requires this heading. Because verification is unverified, treat the subsection below as proposed until the real ProjectHephaestus tests pass. -->

### Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end in this learning capture. Treat as a hypothesis until the ProjectHephaestus tests for issue #1900 pass locally or in CI. Running only `python3 scripts/validate_plugins.py` in ProjectMnemosyne validates this skill file, not the ProjectHephaestus behavior.

### Quick Reference

```python
# S3: plan review crash boundary
await PlanReviewStage(...).step(item, ctx)  # item at EVAL, verdict=ReviewVerdict("GO")
assert gh.has_mutation(issue, "state:plan-go")
assert _classify_from_fake(gh, issue) == StageName.IMPLEMENTATION

# S4: implementation PR creation crash boundary
stage = ImplementationStage(...)
await stage.step(item, ctx)  # ENTER
await stage.step(item, ctx)  # GATE
await stage.step(item, ctx)  # PR_CREATE
assert gh.has_mutation(issue, "gh_pr_create")
assert gh.has_mutation(issue, "defer_auto_merge")
assert _classify_from_fake(gh, issue) == StageName.PR_REVIEW
```

### Detailed Steps

1. **Keep the production invariant as the source of truth.** Before writing or repairing the test, confirm the real stage owns the durable mutation:
   - `PlanReviewStage._eval()` writes `state:plan-go` before it advances or waits for learn.
   - `ImplementationStage.step()` routes `PR_CREATE` to `_create_pr()`.
   - `_create_pr()` creates and stores the PR, defers auto-merge, then advances.

2. **Make fake PR creation durable through the same lookup path the classifier uses.** `FakeStageGitHub.create_pr()` should record created PRs by issue in `_open_prs`. `find_pr_for_issue()` should prefer those durable created PRs over any constructor canned fallback, so a PR emitted by `ImplementationStage` is visible after the simulated crash.

3. **Make classifier helpers read fake GitHub facts by default.** `_classify_from_fake(gh, issue)` should derive open/merged PR facts from fake GitHub by default instead of reading in-memory `WorkItem` fields or requiring explicit overrides for ordinary cases. Use overrides only for the edge case the fake cannot represent.

4. **S3 pattern: drive `PlanReviewStage`, then classify from durable fake state.**
   Put the item at the `EVAL` step and provide a real `ReviewVerdict("GO")`. Call `PlanReviewStage.step()`, assert the `state:plan-go` mutation exists in fake GitHub, simulate crash/re-seeding by discarding the in-memory item state, then call `_classify_from_fake(gh, issue)` and expect `StageName.IMPLEMENTATION`.

5. **S4 pattern: drive `ImplementationStage` through PR creation, then classify from durable fake state.**
   Run `ImplementationStage` through `ENTER -> GATE -> PR_CREATE`. Assert both `gh_pr_create` and `defer_auto_merge` mutations exist. Then call `_classify_from_fake(gh, issue)` without an explicit PR override and expect `StageName.PR_REVIEW`.

6. **Keep the test-only boundary explicit.** This pattern should not require production changes if the invariants above already exist. The edits belong in fake/test helpers and crash-matrix tests unless a real production invariant is missing.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Hand-fabricated S3 by directly adding `state:plan-go` or similar journal state in the test. | It proves the classifier handles a label, but it does not prove `PlanReviewStage._eval()` durably writes that label before the crash boundary. | Drive the real `PlanReviewStage.step()` with a `ReviewVerdict("GO")`, assert the durable mutation, then re-seed/classify. |
| 2 | Hand-fabricated S4 by injecting a PR fact or mutating `WorkItem` state instead of letting implementation create the PR. | It skips the crash-sensitive boundary where `_create_pr()` should create/store the PR, defer auto-merge, then advance. | Drive `ImplementationStage` through `ENTER -> GATE -> PR_CREATE` and assert `gh_pr_create` plus `defer_auto_merge` before classification. |
| 3 | Let `FakeStageGitHub.create_pr()` return a PR but not record it where `find_pr_for_issue()` looks. | Restart classification could not see the PR that the stage just created, so tests needed explicit overrides or stale in-memory state. | Store created PRs by issue in `_open_prs`; make `find_pr_for_issue()` prefer those durable records over canned constructor data. |
| 4 | Implement `_classify_from_fake()` around `WorkItem` state or explicit PR/open/merged overrides. | A crash/restart test should prove reconstruction from durable GitHub facts; reading the pre-crash item state makes the test non-durable. | Default `_classify_from_fake()` to fake GitHub lookup paths for open/merged PR facts; keep overrides exceptional and documented. |

## Results & Parameters

### Expected Test Signals

```text
S3 crash boundary:
  setup: item enters PlanReviewStage at EVAL with ReviewVerdict("GO")
  durable evidence: mutation log contains state:plan-go
  restart classification: StageName.IMPLEMENTATION

S4 crash boundary:
  setup: item runs ImplementationStage through ENTER -> GATE -> PR_CREATE
  durable evidence: mutation log contains gh_pr_create and defer_auto_merge
  restart classification: StageName.PR_REVIEW
```

### Production Invariants To Re-Check

- `PlanReviewStage._eval()` writes `state:plan-go` before any advance or learn-wait behavior.
- `ImplementationStage.step()` dispatches the `PR_CREATE` step to `_create_pr()`.
- `_create_pr()` creates and stores the PR, defers auto-merge, and only then advances.

### Verification Notes

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1900 crash-matrix coverage | Verification level remains `unverified` in this skill until the real ProjectHephaestus tests are run. ProjectMnemosyne skill validation alone does not verify the crash-matrix behavior. |
