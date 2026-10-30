---
name: matplotlib-grouped-bar-date-offset-truncation
description: "Draw grouped bar series on numeric x positions with date tick labels. Use when date-valued bars overlap or a fractional-day offset collapses onto one position."
category: debugging
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags:
  - matplotlib
  - grouped-bar
  - date-arithmetic
  - datetime
  - timedelta
  - overlapping-bars
  - numeric-x-axis
  - chart-offset
---

# Matplotlib Grouped Bars: Date Offsets Truncate

## Overview

| Field | Value |
| ------- | --------- |
| **Date** | 2026-10-30 |
| **Objective** | Make grouped bar series sit side by side when the x values are dates. |
| **Outcome** | Successful. The bars separated after the chart moved from date offsets to numeric positions. |

## When to Use

Use this skill when these conditions apply:

- A grouped bar chart passes `datetime.date` values to `Axes.bar()`.
- Each series offsets its x values by a fraction of a day, such as `± timedelta(days=0.27)`.
- Two or more series draw at the same x, so the last series covers the others.
- The bar width is a fraction of a day, and the offset equals the width.

## Verified Workflow

### Quick Reference

Use numeric x positions and set the date labels on the ticks:

```python
positions = list(range(len(days)))
width = 0.27
ax.bar([x - width for x in positions], left_values, width=width, label="left")
ax.bar(positions, middle_values, width=width, label="middle")
ax.bar([x + width for x in positions], right_values, width=width, label="right")
ax.set_xticks(positions)
ax.set_xticklabels([d.isoformat() for d in days], rotation=45, ha="right")
```

### Suggested Approach

1. Identify the x value type. `datetime.date` keeps only whole days from a
   `timedelta`. `datetime.datetime` keeps the fraction.
2. Use numeric positions for grouped bars. The date unit conversion then does not
   apply to the bar geometry, and the offsets cannot truncate.
3. Keep the labels readable. Rotate the tick labels and set `ha="right"` when the
   labels are long or the axis is narrow.
4. Remove `Figure.autofmt_xdate()` when the x axis is numeric. It formats date
   ticks only.
5. Verify the figure. Each day must show one bar per series, and no bar must cover
   another.

If a numeric axis is not practical, use `datetime.datetime` values. Add the offset
to a combined date and time, and format the ticks yourself.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Attempt 1 | Offset `datetime.date` x values by `± timedelta(days=0.27)` to group three series. | `datetime.date` addition uses only `timedelta.days`. The 0.27-day fraction became 0, so all three series used the same x. | A sub-day offset needs a numeric x axis, or `datetime.datetime` values. |
| Attempt 2 | Rebuild the figure and expect the offset to appear. | The render was correct for the code. The positions were identical, so the output did not change. | When grouped bars overlap, check the x values, not the render step. |

## Results & Parameters

### Configuration

```python
width = 0.27                 # one third of a day, in axis units
positions = list(range(len(days)))
offsets = (-width, 0.0, width)
```

### Expected Output

- One bar per series per day.
- Bars adjacent, not overlapping.
- Date labels on numeric ticks.
- No `autofmt_xdate()` call on a numeric axis.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Report renderer | Weekly operations report figure | Three series over a date range. The numeric-position change separated the bars. See [notes.md](matplotlib-grouped-bar-date-offset-truncation.notes.md). |

## References

- [Matplotlib `Axes.bar` documentation](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.bar.html)
- [Python `datetime.date` documentation](https://docs.python.org/3/library/datetime.html#datetime.date)
- [Fix Altair facet layering](fix-altair-facet-layering.md)
