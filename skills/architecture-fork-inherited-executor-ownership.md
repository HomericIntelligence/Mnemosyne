---
name: architecture-fork-inherited-executor-ownership
license: BSD-3-Clause
description: "Give each forked process its own bounded worker pool and take the admission slot after pool resolution. Use when a module-level executor serves a process that forks, when work submitted in the child never runs, or when in-flight accounting drifts after fork."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - fork
  - thread-pool-executor
  - worker-pool
  - process-ownership
  - admission-control
  - multiprocessing
  - event-loop
  - backpressure
---

# Fork-Inherited Executor Ownership

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Keep a shared worker pool usable after a process forks, and keep its admission counter correct. |
| **Outcome** | Operational |

A forked child receives a copy of the executor object. It does not receive the
parent's worker threads. A child that submits work to the inherited pool queues
that work forever, because no thread exists to run it. The child then blocks or
times out with no error, which hides the cause.

## When to Use

- A module-level, process-wide `ThreadPoolExecutor` serves code that a test
  harness or a service can fork from.
- A request in a forked child hangs while the parent reports the same call as
  fast.
- An in-flight or admission counter disagrees with the work that actually runs,
  and the count can go below zero.
- A bounded queue rejects work that should fit, or accepts work that should be
  rejected.

## Verified Workflow

### Quick Reference

Create the pool lazily for each process, and resolve the pool before you take
an admission slot:

```python
_pool: ThreadPoolExecutor | None = None
_pool_pid = -1
_pool_lock = threading.Lock()

def process_pool() -> ThreadPoolExecutor:
    global _pool, _pool_pid, _inflight
    with _pool_lock:
        if _pool is None or _pool_pid != os.getpid():
            _pool = ThreadPoolExecutor(max_workers=WORKERS)
            _pool_pid = os.getpid()
            with _inflight_lock:
                _inflight = 0          # the parent's count is not the child's
        return _pool

def submit(fn, *args):
    global _inflight
    pool = process_pool()              # first: creation can reset the counter
    with _inflight_lock:
        if _inflight >= MAX_INFLIGHT:
            raise QueueFull()
        _inflight += 1
    pending = pool.submit(fn, *args)
    pending.add_done_callback(release)  # release only when the thread ends
    return pending
```

### Suggested Approach

1. Find the ownership boundary. A pool is process-owned. If the code can fork
   after the pool exists, the pool must be created per process, not at import.
2. Create the pool on first use, and record `os.getpid()` with it. Rebuild the
   pool when the recorded PID differs from the current PID.
3. Reset the admission counter during that rebuild. A counter copied from the
   parent describes threads that do not exist in the child.
4. Take the admission slot only after the pool is resolved. Pool creation can
   reset the counter, so an increment that comes first is erased. The count can
   then go negative, and the bound stops working.
5. Release the slot in a done-callback, not in the caller. A call that passes
   its deadline keeps its slot until its thread ends. This keeps the bound true
   for a stuck filesystem or network call.
6. Reproduce the fault with a real fork. Call the pool once in the parent, fork,
   and call it again in the child with a bounded wait. A child that never
   answers confirms the fault.
7. Keep the regression test. It holds the contract when a later change moves the
   pool back to module level or to import time.

If the runtime cannot fork, the per-process check stays correct and cheap. The
PID matches, so the pool is created once. Keep the check, because the same code
can run under a forking test runner.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Create one bounded pool at import time and reuse it everywhere. | A forked child inherited the object but not the threads. A request in the child queued work that no thread ran, and the request never answered. An existing test that forked after the parent used the pool caught this. | A pool is process-owned. Create it per process and reset the admission counter on rebuild. |
| 2 | Add the PID rebuild, but keep the increment before the pool lookup. | The rebuild reset the counter after the increment, so the first stuck call freed its slot early and a later call was admitted. The count reached `-1`. | Resolve the pool before you take the slot. |
| 3 | Compare the failing test against the default branch before any fix. | The test passed on the default branch, so the change caused the regression. | Confirm the baseline first. This tells a regression apart from a known failure. |

## Results & Parameters

### Configuration

```yaml
pool_scope: per-process        # rebuild when os.getpid() changes
pool_creation: on-first-use    # not at import
slot_order: pool-then-slot     # resolve the pool before _inflight += 1
slot_release: done-callback    # a deadline keeps its slot until the thread ends
max_inflight: workers + headroom  # a stuck call keeps its slot
```

### Expected Output

- A parent and a forked child both run pool calls and answer.
- A blocked call holds its slot after its deadline, so the next call fails
  closed with the full-queue error.
- The slot returns after the stuck thread ends, and later calls succeed.
- A regression test that forks after a parent call stays green.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet | New bounded shared-filesystem helper for a single-loop proxy; an existing test forks a child after the parent used the pool | Local: fork reproduction script, new fork unit test, and the previously failing batch-read tests, all green (see [notes](architecture-fork-inherited-executor-ownership.notes.md)) |

## References

- Python `concurrent.futures` documentation: executor threads are not inherited
  across `fork`.
- `os.getpid()` for the process identity check.
- Related: [pytest-async-mock-isolation-patterns](pytest-async-mock-isolation-patterns.md)
  for executor workers that outlive a test.