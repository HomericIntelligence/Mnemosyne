# Fork-Inherited Executor Ownership — Notes

Supporting evidence for
[architecture-fork-inherited-executor-ownership](architecture-fork-inherited-executor-ownership.md).
These notes are not part of normal retrieval.

## Context

A proxy served one event loop per process. The change moved blocking
shared-filesystem calls to a bounded worker pool under a deadline. The pool was
created at module import time.

The proxy test suite includes a test that replaces a result file with a FIFO,
forks a child process, and asserts that the request in the child answers within
2 seconds. The parent process had already used the pool during setup.

## Evidence

- Baseline check: the FIFO test passed on the default branch. The change caused
  the regression, so it was not a known failure.
- Reproduction: a small script called the pool in the parent, called `os.fork()`,
  then submitted to the inherited pool in the child. The child never answered.
- Diagnosis: when the child builds a new pool, it reset the inherited admission
  counter. With the increment placed before the pool lookup, the reset erased
  the increment. The counter read `0` during a running call and reached `-1`
  after the call ended. A stuck call therefore did not hold its slot.
- Fix: create the pool on first use, rebuild it when the recorded PID differs
  from the current PID, and reset the admission counter only during the
  rebuild. Resolve the pool before the increment.
- Verification: the fork unit test passed, and the FIFO test and the other
  batch-read tests passed. A standalone script showed the stuck call holding
  its slot (count `1`) and the next call rejected with the full-queue error.

## Diagnostic steps that worked

1. Read the failing test to find where the child process starts.
2. Compare the same test on the default branch.
3. Reproduce without the test harness. This showed that the partial log message
   that looked like a patched value was only float formatting and not the cause.
4. Print the counter, the future state, and the thread state. A future in the
   `RUNNING` state with a released slot showed that the release source was wrong.
5. Trace the release callback and every counter change with a timestamp and a
   thread name. This showed the reset that occurred inside the pool lookup.

## Limits

- The project provides local test evidence. CI/CD is pending.
- The scheduler-managed deployment template was checked with a lifecycle test
  that runs in a normal process. The probe logic itself was not part of this
  lesson.