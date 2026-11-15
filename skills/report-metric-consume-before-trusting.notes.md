# Notes: report-metric-consume-before-trusting

Supporting evidence for `skills/report-metric-consume-before-trusting.md`.
This file is not part of normal retrieval.

## Source context

A weekly usage report was generated from a collector script, a renderer script,
and several prose sections. The author of the report edited prose sections by
hand. The renderer wrote only some of the tables.

A reviewer found that a per-model user count was wrong. The count was 5, 4, 4, 4
for four weeks. The correct values were 5, 6, 8, 7.

## Root cause chain

1. The collector query counted a different entity than the label stated. The
   label asked for distinct users connected. The query counted something else.
2. The collector returned a `users_connected` key, and no code read that key.
   The renderer metrics map did not include it.
3. The prose author wrote the count by hand in a table. It had no path to the
   query result, so a query change could not change the output.

## Repair sequence that worked

1. Correct the query. Count distinct usernames with at least one request in the
   period. Exclude the service's own account.
2. Add the value to the renderer metrics map:
   `metrics["users_connected"] = row.get("users_connected", 0)`.
3. Extend the existing metrics test with the new input field and assert the
   output field.
4. Run the test with the reader removed. It failed. Run it with the reader
   in place. It passed.

## Second failure in the same session

The report held daily request totals. One rollup table reported 14,114 and 9,938
requests for two days. A second table, used by the rest of the report, reported
14,054 and 9,445 for the same days. The second table also had a partial day
where the first table undercounted by about 15 percent.

The correct action was to keep the table that already supplied the report
totals and correct the hand-written lines to match it. The wrong action was to
mix values from both tables in one report.

## Third failure in the same session: rate denominator

A later report stated per-day rates in a figure, a table, and the prose. The
collection window was 6.858 days and ended at a partial day. The event data had
records on 7 distinct calendar dates.

The figure builder counted the dates with data and used 7 as the divisor. The
table and prose read the window duration from the collection metadata and used
6.858. Every numerator came from the same query. Only the divisor differed, so
the figure was about 2% high.

The repair read the window duration from the collection metadata and passed the
same value to the figure builder. If that key is absent, derive the duration
from the window start and end timestamps. Do not fall back to a date count for
a window that is not a whole number of days.

The check that would have caught this defect compares the divisor, not only the
numerator, across every artifact that states the rate. This session found the
defect by reading the figure and the table side by side. No automated check
compared them before the repair.

## Limits of this evidence

- The entry is general. Project names, paths, table names, and account names
  are omitted from the rule.
- The workflow was validated on one reporting pipeline. The same rule applies to
  other generated documents, but this session did not test them.
- The rate-denominator failure was found by inspection. The reported values
  were verified against the collection metadata after the repair, but the
  session did not add a regression test for the figure builder.
