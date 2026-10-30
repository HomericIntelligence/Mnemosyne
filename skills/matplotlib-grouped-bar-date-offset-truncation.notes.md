# Notes: matplotlib-grouped-bar-date-offset-truncation

## Reproduction

A report renderer drew three daily series as grouped bars:

```python
days = [date(2026, 9, 29), date(2026, 9, 30), date(2026, 10, 1)]
width = 0.27
ax.bar([d - timedelta(days=width) for d in days], commits, width=width, label="commits")
ax.bar(days, merged, width=width, label="merged")
ax.bar([d + timedelta(days=width) for d in days], closed, width=width, label="closed")
fig.autofmt_xdate()
```

The rendered figure showed one bar per day. The other two series were hidden below
the last one.

## Cause

`datetime.date + timedelta` adds only `timedelta.days`. For
`timedelta(days=0.27)`, `timedelta.days` is 0. These three expressions are equal:

```python
d - timedelta(days=0.27) == d
d == d
d + timedelta(days=0.27) == d
```

All three `bar()` calls therefore used the same x values. The last call painted over
the first two. `datetime.datetime` does not have this limit because it keeps the
time part.

## Fix

Use numeric positions and put the dates on the tick labels:

```python
positions = list(range(len(days)))
ax.bar([x - width for x in positions], commits, width=width, label="commits")
ax.bar(positions, merged, width=width, label="merged")
ax.bar([x + width for x in positions], closed, width=width, label="closed")
ax.set_xticks(positions)
ax.set_xticklabels([d.isoformat() for d in days], rotation=45, ha="right")
```

Remove `autofmt_xdate()` because the axis is numeric.

## Verification

- The regenerated figure showed three adjacent bars per day.
- A second figure with long category labels needed `rotation=25` and `ha="right"`
  to prevent label collisions. Rotation is a readability fix, not part of the
  offset fix.
- The report table that used the same daily values did not change.

## Related observation

A stacked or overlaid chart is a different intent. Use grouped bars only when each
series must stay visible at the same x. Use a stacked chart when the series form a
total.
