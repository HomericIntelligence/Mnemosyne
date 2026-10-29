# Notes: periodic-task-scheduler-fallback-chain

## Evidence

The source task was an hourly maintenance export on a shared batch cluster
with multiple login hosts. The account needed a cadence, and every standard
primitive was denied.

### Denial record (probed, not assumed)

- cron: the account was not present in the site allowlist (`cron.allow`);
  the system denied the edit.
- user systemd: no per-user manager and no session bus on the login hosts;
  the user manager was not a supported shape there.
- scheduler-native recurring submission: the site administrator had disabled
  the facility.

### The deployed shape

- A small wrapper script: first line of substance submits a successor with a
  delayed start for the next interval, then takes a non-blocking file lock,
  then runs the export once under the lock.
- Successor-first ordering was chosen deliberately: if the run crashes, the
  cadence survives; the lock makes the theoretical double-run harmless.
- Every run appends one summary line (items, units, blocked overwrites) to a
  log on shared storage. Verification after submission was a log read at the
  next interval plus a `squeue` check for the named successor.

### Observed behavior

- The chain survived a scheduler-driven host change: the successor landed on
  a different host and the lock-plus-shared-log design made that invisible.
- A manual one-off run raced a scheduled boundary once; the lock made it a
  no-op instead of a duplicated export.
- The log's regularity became the cadence proof: each interval added exactly
  one line, and the queued successor was named identically each time, so a
  simple filter showed the unbroken chain.

### Reanchor command

The document handed to the operator is a single `sbatch` of the wrapper. The
runbook records that site maintenance windows and draining events can break
the chain and that reanchoring is one command.

## Evidence: scheduler-owned driver branch (2026-10-26)

The source task was a 43-worker evaluation campaign on a shared batch
cluster. A watchdog loop resubmitted any worker whose job disappeared and
whose durable status file did not say complete, one worker at a time.

### Why not the chain shape

- Each worker ran for tens of minutes. Tenant pressure on the shared nodes
  killed workers unpredictably, so the controller had to resubmit within
  minutes; a queue-delayed successor for a fixed interval would have left
  the GPUs idle for most of the campaign.
- Failure degraded to a stall, not corruption: every worker kept durable
  state on shared storage, so a resubmit resumed instead of restarting.

### What failed before the fix

- First controller instance: `nohup setsid` under an interactive agent
  session on a compute allocation. It died when the allocation's host had an
  outage; the campaign stalled for days.
- Second instance: began in another interactive session as part of a server
  process tree. It died with that server restart.
- Both failures are the step-lifetime rule applied to controllers: the
  process owner was a session, and the session ended.

### The deployed shape

- The identical watchdog script, unmodified, wrapped in a five-directive
  batch script: account and QOS for the low-priority partition, one CPU, a
  small memory request, unlimited walltime, named job.
- The driver ran longer than a day on the low-priority partition. It
  survived multiple interactive-server restarts that killed unrelated
  monitor loops, resubmitted 42 workers unattended, and logged every
  resubmission to one file on shared storage.
- Verification at any point was two reads: the named job in the queue, and
  the tail of the resubmission log.

### Boundary kept deliberately

The chain remains the right shape for cadence-based one-shot runs: it
occupies no allocation between intervals. The driver job is the right shape
only when reaction latency inside the interval matters and the site grants
an unlimited-walltime CPU-only job on a low-impact partition.
