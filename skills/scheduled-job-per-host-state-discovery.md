---
name: scheduled-job-per-host-state-discovery
license: BSD-3-Clause
description: "Make a self-launched or scheduled job resolve the per-host application state directory at job start instead of binding one static path. Use when: (1) a scheduled, cron, or self-resubmitting job reads application state such as a database or cache, (2) the job runs on different hosts or allocations over time, (3) an application can keep its live state under host-local scratch (for example /var/tmp/<user>) instead of the default home path, (4) an hourly job logs 'not found' repeatedly without anyone noticing, or (5) a lock acquisition status is confused with a real job failure in logs."
category: tooling
date: 2026-10-24
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - scheduled-job
  - self-resubmitting
  - state-discovery
  - xdg-data-home
  - host-local-scratch
  - silent-no-op
  - fail-loud
  - heartbeat
  - slurm
  - flock
---

# Scheduled Job Per-Host State Discovery

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Keep a re-launched job working when the live application state moves to a different host or a different directory layout, and surface every silent no-op promptly. |
| **Outcome** | Operational. An hourly export job that silently collected nothing for three days on a relocated host now resolves state from a precedence list, exits non-zero with every searched path when nothing matches, records a heartbeat on each success, and no longer logs a busy lock as a failure. |
| **Verification** | verified-live: discovery selected the correct database on a live host; the no-database path returned exit 2 and listed every searched candidate; two concurrent runs produced one worker and one silent clean exit; recovered archive was verified by message-count equality and byte-identical comparison of every file. See [notes](scheduled-job-per-host-state-discovery.notes.md). |

## When to Use

- A scheduled, cron, or self-resubmitting job reads application state (database, cache, queue, index) from a filesystem path.
- The job lands on different hosts or allocations over time (batch scheduler, container rescheduling, multi-node cluster).
- The application permits its state directory to move per host: an `XDG_DATA_HOME`-style environment override, host-local scratch such as `/var/tmp/<user>`, or a launch wrapper that redirects state away from a shared home.
- An export or sync job logs `not found` or `database not found` on every run and continues anyway.
- A wrapper script conflates two distinct exit conditions, for example a busy lock with a real job failure.

## Verified Workflow

### Quick Reference

Resolve the state location at job start from a precedence list, and fail loud:

```bash
# Precedence: $XDG_DATA_HOME/app, home default, host-local scratch.
# If none exists: exit non-zero and print every path searched.
for dir in "${XDG_DATA_HOME:+$XDG_DATA_HOME/app}" "$HOME/.local/share/app" "/var/tmp/$USER/app"; do
    [ -e "$dir/app.db" ] && DB="$dir/app.db" && break
done
[ -n "${DB:-}" ] || { echo "no state database; searched: ${XDG_DATA_HOME:-unset} $HOME/.local/share/app /var/tmp/$USER/app" >&2; exit 2; }
```

Apply the same rule at every boundary that reads or writes state, including the output destination.

### Suggested Approach

1. **Never bind the state path at author time.** A default path fixed in the script (or worse, evaluated at import time in the producer) becomes wrong the moment any host redirects state. Resolve from the runtime environment on every invocation: standard override variable first, home default second, known host-local convention last. An explicit `--db`-style argument still wins over all discovery.
2. **Fail loud, and name the evidence.** When no candidate exists, exit non-zero and print every searched path plus how to override. A quiet log line with exit 0 lets a silent gap last for days; a real exit code plus the searched paths gives an operator both the signal and the repair instruction in one run.
3. **Verify outcomes, not exit codes.** Write a heartbeat timestamp on each successful run. A stale heartbeat is the cheapest possible alarm. If the consumer of the output is another system, cross-check counts against the state source (for example sessions in the database vs. artifacts on disk) — filename presence is not proof; compare content.
4. **Keep lock status separate from job status.** With `flock -n`, take the lock on its own descriptor and treat "busy" as a clean no-op exit. Do not let a busy lock produce a failure log entry indistinguishable from a genuine job failure.
5. **Tolerate nullable metadata.** If a schema column has no NOT NULL constraint, some row will eventually carry NULL (here: a timestamp column that crashed arithmetic across the entire job). Treat NULL as "unknown, cannot prove currency" and re-do the work for that row; never let one bad row abort all rows.
6. **When recovering state from a dead host onto shared storage, verify before and after merge.** Diff scheduled-accounting history against output contents; confirm the recovered database integrity before reading it; before any overwrite of existing artifacts, prove a superset or byte-identity — see `durable-export-overwrite-guard` for the overwrite policy itself.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Static default path | The export defaulted to one home-relative state path for every host. | One host kept live state on node-local scratch; the job logged "not found" 29 times across three days and collected nothing. | Per-host state layout must be discovered at job start from a precedence list. |
| Log-and-continue failure mode | The job printed the error and exited 0. | Nothing surfaced the gap until output was audited; the silent window covered most of the lost period. | A missing state source is an operator event: exit non-zero and print every searched path. |
| `flock -n` chained to the job | The wrapper branched on the combined exit code of `flock -n` plus the worker. | A busy lock reads as rc 1, identical to a real job failure; every overlapping run was logged as a failure. | Acquire the lock on its own descriptor; let busy lock exit 0 quietly; log real failures with host and exit code. |
| Trusting filename presence for merge completeness | Counted output files present after a copy. | Presence cannot show a same-name file with different content. | Compare content (byte-level) for every merged file before claiming the merge is complete. |

## Results & Parameters

### Configuration

State-path precedence used in the verified run:

```text
1. $XDG_DATA_HOME/app/app.db     (application-standard override; highest priority)
2. $HOME/.local/share/app/app.db (the default)
3. /var/tmp/$USER/app/app.db     (host-local scratch convention; lowest priority)
Explicit --db argument            (always wins; a missing explicit path exits 1)
```

Wrapper elements that made failures observable:

```bash
exec 9>"$LOCK"                      # lock on its own descriptor
flock -n 9 || exit 0               # busy lock = quiet clean exit
job >>"$LOG" 2>&1; rc=$?
[ "$rc" -eq 0 ] && date -Is >"$HEARTBEAT"   # heartbeat only on success
```

### Expected Output

- On a matching host the job discovers state without configuration and dumps it; on a host with no state it exits 2 with the full searched-path list.
- A heartbeat file advances on every success; a stale heartbeat identifies a broken run before any output audit.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A session-history export pipeline on a batch-compute cluster | Recovery of state stranded on a dead compute node; fix merged upstream via review | See [notes](scheduled-job-per-host-state-discovery.notes.md). |

## References

- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/)
- [durable-export-overwrite-guard](durable-export-overwrite-guard.md) — the write-side guard for rerunnable exports whose divergent-history policy this workflow defers to
- [pola-consolidate-duplicated-silent-default-resolver](pola-consolidate-duplicated-silent-default-resolver.md) — the same fail-loud principle applied to duplicated magic defaults
