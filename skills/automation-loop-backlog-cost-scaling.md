---
name: automation-loop-backlog-cost-scaling
description: "Profile and bound Hephaestus automation-loop cost for large issue backlogs. Use when: (1) launching an audit-sized issue sweep, (2) a loop seems slow and tests may be blamed, (3) choosing worker count or phase scope, (4) automatic learn work dominates wall time."
category: tooling
date: 2026-07-15
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [hephaestus, automation-loop, performance, backlog, codex, observability, batching]
---

# Automation Loop Backlog Cost Scaling

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Objective** | Distinguish automation-loop agent cost from test time and bound the cost of a large Hephaestus audit backlog before launching it. |
| **Outcome** | A 50-issue, four-worker Codex loop was measured locally; aggregate agent work, slow-job classes, and a batching decision procedure were established. |
| **Verification** | verified-local — observed from the live loop event/log data and a completed local unit-suite run; CI validation is not applicable to this operational workflow. |

## When to Use

- Starting `hephaestus-automation-loop` for tens of audit findings rather than one deliberately scoped issue.
- A run takes hours and someone needs to determine whether the delay is model work, automatic learning, queueing, or tests.
- Selecting a safe batch size and `--max-workers` for Sol/Terra role assignments.
- Reviewing loop telemetry before deciding to scale out or run a second wave.

## Verified Workflow

### Quick Reference

```bash
# Keep a live, line-buffered log for a deliberately bounded first wave.
pixi run hephaestus-automation-loop \
  --agent codex \
  --planner-model sol \
  --implementer-model terra \
  --reviewer-model terra:default \
  --issues "<small, homogeneous issue batch>" \
  --max-workers 4 --loops 1 --verbose \
  2>&1 | tee build/automation-loop-$(date -u +%Y%m%dT%H%M%SZ).log

# Measure unit-test duration separately; do not infer it from loop wall time.
time pixi run pytest tests/unit -q

# After the wave, summarize event telemetry before adding another batch.
rg -n 'completed|implementation|test|learn|failed|duration' build/.issue_implementer/pipeline-events-*.jsonl
```

### Detailed Steps

1. **Classify the backlog before launching.** Separate independent, low-risk fixes from broad refactors, documentation changes, and workflow/process changes. Start with a small homogeneous batch; do not treat an audit's entire issue list as one scheduling unit.
2. **Set the role configuration explicitly.** For the observed run, planning used GPT-5.6 Sol at `xhigh`, implementation used GPT-5.6 Terra at `xhigh`, and review used GPT-5.6 Terra at its default reasoning effort. Record the exact model/effort choices with the run log so comparisons are meaningful.
3. **Capture loop telemetry and calculate both clocks.** Record wall-clock duration and the sum of completed-job agent seconds. Four workers can make aggregate agent time much larger than wall time; neither number is a substitute for the other.
4. **Break down the slowest jobs by phase.** Inspect implementation/test and automatic `/learn` jobs separately. A slow test-labelled agent job often contains implementation, analysis, review, and tool time; it is not evidence that the repository test suite itself is slow.
5. **Run the actual test suite as a separate measurement.** Use a direct unit-suite invocation and retain its elapsed time/output. Compare it with the job-level phase timings rather than attributing the whole loop duration to tests.
6. **Decide the next wave from evidence.** If automatic `/learn` or complex implementation work dominates, reduce scope, group homogeneous issues, and defer or disable optional learning work through the applicable loop policy/configuration. Do not merely raise worker count: it increases concurrent agent spend and may not improve the serial slow-job path.
7. **Only then expand.** Launch the next bounded wave after the prior wave's failures have been turned into concrete, deduplicated GitHub issues and its timing data has been reviewed.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treating loop wall time as test time | A 50-issue four-worker loop ran for about 2.5 hours, creating the impression that unit tests were slow | Completed-job telemetry showed the time was model-driven implementation/review/learning work; the full unit suite itself completed in 2m11s | Measure direct tests independently before diagnosing test performance. |
| One large audit backlog as a single run | 50 audit issues were admitted together with `--max-workers 4` | The run accumulated 36,777 aggregate agent seconds across 138 completed jobs; several individual jobs took tens of minutes | Batch by risk and work type; use one wave's telemetry to size the next. |
| Leaving automatic learning unexamined | `/learn` jobs were treated as incidental loop work | Automatic learning contributed individual jobs of up to 27 minutes, comparable to implementation work | Account for optional learning separately and defer it for bulk execution when it is not the immediate deliverable. |

## Results & Parameters

### Observed Local Run

| Metric | Observed value |
|-------|-------|
| Issue scope | 50 Hephaestus audit/backlog issues |
| Worker limit | 4 |
| Completed jobs | 138 |
| Aggregate agent time | 36,777 seconds (about 10.2 agent-hours) |
| Wall-clock duration | About 2.5 hours |
| Slow implementation/test job | Up to 42 minutes |
| Slow automatic `/learn` job | Up to 27 minutes |
| Separate unit-suite measurement | 6,226 passed, 24 skipped in 2m11s |

### Interpretation Rules

- **Aggregate agent seconds ≠ elapsed time.** With concurrent workers, 36,777 agent seconds can accrue during a much shorter wall-clock run.
- **A phase name is not a resource attribution.** An implementation/test job can spend most of its time in model reasoning or tool orchestration.
- **More workers are not a free speedup.** They can raise total spend and amplify contention while a few long jobs still determine completion time.
- **Learning is real scheduled work.** Include automatic `/learn` in estimates, or intentionally defer it while processing a large backlog.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | 50-issue audit-backlog automation-loop run | Live local telemetry: 138 completed jobs, 36,777 aggregate agent seconds, ~2.5h wall time; direct full unit suite measured separately at 2m11s. |
