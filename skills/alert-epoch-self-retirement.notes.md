# Alert Epoch Self-Retirement — Notes

Supporting evidence for [alert-epoch-self-retirement.md](./alert-epoch-self-retirement.md).
This file is not part of normal retrieval.

## Provenance

- Source: one implementation-review round on a single pull request in an internal repository.
- The reviewer raised five findings. Four findings touched the same alerts module, and one touched
  the documentation target.
- Every fix landed as a signed commit on the pull request branch. The focused unit tests and ruff
  check and format passed locally.
- The SQL path was not executed against a live database in the source session, because the pinned
  PostgreSQL test service was not configured. A reviewer must confirm the migration behavior in CI.

## Findings that produced the rules

Round two (v1.1.0) corrected a rule from round one. The round-one rule "keep the `IS NOT NULL`
filter before the aggregation" was wrong. The stored newest row of a cluster carried no epoch,
because a scrape without the series stores NULL. The value filter therefore returned an older
positive epoch, and the lane reported an object that had already recovered.

| ID | Severity | Finding | Rule that it produced |
| --- | --- | --- | --- |
| A | major | The lane had no age bound on the gauge epoch, so it could stay red forever when the exporter never clears the gauge | Bound the lane by the epoch freshness |
| B | minor | A broad catch replaced the row list with an empty list and gave no signal | Catch the undefined-column class only, and log other failures |
| C | nit | The filter before the aggregation was deliberate but undocumented and untested | **Superseded in v1.1.0.** The filter is a defect, not a choice |
| D | nit | The alert line dropped the per-object labels | Keep the identity of the newest epoch |
| E | major | The documentation hunk targeted a page that the base branch had deleted | Find the current owner page before you append prose |
| F | major (round two) | A value filter before the aggregation returned an older positive epoch after the object stopped reporting. Reproduced through the producer, the storage, and the consumer | Order the newest sample by time, and let the age bound end the lane |
| G | minor (round two) | The alert line rendered the age in per-run seconds, so every run changed the line and the one-line cap truncated later lanes | Render the age in whole units |
| H | minor (round two) | The partial index predicate matched the filter that finding F removed | Keep the index predicate in step with the query |

The round-two reviewer found finding F after two earlier reviews had approved the filtered query.
An earlier review comment called the filter deliberate and asked for documentation only. A review
comment is not evidence that the behavior is correct. Reproduce the behavior through every stage
before you accept the rationale.

The first reproduction attempt for finding F failed. It fed a negative epoch to confirm the
retirement branch, but the ingest drops negative values and the migration checks the column
`>= 0`, so that fixture was unreachable from storage. Build the reproduction from stored rows.

## Verified test commands

```bash
TMPDIR=/tmp uv run --locked --extra dev pytest <alerts tests> <monitor tests> <ingest tests> -q
uv run --locked --extra dev ruff check --output-format concise <changed files>
uv run --locked --extra dev ruff format --check <changed files>
```

The temp-root override was necessary because the host temp root caused unrelated path assertions to
fail.

## Observation on the test clock

One test used a fixed epoch from several years ago. The new age bound suppressed the lane, and the
test failed after the bound landed. The correction was to build the epoch from the current clock.
Keep this in mind for every test of a time-bounded lane.