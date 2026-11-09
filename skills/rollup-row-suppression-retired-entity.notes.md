# Supporting details: rollup row suppression for a retired entity

This file holds source evidence for
[rollup-row-suppression-retired-entity](./rollup-row-suppression-retired-entity.md). Use it
when you need the failure chain, the test matrix, or the observed results. The rule does not
depend on these details.

## Source case

One serving cluster advertised several retired models for weeks. The public status document
reported `live_replicas: 0` for each retired model and positive counts for the two active
models. Panel legends and zero series for the retired models never ended, for example on a
prefix-cache token-flow panel.

## Failure chain

1. The supervisor builds one pool report for each advertised pool, including a pool scaled to
   zero. A pool with no records returns a zeroed diagnostic record with a readiness flag of
   `0`, not `null`.
2. The ingest handler normalizes that report into one raw history row for each pool. The raw
   row carries `live` (always written) and the activity counters.
3. Three writers build the derived five-minute rollups from that history:
   - a payload row builder for GPU diagnostics;
   - a payload row builder for capacity;
   - a bucket recompute that aggregated the stored raw rows for the cache family.
4. The bucket recompute screen tested the cache telemetry columns for non-null. The dead sample
   wrote `0` for the readiness flag, so the sample passed the screen and the recompute wrote a
   zero row for each bucket.
5. The visualizer queries the rollup table over a range. A bucket that holds a row keeps the
   series in the window for the whole range.

## Seams changed

| Seam | Family | Before | After |
| --- | --- | --- | --- |
| Payload row builder | GPU diagnostics | Kept every serving-engine pool | Skips a retired sample |
| Payload row builder | Capacity | Skipped only when all of ready, desired, and allocation were absent | Skips a retired sample unless an allocation or donor node exists |
| Bucket recompute | Cache | Aggregated every sample that held a telemetry column | Aggregates only samples that pass the filter |
| Operator backfill | GPU diagnostics and capacity | Rebuilt rows for every sample | Applies the same filter |

Per-replica families needed no change. A retired entity publishes no replica telemetry list,
so those families already emit no rows.

## Test matrix used

| Case | Input | Expected |
| --- | --- | --- |
| Retired | `live = 0`, every keep-signal null or zero | No row in any family |
| Live but idle | `live = 1`, every activity signal null | Row kept |
| Transition down | `live = 0`, one nonzero activity counter | Row kept |
| Restart flap | `live = 0`, positive `desired` | Row kept |
| Allocated capacity | `live = 0`, one running scheduler job | Capacity row kept; GPU row absent |
| Absent key | no `live` key | Row kept |
| Malformed signal | `live = 0`, negative or non-numeric activity | No row |
| Key parity | each key name against each SQL twin | Every key present in every twin |

The database behavior test also checked that a bucket that holds one live sample and one dead
sample aggregates the live sample only, that a row written before the change survives a
recompute, and that raw history rows stay complete.

## Observed results

- Focused unit suite for the row builders and the predicate: 22 passed.
- Source-shape and rollup module suite: 16 passed.
- Both files together: 95 passed.
- Format and lint checks passed on every changed file.
- The database-marked suite did not run on the host because the disposable database
  environment variables were absent. The database behavior test is therefore unverified on
  the host and relies on CI.

## Limits

- The source case held one cluster and one ingest service. The rule assumes one writer per
  family. A second writer that builds the same table needs the same filter.
- The rule does not bound how long an existing row stays visible. The visualizer range decides
  that. Shorter ranges lose the entity first.
- The rule does not restore a series that was already suppressed. A backfill can rebuild the
  range you choose.