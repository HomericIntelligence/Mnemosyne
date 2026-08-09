---
name: testing-deterministic-clock-vs-thread-sleep-classification
description: "Eliminate scheduler-sensitive timing assertions from tests by classifying what a wait proves. Mock the exact production clock for timer boundaries, use synchronization primitives for thread ordering, and patch sleep to raise when a branch must never wait. Use when: (1) tests measure elapsed time to prove a fast or disabled path, (2) time.sleep appears near timeout logic, (3) threads rely on scheduler delays, (4) a token bucket or backoff path should return without sleeping."
category: testing
date: 2026-08-05
version: "2.1.0"
history: testing-deterministic-clock-vs-thread-sleep-classification.history
user-invocable: false
verification: verified-local
tags:
  - time-sleep
  - monotonic
  - mock-clock
  - threading-event
  - condition-wait-instrumentation
  - deterministic-test
  - circuit-breaker
  - recovery-timeout
  - thread-coordination
  - happens-before
  - flaky
  - yagni
  - dry
  - kiss
  - ruff-unused-import
  - mock-sleep
  - no-wait
  - token-bucket
  - state-transition
---

# Deterministic Clock vs Thread-Sleep: Classify Before You Fix

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Remove scheduler-sensitive timing assertions and real sleeps from unit tests without changing production APIs or weakening concurrency coverage. |
| **Outcome** | Successful and verified locally across three patterns: mocked clocks for timer boundaries, deterministic events for thread ordering, and raising sleep mocks plus exact state assertions for branches that must not wait. |
| **Verification** | verified-local — prior circuit-breaker/status-tracker suites passed locally; the rate-limit amendment passed 2 focused tests, all 7 throttle tests, and all 75 rate-limit tests with `--no-cov`. CI remains pending. |

## When to Use

- A refactor/issue asks to remove real `time.sleep()` from unit tests for speed or determinism.
- You see `time.sleep(...)` immediately before an assertion about a timeout having elapsed (circuit-breaker `recovery_timeout`, backoff windows, TTL expiry).
- You see `time.sleep(...)` near `threading.Barrier`/`Condition`/`Event` with comments like "give threads time to start waiting" or "release after delay".
- You are tempted to add a `clock`/`time_source` constructor parameter to production code that already calls `time.monotonic()` directly at module scope.
- You are tempted to mark a thread-coordination test `@pytest.mark.slow` instead of making it deterministic.
- A fast, disabled, or full-capacity branch uses elapsed-time ceilings such as
  `assert elapsed < 0.05` to claim that no wait occurred.
- A token bucket, backoff, or retry test must prove both the absence of sleeping and the
  exact state transition performed before returning.

## Verified Workflow

### Quick Reference

```python
# CLASS 1 — Timer-boundary sleep: patch the EXACT clock the production code reads.
# First confirm the source: grep for the clock call in the module under test.
#   grep -n "time.monotonic\|time.time" hephaestus/resilience/circuit_breaker.py
# Then patch that exact attribute path (the name in the MODULE UNDER TEST, not `time`).
# CRITICAL ORDERING: production _record_failure stamps _last_failure_time = time.monotonic()
# AT FAILURE TIME, so advance the clock AFTER the failing call returns, NOT at construction.
import unittest.mock as mock

@mock.patch("hephaestus.resilience.circuit_breaker.time.monotonic")
def test_recovers_after_timeout(self, mono):
    mono.return_value = 1000.0          # baseline read while tripping the breaker
    cb = CircuitBreaker(recovery_timeout=30.0)   # use a NON-tiny timeout
    # ... trip the breaker: _record_failure() now stamps _last_failure_time = 1000.0 ...
    mono.return_value = 1030.0          # advance PAST the boundary AFTER the failing call
    assert cb.allow()                    # half-open transition, no real sleep

# CLASS 2 — Thread-coordination sleep: NO clock to mock. Make it DETERMINISTIC, not slow.
# Instrument condition.wait to fire an Event from inside the lock right before parking,
# so the releaser provably cannot run until the main thread is parked in wait().
import threading

def test_release_unblocks_waiter(self):
    waiting = threading.Event()
    real_wait = tracker.condition.wait

    def wait_announcing(timeout=None):
        waiting.set()                    # fires while still holding the condition lock
        return real_wait(timeout=timeout)

    tracker.condition.wait = wait_announcing  # type: ignore[method-assign]

    def release_when_waiting():
        assert waiting.wait(timeout=5.0)  # safety net only, never the happy path
        tracker.release_slot(slot_id)     # contends for the SAME lock -> happens-after

    # ... start release_when_waiting in a thread, then acquire the (full) slot ...
```

```python
# CLASS 3 — No-wait branch: make ANY attempted sleep fail immediately and assert
# exact boundary calls plus externally visible state. Patch the names read by the SUT.
from unittest.mock import patch

with (
    patch("package.rate_limit.time.monotonic", return_value=1_000.0) as clock,
    patch(
        "package.rate_limit.time.sleep",
        side_effect=AssertionError("full bucket must not sleep"),
    ) as sleep,
):
    acquire()

clock.assert_called_once_with()
sleep.assert_not_called()
assert load_state() == {"tokens": 9.0, "updated": 1_000.0}

# In a separate disabled/early-return test, neither boundary nor persistence is touched.
with (
    patch("package.rate_limit.time.monotonic") as disabled_clock,
    patch(
        "package.rate_limit.time.sleep",
        side_effect=AssertionError("disabled path must not sleep"),
    ) as disabled_sleep,
):
    acquire_disabled()

disabled_clock.assert_not_called()
disabled_sleep.assert_not_called()
assert not state_path.exists()
```

```bash
# Housekeeping after edits:
#  - removing the last time.sleep -> `import time` is now unused -> ruff F401, delete it
#  - making thread tests deterministic -> remove @pytest.mark.slow AND the now-unused
#    `import pytest` if it was only used for the marker
ruff check tests/unit/resilience/test_circuit_breaker.py tests/unit/automation/test_status_tracker.py
# Re-grep rather than trusting cited line numbers — they drift between reads:
grep -rn "time.sleep" tests/unit/
```

### Detailed Steps

1. **Inventory every `time.sleep` by re-grepping** (`grep -rn "time.sleep" tests/`). Do
   NOT trust line numbers from a prior read — they drift.
2. **Classify each sleep** as either **timer-boundary** (waits only for a clock to cross a
   threshold) or **thread-coordination** (orders real OS threads against a sync primitive).
   This classification, not the call site, drives the fix.
3. **For timer-boundary sleeps**: confirm the production clock source first
   (`grep -n "time.monotonic\|time.time" <module>.py`). Patch THAT exact name with
   `@patch("<module_under_test>.time.monotonic")`. `@patch` targets the name in the module
   under test, not the global `time` module. Seed the baseline value, then advance
   `return_value` past the threshold.
4. **Respect the failure-time stamp ordering (the #1 bug here).** Production
   `_record_failure` writes `_last_failure_time = time.monotonic()` at the moment of
   failure. So set the post-timeout advance AFTER the failing call returns — advancing the
   clock before/at construction corrupts the baseline and the boundary math is wrong.
5. **Pick a non-tiny timeout** (e.g. `30.0`) and large explicit advances so the boundary
   crossing is unambiguous, replacing the original sub-second values.
6. **For a branch that must not wait**, patch the production module's `time.sleep` with an
   exception-raising `side_effect`. `assert_not_called()` documents intent, while the
   exception makes an unexpected wait fail at the call boundary rather than block or rely on
   scheduler speed. Patch `time.monotonic` too: assert zero reads for an early return, or freeze
   it and assert the exact read count for a stateful immediate-return transition.
7. **Assert the semantic transition, not just “fast.”** A disabled path should create no state
   file. An initially full token bucket should consume exactly one token and persist the frozen
   timestamp, while retaining directory/file permissions. This separates “returned quickly”
   from “executed the correct branch.”
8. **For thread-coordination sleeps**: do NOT clock-mock — there is no clock. Do NOT mark
   them `@pytest.mark.slow` either (see Failed Attempts — a reviewer rejected this). Make
   the happens-before **deterministic** by instrumenting the synchronization primitive:
   wrap `tracker.condition.wait` so it sets a `threading.Event` from INSIDE the lock,
   immediately before parking. The releaser then `event.wait(timeout=5.0)`s on that Event
   before acting. Because the releaser contends for the SAME condition lock, it cannot
   proceed until the main thread atomically releases the lock by entering `wait()`. The
   5.0s timeout is a safety net only; the happy path has zero wall-clock dependence.
9. **For pure-contention "simulate work" sleeps** (e.g. `time.sleep(0.01)` inside a worker
   that the test only checks "eventually acquired/released"): just DELETE the sleep. The
   assertions (all N threads acquired, all slots released) need no artificial delay;
   removing it keeps the contention test valid and fast.
10. **A clock-mocked test that still spawns real threads** (concurrency assertions with
   `threading.Barrier`) keeps the thread machinery; only the timer-boundary sleep inside
   it is mocked. This is SAFE because a `MagicMock.return_value` is a frozen, lock-free,
   thread-shared read AND those tests assert on state/counters/peak-concurrency, never on
   elapsed/ETA time. Advance the frozen clock BEFORE spawning threads.
11. **Fix imports last**: after removing the last `time.sleep`, `import time` is unused
   (ruff F401) — delete it. After removing `@pytest.mark.slow`, delete a now-unused
   `import pytest`.
12. **Run the full targeted suite multiple times** to confirm determinism (flakiness only
    shows up intermittently). Here: 23 status_tracker + 35 circuit_breaker tests green
    across 3 runs.

### If you DO end up marking tests slow (coverage gate check)

If a thread test genuinely cannot be made deterministic and you fall back to
`@pytest.mark.slow`, verify the module under test still clears the coverage gate on the
fast path: `pytest -m "not slow" --cov=<module>`. In issue #1469 `status_tracker.py` held
91.76% even with the candidate tests deselected — but the deterministic Event fix made the
marker (and this check) unnecessary, which is the preferred outcome.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Elapsed-time upper bound for a no-wait branch | Timed the call with real `time.monotonic()` and asserted completion under 50 or 100 ms | Ambient load and scheduler delays can fail a correct implementation, while an unintended short sleep can still pass | Patch `sleep` to raise immediately; assert clock calls and semantic state instead of wall-clock duration |
| `@pytest.mark.slow` for thread-coordination sleeps | Quarantined the thread tests behind the `slow` marker so the fast CI path deselects them (the v1.x recommendation) | A reviewer REJECTED it: deselecting removes the wait/notify code under test from the default fast suite (less coverage of exactly that logic) AND leaves the underlying flakiness intact, just hidden | Thread-coordination sleeps must be made DETERMINISTIC (instrument `condition.wait` to fire an Event before parking), not quarantined |
| Constructor-injected clock | Considered adding a `clock`/`time_source` parameter to production code so tests pass a fake clock | YAGNI: the production code already calls `time.monotonic()` at module scope, so a `@patch` of that name is sufficient and changes no production API | When the code already reads a module-level clock, mock the name (KISS) — don't widen the constructor surface just for testing |
| `@patch("time.monotonic")` (global) | Patching the global `time` module instead of the name imported in the module under test | `@patch` resolves the attribute on the target object; the SUT reads `circuit_breaker.time.monotonic`, so the global patch may not intercept the call the SUT actually makes | Patch the EXACT attribute path the module under test reads, confirmed by grepping the source first |
| Remove thread-coordination sleeps via mocked clock | Treating "give threads time to start waiting" sleeps the same as timeout sleeps and trying to mock them away | There is no clock involved — the wait is on the OS scheduler; removing the sleep with no replacement creates a notify-before-wait race | Thread-ordering sleeps are a different class; instrument the sync primitive for a deterministic happens-before |
| Advance the mocked clock at construction time | Set `monotonic.return_value` past the boundary before tripping the breaker | `_record_failure` stamps `_last_failure_time = time.monotonic()` at FAILURE time, so a pre-set advance corrupts the baseline — the boundary delta is then wrong | Advance the clock AFTER the failing call returns; the baseline is the value LIVE when `_record_failure` runs, not at construction |
| Single fixed mock value across the whole `call()` path | Setting one constant `monotonic.return_value` and assuming all reads are equivalent | The mocked value is read multiple times within one `call()` (`_effective_state` AND the `time_until` ETA); a value that makes the boundary cross can make an ETA assertion read `0.0`/negative | When the same mocked clock feeds an ETA assertion (`time_until_recovery > 0`), choose the value so `recovery_timeout - elapsed > 0` still holds |
| Keep "simulate work" `time.sleep(0.01)` in a contention test | Left an artificial work delay inside worker threads of a pure contention test | The test only asserts all threads eventually acquired and all slots released — the delay adds wall-clock time and flakiness for no assertion benefit | Pure-contention tests need no artificial work delay; just delete the sleep |
| Trusting cited line numbers | Planning edits against offsets from a single read | Line numbers drift between reads as files change | Re-grep `time.sleep` and the markers at implementation time; never trust a prior read's offsets |

## Results & Parameters

**Two-class decision rule (the core durable insight):**

| Class | What the sleep waits on | Correct fix | Anti-pattern |
|-------|-------------------------|-------------|--------------|
| Timer-boundary | A monotonic/wall clock crossing a timeout threshold (`recovery_timeout`) | `@patch("<module>.time.monotonic")`, advance `return_value` past the threshold AFTER the failing call | Constructor-injected clock (YAGNI); patching global `time`; advancing at construction |
| No-wait branch | Nothing: sleeping is forbidden, and the branch should return immediately | Patch the SUT's `time.sleep` with a raising `side_effect`; assert no call, exact clock reads, and resulting state | Measuring an elapsed-time ceiling, which tests the scheduler more than the branch contract |
| Thread-coordination | Real OS threads ordered against `threading.Condition`/`Event`/`Barrier` | Instrument the sync primitive (set an `Event` from inside `condition.wait` before parking) for a deterministic happens-before | `@pytest.mark.slow` (hides flakiness, drops coverage — reviewer-rejected); mocking a clock that does not exist |
| Pure-contention "simulate work" | Nothing semantic — just adds delay so threads overlap | DELETE the sleep; assertions are "eventually acquired/released" | Keeping the delay (slow + flaky for no assertion benefit) |

**The deterministic thread-coordination technique (the key technique that converged the review):**

```python
# Instead of time.sleep(0.1) to "give threads time to start waiting":
waiting = threading.Event()
real_wait = tracker.condition.wait

def wait_announcing(timeout=None):
    waiting.set()                       # set INSIDE the lock, right before parking
    return real_wait(timeout=timeout)

tracker.condition.wait = wait_announcing  # type: ignore[method-assign]

def release_when_waiting():
    assert waiting.wait(timeout=5.0)    # generous safety net, never the happy path
    tracker.release_slot(slot_id)       # contends for the SAME lock -> provably happens-after
```

Why it is race-free: `release_slot` contends for the same `condition` lock the main thread
holds, so it cannot proceed until the main thread atomically releases that lock by entering
`wait()`. The `Event` makes the parked state observable; the lock makes the ordering
enforced. Wall-clock independence with a timeout only as a backstop.

**Mocked-clock-across-threads safety reasoning:** when a circuit-breaker concurrency test
spawns real worker threads that read the patched `time.monotonic`, a `MagicMock.return_value`
is a frozen, lock-free, thread-shared read — SAFE precisely because those tests assert on
state/counters/peak-concurrency, never on elapsed/ETA time. Advance the frozen clock BEFORE
spawning threads.

**No-wait token-bucket pattern:**

```python
with (
    patch("package.rate_limit.time.monotonic", return_value=now) as clock,
    patch(
        "package.rate_limit.time.sleep",
        side_effect=AssertionError("full token bucket must not sleep"),
    ) as sleep,
):
    acquire()

clock.assert_called_once_with()
sleep.assert_not_called()
assert json.loads(state_path.read_text(encoding="utf-8")) == {
    "tokens": burst - 1.0,
    "updated": now,
}
```

For a disabled early return, use the same raising sleep mock but assert both clock and sleep
were never called and the state file was never created. A raising `side_effect` and
`assert_not_called()` are intentionally redundant: one fails immediately if execution reaches
the forbidden boundary; the other states the expected interaction in the test contract.

**Verified numbers (issue #1469, local):**

- `tests/unit/resilience/test_circuit_breaker.py`: 13 timer-boundary sleeps removed; 35 tests green ×3 runs.
- `tests/unit/automation/test_status_tracker.py`: 6 thread-coordination sleeps across 5 methods removed; 23 tests green ×3 runs.
- ruff clean; `import time` / `import pytest` removed where they became unused.
- `tests/unit/github/test_rate_limit.py`: proposed no-wait patch passed 2 focused tests, all
  7 `TestGlobalThrottle` tests, and all 75 module tests locally with `--no-cov`. The unmodified
  global coverage gate makes narrow selections exit nonzero despite passing assertions, so CI
  and the full coverage suite remain pending.

**Source-of-truth anchors (re-verify before editing):**

- Production clock source: `hephaestus/resilience/circuit_breaker.py` calls `time.monotonic()` at module scope — patch `hephaestus.resilience.circuit_breaker.time.monotonic`.
- `_record_failure` stamps `_last_failure_time = time.monotonic()` at failure time — advance the mock AFTER the failing call.
- ETA computation reuses the same clock — keep `recovery_timeout - elapsed > 0` for any `time_until_recovery > 0` assertion.
- Status tracker uses a `threading.Condition`; instrument `tracker.condition.wait` to announce parking via an `Event`.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1469 / PR #1725 — replaced real `time.sleep()` in `tests/unit/resilience/test_circuit_breaker.py` (mocked clock) and `tests/unit/automation/test_status_tracker.py` (deterministic Event coordination); 58 tests green ×3 runs locally, CI pending | No notes file |
| ProjectHephaestus | Rate-limit throttle test amendment validated in an isolated worktree at `446b0fea`; 2 focused, 7 throttle, and 75 module tests passed with `--no-cov`; CI pending | No notes file |
