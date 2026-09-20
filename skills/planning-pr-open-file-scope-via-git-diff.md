---
name: planning-pr-open-file-scope-via-git-diff
license: BSD-3-Clause
description: "Ground PR file-scope claims in the actual diff when plan paths or expected file counts may be stale."
category: architecture
date: 2026-07-02
version: "1.1.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - pr-open
  - file-scope
  - git-diff
  - hardcoded-paths-hazard
  - allow-list
  - branch-state
---

# Planning: Ground PR File-Scope Claims in the Actual Diff

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-02 |
| **Objective** | Prevent plan-authored hardcoded file paths (e.g. `train.mojo`, `tests/models/test_mobilenetv1_train_step.mojo`) from making it into PR-open plans and then into PR bodies without verification against the branch's actual diff. |
| **Outcome** | PLAN ONLY — captured during ProjectOdyssey #5527 planning where the plan hardcoded two file paths without running `git diff --name-only` against the feature branch. The paths may be right; they were not verified. This skill formalizes the corrective pattern. |
| **Verification** | unverified |

## When to Use

- Planning a PR-open task where the plan wants to name the files that will change.
- Planning a PR that touches source + tests: the planner knows the source filename and is tempted to derive the test filename by convention (`test_<source>.mojo`), then hardcode it — but naming conventions vary between subprojects and the actual test may live at `tests/training/test_train.mojo` rather than `tests/models/test_<model>_train_step.mojo`.
- Any planning session where a file path in the plan does not appear in a `git diff --name-only` output the planner has actually seen (either because the branch is not checked out yet or because the planner is drafting the plan from memory).
- Preparing a PR summary whose file list may differ from an earlier plan.

## Verified Workflow

This is unverified planning guidance. Use current source to locate intended edits and the final diff
to describe completed work. A plan can name verified paths; patterns are useful when the exact path
is not yet known.

### Quick Reference

```bash
git diff --name-only <base>...HEAD
git diff <base>...HEAD -- <path>
```

### Detailed Steps

1. Inspect the intended source and test locations rather than deriving one filename from another.
2. Compare the current changed-file list with the task's authorized scope.
3. Investigate unexpected files or counts. A necessary test, documentation update, or renamed path
   may explain the difference without requiring permission or a halt.
4. Correct unintended edits while preserving unrelated existing work. Ask only when the necessary
   change would materially expand the authorized task.
5. Summarize the actual behavior and relevant files in the PR. A verbatim file inventory is optional
   unless the repository's PR format consumes it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | ProjectOdyssey #5527 planning session: hardcode `train.mojo` and `tests/models/test_mobilenetv1_train_step.mojo` in the plan as the exact files the PR touches, without running `git diff --name-only` against the feature branch. | The plan cannot verify the paths without either checking out the branch or trusting a mental model of what was committed. If `train.mojo` is actually under `src/projectodyssey/training/` or the test file is under `tests/training/`, the hardcoded paths in the PR body will be wrong. | Use allow-list patterns in the plan; materialize actual paths from `git diff --name-only` at execute time. |
| Attempt 2 | Derive the test filename from the source filename by convention (`test_<source>.mojo`). | The convention is not universal — different subprojects use different test paths (`tests/training/`, `tests/models/`, `tests/integration/`). Conventions drift; the branch is authoritative. | Grep the repo's actual test-file naming pattern with `git ls-files` before writing any allow-list. |

## Results & Parameters

- Input: requested behavior, intended base, current source, and the candidate diff.
- Output: an accurate PR summary and resolved or explicitly reported scope discrepancies.
- File counts and allow-list patterns are investigation aids unless an actual repository contract
  makes them binding. An unexpected count alone is not a reason to stop the task.
- Verification remains `unverified`; no executed implementation result is claimed.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #5527 planning session (2026-07-02) — captured the anti-pattern (hardcoded `train.mojo` and `tests/models/test_mobilenetv1_train_step.mojo` in plan). Corrective pattern PLAN ONLY, not executed. | See ProjectOdyssey issue #5527 comments. |

## References

- [fix-hardcoded-target-path](fix-hardcoded-target-path.md) — sibling skill; covers hardcoded paths in SCRIPTS, whereas this skill covers hardcoded paths in PR-open PLANS.
- [planning-pr-body-extract-sibling-artifact-at-runtime](planning-pr-body-extract-sibling-artifact-at-runtime.md) — companion skill; uses the same `<<TOKEN>>` placeholder pattern for cross-issue artifact content.
- [planning-pr-body-numeric-claims-source-derived](planning-pr-body-numeric-claims-source-derived.md) — companion skill for numeric claims.
- [planning-pr-open-load-bearing-assumption-hygiene](planning-pr-open-load-bearing-assumption-hygiene.md) — companion skill for repo-settings and compat-script probes.
