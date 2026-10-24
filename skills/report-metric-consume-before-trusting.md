---
name: report-metric-consume-before-trusting
description: "Keep a reported number correct when a collector query, a prose writer, and a renderer meet. Use when a report number comes from a query, a table row is written by hand, or a metric change must reach the output."
category: tooling
date: 2026-10-24
version: "1.0.0"
user-invocable: false
verification: verified-runtime
tags:
  - reporting
  - metric-pipeline
  - consumer-wiring
  - dead-metric
  - generated-prose
  - hand-written-prose
  - data-source-truth
  - number-drift
---

# Report Metric: Consume the Number Before Trusting It

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Make a reported number come from one source and check that the source is the one that answers the reader's question. |
| **Outcome** | Operational. A wrong count in a generated report was corrected at the query, but the row still showed the old value until the renderer read the new metric. |

## When to Use

- A report holds a number that a collector query computes.
- A report row or sentence is written by a hand-editing author or by a model prompt, not by the renderer.
- You change a query and expect the report to change.
- Two database tables have the same metric with different totals, and you must select one.
- A reviewer reports a number as wrong and you must decide if the number or the query is wrong.

## Verified Workflow

### Quick Reference

```bash
# 1. Does the metric reach the output at all?
grep -rn '<metric_name>' <renderer> <template> <prompt_builder> <report_source>
# A query key with no reader is a dead metric. The prose fills the row from memory.

# 2. Does the metric come from the table that answers the question?
#    Count requests from a request rollup, not from the number of rollup rows.
```

Run all three checks before you accept a report number:

1. **The query answers the reader's question.** Select the table that holds the
   event that the label names. A label "requests" must sum a request count. It
   must not count table rows, and it must not count accounts that only hold a
   key. If two tables hold the same metric, one of them can be short for some
   partitions. Use the table that the rest of the report already uses, and
   record the choice.
2. **A consumer reads the metric.** Find the reader in the renderer, the
   template, or the prompt builder. If there is no reader, the metric is dead.
   Wire the reader in the same change. Until then, the report keeps the value
   that the author wrote by hand.
3. **A test shows the value arrives.** Extend the test that already covers the
   metrics function. Assert the value from the input is present in the output.
   Run the test with the reader removed, and make sure that it fails. Then run
   it with the reader in place, and make sure that it passes.

### Suggested Approach

Treat the renderer, the template, and the prompt builder as the consumer set.
A hand-editing author or a model prompt is not a consumer, because it cannot
fail when the metric is absent.

When a value is wrong, repair the query first. Then confirm that the output
changes. If the output does not change, the reader is missing. Do not accept a
hand edit of the output as the repair, because the next rebuild discards it.

When the renderer and the author both write the same number, keep the number
in the renderer. Give the author the value through the prompt metrics.

Keep one table as the source for a report. If a second table has the same
metric with a different total, report the difference. Do not mix values from
both tables in one report.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Corrected the query only | The query was changed to count distinct request usernames. The report still showed the old count. | No renderer read the metric key. The author wrote the row by hand, so the query change had no effect on the output. | Search for a reader before you trust a metric. Wire the reader in the same change. |
| Trusted a count from the wrong table | One rollup table was read for daily totals, and the totals disagreed with the table that the report used. | One table was short for some partitions. A sum of a second table is not a substitute for the table with the full event set. | Select the event table that the report already uses. State the choice in the change. |
| Fixed a count but not its cause | A reviewer found a count that did not match the database. | The reviewer counted table rows. The label asked for requests. | Compare a reported number against the definition of its label, not against a row count. |

## Results & Parameters

### Configuration

```yaml
# Checks before a reported number is accepted
source_table: the table that holds the event that the label names
consumer: renderer, template, or prompt builder that reads the metric key
test: the existing metrics test, extended with the new field
```

### Expected Output

- The renderer returns the metric in its metrics map.
- The report row shows the value from the query.
- The test fails when the reader is absent and passes when it is present.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Comet | Weekly report pipeline; collector query, renderer metrics, and an author-written table | The query change did not change the report until the renderer read the metric. A test with the reader removed failed and passed with the reader in place. [notes.md](./report-metric-consume-before-trusting.notes.md) |

## References

- [ci-gate-verify-artifact-is-consumed-before-guarding.md](ci-gate-verify-artifact-is-consumed-before-guarding.md) — the same consumer question for CI gates.
- [process-metrics-pipeline-integration.md](process-metrics-pipeline-integration.md) — metrics that cross more stages.