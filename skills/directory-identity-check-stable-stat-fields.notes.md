# Notes: Directory Identity Check with Stable Stat Fields

Supporting evidence for `directory-identity-check-stable-stat-fields.md`.
Identifiers of the private deployment (product, pool, host, job, repository,
and issue values) are withheld. Only decision-relevant shapes are kept.

## Verified failure shape (before the correction)

- A long-running management process repeatedly re-resolved its deployment
  root with a fail-closed guard. The guard compared a resolved path plus
  volatile stat fields (including directory mtime at nanosecond precision)
  between an open descriptor and the freshly read path.
- A separate heartbeat writer flushed status into the same tree on a short
  periodic cadence. Each flush updated the checked directory's volatile
  fields and nothing else: no replacement, no permission change, no
  ownership change.
- The management process died with a changed-during-resolution error after
  long uptime. The failure message showed equal path strings and differing
  volatile metadata, and the failure time fell on the heartbeat cadence.
- Recurrence was at week scale across the fleet, which matches the window
  arithmetic below. Ordinary validation never reproduced it.

## Window analysis

- The guard's vulnerable window is the time between the descriptor read and
  the path read: sub-millisecond.
- The writer flushed on a fixed period of seconds. Each flush had a
  probability below one in a million of landing inside a given window. The
  guard ran many thousands of windows per day across the fleet, which
  pushed the expected time to a false kill into the days-to-weeks range.
- Consequence: absence of failures in any finite soak is uninformative.
  Only field-class analysis (which fields can change without an identity
  change) or a boundary-injected test can find this defect.

## Correction and its verification

- The corrected guard compares `st_dev` and `st_ino` (filesystem and object
  identity) and keeps `st_mode`, `st_uid`, and `st_gid` in the compared set
  because permission and ownership changes are identity-relevant at this
  trust boundary. It no longer compares mtime, ctime, size, or link count.
- Regression coverage executed at the incident site on the production code
  paths:
  - A seam at the guard's stat reads lets the test run a directory mutation
    between the descriptor read and the path read. No sleeps, no threads.
  - Benign-churn arm: before the correction, the same benign write pattern
    the heartbeat performs made the guard fail; after the correction, the
    guard passes.
  - Real-replacement arm: replacing the directory at the same path (new
    inode) fails closed before and after the correction. The guard lost no
    protective strength.
- Deployment of the correction at the incident site is parked on the
  incident record at authoring time, pending an independent release owned
  outside this work. The design rule does not depend on that deployment.

## Why the first deterministic test was silently vacuous

- The first version simulated a benign write with file create+unlink inside
  the target directory, a minimal mutation.
- Sampled metadata before and after the pair was identical: the shared
  filesystem's timestamp granularity could render mtime and ctime equal,
  directory size returned to its prior value, and parent link count never
  changes on file add/remove. The guard therefore compared equal data in a
  test that claimed to exercise a race. The test passed and proved nothing.
- The fix on the test side was a created-and-kept empty subdirectory. It
  increments the target directory's `st_nlink` on typical filesystems and
  sets fresh mtime and ctime, so the injected churn is guaranteed-visible
  regardless of timestamp granularity. The corrected test then failed
  deterministically on the volatile-field guard and passed on the
  stable-field guard.
- General rule: inject churn that is observable in the data the guard
  compares, not churn that is only observable in the write syscall count.

## Operational notes

- Crash-looping watchdogs can mask this event class: the process restarts
  automatically and the rare fatal error scrolls out of sight between
  buffer flushes and log restarts. Count process starts over days when you
  suspect it, and correlate each start time with the writer cadence.
- Block-buffered service logs make the incident harder to read: the log
  file can appear stale for many hours while the process is healthy.
  Verify liveness through the process table (CPU time advancing, spawned
  scheduler-probe children) before you restart anything; a quiet log is
  not evidence of a hang.
