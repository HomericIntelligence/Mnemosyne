---
name: pytest-asyncio-hang-and-mock-hazards
description: "Diagnosing and fixing pytest tests that hang or produce false results due to asyncio event loops, sleep mocks, and coroutine patching. Use when: (1) pytest CI step times out without reporting a test failure — hang signature, (2) async daemon tests block in epoll.poll(-1) and pytest-timeout does not interrupt them, (3) a coroutine internally reassigns a global asyncio.Event making pre-set fixtures ineffective, (4) patch('module.time.sleep') causes OOM via runaway retry loops, (5) FastAPI Depends() ignores a patched get_settings because the function reference was captured at import time, (6) a code-quality bot flags `await <asyncio.Task>` as a no-effect statement."
category: testing
date: 2026-06-02
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: pytest-asyncio-hang-and-mock-hazards.history
tags:
  - asyncio
  - pytest
  - hang
  - timeout
  - epoll
  - AsyncMock
  - coroutine
  - patch
  - time-sleep
  - oom
  - fastapi
  - pydantic-settings
  - event-loop
  - python
  - pytest-timeout
  - false-positive
  - unmocked-blocking-call
  - subprocess-hang
  - baseline-duration-diagnosis
  - faulthandler
---

# Pytest Asyncio Hang and Mock Hazards

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-19 |
| **Objective** | Consolidate recurring asyncio/pytest pitfalls: event-loop hangs, sleep-mock OOM, FastAPI DI isolation, and bot false positives |
| **Outcome** | SUCCESS — seven skills merged; patterns verified across ProjectKeystone, ProjectHephaestus, ProjectScylla, ProjectHermes |
| **Verification** | verified-ci (members individually verified) |

## When to Use

1. **CI job times out (no test failure output)** — tests hang in `epoll.poll(-1)` because an asyncio event never fires
2. **`pytest-timeout` fires but the test keeps running** — default signal method cannot interrupt a blocked C-level syscall
3. **Coroutine reassigns a global `asyncio.Event` internally** — pre-setting the module variable is silently overwritten
4. **`patch("module.time.sleep")` causes OOM or runaway loops** — the patch leaks to all callers in the process
5. **`patch("app.get_settings", return_value=mock)` has no effect** — `Depends()` captured the original function at import time
6. **Bot flags `await <asyncio.Task>` as "Statement has no effect"** — static analyser false positive; do not remove the `await`
7. **Wall-clock timing assertions are flaky** — replace with deterministic `time.sleep` mock assertions
8. **A newly-added blocking call hangs the FULL suite but not the module's own tests** — a sibling `run()`-level test reaches the new call without mocking it; root-cause by baseline-duration comparison + faulthandler

## Verified Workflow

### Quick Reference

```python
# --- Pattern A: Patch the COROUTINE FUNCTION, not its internals ---
from unittest.mock import AsyncMock, patch

@patch("mymodule.daemon.run", new_callable=AsyncMock, return_value=0)
def test_main_starts(mock_run, caplog):
    result = main(["--log-level", "INFO"])
    assert result == 0
    mock_run.assert_called_once()

# For signal handlers: asyncio.run() registers SIGINT internally — use assert_any_call
mock_signal.assert_any_call(signal.SIGTERM, ANY)


# --- Pattern B: Patch asyncio.Event CONSTRUCTOR when coroutine reassigns the global ---
mock_event = asyncio.Event()
mock_event.set()  # pre-set so wait() returns immediately

with patch("mymodule.daemon.asyncio.Event", return_value=mock_event):
    result = await mymodule.daemon.run(settings)


# --- Pattern C: pytest-timeout thread method (pyproject.toml) ---
# [tool.pytest.ini_options]
# addopts = "--timeout=30 --timeout-method=thread"


# --- Pattern D: Patch the wait HELPER, not time.sleep ---
with patch("mymodule.wait_until") as mock_wait:
    _call_that_retries(max_retries=2)
mock_wait.assert_called_once()

# If you must patch time.sleep, use a deterministic mock assertion:
with patch("mymodule.retry.time.sleep") as mock_sleep:
    result = decorated()
mock_sleep.assert_any_call(0.1)
mock_sleep.assert_any_call(0.2)

# Add a defensive iteration cap to any production while-True loop:
iterations = 0
while True:
    time.sleep(1)
    iterations += 1
    if iterations >= 100_000:
        logger.warning("iteration cap reached; bailing out")
        return


# --- Pattern E: FastAPI / pydantic-settings isolation ---
import os
from contextlib import contextmanager
from fastapi.testclient import TestClient

@contextmanager
def _settings_client(overrides: dict):
    from myapp.server import app
    from myapp.config import get_settings

    old_env = {k: os.environ.get(k) for k in overrides}
    os.environ.update(overrides)
    get_settings.cache_clear()
    try:
        yield TestClient(app)
    finally:
        get_settings.cache_clear()
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

# SlowAPIMiddleware MUST be registered for rate-limit enforcement:
app.add_middleware(SlowAPIMiddleware)

# Use AsyncMock side_effect directly — do NOT patch asyncio.wait_for:
mock_js.publish = AsyncMock(side_effect=asyncio.TimeoutError())


# --- Pattern F: Bot false positive — do NOT remove await on asyncio.Task ---
advance_task = asyncio.get_event_loop().create_task(some_coroutine())
# ... assertions ...
await advance_task   # correct cleanup; bot "Statement has no effect" is a false positive
```

### Detailed Steps

#### A — Patch the Coroutine Function Itself

1. **Trace the actual call chain from `main()`** — determine which function is directly invoked by `asyncio.run()`:

   ```python
   return asyncio.run(run(settings))   # run() is the coroutine to patch
   ```

2. **Patch `run` with `AsyncMock`**, not internal helpers that `main()` never calls directly:

   ```python
   # BEFORE (no-op — main() never calls run_routing_loop):
   @patch("mymodule.daemon.run_routing_loop", return_value=None)

   # AFTER (correct — asyncio.run() still executes but receives the fast AsyncMock):
   @patch("mymodule.daemon.run", new_callable=AsyncMock, return_value=0)
   ```

3. **Audit log assertions** — remove assertions for logs emitted inside the mocked coroutine.

4. **Switch `assert_called_once_with` to `assert_any_call`** on `signal.signal` — `asyncio.runners.Runner` registers SIGINT internally, making the total count 2.

#### B — Patch asyncio.Event Constructor for Internal Reassignment

1. **Identify the reassignment inside the coroutine**:

   ```python
   global _shutdown_event
   _shutdown_event = asyncio.Event()   # new unset event every call
   await _shutdown_event.wait()        # hangs in test context
   ```

2. **Pre-setting the module variable is ineffective** — the coroutine overwrites it immediately.

3. **Patch the constructor in the module's namespace**:

   ```python
   mock_event = asyncio.Event()
   mock_event.set()
   with patch("mymodule.daemon.asyncio.Event", return_value=mock_event):
       result = await mymodule.daemon.run(settings)
   ```

4. **Diagnose via timeout stack trace** — `epoll.poll(timeout=-1)` at the bottom confirms the event loop is blocked on an unset Event.

#### C — Fix pytest-timeout Not Interrupting Epoll

The default `--timeout-method=signal` delivers SIGALRM to the Python handler only when the blocked `epoll.poll(-1)` syscall returns — which never happens with no file descriptor events. The thread method uses `thread.interrupt_main()`, which delivers a `KeyboardInterrupt` into the main thread even while inside a C-level syscall.

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--timeout=30 --timeout-method=thread"

[project.optional-dependencies]
dev = [
    "pytest-timeout>=2.3,<3",
]
```

Both flags **must be set together** — `--timeout=30` alone still uses signal method.

#### D — time.sleep Mock Hazard and Flaky Timing Tests

`patch("module.time.sleep")` replaces the `sleep` attribute on the **shared singleton `time` module object** — neutralising `time.sleep` for every caller in the process. If any background loop contains `while True: time.sleep(N)`, it spins at full CPU and can OOM the host.

Safe alternatives:

1. Patch the dedicated wait helper (`wait_until`, `poll_for`, etc.) instead of `time.sleep`.
2. Patch probe functions at their **source namespace** (where defined), not via re-export.
3. If mocking `time.sleep` directly, patch at the module's import path: `"mymodule.retry.time.sleep"` (not `"time.sleep"`).
4. Add a defensive iteration cap to any `while True: time.sleep(N)` loop in production code.
5. Replace wall-clock `assert elapsed >= N` assertions with mock call assertions (`mock_sleep.assert_any_call(N)`).

```bash
# Diagnose OOM test: high CPU + low I/O + growing captured-stdout buffer
python -X tracemalloc=10 -m pytest tests/unit/test_suspect.py -v
```

#### E — FastAPI / pydantic-settings Test Isolation

`Depends(get_settings)` captures the **function object** at import time. Patching the module-level name has no effect on what FastAPI's DI calls. Instead:

1. **Set env vars** so the real `get_settings` returns the desired values.
2. **Call `get_settings.cache_clear()`** before and after the test (required when decorated with `@lru_cache`).
3. **Register `SlowAPIMiddleware`** on the app — `@limiter.limit()` alone does not enforce limits.
4. **Use `AsyncMock(side_effect=asyncio.TimeoutError())`** instead of patching `asyncio.wait_for`.

#### F — Bot False Positive: `await asyncio.Task`

`await <asyncio.Task>` is required cleanup: it blocks until the task completes, propagates exceptions, and prevents `RuntimeWarning: Task was destroyed but it is pending!`. The GitHub code-quality bot incorrectly models `await expr` as a bare expression statement. No code change is needed — dismiss the bot comment.

#### G — Newly-Added Blocking Call Hangs the Full Suite (Unmocked-Wait Hang)

This is the **non-async sibling** of the epoll hang: same CI symptom (job stuck, no test-failure output), different root cause. You add a new method that loops over a **real `subprocess` call + real `time.sleep`** bounded by a long env timeout, wire it into a hot code path, and the module's *own* targeted tests still pass (they mock the new method) — but a **sibling test in the same directory** drives the changed code path without mocking the new call, so the worker blocks on the real wait for the full timeout.

**Worked example.** A new `_wait_for_pr_terminal` loops calling `gh pr view` plus `time.sleep(min(2**n, 60))` bounded by an 1800 s env timeout, wired into the green/auto-merge-armed branch of `_drive_issue`. `test_ci_driver.py` passed in isolation (it mocked `_wait_for_pr_terminal`, and `gh` returned fast locally). But the full CI unit job (`pytest tests/unit`) hung for ~16 min vs a ~4 min baseline. Cause: two `run()`-level tests — `TestRunCleanup::test_cleanup_all_called_on_success` and `test_preserved_worktrees_are_logged` — drove `CIDriver.run()` to a green, auto-merge-armed PR with `_enable_auto_merge` mocked `True` but **did not patch `_wait_for_pr_terminal`**, so the worker blocked on the real `gh pr view` + real `time.sleep`.

**Diagnosis technique (reusable):**

1. **Compare elapsed time to the baseline of the same job on main** — variance is not 4×:

   ```bash
   gh run list --workflow=ci.yml --branch=main --json createdAt,updatedAt \
     --jq '.[] | ((.updatedAt|fromdate) - (.createdAt|fromdate))'
   # 16 min on the PR vs ~4 min baseline = real hang, not noise
   ```

2. **Confirm the CI command runs the WHOLE dir** (`pytest tests/unit`), not just the module you tested in isolation — the hang can hide in a *sibling* test that exercises the changed path.

3. **Reproduce locally with the EXACT CI flags + faulthandler** so the hung thread stack dumps on SIGABRT:

   ```bash
   PYTHONFAULTHANDLER=1 timeout --signal=ABRT 120 \
     python -X faulthandler -m pytest tests/unit -p no:cacheprovider
   # faulthandler prints the blocked stack — e.g. time.sleep / subprocess.run inside _wait_for_pr_terminal
   ```

   `--timeout=<N>` requires the `pytest-timeout` plugin; if it is absent, use the `timeout`+faulthandler approach above.

4. **Or find it by inspection** — audit every call site of the changed method for an unmocked path:

   ```bash
   grep -n "_drive_issue(\|\.run()" tests/unit/test_*.py
   # then check which of those tests reach the new blocking call without patching it
   ```

**Fix (reusable rule):** when you add a blocking call to a hot code path, **every** test that reaches that path must mock the new call — mocking the *trigger* (`_enable_auto_merge`) is not enough; mock the *actual blocking call*:

```python
# In every green-path and run()-level test that reaches the new wait:
patch.object(driver, "_wait_for_pr_terminal", return_value="MERGED")
# ...or "TIMEOUT" where the test asserts the still-pending branch.
# Alternatively, set the wait's timeout env to 0.
```

After patching, the full automation suite ran **1003 passed in 93 s** (no hang).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Patch `run_routing_loop` | `@patch("mymodule.daemon.run_routing_loop", return_value=None)` | `main()` never calls that helper; patch is a silent no-op; real coroutine runs and hangs | Trace the actual call chain from the entry point before choosing a patch target |
| Patch `asyncio.run` | `@patch("mymodule.daemon.asyncio.run", return_value=0)` | Prevents hang, but coroutine body never runs; log assertions inside the coroutine silently fail | Patching `asyncio.run` skips the entire coroutine — only safe when no assertions depend on coroutine-internal side effects |
| `assert_called_once_with(signal.SIGTERM, ...)` | Exact-count assertion on `signal.signal` mock | `asyncio.runners.Runner` calls `signal.signal(SIGINT, ...)` internally; total count is 2 not 1 | Use `assert_any_call` for signal handlers when `asyncio.run()` is involved |
| Pre-set module-level event variable | `mymodule._shutdown_event = asyncio.Event(); mymodule._shutdown_event.set()` before calling `run()` | `run()` immediately overwrites it with `_shutdown_event = asyncio.Event()`; the pre-set value is discarded | Setting a module variable before a coroutine that reassigns it is a no-op — patch the constructor instead |
| `asyncio.create_task` concurrent setter | Spawned a task to set the event concurrently after `run()` started | Fragile scheduling — no guarantee the setter runs before `wait()` is reached; also flagged by CodeQL | Constructor patching is safer and deterministic |
| Default `--timeout-method=signal` | `--timeout=30` only, relying on default SIGALRM | SIGALRM fires only when `epoll.poll(-1)` returns — which never happens with no events | Both `--timeout` and `--timeout-method=thread` are required |
| `--timeout=30` without `--timeout-method` | Added `addopts = "--timeout=30"` only | Still defaults to signal method; CI still times out at job level | Always set `--timeout-method=thread` alongside `--timeout` |
| `patch("module.time.sleep")` globally | Patched `time.sleep` to skip waits in retry test | Patch leaked to every other module sharing the same `time` singleton; runaway print loop OOMed WSL host | `patch("module.time.sleep")` is process-wide, not module-scoped |
| Patch probe via re-export namespace | `patch("module_b.func")` when `module_a` is the actual call site | Lookup happens in `module_a`'s namespace; patch is a no-op; real function ran and triggered the OOM loop | Patch at the source namespace where the call site resolves the name |
| Wall-clock timing assertion | `assert elapsed >= 0.3` after calling a function that sleeps internally | Flaky under CPU contention, OS scheduler jitter, and coverage overhead | Replace with `mock_sleep.assert_any_call(N)` — deterministic and verifies delay values |
| `@pytest.mark.skipif(COVERAGE_RUN == "1")` workaround | Skipped timing-sensitive test under coverage | Masks flakiness; test still fails in full-suite non-coverage runs | Remove skip workarounds; refactor to use mocks instead |
| `patch("hermes.server.get_settings", return_value=mock)` | Patched the module-level name bound by `Depends()` | `Depends()` captured the original function object at import time; module-name patch is ignored by FastAPI DI | Manipulate env vars and call `get_settings.cache_clear()` instead |
| Assumed blank env state | Tests assumed no `.env` was present | `.env` at project root supplies real secrets locally but not in CI; tests passed in CI, failed locally | Always explicitly set or unset every env var a test depends on |
| `@limiter.limit()` decorator only, no middleware | Added rate limit decorator without registering `SlowAPIMiddleware` | Requests returned 202; rate limit was never enforced | `SlowAPIMiddleware` is mandatory — the decorator alone registers the limit but does not evaluate it |
| Patched `asyncio.wait_for` with real `async def` | `async def _timeout(): raise asyncio.TimeoutError()` + `patch("asyncio.wait_for", side_effect=_timeout)` | Produced `RuntimeWarning: coroutine '_timeout' was never awaited` | Use `AsyncMock(side_effect=asyncio.TimeoutError())` directly on the mock method |
| Removed `await` on `asyncio.Task` | Removed `await advance_task` to silence bot | Causes `RuntimeWarning: Task was destroyed but it is pending!` and silently swallows background exceptions | Never remove task awaits to satisfy a static analysis bot |
| `_ = await advance_task` assignment | Assigned result to `_` to suppress "no effect" warning | Bot flags the `await` expression itself, not the assignment | Dismiss the bot comment; the code is correct |
| `# noqa` comment to suppress bot | Added inline suppression | GitHub code-quality bot does not respect Python `# noqa` directives | Bot suppression requires config-file exclusions; correct response is dismissal |
| Module-only test run passed, declared done | Ran only `test_ci_driver.py` (mocked the new `_wait_for_pr_terminal`) and called it green | The hang lived in a sibling `run()`-level test the isolated run never covered; `gh` returned fast locally so it passed there | Always run the full dir the way CI does (`pytest tests/unit`) before claiming green |
| Assumed slow = variance | Treated the 16-min job as a slow runner / noise | It was a real hang on a blocked `time.sleep`/`subprocess.run`, not jitter | Compare to the baseline job duration on main; 4× the baseline is a hang, not variance |
| Mocked `_enable_auto_merge` but not the downstream wait | Patched the auto-merge trigger to `True` but left `_wait_for_pr_terminal` real | Mocking the trigger still let the green path reach the real `gh pr view` + `time.sleep` and block to the 1800 s timeout | Mock the actual blocking call (`patch.object(driver, "_wait_for_pr_terminal", ...)`), not just the trigger that precedes it |

## Results & Parameters

### pytest Configuration (copy-paste ready)

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "--cov=src/<package> --cov-report=term-missing --cov-report=xml --timeout=30 --timeout-method=thread"
testpaths = ["tests"]

[project.optional-dependencies]
dev = [
    "pytest>=8.3,<9",
    "pytest-asyncio>=0.24,<1",
    "pytest-cov>=6.0,<7",
    "pytest-timeout>=2.3,<3",
]
```

### Timeout Value Guidelines

| Scenario | Recommended `--timeout` |
| --------- | ------------------------ |
| Unit tests only | 10–30 s |
| Integration tests with I/O | 30–60 s |
| Tests involving network calls | 60–120 s |
| Full daemon startup tests | 30 s (with coroutine patching) |

### Diagnostic Stack Trace (epoll hang signature)

```
File ".../asyncio/selector_events.py", line NNN, in _run_once
    event_list = self._selector.select(timeout)
File ".../selectors.py", line NNN, in select
    fd_event_list = self._selector.poll(timeout, max_ev)
```

`timeout=-1` at the bottom means the event loop is waiting forever — signature of an unset `asyncio.Event`.

### Full Async Daemon Test Pattern

```python
import signal
import logging
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import pytest

# Pattern A: patch coroutine function, use assert_any_call for signal
class TestMain:
    @patch("mymodule.daemon.run", new_callable=AsyncMock, return_value=0)
    def test_main_returns_zero(self, mock_run, caplog):
        with caplog.at_level(logging.INFO):
            result = main(["--log-level", "INFO"])
        assert result == 0
        mock_run.assert_called_once()

    @patch("mymodule.daemon.signal.signal")
    @patch("mymodule.daemon.run", new_callable=AsyncMock, return_value=0)
    def test_main_registers_sigterm(self, mock_run, mock_signal):
        main(["--log-level", "INFO"])
        mock_signal.assert_any_call(signal.SIGTERM, ANY)

# Pattern B: patch asyncio.Event constructor
def _make_run_mocks():
    mock_event = asyncio.Event()
    mock_event.set()  # pre-set — wait() returns immediately
    return mock_event

class TestRun:
    async def test_run_returns_zero(self) -> None:
        mock_event = _make_run_mocks()
        with patch("mymodule.daemon.asyncio.Event", return_value=mock_event):
            result = await mymodule.daemon.run(Settings(shutdown_timeout=0.1))
        assert result == 0
```

### FastAPI / pydantic-settings Test Template

```python
import os
from contextlib import contextmanager
from fastapi.testclient import TestClient
from slowapi.middleware import SlowAPIMiddleware

_TEST_SECRET = "test-secret-value-that-is-at-least-32-chars"

@contextmanager
def _settings_client(overrides: dict):
    from myapp.server import app
    from myapp.config import get_settings

    old_env = {k: os.environ.get(k) for k in overrides}
    os.environ.update(overrides)
    get_settings.cache_clear()
    try:
        yield TestClient(app)
    finally:
        get_settings.cache_clear()
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
```

### Bot False Positive Reference

| Situation | Bot Correct? | Action |
| ----------- | ------------- | -------- |
| `await asyncio.Task` stored in local var | No — false positive | Dismiss, keep code |
| `x` (bare expression, non-awaitable) | Yes — true positive | Remove dead statement |
| `await coroutine_function()` (result unused) | Sometimes | Review intent |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectKeystone | PR #451 — daemon coroutine patch | 9 hanging daemon tests fixed; CI green |
| ProjectKeystone | PRs #535, #541 — asyncio.Event constructor patch + timeout-method | `--timeout-method=thread` revealed epoll stack trace; constructor patch fixed hang |
| ProjectKeystone | PR #428 — bot false positive | `await advance_task` dismissed |
| ProjectHephaestus | PR #412 — time.sleep OOM fix | 113 tests pass in 2.6 s after fix vs 30 s + OOM before |
| ProjectScylla | PR #1217 — flaky sleep mock | 3257 tests pass; wall-clock assertion replaced with mock |
| ProjectHermes | CI — FastAPI webhook rate-limit and timeout tests | All five isolation patterns confirmed |
| HomericIntelligence | CI — `_wait_for_pr_terminal` unmocked-wait hang | Full `pytest tests/unit` hung ~16 min vs ~4 min baseline; sibling `run()`-level tests reached the new `gh pr view`+`time.sleep` unmocked; patched `_wait_for_pr_terminal` in all green-path tests → 1003 passed in 93 s, CI green |
