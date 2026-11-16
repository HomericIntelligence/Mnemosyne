---
name: required-aggregate-gate-green-because-upstream-skipped
description: "Detect a required check that reports success only because every real job was skipped by a label or event condition, and report it as not run. Use when a required aggregate or fan-in gate is green while lint, typecheck, or test jobs show skipped, when a pull request has been open for a long time with no failing check, or before a verdict claims a required check passed."
category: ci-cd
date: 2026-11-02
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
tags:
  - aggregated-check
  - fan-in-gate
  - skipped-jobs
  - required-check
  - label-gated-ci
  - vacuous-success
  - branch-protection
  - job-steps
  - check-runs
---

# Required Aggregate Gate Green Only Because Every Upstream Job Was Skipped

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Decide whether a green required check is real evidence or the result of a condition that skipped every job behind it. |
| **Outcome** | Successful — a required aggregate check reported `success` at every push while lint, typecheck, and 32 test shards were all `skipped`. The rollup counted one green conclusion and no red one. Applying the gating label started real work, and the same check then reported `success` with the lint, typecheck, and policy jobs executed. |

A required aggregate or fan-in gate usually only collects the results of other jobs. When a job
condition skips every upstream job, the gate has nothing red to collect. The gate reports
`success`, and the branch reads as verified. The gate is green. The work did not run.

## When to Use

- A required aggregate check is green, but lint, typecheck, or test jobs are `skipped`.
- A pull request has many pushes and no failing check, and nobody applied a repository label.
- A review verdict must state whether a required check passed for an exact commit.
- An event condition (label, path filter, draft state, or branch name) controls whether the
  workload starts.

## Verified Workflow

### Quick Reference

```bash
H=<commit>
# 1. Which checks are not skipped, and what did they conclude?
gh api repos/<user>/<repo>/commits/$H/check-runs \
  --jq '.check_runs[] | select(.conclusion != "skipped")
        | [.name, .status, .conclusion] | @tsv'
# 2. The number of skipped checks is the warning sign.
gh api repos/<user>/<repo>/commits/$H/check-runs \
  --jq '[.check_runs[] | select(.conclusion == "skipped")] | length'
# 3. Read the aggregate job's own steps. A skipped job has no steps.
gh api repos/<user>/<repo>/actions/jobs/<job-id> \
  --jq '{conclusion, steps: [.steps[] | [.name, .conclusion] | @tsv]}'
```

### Suggested Approach

1. **Separate the gate from the workload.** Read every check run at the commit. Keep the real jobs
   (lint, typecheck, test shards) apart from the aggregate gate.
2. **Count skipped real jobs.** Any skipped lint, typecheck, or test job means the gate did not
   judge work.
3. **Find the skip condition.** Read the workflow's `if:` expressions on the real jobs and on the
   gate. Look for a label gate, a path filter, a draft check, or an event-type condition.
4. **Read the gate's steps.** Fetch the aggregate job by id. If the steps ran, the job started. If
   the step names show only setup and reporting, the gate collected empty results. Compare the
   step list before and after the condition is satisfied.
5. **Satisfy the condition, do not change the workflow.** Apply the label, convert the draft, or
   change the path. Wait for a new run at the same commit or a new commit. Do not edit the gate to
   make the result real. The gate is correct by design. The condition was not met.
6. **Reapply the same test.** After the condition is satisfied, confirm that lint, typecheck, and
   test steps ran and concluded. A green gate with executed steps is evidence. A green gate with
   skipped steps is not.
7. **Report the state precisely.** Write "the required check passed" only when the workload ran.
   For a skipped run, write "not run: the label or event condition was absent".

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------------- | ----------------- | --------------- | ---------------- |
| Read the rollup color | Read the required check as `success` on the pull request page | A skipped job does not fail the aggregate. The rollup had one green conclusion and no red one, so it never showed the absence | A green aggregate says nothing about the workload. Count skipped real jobs first |
| Change the workflow gate | Considered an edit to the aggregate `if: always()` or the label condition to make the check honest | The gate design was correct. The pull request did not meet the condition | Fix the condition, not the gate. Apply the label or change the event |
| One-rollup conclusion in a verdict | Prepared to write that the required check passed at the head | The check steps were setup and reporting only. No lint or test ran | Read the aggregate job's steps before a verdict cites its result |
| Rerun the workflow | Re-ran the green aggregate job | A rerun repeats the same condition result | Reruns do not create work that a condition skips |

## Results & Parameters

### Configuration

```yaml
# Shape that produces a vacuous green aggregate.
real_job:
  if: contains(github.event.pull_request.labels.*.name, 'state:implementation-go')
aggregate_required_check:
  needs: [real_job, ...]
  if: always()          # collects results even when real jobs are skipped
```

- Record per commit: the names and conclusions of executed checks, the count of skipped checks, and
  the aggregate job's step list.
- Treat a required-check result as evidence only when the workload steps ran.

### Expected Output

- Before the condition: real jobs `skipped`, aggregate `success`, aggregate steps limited to setup
  and reporting.
- After the condition: real jobs `success`, aggregate `success`, aggregate step names include the
  upstream-success requirement.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| a public repository with sharded CI | Review of a long-lived pull request | The required aggregate check was green while 32 test shards and lint were skipped. One label started real runs and all steps passed. |

## References

- [PR CI failure triage: pre-existing vs introduced](pr-ci-failure-triage-preexisting-vs-introduced.md)
- [Post-merge CI failure attribution](post-merge-ci-failure-attribution.md)
- [Pre-commit whole-directory hook blocks unrelated commits](ci-precommit-whole-dir-format-drift-blocks-unrelated-commits.md)