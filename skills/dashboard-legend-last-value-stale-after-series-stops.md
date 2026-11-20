---
name: dashboard-legend-last-value-stale-after-series-stops
description: "Find and fix a dashboard legend that shows an old non-zero value for a resource that no longer exists. Use when: (1) a time-series legend uses a last-non-null calculation, (2) the data source writes no row for an idle or retired entity, (3) the dashboard shows a count above zero while the live system shows none, or (4) a count panel must show zero after scale-down."
category: debugging
date: 2026-11-20
version: "1.0.0"
user-invocable: false
tags:
  - dashboard
  - grafana
  - legend
  - last-non-null
  - zero-fill
  - rollup
  - scale-to-zero
  - stale-value
---

# Dashboard Legend Keeps an Old Value After a Series Stops

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-20 |
| **Objective** | Make a count panel show zero when an entity scales down and its source stops writing rows. |
| **Outcome** | Successful. The panel query adds zero points for a silent series. The ingest code did not change. |

## When to Use

- A legend column uses "last non-null" (`lastNotNull`) and shows a value above zero for an entity that is down.
- The live system, the scheduler, and the client error all agree that the entity has no instances.
- The source table has no row for the entity after it went idle. An ingest rule drops samples with no allocation and no activity.
- Other idle entities show zero. Those entities still have a keep-alive signal, such as a pending job or a desired count above zero.

## Verified Workflow

### Quick Reference

Check the data before you blame the live system. A series that ends is not a series that reads zero.

```sql
-- Close each series that is silent for more than two buckets with zero points.
WITH horizon AS (
  SELECT cluster, max(ts_bucket) AS latest FROM rollup WHERE <time filter> GROUP BY 1
), silent AS (
  SELECT s.cluster, s.model, s.last_bucket, h.latest
  FROM (SELECT cluster, model, max(ts_bucket) AS last_bucket FROM capacity GROUP BY 1, 2) s
  JOIN horizon h USING (cluster)
  WHERE s.last_bucket < h.latest - interval '10 minutes'
)
SELECT ts_bucket, cluster, model, value FROM capacity
UNION ALL SELECT last_bucket + interval '5 minutes', cluster, model, 0 FROM silent
UNION ALL SELECT latest, cluster, model, 0 FROM silent
```

### Suggested Approach

1. Compare three sources: the scheduler queue, the gateway log, and the panel. If the first two show zero, the panel is stale.
2. Read the panel query and the legend calculation. Then read the ingest rule that writes the table. Look for a skip rule for idle entities.
3. Choose the fix by the owner of the number:
   - Fix the query when the skip rule is correct for storage. Use the horizon from the whole source, not from the selected series. A selection of only silent series then still has a reference time.
   - Change the legend to "last" only if a gap must show as no data.
   - Do not change ingest only to fix a legend, because the skip rule keeps the table small.
4. Apply the same change to every panel that reads the same table. Sibling panels for nodes and GPUs have the same fault.
5. Test the query on a database with one active series and one retired series. Assert that the last value of the retired series is zero. Update any older test that matches the previous query text.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust the panel | Read the legend value as the live count. | The legend showed the last value before the series ended. | Check the live source first. |
| Fill gaps for every bucket | Generate a zero point for each missing bucket. | It needs a series generator and many rows for long ranges. | Two closing points are enough for a step-style line and the legend. |

## Results & Parameters

### Configuration

```yaml
silence_threshold: 10 minutes   # two 5-minute buckets plus ingest lag
closing_points: [last_bucket + 5 minutes, horizon]
interpolation: stepAfter        # keeps the zero step flat to the end
```

### Expected Output

- A retired entity shows zero in the legend.
- An active entity keeps its real value.
- A panel with only silent entities still shows zero.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Model-serving fleet dashboard | Three capacity panels fixed in one change. | The query test needs a real PostgreSQL service. |

## References

- [Template](../templates/skill-template.md)
