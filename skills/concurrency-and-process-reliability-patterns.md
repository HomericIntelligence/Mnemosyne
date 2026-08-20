---
name: concurrency-and-process-reliability-patterns
description: "Debug Python concurrency and process failures: blocked stdin, broken signal delivery, worker-thread terminal calls, global parallelism, OOM, optional-import traps, transient subprocess errors, leaked child trees, and finite timeout cleanup."
category: debugging
date: 2026-08-06
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: concurrency-and-process-reliability-patterns.history
tags:
  - subprocess
  - process-group
  - signals
  - multiprocessing
  - asyncio
  - semaphore
  - pytest
  - oom
  - retry
  - nats
---

# Concurrency and Process Reliability Patterns

## Overview

Separate resource exhaustion, signal topology, blocking I/O, and leaked-lifetime failures before
changing code. Give every subprocess noninteractive I/O and a finite bound, cap the resource that
is actually scarce, own descendant cleanup explicitly, and keep optional imports narrow.

Most patterns have local or CI case evidence, but the generalized finite-timeout wrapper from
ProjectHephaestus issue #2398 remains unverified design guidance. Case provenance is indexed in
[concurrency-and-process-reliability-patterns.notes.md](concurrency-and-process-reliability-patterns.notes.md),
and complete prior content is in
[concurrency-and-process-reliability-patterns.history](concurrency-and-process-reliability-patterns.history).

## When to Use

- Parallel workers hang on exit or ignore Ctrl+C.
- A child waits on inherited stdin or terminal operations block from a worker thread.
- Multiple executors exceed a global concurrency or memory budget.
- Pytest disappears under OOM or hangs on expensive unmocked simulation.
- An optional NATS import silently disables support because an unrelated enum import failed.
- Git clone or another idempotent network subprocess needs bounded retry.
- Agent fan-out exhausts a host despite a `ThreadPoolExecutor` limit.
- Executor shutdown leaves an already-running child or descendant alive.
- A direct subprocess needs a validated timeout, tree cleanup, stable diagnostics, and portability.

## Verified Workflow

### Triage sequence

1. Capture process trees, open descriptors, thread stacks, memory, and the last test or task ID.
2. Determine whether the blocked resource is stdin, terminal state, a semaphore, memory, network,
   executor lifetime, or child-process lifetime.
3. Reproduce with a finite external bound.
4. Fix ownership at the process or task boundary.
5. Verify cleanup under success, failure, timeout, cancellation, and Ctrl+C.

## Patterns

### Make subprocesses noninteractive

```python
completed = subprocess.run(
    argv,
    stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    timeout=timeout_seconds,
)
```

Inherited stdin lets a background child wait for input forever. Use explicit streams and a finite
timeout; never rely on a worker's ambient terminal.

### Preserve terminal signal delivery

Do not call `os.setpgrp()` or `os.setsid()` on the main application merely to organize workers;
that can detach it from the foreground process group and break Ctrl+C delivery. Isolate individual
children instead with `start_new_session=True` when descendant cleanup is required.

Keep `stty` and terminal restoration on the main thread and bound the cleanup command:

```python
subprocess.run(
    ["stty", "sane"],
    stdin=subprocess.DEVNULL,
    timeout=2,
    check=False,
)
```

Treat failure as a stable warning; cleanup must not become a second hang.

### Enforce global parallelism at the scarce operation

A per-executor `max_workers` does not cap several executors or nested agent sessions. Share a
cross-process semaphore and acquire it immediately around the expensive operation:

```python
manager = multiprocessing.Manager()
global_slots = manager.BoundedSemaphore(limit)


def worker(item):
    with global_slots:
        return run_expensive_operation(item)
```

Use a manager-backed semaphore when the limit must be shared by separately created processes; a
plain `multiprocessing.Semaphore` passed through incompatible process construction paths may not
provide the intended shared coordination.

For coroutines, use one shared `asyncio.Semaphore` around agent/session creation. Thread count is
not the same resource as concurrent external sessions.

Also cap per-child build parallelism: total runnable jobs are approximately agent sessions times
jobs per build. Avoid giving every child `nproc` workers.

### Diagnose OOM with a recoverable memory limit

```bash
ulimit -v 4194304
pytest -vv path/to/suspect_tests
```

Use a child shell or wrapper so the limit does not alter the parent session. Bisect by test file,
then by test ID, then reproduce the underlying allocation with `tracemalloc`. A virtual-memory cap
turns host-level SIGKILL into a bounded failure when supported; document platform limitations.

If a test invokes Monte Carlo or another expensive simulation incidentally, patch the simulation
boundary and assert requested parameters. Keep a separate bounded integration/performance test for
the real implementation.

### Keep optional import guards narrow

```python
try:
    import nats
except ImportError:
    nats = None

STATUS_CONNECTED = "CONNECTED"
```

Do not place local enums or unrelated imports inside the same `try`: their failure masquerades as
an absent optional dependency. Report connection state through controlled logging/callbacks rather
than allowing library stack traces to become the user interface.

The recorded fail-fast connection case used copy-ready parameters:

```python
options = {"allow_reconnect": False, "connect_timeout": 3}
connection = await asyncio.wait_for(nats.connect(**options), timeout=5)
logging.getLogger("nats").setLevel(logging.CRITICAL)
```

If the caller owns retries instead, the recorded interval was 5 seconds. Do not combine internal
reconnect loops with an external retry loop without one documented total bound.

### Retry only transient, idempotent subprocess failures

```python
TRANSIENT = ("timed out", "connection reset", "temporary failure", "early eof")


def run_with_retry(argv, attempts=3):
    for attempt in range(1, attempts + 1):
        result = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        detail = f"{result.stdout}\n{result.stderr}".lower()
        if result.returncode == 0:
            return result
        if attempt == attempts or not any(token in detail for token in TRANSIENT):
            raise RuntimeError("command failed")
        time.sleep(min(2 ** (attempt - 1), 8))
    raise AssertionError("unreachable")
```

Validate `attempts` and timeout bounds. Do not retry authentication, syntax, policy, or other
permanent errors. Redact credentials and sensitive arguments from diagnostics.

### Reap in-flight child process groups

`ThreadPoolExecutor.shutdown(cancel_futures=True)` cancels queued futures only; it cannot stop a
subprocess already running inside a worker. Spawn each owned child in a new session, register its
process group while blocking, and unregister in `finally`:

```python
proc = subprocess.Popen(argv, start_new_session=True)
registry.add(proc.pid)
try:
    return proc.wait(timeout=timeout_seconds)
finally:
    registry.discard(proc.pid)
```

Shutdown order:

1. stop accepting work;
2. signal every registered group with `SIGTERM`;
3. wait for a short fixed grace period;
4. send `SIGKILL` to surviving groups;
5. reap direct children;
6. shut down the executor without an unbounded join.

Guard the registry with a lock. Ignore only expected process-race errors such as an already-exited
group; surface permission and ownership failures.

### Bound direct subprocesses and clean descendants

Validate operator overrides as integers in a deliberate range, for example `1..86400` seconds.
On POSIX, start a new session and terminate the group on timeout. On platforms without process
groups, terminate then kill the direct child. Use stable redacted diagnostics and exit `124` for a
timeout-facing CLI contract.

Pseudo-code:

```python
try:
    proc.wait(timeout=timeout_seconds)
except subprocess.TimeoutExpired:
    terminate_owned_tree(proc)
    print(f"command timed out after {timeout_seconds}s", file=sys.stderr)
    return 124
```

Bound every cleanup wait. Treat `TimeoutExpired.output` and `.stderr` as hostile optional
bytes-or-text values. Test real descendant termination, missing metadata, non-POSIX success, and
invalid override values. This generalized pattern is design-stage until implementation evidence
for issue #2398 is recorded.

## Decision Rules

- Give every subprocess explicit stdin, output handling, and a finite duration.
- Isolate owned children, not the main application, into process groups.
- Terminal operations belong on the main thread and have bounded cleanup.
- Cap the actual expensive operation across all producers.
- Executor cancellation does not imply process cancellation.
- Register a child before waiting and unregister in `finally`.
- Retry only classified transient failures of idempotent operations.
- Optional import guards include only the optional dependency.
- Memory limits and process-group behavior are platform capabilities, not assumptions.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Inherit child stdin | Background child waits forever | Use `DEVNULL` |
| 2 | Move the main process to a new group | Terminal stops delivering Ctrl+C as expected | Create sessions only for owned children |
| 3 | Run `stty` from workers | Terminal lock or coordination hangs | Restore on main thread with timeout |
| 4 | Limit each executor separately | Aggregate concurrency still exceeds budget | Share one semaphore at the scarce operation |
| 5 | Diagnose shell disappearance from traceback | OOM SIGKILL leaves none | Apply child memory bound and bisect verbosely |
| 6 | Put enum import in optional dependency guard | Local import failure disables NATS silently | Narrow the guard |
| 7 | Retry every nonzero exit | Permanent failures are delayed and obscured | Classify transient errors and bound attempts |
| 8 | Call `shutdown(cancel_futures=True)` | Running child continues after executor shutdown | Track and terminate owned process groups |
| 9 | Kill only the direct child | Grandchildren survive | Terminate group with direct-child fallback |
| 10 | Wait forever during cleanup | Shutdown fix becomes another hang | Bound TERM grace, KILL, and reap phases |

## Results & Parameters

- Direct subprocesses use explicit noninteractive I/O and finite timeouts.
- Operator timeout overrides are validated in a deliberate bounded range such as `1..86400`.
- The recorded OOM diagnostic used `ulimit -v 4194304` (4 GiB) and optionally
  `ulimit -t 180`; size limits should be adjusted to the host budget.
- Timeout-facing CLIs use stable redacted diagnostics and exit code `124`.
- Retry attempts default to a small finite count such as three with capped backoff.
- Owned process groups receive bounded TERM, KILL, and reap phases before executor shutdown.
- Per-executor worker counts do not replace a shared cap on the actual scarce operation.

## Verification Checklist

- Reproduce stdin blocking with and without `DEVNULL`.
- Send Ctrl+C and confirm the main process and children exit predictably.
- Measure peak concurrent expensive operations across multiple executors.
- Run OOM bisection in a disposable bounded shell.
- Assert optional dependency failure reports the correct cause.
- Test retry success, permanent failure, exhausted attempts, and timeout.
- Spawn a real sleeping descendant and prove shutdown completes within a fixed bound.
- Confirm no owned PID or process group remains after timeout or cancellation.
- Run focused tests plus the repository's full concurrency/process suite.

## Evidence Boundary

The semaphore, retry, OOM, optional-import, and leaked-child patterns have indexed local or CI
evidence. The generalized direct-subprocess timeout contract from issue #2398 remains unverified.
