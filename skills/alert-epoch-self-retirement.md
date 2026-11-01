---
name: alert-epoch-self-retirement
license: BSD-3-Clause
description: "Bound an alert lane that reads a remote exporter gauge by the freshness of the epoch inside that gauge, so the alert retires itself when the exporter never clears the value. Use when: (1) an alert fires while a gauge exported by another service stays positive, (2) the documented recovery depends on the exporter clearing the gauge to zero, (3) the planned terminal path removes the watched object, so the clearing scrape never comes, and (4) the operator cannot name the failed object because the aggregation dropped its labels."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - alerting
  - observability
  - prometheus
  - gauge
  - epoch
  - staleness
  - recovery
  - self-retirement
  - label-identity
  - terminal-failure
  - sql
  - python
---

# Alert Epoch Self-Retirement

**Supporting detail:** [notes](./alert-epoch-self-retirement.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Make an alert lane that depends on a remote exporter gauge end on its own when the exporter cannot clear the gauge. |
| **Outcome** | Operational decision procedure. The lane fires only while the gauge epoch is fresh, and the alert line keeps the object identity from the gauge labels. |
| **Verification** | verified-local — focused unit tests and lint passed on the reviewed branch; the SQL path was not run against a live database in the source session. |

## When to Use

- An alert condition is "the newest sample of gauge G is above 0".
- Another service exports G, and the documented recovery waits for that service to set G to 0.
- A planned failure path removes the watched object, or the process that holds G restarts. Either
  event makes the clearing write impossible, so the alert repeats on every cooldown until an
  operator acts.
- The alert loses per-object labels during aggregation, so the operator cannot name the failed
  object.

Do not use this rule when the triggering service writes the alert state itself. In that case the
service already owns the clear path.

## Verified Workflow

### Quick Reference

Fire only while the epoch is fresh. Use the same window for the history query and the age bound.

```python
age = now - last_seen_seconds   # epoch carried by the gauge
if last_seen_seconds <= 0 or age > TERMINAL_WINDOW_S:
    return []                   # the lane retires itself; recovery posts
```

```sql
-- Keep the newest sample that carries the epoch so one empty scrape
-- does not drop the lane.
SELECT DISTINCT ON (object)
       object, epoch_value, total, worker_label, model_label
FROM history
WHERE ts > now() - interval '15 minutes'
  AND epoch_value IS NOT NULL
ORDER BY object, ts DESC
```

### Suggested Approach

1. **Find the clear path before you write the lane.** Read the companion producer contract. Ask
   what writes 0. If the answer is "the object must come back", the lane has no bounded end.
2. **Bound the lane by the epoch, not by the gauge value.** The gauge reports an event time. The
   age `now - epoch` reaches the window edge whether or not the object returns. The lane then
   stops, and the existing recovery message posts.
3. **Use one window value.** The history query window and the age bound must agree. Name the
   constant once and point the SQL comment at it.
4. **Keep the filter before the aggregation.** A `IS NOT NULL` filter before `DISTINCT ON` keeps
   the newest non-null row. One scrape without the series then does not drop the lane. Record
   that choice in the comment because a reviewer will read it as a bug.
5. **State the recovery meaning in the documentation.** A stale epoch shows that the signal went
   quiet. It does not show that the object returned. Say so.
6. **Keep the object identity.** Carry the gauge labels of the newest epoch through the monitor,
   the storage, and the alert line. Name the object in the line when the labels are present, and
   stay silent about identity when they are absent.
7. **Keep storage additions bounded.** Add text columns with a length check. Normalize the value
   at the ingest boundary.
8. **Test the retirement branch.** A fresh epoch must fire, and an out-of-window epoch must stay
   silent. Use a relative epoch in tests that read the clock, so the age bound does not hide the
   behavior you test.

### Failure Modes to Check

| Failure mode | Symptom | Correction |
| --- | --- | --- |
| Lane keyed on a sticky gauge value | Alert repeats at each cooldown with no end | Bound the age of the epoch |
| Broad catch around the lane query | The lane is off with no journal line | Catch the undefined-column class only, and log other failures |
| Aggregation drops labels | The operator cannot name the failed object | Keep the labels of the newest epoch |
| Test uses a fixed past epoch | The age bound suppresses the assertion | Build the epoch from the current clock |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| Original lane | Fired while the newest non-null gauge sample was above 0 | The clear scrape cannot arrive on the removal path, so the lane stayed red indefinitely | A lane that reads a remote gauge needs its own end condition |
| Broad catch | Substituted an empty row list on any fetch error | A persistent failure disabled the lane with no signal | Catch only the documented error class. Log the rest |
| Documentation in an existing catalog page | Appended prose to a page that the base branch had already deleted | The merge stayed in conflict and the contract never landed | Find the current owner page before you append prose |

## Results & Parameters

### Configuration

```yaml
window_seconds: 900        # matches the history query window
clear_value: 0             # exporter clears the gauge on success
filter: "epoch IS NOT NULL"   # before DISTINCT ON
```

### Expected Output

- A fresh epoch posts one alert line that names the object and the age.
- An epoch outside the window posts `recovered: <lane>[<object>]` and stops the lane.
- A missing epoch posts nothing.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal repository | Implementation review round on one pull request; five findings closed | See the [notes](./alert-epoch-self-retirement.notes.md). |

## References

- [Silent boundary exception classification](silent-boundary-observability-exception-classification.md)
- [Readiness from closed status and local alerts](observability-readiness-closed-status-local-alert-recovery.md)