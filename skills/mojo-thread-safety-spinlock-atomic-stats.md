---
name: mojo-thread-safety-spinlock-atomic-stats
description: "Implement thread-safe data structures in Mojo 0.26.1 using os.atomic.Atomic for spinlocks and atomic counters. Use when: (1) adding concurrency to shared mutable state, (2) protecting free lists or pools for parallelize, (3) needing lock-free atomic counters in Mojo."
category: architecture
date: 2025-03-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - mojo
  - thread-safety
  - atomics
  - spinlock
  - concurrency
  - memory-pool
  - parallelize
---

# Mojo 0.26.1 Thread-Safety with SpinLock and Atomic Counters

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2025-03-25 |
| **Objective** | Add thread-safety to TensorMemoryPool in Mojo 0.26.1 using spinlocks and atomic operations |
| **Outcome** | Successful — per-bucket spinlocks + atomic stats, all 19 tests pass (13 existing + 6 new concurrent) |
| **Verification** | verified-local |

## When to Use

- Adding thread-safety to shared mutable data structures in Mojo 0.26.1
- Protecting free lists, pools, or caches accessed via `parallelize`
- Needing lock-free atomic counters (statistics, reference counts)
- Implementing spinlocks when Mojo stdlib lacks Mutex/Lock primitives
- Working around `Atomic` not being `Movable`/`Copyable` in Mojo 0.26.1

## Verified Workflow

### Quick Reference

```mojo
from os.atomic import Atomic
from memory import UnsafePointer, alloc

# SpinLock: heap-allocated Atomic[DType.int64] via UnsafePointer
struct SpinLock(Copyable, Movable):
    var _state: UnsafePointer[UInt8, origin=MutAnyOrigin]

    fn __init__(out self):
        self._state = alloc[UInt8](8)
        for i in range(8):
            self._state[i] = 0

    fn _as_atomic(self) -> UnsafePointer[Atomic[DType.int64], origin=MutAnyOrigin]:
        return self._state.bitcast[Atomic[DType.int64]]()

    fn lock(self):
        var ptr = self._as_atomic()
        while ptr[].fetch_add(1) != 0:
            _ = ptr[].fetch_sub(1)

    fn unlock(self):
        _ = self._as_atomic()[].fetch_sub(1)

    fn __del__(deinit self):
        self._state.free()

# Atomic counter: heap-allocated, accessed via bitcast
var data = alloc[UInt8](8)
for i in range(8): data[i] = 0
var counter = data.bitcast[Atomic[DType.int64]]()
_ = counter[].fetch_add(1)  # atomic increment
var val = counter[].load()   # atomic read
```

### Detailed Steps

1. **Discover available Atomic API** — Mojo 0.26.1 has `from os.atomic import Atomic` with `fetch_add`, `fetch_sub`, `load`, `max` methods. No `store(value)`, no `compare_exchange_weak`. `Atomic` is NOT `Movable`/`Copyable`.

2. **Work around Atomic not being Movable** — Cannot use `Atomic` as a struct field directly (breaks synthesized `__moveinit__`/`__copyinit__`). Instead, heap-allocate `UInt8` bytes and reinterpret via `bitcast[Atomic[DType.int64]]()`.

3. **Implement SpinLock** — Test-and-set pattern using `fetch_add(1)`: if return is 0, lock acquired; otherwise undo with `fetch_sub(1)` and retry. Lock/unlock use `self` (not `mut self`) because mutations happen through the heap pointer.

4. **Make structs Copyable/Movable** — Since `SpinLock` and `AtomicStats` store `UnsafePointer`, copies are shallow (share the same lock/counters). This is intentional for embedding in `List[SpinLock]`.

5. **Per-bucket locking** — Place locks in the pool struct alongside free lists, not inside `FreeList` itself. This keeps `FreeList` simple and avoids changing its trait conformance.

6. **Minimize critical sections** — Hold lock only during `pop()`/`push()` on free list. Do system `alloc()` and atomic stats updates outside the lock.

7. **Define constants at module level** — `comptime` inside structs crashes `mojo format` (known bug). Use module-level `comptime` constants with a naming prefix (e.g., `_ASTATS_ALLOCATIONS`).

8. **Test with parallelize** — Use `@parameter fn worker(tid: Int) capturing` + `parallelize[worker](N)` for concurrent stress tests. Verify stats consistency after join.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Atomic as struct field | `var value: Atomic[DType.int64]` in a struct | `Atomic` is not `Movable`/`Copyable`, breaks synthesized `__moveinit__` and `__copyinit__` | Must heap-allocate Atomic via `UnsafePointer` and access through `bitcast` |
| `alias` inside struct | `alias _SIZE = 56` inside `AtomicStats` struct | Compiler accepts it as `comptime` but `mojo format` crashes with `'_python_symbols' object has no attribute 'comptime_assert_stmt'` | Move constants to module-level `comptime` with a naming prefix |
| `comptime` inside fn body | `comptime NUM_THREADS = 8` inside test function | Same `mojo format` crash | Use `var` instead of `comptime` inside function bodies |
| `int()` for Int64-to-Int conversion | `s.allocations = int(counter[].load())` | `int` is not a known declaration in Mojo 0.26.1 | Use `Int()` constructor: `Int(counter[].load())` |
| `UnsafePointer[Atomic[...]].alloc(1)` | Tried to allocate directly as `UnsafePointer[Atomic[...]]` | `UnsafePointer` with `Atomic` type fails to infer `mut` parameter | Allocate as `UnsafePointer[UInt8]` via `alloc[UInt8](8)` then `bitcast` to Atomic |
| `store(value)` on Atomic | `counter.store(42)` | `store` requires additional argument or is not available as expected | Use `fetch_add`/`fetch_sub` to set values; for zero-init, just zero the backing bytes |

## Results & Parameters

### Atomic API Available in Mojo 0.26.1

```text
from os.atomic import Atomic

Atomic[DType.int64]:
  - __init__(value: Int)     # constructor
  - fetch_add(n) -> Int64    # atomic add, returns old value
  - fetch_sub(n) -> Int64    # atomic subtract, returns old value
  - load() -> Int64          # atomic read
  - max(n) -> None           # atomic max (sets to max of current and n)

NOT available:
  - store(value)             # must zero-init via backing bytes
  - compare_exchange_weak()  # no CAS
  - Movable/Copyable traits  # cannot embed directly in structs
```

### SpinLock Performance

- Uncontended: near-zero overhead (single atomic fetch_add)
- 8 threads × 5000 iterations: completes in < 1 second
- 8 threads × 300 iterations on single bucket (max contention): passes consistently
- 5 consecutive runs: zero flakes

### Architecture Pattern

```text
TensorMemoryPool
├── small_lists: List[FreeList]     # 5 buckets (64B-1KB)
├── medium_lists: List[FreeList]    # 4 buckets (2KB-16KB)
├── _small_locks: List[SpinLock]    # 1 lock per small bucket
├── _medium_locks: List[SpinLock]   # 1 lock per medium bucket
└── _atomic_stats: AtomicStats      # 7 lock-free atomic counters

Thread-safe operations:
  allocate()   — lock bucket → pop from free list → unlock → update atomic stats
  deallocate() — lock bucket → push to free list → unlock → update atomic stats
  get_stats()  — atomic snapshot (no lock needed)

NOT thread-safe (single-threaded only):
  clear(), reset_stats(), trim()
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | PR #5118 — Thread-safe memory pool (issue #4909) | 19 tests pass: 8 part1 + 5 part2 + 6 concurrent stress tests |
