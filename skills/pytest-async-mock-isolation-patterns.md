---
name: pytest-async-mock-isolation-patterns
description: "Diagnose async pytest hangs and cross-test contamination. Use when event loops block, sleep mocks cause retries or OOM, module singletons leak, reload invalidates object patches, FastAPI dependencies ignore name patches, async HTTP faults need state, or executor workers outlive a test."
category: testing
date: 2026-06-07
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
history: pytest-async-mock-isolation-patterns.history
tags:
  - pytest
  - asyncio
  - AsyncMock
  - test-isolation
  - respx
  - circuit-breaker
  - importlib-reload
  - fastapi
  - threadpool
---

# Pytest Async Mock Isolation Patterns

## Overview

Async test hangs are often mock-boundary or shared-state bugs, not asyncio bugs. Patch the unit's
public dependency, reset singleton and loop-bound state at the narrowest reliable boundary, prevent
background workers from escaping the test, and run the full suite before declaring isolation.

Case-level provenance is in
[pytest-async-mock-isolation-patterns.notes.md](pytest-async-mock-isolation-patterns.notes.md).
The byte-complete superseded version is in
[pytest-async-mock-isolation-patterns.history](pytest-async-mock-isolation-patterns.history).

## When to Use

- Pytest hangs in epoll/select or times out only in CI.
- A coroutine replaces a global `asyncio.Event`, defeating a pre-set fixture.
- Patching `time.sleep` makes retry loops run without delay or exhaust memory.
- Tests pass alone but fail together because a breaker, cache, registry, lock, or event leaks.
- `patch.object` stops observing calls after `importlib.reload()`.
- FastAPI `Depends()` keeps using the function object captured at route definition.
- Async HTTP tests need ordered 500/503/timeout/recovery behavior.
- A test reaches an optional CLI or subprocess unavailable in CI.
- A `ThreadPoolExecutor` worker continues after the test and mutates the next test's state.
- Empty input activates a discovery branch that performs a real external call.

## Verified Workflow

### Diagnostic sequence

1. Reproduce the failing group, not only the failing test.
2. Add a bounded timeout with stack dumping.
3. Identify the boundary that owns waiting, I/O, process creation, or global mutation.
4. Patch that boundary at its lookup path.
5. Reset shared state before and after each test.
6. Prevent workers/tasks from surviving fixture teardown.
7. Run the full suite in CI order.

```toml
[tool.pytest.ini_options]
addopts = "--timeout=30 --timeout-method=thread"
```

Both timeout flags matter. Thread mode can dump a main thread stuck in epoll when signal-based
interruption is ineffective.

## Patterns

### Patch the coroutine, not asyncio internals

```python
@patch("package.runner.run_daemon", new_callable=AsyncMock)
def test_main(mock_run: AsyncMock) -> None:
    mock_run.return_value = None
    main()
    mock_run.assert_awaited_once()
```

When `asyncio.run()` registers signals internally, use `assert_any_call` rather than assuming call
order.

### Patch constructors when code replaces synchronization objects

If the coroutine executes `stop_event = asyncio.Event()`, setting the old global event cannot stop
it. Patch the constructor at the module's lookup path:

```python
event = MagicMock()
event.wait = AsyncMock(return_value=True)
with patch("package.daemon.asyncio.Event", return_value=event):
    asyncio.run(run_daemon())
```

For locks and events created at module import, use a lazy fixture so collection does not bind them
to the wrong event loop:

```python
@pytest.fixture(autouse=True)
def reset_async_state():
    from package import state

    state._event = asyncio.Event()
    state._lock = asyncio.Lock()
    yield
    state._event = asyncio.Event()
    state._lock = asyncio.Lock()
```

### Patch the wait helper, not process-wide sleep

```python
with patch("package.retry.wait_before_retry", return_value=None) as wait:
    result = operation()
    wait.assert_called_once_with(expected_delay)
```

Patching `time.sleep` globally can accelerate an unbounded retry loop until OOM. If direct sleep
must be patched, patch the symbol as imported by the unit and assert exact delays and call count.

### Reset singleton state on both sides

```python
@pytest.fixture(autouse=True)
def reset_breaker():
    from package.github import _GH_BREAKER

    _GH_BREAKER.reset()
    yield
    _GH_BREAKER.reset()
```

This fixture is necessary but insufficient if background tasks or threads survive teardown. The
owner must await tasks or join workers before yielding control; unit tests may patch the per-item
worker to avoid creating the executor at all.

### Patch by string after reload

```python
with patch("package.utils.helpers.logger.error") as log_error:
    importlib.reload(helpers)
    helpers.call_something()
    log_error.assert_called()
```

`patch.object(imported_logger, ...)` may hold the pre-reload object and observe nothing.

### Override captured FastAPI dependencies

Route construction captures the dependency callable. Replace it through FastAPI's override table,
and clear cached settings around environment changes:

```python
app.dependency_overrides[get_settings] = lambda: test_settings
get_settings.cache_clear()
try:
    yield TestClient(app)
finally:
    app.dependency_overrides.clear()
    get_settings.cache_clear()
```

Patching the module name alone does not replace the captured callable.

### Build one respx context per async fixture

```python
@pytest.fixture
async def api_mock():
    with respx.mock(assert_all_called=False) as router:
        route = router.get("https://service.test/items")
        route.side_effect = [
            httpx.Response(503),
            httpx.ReadTimeout("timeout"),
            httpx.Response(200, json={"items": []}),
        ]
        yield route
```

Use a synchronous context manager inside the async fixture. Configure ordered side effects on one
route; avoid nested global respx contexts.

### Block every reachable external branch

Inputs determine call graphs. A test of `_discover_prs([])` may call
`_discover_failing_prs()` only when configured issue numbers are empty, and may also call bot
discovery. Patch every branch reachable under the test's exact options:

```python
monkeypatch.setattr(driver, "_discover_failing_prs", lambda: [])
monkeypatch.setattr(driver, "_discover_bot_prs", lambda: [])
monkeypatch.setattr(driver, "_drive_issue", lambda issue: WorkerResult.ok(issue))
```

Return the real contract type. Returning `None` can crash before the intended assertion and conceal
the isolation defect.

### Test fault effects, not only fault commands

A chaos mock that records `kill` or `latency` but does not change responses is not faithful. Model
the externally visible effect: timeouts, status changes, unavailable queues, or recovery order.
Assert both the injected command and the client-observed consequence.

## Decision Rules

- Patch where the dependency is looked up, not where it was originally defined.
- Patch the highest stable boundary that prevents real waiting or I/O.
- Reset shared state before and after; also stop every producer that could mutate it later.
- Use string patches across reload boundaries.
- Use dependency overrides for FastAPI's captured callables.
- Make mock returns satisfy the real type and protocol contract.
- Exercise conditional call paths with their activating inputs.
- Full-suite order is part of the test when diagnosing contamination.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Pre-set an event that the coroutine reassigns | Unit waits on a new object | Patch the Event constructor |
| 2 | Patch global `time.sleep` | Runaway retry becomes CPU/OOM failure | Patch the unit's wait helper and assert bounds |
| 3 | Reset breaker only before a test | Late worker reopens it after reset | Reset both sides and stop/join producers |
| 4 | Use `patch.object` across reload | Patch targets stale object | Patch by import string |
| 5 | Patch `get_settings` name after route creation | `Depends` retains original callable | Use dependency overrides and clear caches |
| 6 | Test only non-empty discovery input | Conditional real-call path remains hidden | Test empty input and patch all activated branches |
| 7 | Record a chaos command without side effects | Test proves invocation, not behavior | Simulate the externally observable fault |
| 8 | Run only the changed test module | Cross-test contamination stays invisible | Run the full suite in CI order |

## Results & Parameters

- Suggested diagnostic timeout: 30 seconds with `--timeout-method=thread`.
- Reset shared state before and after each test, then stop every asynchronous producer.
- Patch by lookup string across reload boundaries and use FastAPI dependency overrides for
  captured callables.
- Exercise the input values and options that activate conditional external-call branches.
- Full-suite order is the acceptance test for cross-test isolation.

Copy-ready baseline; adjust version ranges to the repository's supported runtime:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "--timeout=30 --timeout-method=thread"
testpaths = ["tests"]
markers = [
  "integration: integration tests with mock HTTP services",
  "asyncio: async tests",
]
```

Use 10–30 seconds for isolated unit tests, 30–60 seconds for mocked I/O integration tests, and
60–120 seconds only where real network calls are deliberately in scope. A full daemon test should
normally stay near 30 seconds after its coroutine boundary is patched.

## Verification Checklist

```bash
pytest -q path/to/failing_group --timeout=30 --timeout-method=thread
pytest -q
```

- Remove one isolation patch temporarily and confirm the focused regression fails for the expected
  reason.
- Assert mock calls and meaningful results, not only absence of exceptions.
- Check no pending tasks, executor threads, subprocesses, or respx routes escape teardown.
- Keep test names aligned with all assertions they claim.

## Evidence Boundary

The core patterns have CI evidence across the indexed ProjectHephaestus, ProjectTelemachy, and
ProjectCharybdis cases. Individual cases differ; consult the notes index before claiming a specific
pattern is CI-verified.
