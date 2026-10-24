---
name: paired-sweep-significance-interpretation
description: "Read a multi-task paired evaluation sweep without overclaiming. Use when: (1) a summary says some tasks are significant between two configurations and a decision rests on that count, (2) a paired document flip count is quoted as accuracy loss, (3) an aggregate task count or paired-document total disagrees between a summary and the retained results, or (4) a suite reports failures that look like quantization damage but come from its own matcher."
category: evaluation
date: 2026-10-23
version: "1.0.0"
user-invocable: false
tags: ["evaluation", "paired-test", "mcnemar", "significance", "multiple-comparisons", "benchmark", "accuracy", "precision", "quantization", "verdict"]
---

# Paired Sweep Significance Interpretation

<!-- Use [ASD-STE100](../docs/asd-ste100.md) for prose. Keep the headings and table
columns below so that the entry stays compatible with corpus retrieval. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Decide whether a multi-task paired sweep supports a claim that one configuration keeps the accuracy of another. |
| **Outcome** | Operational. A published accuracy summary understated its own sweep, one of its three significant tasks favoured the baseline, and a flip count was read as accuracy loss. All three were corrected against the retained results. |

## When to Use

- A summary says that one configuration does not regress, and it rests on a count of significant tasks.
- A paired flip count or paired-document total is about to be quoted as evidence of accuracy loss.
- A task count or document total in a summary does not match the retained result files.
- A suite reports failures whose rate looks the same on both configurations.
- Two configurations differ on one axis, and the reader needs to know which parts of the claim are measured and which are assumed.

## The Rules

Four checks turn a sweep result into a defensible claim. Each one fails separately.

| Check | Question | Failure mode if skipped |
| --- | --- | --- |
| Family size | How many tasks were tested, and how many would cross the threshold by chance? | A count of 3 significant tasks is reported as a regression when about 17 were expected by chance |
| Direction | Of the significant tasks, how many favour each side? | One baseline-favouring task is hidden behind a "no regression" summary sentence |
| Metric kind | Is the per-item score a verdict or a probability? | A near-continuous metric flips almost every item at equal score, and the flip count reads as damage |
| Matcher | Do the failures come from the model or from the suite? | Shared suite defects are reported as dtype or precision damage |

## Treat A Significant-Task Count Against Its Chance Rate

A p<0.05 threshold admits about 5 percent of tasks by chance. Multiply the task
count by the threshold before you interpret the count as a finding.

```text
expected_by_chance = task_count * alpha
regression_supported = significant_task_count > expected_by_chance
```

Report the count, the expectation, and the direction split together. A count
below the chance rate supports "no family-level regression" and does not support
"no task regressed". State it that way.

Do not correct for multiple comparisons after you have already read the
per-task results and selected the interesting ones. If a family-wide claim is
required, apply a correction such as Holm in the analysis script and report the
corrected values.

## Read The Flip Count With The Metric Kind

A flip count measures how often a per-item score changed. It does not measure how
often a verdict changed.

| Metric kind | Flips at equal score | What the flip count means |
| --- | --- | --- |
| Correct/incorrect verdict | Few | A real change in outcomes |
| Probability or continuous score | Almost all items | Sensitivity to tiny numeric differences, not accuracy loss |

When most flips sit in probability-scored tasks while those tasks score
identically, the sweep is stable and the flip rate is a property of the metric.
Say so, and give the median and range of the score delta as well.

## Reconcile The Summary With The Retained Results

A task count and a paired-document total are checkable facts. Recount them from
the result files before you repeat them.

Recount at least:

- number of tasks and subtasks scored on both configurations;
- paired documents;
- flips;
- median and range of the score delta.

If a summary and the retained files disagree, mark the summary figure withdrawn
in place and give the reason. Do not adjust it quietly to a number that looks
better.

## Separate Model Failures From Suite Failures

Before you attribute a failure rate to a precision change, confirm that the
failures differ between configurations. Then classify each failure:

| Class | Test | Verdict |
| --- | --- | --- |
| Letter case or punctuation | Compare the output with the expectation after case folding | Suite defect. The model is correct |
| Diacritics or accepted spelling | Compare with the accepted forms | Suite defect. The model is correct |
| Valid synonym the matcher rejects | Read the expectation and the output | Suite defect. The model is correct |
| Wrong answer on both configurations | Compare the outputs directly | Real model limitation, not a configuration effect |

Report a relaxed match as a separate score. State both the strict score and the
relaxed score, and name the cases that remain. A single relaxed number hides
which failures are real.

## Scope The Claim To The Measured Configuration

State the topology, batch shape, and precision that the sweep ran at. When the
deployment differs on any axis, the sweep does not cover the deployed
configuration. Name the uncovered axis as a gap instead of implying coverage.

## Verified Workflow

### Quick Reference

```python
# Family-wide reading of a per-task p-value table
alpha = 0.05
expected = len(tasks) * alpha
significant = [t for t in tasks if t.p < alpha]
favours_candidate = sum(1 for t in significant if t.delta > 0)
favours_baseline = len(significant) - favours_candidate
print(f"{len(significant)} significant of {len(tasks)}; "
      f"chance expectation {expected:.1f}; "
      f"{favours_candidate} candidate / {favours_baseline} baseline")
```

### Suggested Approach

1. Recount the tasks, the paired documents, and the flips from the result files.
   Do not trust a summary line.
2. Compute the chance expectation for the task family.
3. Split the significant tasks by direction.
4. Identify which tasks carry probability metrics, and read their flips against
   their score delta.
5. Classify each shared failure before you attribute any failure to the changed
   configuration.
6. Write the claim at the configuration you measured, and name any uncovered
   deployment axis.

Continue when the per-task p-value table is missing. Report the counts, the flip
rate, and the delta distribution, and mark the significance question as
unanswered rather than calling the sweep clean.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Quoted a task count and flip rate from a summary | Repeated the task count and paired-document total from an issue body without recounting | The retained files held 339 tasks, not the stated smaller count, and the flip rate was different in both directions | Recount tasks, documents, and flips from the result files before repeating them |
| Read a significant-task count as a regression | Reported that no task regressed significantly because only a few crossed p<0.05 | Three tasks crossed the threshold, one of them in favour of the baseline, and three is below the chance expectation for the family | Compare the count with the chance rate and split the direction |
| Read a flip count as accuracy loss | Treated a flip rate above 20 percent as evidence of damage | Most flips came from probability-scored tasks that scored identically on both sides | Read the flip count against the metric kind, and give the median delta |
| Trusted a strict matcher | Treated the suite's own pass rate as the model's accuracy | 16 of the failures were letter-case only, and the suite rejected a correct synonym | Report strict and relaxed scores separately, and classify the remaining failures |

## Results & Parameters

### Configuration

```yaml
family_reading:
  alpha: 0.05
  expected_by_chance: task_count * alpha
  report: [task_count, significant_count, chance_expectation, candidate_favoured, baseline_favoured]
flip_reading:
  report: [flip_count, paired_documents, median_delta, delta_range]
  note: split probability-scored tasks from verdict-scored tasks
matcher_reading:
  report: [strict_pass, relaxed_pass, remaining_cases]
  relaxed_rule: state the rule explicitly, such as case-insensitive containment
```

### Expected Output

- A statement of the family result that gives the count, the chance expectation,
  and both directions.
- A flip reading that separates probability metrics from verdict metrics.
- A strict and a relaxed score, with the remaining failures named.
- A scope sentence that names every axis not measured.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal inference-serving benchmark | Paired accuracy sweep between two cache-precision variants on identical hardware, 339 tasks and a 96-case qualification suite | Project, model, host, job, and issue identifiers are withheld under the privacy rules. The same engagement supplies all three failure modes. See [notes.md](../skills/paired-sweep-significance-interpretation.notes.md). |

## References

- [Technical English policy](../docs/asd-ste100.md)
- [Inference benchmark warmup regime](inference-benchmark-warmup-regime.md)
- [Verification evidence audit](verification-evidence-audit.md)
- [Baseline parity and cross-matrix evaluation](evaluation-baseline-parity-cross-matrix.md)