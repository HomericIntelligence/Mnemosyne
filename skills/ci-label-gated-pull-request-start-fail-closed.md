---
name: ci-label-gated-pull-request-start-fail-closed
description: "Build pull-request CI that starts only after a state label is applied, without a skipped required check that counts as passed. Use when asked to make all pull-request workflows wait for a label, when a gate review finds one job or workflow that still runs unlabeled, or when a gated pull request must restart after a new commit."
category: ci-cd
date: 2026-11-18
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: unverified
tags:
  - github-actions
  - label-gated-ci
  - required-check
  - skipped-jobs
  - pull-request-target
  - fail-closed
  - aggregate-gate
---

# Label-Gated Pull-Request CI That Fails Closed

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Make every pull-request workflow wait for one label, and keep an unlabeled pull request unmergeable. |
| **Outcome** | Operational — the label started the full run on a real pull request. Final green was not confirmed when this entry was written. |

A workflow `on:` block cannot filter by label. The gate has two parts: a trigger that starts a
run only on the `labeled` event, and a job condition that checks the label payload. A job that
only skips is not enough, because a skipped required check counts as passed.

## When to Use

- A request says that no pull-request CI may start until a label is applied.
- A review finds one job, one downstream job, or one other workflow that still runs unlabeled.
- A gated pull request gets a new commit and the old label is still on it.
- A path-filtered gated job fails on a pull request that did not change the code under test.

## Verified Workflow

### Quick Reference

```yaml
on:
  pull_request:
    types: [labeled]          # no opened, reopened, or synchronize
jobs:
  real_job:
    if: ${{ (github.event_name != 'pull_request' || contains(github.event.pull_request.labels.*.name, 'GO_LABEL')) }}
  downstream_always_job:      # a job that uses always() must repeat the gate
    if: ${{ always() && (github.event_name != 'pull_request' || contains(github.event.pull_request.labels.*.name, 'GO_LABEL')) }}
  required_aggregate:         # the one required context
    if: ${{ always() }}
    steps:
      - name: Require the label        # first step, before any checkout
        if: github.event_name == 'pull_request'
        env: { LABELS: "${{ toJSON(github.event.pull_request.labels.*.name) }}" }
        run: grep -q '"GO_LABEL"' <<<"${LABELS}" || { echo "label missing" >&2; exit 1; }
      # every later step: if: <gate>   (an always() step: always() && <gate>)
```

### Suggested Approach

1. **Use the `labeled` type only.** An unlabeled pull request then starts no run, and the
   required context stays pending, which blocks the merge. Do not leave `synchronize` in the list.
2. **Make the required aggregate fail, not skip.** A `labeled` event for any other label starts a
   run in which every gated job skips. A skipped required context passes. Let the aggregate always
   run, fail in its first step when the label is absent, and require `success` from each upstream
   job so that a skipped upstream also fails it. Put the label step before checkout so that no
   pull-request code runs unlabeled. Guard every later step, including `always()` steps that run
   repository scripts.
3. **Enumerate before you claim "every job".** List each workflow that has a `pull_request` or
   `pull_request_target` trigger and each job in it. Gate root jobs, jobs that use `always()`,
   second jobs in the same file, and reusable-workflow calls. A job with `needs` on a gated job
   skips by itself, unless it uses `always()`. A source review found a missed job twice in this
   way, so do the list first.
4. **Gate trusted workflows by failing, not skipping.** A `pull_request_target` check that does
   not check out pull-request code is safe to run, but it is still a required context. Use the
   same first-step failure.
5. **Reset the label on a new commit.** Removal of the label from a `synchronize` event needs a
   `pull_request_target` workflow. That workflow runs from the default branch, so it does nothing
   on the pull request that adds it. Until it merges, remove the label by hand after a push and
   obtain a fresh review. Use the label token rules of the repository: a label that the default
   workflow token applies starts no workflow.
6. **Update the contributor text.** Advice such as "push a new head or reopen the pull request to
   start CI" is false after the change. Say that the label starts CI and that remove-and-apply
   restarts it.
7. **Read the first failing step when a gated, path-filtered job fails.** Such a job starts only
   for a pull request that touches its paths, so a stale fixture on the default branch (for
   example a fixed test-selection manifest that names a deleted test) appears first on the pull
   request that edits the workflow. Compare each manifest entry with the test functions that
   exist, remove the stale entry, and treat the failure as pre-existing, not introduced. See
   [PR CI failure triage: pre-existing vs introduced](pr-ci-failure-triage-preexisting-vs-introduced.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Job-level skip on the aggregate | Skip the required aggregate when the label is absent | A skipped required check counts as passed, so the pull request could merge unchecked | Fail the aggregate in its first step |
| Gate only the root jobs | Add the label condition to the first job of each workflow | Downstream `always()` jobs and a second job in one file still ran unlabeled | List every job in every pull-request workflow |
| Aggregate checks out code first | Keep the checkout, then fail on the label | Pull-request code ran before the label existed | Put the label step before checkout and guard later steps |
| Rely on the new reset workflow | Expect the reset workflow to remove the label on the same pull request | A `pull_request_target` workflow runs from the default branch, so it was absent | Remove the label by hand until the workflow merges |

## Results & Parameters

### Expected Output

- Unlabeled pull request: no run starts; the required context is pending.
- Other label on an unlabeled pull request: the aggregate fails in its first step; all other jobs
  skip; no pull-request code runs.
- Go label applied: the full run starts; each gated job runs; the aggregate needs `success` from
  each.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------------------- |
| a public repository with a sharded CI workflow set | Moving five pull-request workflows behind one label | Source review found the ungated aggregate, a second ungated job, and stale contributor text. The label then started a run with 49 checks passing and one pending. Final green was not confirmed. |

## References

- [Required aggregate gate green only because upstream was skipped](required-aggregate-gate-green-because-upstream-skipped.md)
- [Required-check path-filter pitfall](ci-required-check-path-filter-pitfall.md)
- [PR CI failure triage: pre-existing vs introduced](pr-ci-failure-triage-preexisting-vs-introduced.md)
