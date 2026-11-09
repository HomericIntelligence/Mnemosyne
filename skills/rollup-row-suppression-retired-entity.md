---
name: rollup-row-suppression-retired-entity
license: BSD-3-Clause
description: "Stop derived time-bucket rollups from writing rows for an entity that no longer exists. Use when: (1) retired models, hosts, tenants, or jobs stay on dashboards for weeks after removal, (2) the source of a rollup keeps reporting the entity with live = 0 and zero or null activity, (3) a panel legend must end while older history stays queryable, (4) one family of rollup tables is rebuilt from raw samples and another family is built from the live payload."
category: architecture
date: 2026-11-09
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - rollup
  - suppression
  - retired-entity
  - dashboard
  - time-series
  - liveness
  - keep-signal
  - flap-guard
  - sql-twin
  - backfill
  - sparse-series
---

# Rollup Row Suppression for a Retired Entity

**Supporting details:** [notes](./rollup-row-suppression-retired-entity.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Remove a retired entity from derived dashboard rollups at the writer, without changing raw samples, existing rows, or live-but-idle entities. |
| **Outcome** | Operational. The rule was delivered in one change with unit, source-shape, and database behavior tests. Lint and the focused suites passed; the database-marked suite was not run on the host, so CI supplies that evidence. |

A rollup writer emits one row for each source sample. When the source still advertises a
retired entity and writes `live = 0` with null or zero activity, each scrape writes a fresh
zero-valued row. The visualizer keeps the entity in its window because a row exists. The
entity never disappears. Fix the writer, not the query and not the raw table.

## When to Use

- A dashboard panel keeps a legend entry and a zero series for an entity that has had no
  replicas, hosts, or jobs for a long time.
- The raw sample of a rollup writer carries an explicit liveness count, such as a live or
  running count, separate from the activity counters.
- The raw sample keeps a coverage flag or an expected-count column that stays non-null after
  retirement, so a non-null screen cannot drop the sample.
- The panel must lose the entity within one rollup interval, while a longer range must still
  return older data.

Do not use this rule to delete historical rows. Do not use it to change a query or a
materialized view when the raw writer is the only current source of the symptom. For an entity
that removes itself from the next sample, no change is necessary.

## Verified Workflow

### Quick Reference

Name keep-signals once, then apply one predicate at every writer that rebuilds the family.

```python
LIVENESS_KEY = "live"
KEEP_SIGNALS = ("desired", "running_reqs", "waiting_reqs",
                "cached_prefill_tokens", "computed_prefill_tokens",
                "evicted_tokens", "aborted_requests")


def sample_has_life(sample: dict) -> bool:
    """False only for an explicit zero liveness count with no activity."""
    live = sample.get(LIVENESS_KEY)
    if live is None or live != 0:      # absent key keeps legacy behavior
        return True
    if any(positive(sample.get(key)) for key in KEEP_SIGNALS):
        return True
    return False
```

```sql
-- Same rule for a writer that rebuilds a bucket from stored raw samples.
AND greatest(
    coalesce(live, 0), coalesce(desired, 0),
    coalesce(running_reqs, 0), coalesce(cached_prefill_tokens, 0)
) > 0
```

### Suggested Approach

1. **Separate liveness from activity.** Liveness says whether the entity exists now. Activity
   says whether it did work. Suppress only the state where liveness is an explicit zero *and*
   every activity signal is null or zero. A pool with live replicas but no traffic is deployed
   and idle. It must stay visible.
2. **Treat an absent liveness key as alive.** Legacy, synthetic, and test payloads can omit the
   key. Suppressing on an absent key changes behavior that nobody requested and breaks fixtures.
   Require an explicit zero.
3. **Exclude coverage and structure columns from the keep-set.** A retired entity still reports
   expected GPU counts, node counts, and "telemetry ready = 0". A sample screen that tests those
   columns for non-null keeps the dead sample. Read the producer: a record-less entity commonly
   writes a ready flag of 0, not null.
4. **Keep a flap guard for short zero-replica windows.** During a rolling restart the entity
   returns. Use the demand count (desired replicas, requested capacity) and, where a family can
   see them, allocated scheduler jobs or donor nodes. A bucket-level recompute is a second
   guard: keep the bucket if any sample in it passes the filter.
5. **Apply the predicate at every writer of the family.** Find each writer by grepping the raw
   table name. A family commonly has three seams: a payload row builder, a bucket recompute, and
   an operator backfill. A backfill that omits the rule resurrects the rows later.
6. **Keep one key list and name the twins.** Put the Python predicate next to the existing
   normalization helper and name the SQL twins in each docstring. When a script is loaded
   standalone, a shared SQL fragment constant in that script is acceptable; a cross-module
   import is not necessary.
7. **Do not filter the raw insert.** Keep raw samples complete for audit and for any future
   recompute. Suppress only the derived row. Existing rows stay until the window ages out, so a
   long range stays queryable.
8. **Let a family add its own keep-signal.** A capacity family can see scheduler allocations
   that the activity payload does not carry. Add that signal at that family only, and document
   why.
9. **Test the decision, not the mechanics.** Cover: retired entity suppressed in every family;
   live-but-idle entity kept; activity-only entity kept during scale-down; positive demand kept;
   allocated job kept in the family that sees it; absent liveness key kept. Add one source-shape
   test that asserts each key name appears in each SQL twin, so a key-list edit cannot drift.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| Filter the raw sample screen | Relied on the existing non-null telemetry screen to drop the dead sample | The producer writes a ready flag of 0 for a record-less entity, so the screen matched | Test the liveness count explicitly. Do not infer retirement from coverage columns |
| Filter only the failing family | Changed the one rollup table named in the report | Sibling families rebuild from the same samples and keep writing zero rows | Grep the raw table name and change every writer, including operator backfills |
| Suppress on a missing liveness key | Treated "no live value" as zero | Legacy payloads and fixtures omit the key, so unrelated rows disappeared | Require an explicit zero, and keep the absent-key branch alive |
| Delete historical rows | Purged old rows to clear the legend | Destroyed audit history and the longer-range panels | Suppress at the writer and let older rows age out naturally |

## Results & Parameters

### Configuration

```yaml
liveness_key: "live"          # explicit zero required
absent_key: "alive"           # legacy payloads keep their rows
keep_signals:                 # null or zero does not keep the sample
  - desired                   # flap guard; positive during a restart
  - running_reqs
  - waiting_reqs
  - cached_prefill_tokens
  - computed_prefill_tokens
  - evicted_tokens
  - aborted_requests
family_only_keep_signals:
  capacity: [allocated_jobs, donor_nodes]
excluded_from_keep_signals:
  - telemetry_ready
  - expected_gpus
  - nnodes
```

### Expected Output

- A retired entity writes no row for a new bucket, so the series ends after one rollup interval.
- A live-but-idle entity keeps one row for each bucket.
- A sample with one nonzero activity counter keeps its row.
- Raw samples and existing rows remain unchanged.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal repository | Rollup writer change with unit, source-shape, and database behavior tests | Database-marked tests ran only in CI on the host. See the [notes](./rollup-row-suppression-retired-entity.notes.md). |

## References

- [Alert epoch self-retirement](alert-epoch-self-retirement.md): bounds an alert lane by sample freshness.
- [Derived-artifact gate non-vacuity](derived-artifact-gate-non-vacuity.md): keeps a gate from passing on empty input.
- [SQL migration view-chain PR sequencing](sql-migration-view-chain-pr-sequencing.md): orders SQL object changes across pull requests.