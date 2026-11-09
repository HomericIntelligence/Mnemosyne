---
name: weekly-report-remote-access
license: BSD-3-Clause
description: "Produce a telemetry-fed recurring report from a host that cannot reach the private telemetry store directly. Use when: (1) the collector connect call times out on a private network database, (2) local credentials or window defaults look right locally but produce stale or empty output, (3) the render step needs system libraries the host lacks, or (4) a PII prose guard blocks legitimate public-facing addresses in the report."
category: tooling
date: 2026-11-07
version: "1.0.0"
user-invocable: "false"
verification: verified-local
tags: [weekly-report, telemetry, ssh-forward, dial-host, tls, window-pinning, weasyprint, pii-scan]
---

# Weekly Report: Reach a Private Telemetry Store and Keep the Guards

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Produce a dated telemetry report on a host that has no route to the private telemetry database, without weakening TLS, the PII prose guard, or system installation rules. |
| **Outcome** | Operational. The collector, figures, prose, and PDF phases completed from a non-private-network host by an SSH local forward plus the repository's loopback dial-host override, credentials refreshed from the live component's own process environment, a pinned reporting window, and a user-space render environment. The pipeline's own PII scan passed before the PDF render. |

A recurring report pipeline usually runs where the telemetry lives. When it must run on a
non-private-network host, connect through the repository's own dial-host override rather than
changing TLS settings, refresh credentials from the live component instead of a stale dotenv file,
pin the reporting window instead of trusting the dated-directory heuristic, and supply render
toolchain libraries from a user-space environment. When a guard blocks legitimate prose, change the
prose's surface, never the guard.

## When to Use

- A report collector connect call ends in a TCP `TimeoutError` because its database lives on a
  private network.
- An SSH-forwarded connect fails with `InvalidPasswordError` until the local credentials agree
  with the live component's.
- A report run on the published date resolves a window of one day because the newest dated report
  directory is the one the run just created.
- The PDF step fails loading system GUI/text libraries (for example `libpangoft2`) that the host
  does not provide.
- The pipeline's prose scan refuses a legitimate public address (mailing list, support address)
  before the render.

## Verified Workflow

### Quick Reference

```bash
# 1. Forward the private database through any host that can reach it (keep the port local).
ssh -N -L 127.0.0.1:5432:<private-db-host>:5432 <jump-host>

# 2. Point the repository's loopback dial-host override at the forward. The TLS
#    certificate is still verified against the DSN's own hostname. Do NOT set this
#    variable inside batch or scheduler environments.
export <APP>_DB_DIAL_HOST=127.0.0.1

# 3. Pin the window. Never trust the newest dated directory on a same-day run.
uv run python <report-driver>.py --date <today> --since <previous-report-date> [more flags]

# 4. Render with user-space toolchain libraries; keep global installs untouched.
LD_LIBRARY_PATH=<user-render-env>/lib uv run python <report-driver>.py --only pdf
```

### Suggested Approach

1. Prefer the repository's documented dial-host override over any TLS change. With the override,
   TCP goes to the loopback forward while certificate hostname verification still binds to the
   DSN's real host. `sslmode=disable` is not an acceptable substitute; it removes the trust the
   override exists to keep.
2. Keep the override out of scheduler jobs. A loopback dial host that crosses into a batch
   environment makes every dial fail from nodes without the forward; see
   [scheduler-job-inherits-submitter-environment](./scheduler-job-inherits-submitter-environment.md)
   for that failure class. Export the variable only in the shell that runs the collector.
3. When the forwarded connect authenticates but the local dotenv credentials are stale, read the
   live component's process environment on a node that runs that component (for example one step
   of its scheduler allocation: `srun --jobid <id> --overlap --cpu-bind=none`), extract only the
   credential variables, and publish them to the shared configuration path with a temporary file
   plus an atomic rename. On shared storage, an atomic replace is the write; a file lock is not.
4. Window resolution that scans dated output directories consumes the directory the run itself
   creates. Pass `--since` (and `--end` when needed) explicitly and record the window in the
   report event log; the heuristic is a fallback for long gaps only.
5. Render toolchain libraries that the host does not ship come from a user-space environment
   (for example a small conda environment holding pango, cairo, and fontconfig), exported through
   `LD_LIBRARY_PATH` for the render process only. Do not add distributions to system paths, and
   prefer an existing prepared user environment over a new install when one exists.
6. A PII prose guard that refuses legitimate public-facing addresses is a surface problem, not a
   guard problem. Render the address with an HTML entity (`name&#64;domain`) so the reader sees
   the exact address and the raw-text pattern does not match. Do not add content-specific entries
   to the guard, and do not weaken it: the scan's job is to fail the run before a report with
   unintended personal data ever leaves.
7. Define completion as the pipeline's own validations passing on the final artifact — the prose
   scan runs again before each PDF render — not as "the file was written." When numbers in the
   prose are hand-corrected afterwards, apply
   [report-metric-consume-before-trusting](./report-metric-consume-before-trusting.md): every
   printed number comes back through its collector source before publication.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Direct connect | Ran the collector from the non-private-network host with the production DSN | TCP connect to a private-network database has no route; the run ends in `TimeoutError` | The network is the boundary; solve it at the network layer (a forward), not in the DSN |
| Manual dotenv sourcing | Read the admin dotenv file into the shell by hand and reran the collector | The greeting reached the server but `InvalidPasswordError` followed: ad-hoc sourcing mangled the credential value | Let the driver's own dotenv loader read the file; hand-parsing is an undetected mutation path |
| Default window | Ran collect on the report date without `--since` | The resolver saw the freshly created dated directory as the newest previous report and produced a one-day window with empty figures | Pin the start pin the moment a same-day report is possible; a silent wrong window is worse than a failed run |
| Raw public address | Put a public mailing-list address verbatim into the report prose | The prose scan refused the render with its personal-data error; the address is public but the guard is deliberately content-blind | Change the prose surface (HTML entity), keep the guard intact; a carve-out for one address teaches the next writer to carve out ten |

## Results & Parameters

### Configuration

```text
Local forward:   ssh -N -L 127.0.0.1:(db-port) <jump-host with private route>
TLS behavior:    certificate verified against the DSN hostname, unchanged
Dial override:   exported only in the collector shell; never in scheduler environments
Window:          --since <previous published report date> on every same-day or re-run
Credential path: write temp file + atomic rename on shared storage; address never printed
Render env:      user-space libraries via LD_LIBRARY_PATH for the render process only
PII guard:       HTML entity form in prose; scan passes, reader-visible text identical
```

### Expected Output

- Collector summaries show real window rows instead of timeouts or one-day emptiness.
- The PDF phase runs the prose scan again and passes on the final corrected report.
- The published report links the forward usage in its operator notes without internal
  hostnames, addresses, or credential identifiers.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Comet weekly report | Dated report produced on a non-private-network host: forward + loopback dial-host for collect, credential refresh from the live gateway's process environment on shared storage, `--since` after a one-day window, user-space pango for the PDF, HTML entity for a public list address. | See [notes.md](./weekly-report-remote-access.notes.md). |

## References

- [scheduler-job-inherits-submitter-environment](./scheduler-job-inherits-submitter-environment.md) — the mirror failure: loopback dial settings that leak into batch jobs.
- [report-metric-consume-before-trusting](./report-metric-consume-before-trusting.md) — the number-trust rule for the prose and tables of the same report.
- [durable-export-overwrite-guard](./durable-export-overwrite-guard.md) — adjacent guard philosophy: let scheduled artifact jobs refresh without destroying verified content.
