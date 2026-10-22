# Notes: slurm-walltime-expiry-outage-diagnosis

## Evidence

The source session investigated a reported replica outage inside a
scheduler-backed model-serving pool. The pool runs each replica as a
long-lived scheduler job with a multi-day time limit, and a recycling
mechanism is expected to replace the allocation before expiry.

### Accounting record (values generalized)

| Field | Observed | Classification value |
| ------ | --------- | -------------------- |
| Parent state | COMPLETED, exit code 0:0 | No fault |
| Reason | Empty | No error or administrative hold |
| Steps | CANCELLED, exit code 0:15 | Terminated by signal 15 (SIGTERM) |
| Elapsed | 6 days, 23 hours, 59 minutes, 32 seconds | Within drain grace of the limit |
| Time limit | 7 days | Elapsed equals the limit |

Elapsed within about one minute of the limit, plus SIGTERM delivery to the
steps, plus a clean parent exit, classifies the event as the scheduler's
planned time-limit drain.

### Service log signature (paraphrased)

1. A line records SIGTERM receipt near the reported down time.
2. The service stops taking new work and removes or drains its registered
   workers.
3. The process exits cleanly less than two minutes after the signal.

There is no stack trace, out-of-memory record, or hardware error. The log
corroborates the drain; accounting binds it to the limit.

### Renewal mechanism health

The pool's status record contained a blocked-recycling reason naming a
lease-refresh failure. The allocation was therefore not replaced before
expiry, and the drain converted into a visible outage. The drain was
correct behavior; the blocked renewal is the defect that needs repair.

## Timezone handling

The reporter described the event time as "6:20 pm PST" for an October
date. October in the US Pacific zone is PDT (UTC-7), not PST (UTC-8).
The literal PST reading lands one hour late. Evaluating both variants
bound the evidence window:

- SIGTERM receipt: about two minutes before the reported minute (PDT).
- Clean exit: approximately the reported minute (PDT).

Rule: when a zone abbreviation arrives in its standard form during
daylight-saving months, compute both the standard and the daylight
offset and search the union of the two windows.

## Verification commands

```bash
# Accounting comparison that decided the classification (shape only).
sacct -j <job-id> --format=JobID,State,ExitCode,Reason,Start,End,Elapsed,Timelimit
sacct -j <job-id> --format=JobID,State,ExitCode   # per-step signals

# Both DST variants of a reported local time.
for tz in PST8PDT US/Pacific; do TZ=$tz date -d '<reported-local-time>' -u; done
```

## Privacy

Job identifiers, node names, pool and cluster names, filesystem paths, and
the exact status field names are intentionally omitted. The decision rules
use only generalized scheduler concepts: elapsed versus limit, termination
signal, exit code, drain log signature, and renewal health.
