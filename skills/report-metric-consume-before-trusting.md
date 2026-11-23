---
name: report-metric-consume-before-trusting
description: "Keep a reported number correct when a collector query, a prose writer, a renderer, and a figure meet. Use when a report number comes from a query, a table row is written by hand, a figure and a table disagree, a metric or rate change must reach the output, or a rate divides by allocated rather than utilized capacity."
category: tooling
date: 2026-10-24
version: "1.2.0"
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
  - rate-denominator
  - window-duration
  - figure-table-consistency
  - capacity-universe
  - utilized-capacity
  - grouped-average
---

# Report Metric: Consume the Number Before Trusting It

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Make a reported number come from one source, check that the source answers the reader's question, and divide every rate by the same window duration. |
| **Outcome** | Operational. A wrong count in a generated report was corrected at the query, but the row still showed the old value until the renderer read the new metric. A later figure disagreed with its table because it divided by a date count instead of the collection window. A third rate fell while the engine was unchanged, because its denominator counted allocated capacity and its analyst read a per-row mean as a pool total. |

## When to Use

- A report holds a number that a collector query computes.
- A report row or sentence is written by a hand-editing author or by a model prompt, not by the renderer.
- You change a query and expect the report to change.
- Two database tables have the same metric with different totals, and you must select one.
- A reviewer reports a number as wrong and you must decide if the number or the query is wrong.
- A figure, table, or sentence states a rate, a per-day volume, or another value divided by a time window.
- Two artifacts state the same rate and their values disagree.
- A window starts or ends at a partial day.
- A rate divides by a count of capacity, such as GPUs, replicas, lanes, or workers, and the label calls it efficiency or utilization.
- A grouped telemetry query returns `avg(...)` per model and interval, and you use it as a pool total.

## Verified Workflow

### Quick Reference

```bash
# 1. Does the metric reach the output at all?
grep -rn '<metric_name>' <renderer> <template> <prompt_builder> <report_source>
# A query key with no reader is a dead metric. The prose fills the row from memory.

# 2. Does the metric come from the table that answers the question?
#    Count requests from a request rollup, not from the number of rollup rows.

# 3. Do the figure, table, and prose divide by the same window?
grep -rn 'window\|days_covered\|per_day\|per-day' <figure_builder> <renderer> <report_source>

# 4. Does a test show that the reader supplies the value?
grep -rn '<metric_name>' <tests>

# 5. Does the denominator count capacity that did work?
grep -rn 'allocated\|ready\|utilized\|reporting\|avg(' <collector> <renderer>
```

Run all five checks before you accept a report number:

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
4. **Every artifact uses the same window denominator.** Keep one duration for a
   rate. Read it from the collection metadata, such as `window.days`, or derive
   it from the window start and end timestamps. Do not count the distinct dates
   in the event set, the table rows, or the day buckets. A window that starts
   or ends at a partial day can have more calendar dates than whole days.
   Compare the divisor in each artifact that states the rate: the figure, the
   table, the prose, and the summary. If an artifact must use a different
   denominator, state the difference next to the rate.
5. **Every artifact divides by the same capacity universe.** A rate per
   allocated capacity counts every unit, including the idle ones. A rate per
   utilized capacity counts only the units that did work in the interval,
   weighted by the share of the interval that they were busy. The two answer
   different questions. State which one the label means, and use it in every
   artifact. If the numerator counts only completed output, capacity that
   spent the interval on other work is still charged to that output. Name the
   rate as output per unit-second, not as engine speed.

### Suggested Approach

Treat the renderer, the template, the prompt builder, and the figure builder as
the consumer set. A hand-editing author or a model prompt is not a consumer,
because it cannot fail when the metric is absent.

When a value is wrong, repair the query first. Then confirm that the output
changes. If the output does not change, the reader is missing. Do not accept a
hand edit of the output as the repair, because the next rebuild discards it.

When the renderer and the author both write the same number, keep the number
in the renderer. Give the author the value through the prompt metrics.

Keep one table as the source for a report. If a second table has the same
metric with a different total, report the difference. Do not mix values from
both tables in one report.

When a rate disagrees, check the numerator and the denominator separately.
Correct numerators can still produce a wrong rate. A date count is a frequent
wrong divisor because it looks like the window length.

For example, a window of 6.858 days held records on 7 calendar dates. The
figure divided by 7, while the table and prose divided by 6.858. The figure was
about 2% high. The repair read `window.days` from the collection metadata.

### Read a grouped mean as a per-row value

A grouped telemetry query returns one row per replica, rank, or interval.
`avg(x)` in that query is the mean per row, not the pool total. Multiply it by
the row count, or sum inside a per-scrape subquery, before you compare it with
a pool capacity. A pool with 20 replicas and a per-row mean below 1 running
request is not idle: it holds about 20 requests in total. Before you call a
pool idle or over-scaled, cross-check the reading with an independent signal,
such as device activity or power, and with a pool whose throughput you can
check by arithmetic.

When you add an efficiency rate, keep two rates apart. A rate per allocated
unit answers "what did the budget return?". A rate per utilized unit answers
"how fast did the unit serve when it worked?". Do not publish one under the
label of the other.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Corrected the query only | The query was changed to count distinct request usernames. The report still showed the old count. | No renderer read the metric key. The author wrote the row by hand, so the query change had no effect on the output. | Search for a reader before you trust a metric. Wire the reader in the same change. |
| Trusted a count from the wrong table | One rollup table was read for daily totals, and the totals disagreed with the table that the report used. | One table was short for some partitions. A sum of a second table is not a substitute for the table with the full event set. | Select the event table that the report already uses. State the choice in the change. |
| Fixed a count but not its cause | A reviewer found a count that did not match the database. | The reviewer counted table rows. The label asked for requests. | Compare a reported number against the definition of its label, not against a row count. |
| Used a date count as the divisor | A figure divided a weekly total by the number of distinct calendar dates in the data. | The window ended at a partial day, so the calendar count was larger than the collection window. The figure disagreed with the table and the prose. | Divide by the window duration from the collection metadata. Compare the denominator across every artifact that states the same rate. |
| Divided by allocated capacity | An efficiency rate counted every allocated unit in the denominator. A pool held many replicas with no running request. | The rate fell by more than half while the engine was unchanged. The number measured the budget, not the engine. | Select the capacity universe that the label means. For a utilization rate, count only the units that did work, weighted by their busy share. |
| Read a grouped mean as a pool total | A queue query returned `avg(running_requests)` per model and hour. The analyst compared that value with the replica count and called the pool idle. | The value was the mean per replica. The pool total was the mean times the replica count, about an order of magnitude larger. | Multiply a grouped mean by its row count, or sum per scrape. Cross-check with device activity before you call a pool idle. |

## Results & Parameters

### Configuration

```yaml
# Checks before a reported number is accepted
source_table: the table that holds the event that the label names
consumer: renderer, template, prompt builder, or figure builder that reads the metric key
test: the existing metrics test, extended with the new field
denominator: window.days from the collection metadata, or the window start and end timestamps
capacity_universe: allocated (every unit) or utilized (units that did work, weighted by busy share); state which
grouped_mean: a per-row mean; multiply by the row count, or sum per scrape, before you call it a total
```

### Expected Output

- The renderer returns the metric in its metrics map.
- The report row shows the value from the query.
- The test fails when the reader is absent and passes when it is present.
- Every artifact that states a rate divides by the same window duration and the
  same capacity universe.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Comet | Weekly report pipeline; collector query, renderer metrics, and an author-written table | The query change did not change the report until the renderer read the metric. A test with the reader removed failed and passed with the reader in place. [notes.md](./report-metric-consume-before-trusting.notes.md) |
| Comet | Weekly report pipeline; per-day figure compared with a rendered table and prose | A figure divided by 7 calendar dates while the table and prose divided by 6.858 days. The figure was about 2% high with correct numerators. [notes.md](./report-metric-consume-before-trusting.notes.md) |
| Serving fleet report | A per-model efficiency rate and a grouped queue mean | The rate counted allocated units, so idle replicas lowered it. A grouped mean read as a pool total made an over-scaled pool look idle. The repaired rate counts utilized unit-seconds. [notes.md](./report-metric-consume-before-trusting.notes.md) |

## References

- [ci-gate-verify-artifact-is-consumed-before-guarding.md](ci-gate-verify-artifact-is-consumed-before-guarding.md) — the same consumer question for CI gates.
- [process-metrics-pipeline-integration.md](process-metrics-pipeline-integration.md) — metrics that cross more stages.
