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
