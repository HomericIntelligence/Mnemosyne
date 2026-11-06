---
name: cache-tier-verdict-depends-on-reuse-shape
description: "Decide whether to enable a KV or response cache tier by measuring the workload's reuse shape first. Use when: (1) a cache tier or host-memory tier is about to be enabled on the strength of its purpose rather than a measurement, (2) a benchmark measured a cache tier on a workload that repeats no prompt prefix, (3) a tier is reported as having no benefit and the benchmark removed reuse by design, (4) a per-GPU throughput comparison mixes runs whose prefix-reuse rates differ, or (5) available device cache and host cache are being compared as interchangeable capacity."
category: optimization
date: 2026-11-06
version: "1.0.0"
user-invocable: false
tags:
  - benchmarking
  - caching
  - prefix-cache
  - inference
  - serving
  - throughput
  - measurement-validity
---

# Cache Tier Verdict Depends On Reuse Shape

<!-- Use [ASD-STE100](../docs/asd-ste100.md) for prose. Keep the headings and table
columns below so that the entry stays compatible with corpus retrieval. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-06 |
| **Objective** | Reach a defensible decision about a cache tier by measuring the workload's reuse shape before the tier, instead of judging the tier on one workload shape. |
| **Outcome** | Operational. A tier measured on a no-reuse workload showed a 5 to 8 percent loss. The same tier on a shared-prefix workload returned about 6 percent. The workload shape moved the result by more than the tier did: a repeated prefix alone changed throughput by about 3x. |

## When to Use

- A cache tier will be measured, enabled, or removed from a serving deployment.
- A benchmark reports that a cache tier does not help, and the harness cleared caches or used random prompts.
- A benchmark reports that a cache tier helps, and the harness reused one prompt set across levels.
- Results from runs with different prefix-reuse rates are about to be placed in one comparison table.
- Device memory and host memory are compared as if they were the same pool of capacity.

## The Rule

A cache tier is a **hit-rate device**. Its value depends on the
reuse present in the traffic, not on the tier alone. The same
tier is a cost on one workload and a gain on another, and a
benchmark that fixes the workload fixes the verdict.

Measure in this order, because each step can make the next
step unnecessary:

| Step | Question | If the answer is no |
| --- | --- | --- |
| 1 | Does the traffic repeat long prefixes? | Enable no tier. A tier adds transfer cost with no hit to recover it. |
| 2 | Does the device cache already hold the repeated prefix? | A host tier can help. Measure it. |
| 3 | Does the device cache overflow under real load? | Keep the device cache. A host tier duplicates it with slower access. |
| 4 | Does a host tier beat the device-only row on this shape? | Enable no tier. |

The default engine prefix cache is not the tier under test.
It is on by default and it captures the reuse. A benchmark that
measures "reuse versus a tier" must isolate the two: a plain row
on a shared-prefix workload already contains device-cache reuse,
so the tier's contribution is the difference between that row
and the tiered row, never the difference against a no-reuse row.

## Do Not Let One Shape Decide

A no-reuse workload is a legitimate measurement, but its scope
is narrow. State the scope in the result, in the same sentence
as the verdict. A verdict of "the tier costs 8 percent" written
without "when no prompt prefix repeats" will be read as a
general statement about the tier.

| Workload shape | What the tier does | How to report it |
| --- | --- | --- |
| Random prompts, cache cleared per level | Costs transfer overhead; gains nothing | Report as the cost floor, scoped to that shape |
| Mixed traffic | Somewhere between the two floors | Report the hit rate alongside the number |
| One shared long prefix | Gains at most a single-digit percentage, because the device cache already captures most of it | Report against a plain shared-prefix row, not a random row |

Keep cache hygiene separate from cache measurement. Clearing
caches between levels is correct when the goal is to compare
compute. It is wrong when the goal is to measure reuse, because
it removes the variable under test. For the contamination case,
use the warmup-regime entry; do not copy that rule here.

## Verified Workflow

### Quick Reference

```bash
# 1. Establish the reuse shape before any tier measurement.
#    Random prompts (no reuse) and one shared long prefix (maximum reuse)
#    bracket the answer; a real workload lands between them.

# 2. Measure the plain row on BOTH shapes. The plain shared-prefix row
#    already contains device-cache reuse.

# 3. Measure the tiered row on both shapes.

# 4. Compare tiered against plain WITHIN each shape.
#    Never compare tiered-with-reuse against plain-without-reuse.

# 5. Confirm the reuse took effect. Look for a first-token time
#    distribution with a low minimum and a warm median, not for an
#    aggregate counter that may not exist.
```

### Suggested Approach

1. Establish the reuse shape of the real traffic first. If it
   cannot be sampled, bracket it: one no-reuse run and one
   maximum-reuse run.
2. Measure the plain configuration on both shapes. This costs
   one extra cell and it is the cell that most reports omit.
3. Measure the tiered configuration on both shapes.
4. Compare within a shape. A cross-shape comparison answers a
   different question and it will overstate the tier.
5. Report the tier effect and the shape effect as two separate
   numbers. The shape effect is usually larger.
6. Scope the verdict to the measured shape in the same sentence.
7. When the tier helps on one topology and hurts on another,
   report each cell as a single sample and claim no ranking.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Concluding a tier has no value from a no-reuse benchmark | Measured several cache tiers on random prompts with the cache cleared per level, then wrote that no tier improved throughput | The verdict was correct for that workload and wrong as a general statement; the same tier returned a gain on repeated prefixes | State the shape in the verdict sentence, and measure the other shape before generalizing |
| Attributing the shared-prefix gain to the tier | Saw a large throughput gain appear on the workloads that had the tier enabled | The plain configuration on the same shape captured most of the gain through the default engine prefix cache | Measure a plain shared-prefix row; the tier's contribution is the delta against it |
| Comparing tiered reuse against plain no-reuse | Put a high-reuse tiered row next to a low-reuse plain row in one table | The comparison mixed two variables and produced an effect much larger than the tier | Compare within one shape; report the shape effect separately |
| Trusting a client error field | Read a per-request error list that reported one entry per request and treated it as a batch failure | The entries were empty strings, meaning no error; the run was clean | Read the completed-request count and the success line, not the length of the error list |
| Treating a host tier as extra capacity | Compared total device KV tokens against device plus host allocations | The host tier does not raise the request cap the engine enforces, so extra tokens did not raise servable concurrency | Read the engine's request cap under each tier; capacity that the engine will not schedule is not capacity |

## Results & Parameters

### Configuration

```yaml
measure_order: [reuse_shape, plain_per_shape, tiered_per_shape]
compare_within_shape: true          # never across shapes
plain_shared_prefix_row: required   # isolates device cache from tier
scope_in_verdict: true              # name the shape in the verdict sentence
cache_cleared_between_levels: false # only when reuse is the variable under test
single_sample_cells: no_ranking_claim  # one run per cell cannot rank topologies
evidence_of_reuse: ttft_distribution  # low minimum plus warm median
```

### Expected Output

- Two shape rows for the plain configuration and two for the
  tiered configuration, each with a per-unit throughput figure.
- One tier effect per shape, expressed as a delta against the
  plain row of the same shape.
- One shape effect, expressed as a delta between the plain rows.
- A verdict sentence that names the measured shape.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal inference-serving benchmark on a shared preemptible cluster | Ten configuration variants measured on two workload shapes with identical request totals | The no-reuse shape made every tier a 5 to 8 percent loss. The shared-prefix shape made one tier a 6 percent gain on one topology and a 10 percent loss on another, and the plain shared-prefix rows reached roughly 3x the no-reuse throughput. Project, model, host, queue, job, and issue identifiers are withheld under the privacy rules. See [notes.md](../skills/cache-tier-verdict-depends-on-reuse-shape.notes.md). |

## References

- [Inference Benchmark Warmup Regime](inference-benchmark-warmup-regime.md)
- [Slurm-Scheduled Serving Benchmark Sweeps](slurm-scheduled-serving-benchmark-sweeps.md)
- [Benchmark Artifact Triage and PR Splitting](benchmark-artifact-triage-pr-splitting.md)