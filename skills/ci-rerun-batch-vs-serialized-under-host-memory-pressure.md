---
name: ci-rerun-batch-vs-serialized-under-host-memory-pressure
license: BSD-3-Clause
description: "Choose between batch and single-job reruns when CI image-build jobs fail with exit 137 or a package-mirror 5xx. Also use when a batch failed-job rerun repeats the failure with a different signature, when an emulated build compiles with all local CPUs, or when several failed jobs share one build stage that no source change can affect."
category: ci-cd
date: 2026-11-06
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - ci-cd
  - github-actions
  - rerun
  - exit-137
  - oom
  - podman
  - image-build
  - concurrency
  - podman-builder
history-source: "session 2026-11-06 (read-only session evidence; no prior Mnemosyne version)"
---

# Batch Versus Serialized CI Reruns Under Host Memory Pressure

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-06 |
| **Objective** | Pick the rerun shape that finishes a red CI run when the failing jobs build a container image, so a retry does not convert one transient failure into a repeated one. |
| **Outcome** | Verified live on one pull request: two batch failed-job reruns repeated the build failure with a new signature, four single-job reruns passed their jobs under the same load, and the fifth passed after a longer wait. |
| **Verification** | verified-live. The observations come from one session on one repository. The memory mechanism is an inference, not a measured cgroup report. |

## When to Use

- Several jobs in one run fail in a shared container-image build stage: the log names the image build, the `RUN` step, or `building at STEP`, and no repository tool ran.
- A failed job reports exit 137, `Killed`, or `Process completed with exit code 137`.
- A failed job reports a package-mirror 5xx, for example `TooManyRequests 503` from an apt snapshot host.
- A failed job reports an unstable builder store error, for example `unmounting build container ... layer not known`.
- A batch failed-job rerun repeats the failure with a different signature in the same stage.
- Several failing jobs share one build stage, so no source change can alter their result.

## Verified Workflow

### Quick Reference

```text
Job failed in a shared image-build step?
  Batch failed-job rerun  ->  run it ONCE.
  Same stage fails again with a DIFFERENT signature?
      ->  STOP batch reruns. Serialize.
  Serialize: ONE job at a time.
      rerun a single job, wait for it to conclude, then rerun the next.
  A job still fails alone after a quiet wait?
      ->  classify host load. Record the evidence. Retry with a longer wait.
```

```bash
# Batch rerun: use it once, not as a loop.
gh run rerun <RUN_ID> --failed

# Serialized rerun: one job, then wait for its conclusion.
JOB=$(gh api "repos/<user>/<repo>/actions/runs/<RUN_ID>/jobs?per_page=50" \
  --jq '.jobs[] | select(.name=="<job name>") | .id')
gh run rerun <RUN_ID> --job "$JOB"
gh api "repos/<user>/<repo>/actions/runs/<RUN_ID>/jobs?per_page=50" \
  --jq '.jobs[] | select(.name=="<job name>") | [.status, (.conclusion // "running")] | @tsv'

# Read a failure from the log of its own job, not from a batch summary.
gh api "repos/<user>/<repo>/actions/jobs/<JOB_ID>/logs" > job.log
grep -E "TooManyRequests|Killed|exit (status|code) [0-9]+" job.log | tail -5

# Job-scoped rerun re-plans the run, so new jobs can appear.
gh api "repos/<user>/<repo>/actions/runs/<RUN_ID>/jobs?per_page=50" \
  --jq '.jobs[] | [.name, .id, (.conclusion // "running")] | @tsv'
```

### Suggested Approach

1. Read the failing step before you rerun. If the failure is in the image build, no diff, patch, or test edit can change the result. Record that classification on the pull request with the signatures and the attempt numbers.
2. Run one batch failed-job rerun. A single batch rerun is the correct default for a transient failure.
3. Compare the second failure with the first. When the same stage fails with a different signature, for example a mirror 5xx followed by exit 137, the batch shape is now the cause. Each rerun starts one emulated build for every failed job, and each build compiles with all available CPUs. Concurrent emulated builds on one host compete for the same memory.
4. Switch to serialized single-job reruns. Rerun one job, wait for its conclusion, then rerun the next job. Keep a run of single-job passes as the evidence that one build fits.
5. When a job still fails alone, classify host load and wait. A logs signature of an out-of-memory kill during a small package install, while sibling single-job reruns pass, is not a repository defect. Wait for a longer quiet period and rerun that one job.
6. Re-plan after each job-scoped rerun. A job rerun can re-evaluate the changes gate and add jobs that the earlier attempt skipped. Read the job list again before you report the run state.
7. Record the disposition on the pull request. State that the failing step precedes every repository tool, name the signatures by attempt, and name the reruns that passed.

Do not use a source push to clear a build-stage failure. A new head discards review evidence and starts the same builds again.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Reran all failed jobs together after a mirror 5xx | The same stage failed again, now with exit 137 during a source compile | A different signature in the same stage means the batch shape is the cause |
| 2 | Reran all failed jobs together a second time | The same exit-137 signature repeated, and one job's builder store became inconsistent | Repeated batch reruns amplify host pressure; change the shape instead of repeating the call |
| 3 | Waited for the load to fall, then repeated the batch rerun | The batch build pressure reproduced the kill again | A quiet window shortens the queue; it does not make concurrent builds fit |
| 4 | Wrote the CI classification only in the session output | The pull request showed red checks with no cause recorded | Publish the evidence on the pull request so the next reader does not re-triage |

## Results & Parameters

- Batch failed-job reruns: one. Serialized single-job reruns: one per job, in sequence.
- Single-job reruns passed for every job except one build job, which passed after a longer quiet wait.
- Separate workflows that ran on the same head passed throughout. Their success shows that their build step held at that time and does not explain the failing workflow.
- The final run reached a success conclusion with every job green.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| An organization repository | Pull request implementation session, 2026-11-06 | One run with a shared container-image build. Two batch failed-job reruns failed with a mirror 5xx and then with exit 137. Four single-job reruns passed under the same load and the last job passed after a longer wait. The run then concluded green. |