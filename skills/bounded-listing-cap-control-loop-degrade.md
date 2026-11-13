---
name: bounded-listing-cap-control-loop-degrade
license: BSD-3-Clause
description: "Size the read of a scheduler listing in a control loop from measured per-item size, and degrade on a read error. Use when: (1) a supervisor parses scheduler or queue listings with a fixed byte cap, (2) a verbose JSON listing grows with the fleet, (3) a byte cap and a row cap disagree, or (4) a read error could stall the loop."
category: architecture
date: 2026-11-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [control-loop, supervisor, size-bound, byte-cap, streaming, degraded-mode, scheduler]
---

# Control-Loop Listing: Measure, Stream, Degrade

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-13 |
| **Objective** | Keep a supervisor loop alive as the listing it reads grows. |
| **Outcome** | Operational. A verbose JSON listing grew about 26 KB per job and hit a 1 MiB byte cap at about 39 jobs, while a separate row cap allowed thousands. The loop stalled. |

## When to Use

- A supervisor reads scheduler listings with a fixed byte cap.
- The listing format is verbose (full JSON per item).
- Two bounds (bytes and rows) give different limits.

## Verified Workflow

### Quick Reference

```text
1. Measure bytes per item on the real system. cap / bytes_per_item = real row limit.
2. Ask for a compact field format (only needed fields).
3. Parse rows as a stream. No cap on the job count.
4. Read error -> return "degraded", keep the last good state.
5. Log one degraded line per cause per period.
```

### Suggested Approach

1. Measure the real size of one item before you choose a bound. A bound with no measurement hides a limit far below the intended one.
2. Use a compact output format with only the fields the loop uses.
3. Parse as a stream so memory does not grow with the fleet. Put no cap on the number of jobs. Keep a cap only on one row.
4. On a read or parse error, return a degraded result and keep the last good state. Do not stop the loop and do not treat the error as an empty fleet (that starts surplus units or drops state).
5. Log one line per cause per period so a persistent fault does not flood the log.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Fixed 1 MiB byte cap on a JSON listing | Read the whole listing and refuse above the cap. | The cap was reached at about 39 jobs; the loop stalled. | Measure per-item size first. |
| A row cap of thousands next to the byte cap | Assumed the row cap was the real bound. | The byte cap bound first. | Keep one bound that matches the real limit, or none. |

## Results & Parameters

```yaml
listing_read:
  format: compact_fields
  parse: stream
  job_count_cap: none
  per_row_cap: yes
  on_error: {result: degraded, state: last_good, log: one_line_per_cause_per_period}
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Project-neutral scheduler supervisor | Release and deployment session | The loop stalled at a small fleet size. |

## References

- [Runtime component checks degrade, they do not stop](runtime-component-checks-degrade-not-stop.md)
