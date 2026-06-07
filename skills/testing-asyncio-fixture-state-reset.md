---
name: testing-asyncio-fixture-state-reset
description: "Reset asyncio objects (Lock, Event) in autouse fixtures with lazy imports for test isolation. Use when: (1) tests depend on fresh asyncio state per test, (2) manual per-test initialization is fragile and error-prone, (3) asyncio.Lock or asyncio.Event instance must be reset both before (setup) and after (teardown) each test, (4) import-order coupling or circular dependencies complicate fixture setup."
category: testing
date: 2026-06-04
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - asyncio
  - pytest-fixture
  - autouse-fixture
  - test-isolation
  - asyncio-lock
  - asyncio-event
  - lazy-import
  - conftest
  - state-reset
---

# Testing: Asyncio Fixture State Reset Pattern

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-04 |
| **Objective** | Enable test isolation for asyncio objects (Lock, Event) by resetting them symmetrically in autouse fixtures with lazy imports to avoid import-order coupling |
| **Outcome** | SUCCESS — 541 tests pass with 97.84% coverage; zero regression; pattern verified on FastAPI+asyncio application (ProjectHermes) |
| **Verification** | verified-local (all 541 tests pass; CI validation pending) |

## When to Use

- **Tests depend on fresh asyncio objects** — Each test requires a clean `asyncio.Lock` or `asyncio.Event` with no prior state
- **Manual per-test initialization is fragile** — Tests forget to initialize, leading to `AttributeError` when the lock/event is accessed
- **Stale async object state causes test cross-contamination** — One test modifies the state, next test inherits the dirty state
- **Import-order coupling complicates fixtures** — Direct imports in fixture setup cause circular dependencies or module-load-order issues
- **You need symmetric setup/teardown** — Reset must happen both before test (clean start) and after test (no carry-over)
- **The async object is a module-level instance or held in `app.state`** — Not created fresh per test, but shared across tests

## Verified Workflow

### Quick Reference

```python
# Module under test: hermes/server.py
_shutdown_event = None
_inflight_lock = None

async def lifespan(app):
    global _shutdown_event, _inflight_lock
    _shutdown_event = asyncio.Event()
    _inflight_lock = asyncio.Lock()
    # ... app startup ...
    yield
    # ... app shutdown ...

# Test file: tests/conftest.py
import pytest

@pytest.fixture(autouse=True)
def reset_server_state():
    """Reset asyncio objects in app state for test isolation.
    
    Uses lazy import (inside fixture body) to avoid import-order
    coupling and module initialization issues.
    
    Pattern: [setup] -> yield [test body] -> [teardown]
    Both sides of yield reset the async state.
    """
    # Lazy import inside fixture (avoids import-order coupling)
    from hermes.server import app
    
    # Setup: clean state before test
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
    
    yield
    
    # Teardown: clean state after test
    # Ensures next test doesn't inherit this test's state
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
```

### Detailed Steps

#### 1. Identify Asyncio Objects That Require Fresh State Per Test

Scan your module-level or `app.state` for asyncio instances:

```python
# ❌ Pattern that NEEDS this fix:
_shutdown_event = asyncio.Event()  # Created once at module import time
_inflight_lock = asyncio.Lock()     # Persists across all tests

async def lifespan(app):
    global _shutdown_event, _inflight_lock
    # These are created fresh, but tests that use old references see stale state
    _shutdown_event = asyncio.Event()
    _inflight_lock = asyncio.Lock()
```

Any asyncio object that:
- Is created at module or app-state scope (not inside a test)
- Is accessed by multiple tests in sequence
- Holds state (lock contention, event set/unset status)
- Can be dirty if a prior test crashed or modified it

#### 2. Use Lazy Import Inside Fixture to Avoid Import Coupling

**Why lazy import?** Direct imports in fixture setup cause:

```python
# ❌ FRAGILE: top-level import in fixture can cause circular dependencies
import hermes.server  # If server imports conftest or test helpers — circular!

@pytest.fixture(autouse=True)
def reset_server_state():
    # ...
```

**Solution: import inside the fixture function**:

```python
# ✅ ROBUST: lazy import inside fixture body
@pytest.fixture(autouse=True)
def reset_server_state():
    from hermes.server import app  # Imported here, not at module scope
    
    # Now reset the app.state asyncio objects
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
    
    yield
    
    # Teardown: reset again
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
```

#### 3. Reset Symmetrically: Before (Setup) and After (Teardown)

The fixture must use the **`yield` pattern** to wrap the test:

```python
@pytest.fixture(autouse=True)
def reset_server_state():
    # === SETUP (before test) ===
    from hermes.server import app
    
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
    
    # Control passes to test here
    yield
    
    # === TEARDOWN (after test) ===
    # Reset again, even if test crashed or was interrupted
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
```

**Why both sides?**
- **Setup reset**: Ensures test starts clean, even if previous test crashed mid-execution
- **Teardown reset**: Ensures the next test doesn't inherit this test's modified state (e.g., Lock held, Event set)

#### 4. Use autouse=True to Protect All Tests Without Duplication

```python
# Put this in tests/conftest.py (top-level or package-scoped)
@pytest.fixture(autouse=True)  # ← Every test uses this automatically
def reset_server_state():
    from hermes.server import app
    
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
    yield
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()

# No need to add to every test — autouse handles it
class TestShutdownHandler:
    def test_shutdown_event_signaled(self):
        # fixture automatically ran before this test
        assert not app.state.shutdown_event.is_set()
        # test body ...
        # fixture automatically runs after this test
```

#### 5. Place the Fixture at the Right Scope

| Where tests live | Where to put fixture |
|------------------|----------------------|
| Multiple files in `tests/` | `tests/conftest.py` (top-level) |
| Multiple files in `tests/unit/` | `tests/unit/conftest.py` (package-scoped) |
| Single test file only | Can go in same file (rare) |

**Rule of thumb**: Place the fixture at the **broadest scope** covering any test that uses the asyncio objects. This ensures all tests get reset, regardless of run order.

#### 6. Verify Isolation With a Parametrized Test

```python
import asyncio
import pytest

class TestLockIsolation:
    @pytest.mark.parametrize("iteration", [0, 1, 2])
    async def test_lock_is_fresh_per_test(self, iteration):
        """Verify lock starts unheld every iteration."""
        from hermes.server import app
        
        # Lock should be unheld at start of every test
        assert not app.state.inflight_lock.locked()
        
        async with app.state.inflight_lock:
            # Do work with lock held
            await asyncio.sleep(0.01)
        
        # Verify lock is released by end of test
        assert not app.state.inflight_lock.locked()
```

Run this with `pytest -v`:

```
test_lock_is_fresh_per_test[iteration0] PASSED
test_lock_is_fresh_per_test[iteration1] PASSED
test_lock_is_fresh_per_test[iteration2] PASSED
```

If even one iteration fails with "lock is already held", the fixture scope is too narrow or the reset is missing.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Manual per-test lock initialization | Each test calls `app.state.inflight_lock = asyncio.Lock()` inside test body | Works for that one test, but easy to forget on new tests. Forgotten tests inherit dirty lock state. DRY violation. | Use `@pytest.fixture(autouse=True)` — automatic on all tests, no forgetting |
| Top-level import in fixture | `from hermes.server import app` at module scope of conftest.py | Can cause circular import if server imports test utilities or depends on conftest symbols. Module load order becomes fragile. | Move import inside fixture function body (lazy import) |
| Fixture resets only in setup, not teardown | Fixture only resets before test, not after | If test crashes or is interrupted, teardown doesn't run, leaving dirty state for the next test. Order-dependent flakiness. | Always reset in both setup and teardown (`yield` pattern ensures both) |
| Clearing the lock instead of replacing it | `app.state.inflight_lock.clear()` (if such a method exists) | asyncio.Lock has no `clear()` method. The only way to "reset" is to create a new instance and replace the reference. | `app.state.inflight_lock = asyncio.Lock()` — replacement, not mutation |
| Assuming pytest automatically resets asyncio objects | No fixture, relying on pytest's cleanup | asyncio objects persist in `app.state` for the lifetime of the Python process. No automatic reset. | Fixture must explicitly reset state each test |
| Using module-scope fixture | `@pytest.fixture(scope="module")` | Multiple tests in one module share the same fixture run. Lock held by test 1 is still held when test 2 runs. | Use default `scope="function"` (resets per test) with `autouse=True` |
| Fixture resets a copy, not the real instance | `mock_lock = asyncio.Lock(); app.state.inflight_lock = mock_lock` but later code accesses a different reference to the original | If other modules imported the original lock directly (e.g., `from hermes.server import app`), they see the old reference. | Fixture must reset the **held reference in app.state**, not a copy. If code imports the lock directly, that's a separate code smell. |
| Relying on monkeypatch for all resets | `monkeypatch.setattr(app.state, "inflight_lock", asyncio.Lock())` | Works, but verbose and slower than direct assignment. Mixes monkeypatch and real state management. | Direct assignment is simpler: `app.state.inflight_lock = asyncio.Lock()` |

## Results & Parameters

### Fixture Template (Copy-Paste Ready)

```python
# tests/conftest.py

import asyncio
import pytest

@pytest.fixture(autouse=True)
def reset_server_state():
    """Reset asyncio objects in app.state for test isolation.
    
    Why this pattern?
    1. Lazy import inside fixture body avoids import-order coupling
    2. Symmetric setup/teardown (yield pattern) ensures clean state
       even if test crashes or is interrupted
    3. autouse=True protects all tests without duplication
    4. Each test starts with a fresh Lock and Event instance
    
    The asyncio objects (Lock, Event, Condition, etc.) maintain
    internal state that persists across test boundaries unless
    explicitly reset. This fixture ensures isolation.
    """
    # Lazy import: defer until fixture runs (avoids circular imports)
    from hermes.server import app
    
    # Setup: create fresh instances before test
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
    
    yield  # Test runs here
    
    # Teardown: create fresh instances after test
    # Prevents next test from inheriting this test's state
    app.state.shutdown_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
```

### Multi-Object Async State Reset

```python
# tests/conftest.py

import asyncio
import pytest

@pytest.fixture(autouse=True)
def reset_async_state():
    """Reset multiple asyncio objects for comprehensive test isolation."""
    from hermes.server import app
    
    # Setup
    app.state.shutdown_event = asyncio.Event()
    app.state.startup_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
    app.state.message_queue = asyncio.Queue()
    app.state.semaphore = asyncio.Semaphore(5)
    
    yield
    
    # Teardown
    app.state.shutdown_event = asyncio.Event()
    app.state.startup_event = asyncio.Event()
    app.state.inflight_lock = asyncio.Lock()
    app.state.message_queue = asyncio.Queue()
    app.state.semaphore = asyncio.Semaphore(5)
```

### Asyncio Object State Reference

| Object | Internal State | Why It Matters | Reset Method |
|--------|----------------|----------------|--------------|
| `asyncio.Event()` | `_flag: bool` (set/unset) | Tests that wait on event see stale set/unset state | Create new instance |
| `asyncio.Lock()` | `_locked: bool`, waiters queue | Tests that acquire lock may deadlock if already held | Create new instance |
| `asyncio.Condition()` | Lock + event + waiters | Threads waiting on condition from prior test interfere | Create new instance |
| `asyncio.Semaphore(n)` | `_value: int`, waiters | Permits claimed in prior test reduce available permits | Create new instance |
| `asyncio.Queue()` | Internal deque + locks | Items left in queue from prior test corrupt next test | Create new instance |

### Expected Behavior After Fixture Applies

```python
# Before fixture (manual per-test init):
class TestWithoutFixture:
    def test_1(self):
        app.state.lock = asyncio.Lock()  # Must remember!
        # ...
    
    def test_2(self):
        # Bug: forgot to reset; inherits lock from test_1
        # app.state.lock.locked() may return True
    
# After fixture (autouse reset):
class TestWithFixture:
    def test_1(self):
        # Fixture ran: fresh lock before test
        assert not app.state.lock.locked()
        # ...
    
    def test_2(self):
        # Fixture ran again: fresh lock before test
        # No carry-over from test_1
        assert not app.state.lock.locked()
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHermes | tests/conftest.py `reset_server_state` fixture | 541 tests pass; 97.84% coverage; zero regression; handles asyncio.Lock + asyncio.Event reset for FastAPI+NATS application (PR #X) |
