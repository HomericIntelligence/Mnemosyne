---
name: inference-benchmark-warmup-regime
description: "Measure inference-serving latency in steady state rather than on the first request. Use when: (1) a reported time to first token is far above the value seen on a later request, (2) a single-run latency comparison is about to be quoted as a result, (3) a latency delta is small enough that run-to-run variance could reverse its direction, (4) a published latency comparison needs correction or withdrawal, or (5) a relative change is about to be computed against a baseline value that no retained run artifact contains."
category: optimization
date: 2026-10-17
version: "1.2.0"
user-invocable: false
tags: ["benchmarking", "latency", "warmup", "ttft", "inference", "serving", "vllm", "sglang"]
---

# Inference Benchmark Warmup Regime

<!-- Use [ASD-STE100](../docs/asd-ste100.md) for prose. Keep the headings and table
columns below so that the entry stays compatible with corpus retrieval. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-17 |
| **Objective** | Report a serving-latency comparison that survives a reviewer who asks how the number was produced. |
| **Outcome** | Operational. A repeated steady-state measurement replaced a single first-request sample, reversed the direction of the reported result, and required withdrawing a published claim. |

## When to Use

- A time to first token reading sits far above the value seen on a later request to the same engine.
- One request per configuration produced the number that a decision now rests on.
- Two configurations differ by only a few percent, and the run-to-run spread is of the same order.
- A latency claim is already published and later evidence contradicts it.
- A benchmark harness sends its first request immediately after the engine reports ready.
- A repeated run reports a large throughput gain, or a time to first token far below the first run.
- A relative change is about to be quoted, and the baseline value cannot be traced to a retained result file.

## The Rule

Warmup has **two independent causes**, and a comparison needs both removed:

| Cause | Depends on | Symptom | Fix |
| --- | --- | --- | --- |
| prefix-cache state | the prompt | time to first token collapses by an order of magnitude on repeats | a distinct prompt set per run |
| kernel, graph, and autotune state | the process | the first run is slow even with fresh prompts | discard the first run |

Removing only one cause still produces a wrong answer. Removing the wrong one produces an answer that looks favourable.

Report the warmup sample and the steady-state samples separately. Do not average them together.

## Resolve The Baseline Before You Compute A Delta

A warmup defect and a missing baseline are different defects, and either one alone makes a relative change wrong. Before you quote a percentage, resolve the baseline to a retained result file for the same configuration.

| Check | Pass condition | Action when it fails |
| --- | --- | --- |
| Baseline exists in the retained results | A result file for the baseline configuration names the value you use | Do not compute the delta. Re-measure the baseline or state that no comparison is available |
| Baseline row and candidate row are matched | Same shape, same topology, same image, one changed variable | Report the deltas rather than one aggregate percentage |
| Baseline value has one source | The value appears in one named artifact | Treat duplicated or inferred sources as unresolved |

A number can survive in a document after its source run is lost. Text that merely contains the same digits as your baseline is not the baseline. That pattern is easy to accept because it confirms the figure you already expected.

When a baseline cannot be traced, the honest output is that the comparison is unavailable. Withdrawing a published figure and re-measuring is cheaper than defending a delta whose baseline nobody can produce.

## A Repeated Prompt Set Reads As A Large Win

A harness that resends one prompt set on every run reports throughput far above reality, because the cache serves every repeat. In the evidence for this skill, measured time to first token fell from about 39 s to under 1 s on the second run.

That direction is the dangerous one. A cold first run makes the candidate look slower, which reads as a cost and invites a small discount. A warm repeat makes it look faster, which reads as a win and invites a decision. Neither is a measurement.

Give every run a distinct prompt set, seeded per run, so no sample can be served from cache. Prefer a seed offset over a positional argument when existing invocations must keep working.

## Verified Workflow

### Quick Reference

```bash
# Discard repeat 1, then report the warm steady-state distribution.
repeats=20
tail -n +2 runs.log > warm.log
```

State the regime with every number. Write `warm steady state, 19 repeats`, not `latency`.

### Test Significance Against Variance

Do not report a percentage difference on its own. Compare the difference against the pooled standard error of the two means:

```text
pooled_se = sqrt(stdev_a**2 / n_a + stdev_b**2 / n_b)
ratio     = abs(mean_a - mean_b) / pooled_se
```

Treat `ratio` below 2 as indistinguishable from run-to-run variation. Report the ratio, not only the percentage.

### Suggested Approach

1. Send at least one warmup request and discard it.
2. Repeat the request enough times that the pooled standard error is well below the difference you care about.
3. Resolve every baseline value to a retained result file before you compute a difference. Do not continue with a baseline you cannot locate.
4. Report mean, standard deviation, and a tail percentile such as p90 for each configuration.
5. State the sign convention so that the reader cannot invert the result. For example, state that a positive change means the candidate is faster.
6. Re-check any earlier claim that used a single post-start request. Withdraw or restate it.
7. Re-check any earlier claim whose baseline has no retained source. Withdraw it and re-measure, or declare the comparison unavailable.

Continue when a warmup sample is unavailable. Report the regime you did measure and mark the result provisional rather than dropping the comparison.

## Why One Sample Is Not Enough

A single sample can invert the direction of a conclusion. In the evidence for this skill, one request per configuration reported a candidate configuration as faster on per-token latency. Nineteen warm repeats per configuration reported it as slower on the same metric, and faster on time to first token. The per-token difference was about 25 times the pooled standard error, so the reversed direction was real and not scatter.

The error was not a small-sample problem. The first-request time to first token was roughly three times the steady-state value, so the sample measured warmup rather than serving. Averaging or extending it would not have fixed it. Only discarding it did.

A second instance of the same class appeared at higher concurrency. There, a harness that resent one prompt set made the candidate look faster by roughly an order of magnitude on time to first token, because every repeat was served from cache. Discarding the first run did not help, because the effect fell on the later runs. Distinct prompts per run were needed as well. One of the two causes had been addressed and the result was still wrong.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| One request per configuration | Measured time to first token and per-token latency once, then compared percentages. | The sample measured cold kernel warmup, and its direction was the reverse of the steady-state result. | A single post-start request is a warmup sample, not a latency measurement. |
| Reported a sub-percent delta as a result | Compared means and stated the percentage. | Run-to-run variance was of the same order, so the sign was not established. | Compare the difference against a pooled standard error before calling it a result. |
| Averaged warmup with steady state | Took a mean across every repeat. | One warmup sample shifted the mean enough to mislead. | Report warmup and steady state separately, or exclude warmup explicitly. |
| Repeated one prompt set across runs | Re-ran the concurrency test without changing the prompt seed. | Every repeat was served from the prefix cache and time to first token fell by an order of magnitude. | Seed a distinct prompt set per run; discarding the first run does not fix this. |
| Quoted a delta against an unresolved baseline | Computed a percentage against a baseline value that appeared nowhere in the retained results, only as coincidental digit matches in unrelated logs. | No run ever produced that baseline, so the delta described a configuration that was never measured. The figure had to be withdrawn. | Resolve the baseline to a retained result file before you compute any difference, and refuse the delta when you cannot. |

## Results & Parameters

### Configuration

```yaml
warmup_requests: 1        # discarded, never averaged; clears kernel and graph warmup
measured_repeats: 19      # raise until the pooled standard error is well below the delta
distinct_prompt_set_per_run: true  # clears prefix-cache state; seed per run
distinct_prompt_per_sample: true   # clears reuse within a run
report: [mean, stdev, p90, n]
sign_convention: state explicitly, and verify the label against the printed values
baseline_source: a named result file, never text that contains the same digits
```

Check the sign label against the data before publishing. State the convention
per metric, because a percentage that reads "faster" for throughput reads
"slower" for a latency row.

### Expected Output

- A table with one row per metric and one column per configuration, each cell showing mean, standard deviation, percentile, and sample count.
- A stated regime, so the reader knows the warmup sample was excluded.
- A named source for each baseline value, so a reader can check the comparison.
- A significance ratio against the pooled standard error for any difference the reader might act on.

## Reusing a Published Comparison

When later evidence contradicts a published latency number, correct the source rather than adding a second table beside it.

1. Mark the superseded figure as withdrawn in place, and give the reason.
2. State which regime the withdrawn figure came from, so the reader can tell whether other figures share the defect.
3. Name the baseline that the withdrawn figure used, and say whether that baseline was ever measured.
4. Search for downstream copies, because a correction in one place does not correct a claim repeated in a decision record or an implementation brief.
5. Keep the corrected direction even when it is less favourable. A reversed conclusion is still a conclusion.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal inference-serving benchmark | Repeated single-stream latency comparison across two cache-precision variants on identical hardware | Twenty repeats per variant against a serving shape of roughly 75k input and 685 output tokens. Project, model, host, job, and issue identifiers are withheld under the privacy rules. The same engagement supplied the unresolved-baseline case. See [notes.md](../skills/inference-benchmark-warmup-regime.notes.md). |

## References

- [Technical English policy](../docs/asd-ste100.md)
- [Prefix-cache shape and kernel evidence](debugging-prefix-cache-nsight-kernel-evidence.md)