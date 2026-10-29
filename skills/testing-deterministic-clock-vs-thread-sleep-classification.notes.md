# Notes: testing-deterministic-clock-vs-thread-sleep-classification

Supporting evidence for the asyncio event-loop hazard amendment (v2.2.0).
Generalized from one live test failure and repair; identifiers are omitted
under the privacy rules.

## Frozen event-loop incident (2026-10-26)

1. A gateway service serves a cached key snapshot during key-sync degradation.
   The pacing of the degraded mode (log interval, refresh checks) is driven by
   a module-level interval constant that production compares against
   `time.monotonic()`.
2. A test patched `proxy_app.time.monotonic` directly to control the pacing
   clock. The app runs an in-process async server (ASGI transport) with a
   lifespan-scoped startup and live request handlers.
3. The test suite hung. A faulthandler dump showed the test thread idle in
   `selectors.select` with no ticking coroutine — the event loop was parked
   with nothing scheduled to fire.
4. Root cause: `proxy_app.time` is the shared stdlib `time` module object.
   Patching its `monotonic` attribute is process-global: asyncio's event loop
   sources `loop.time()` (and therefore every `asyncio.sleep`, `wait_for`,
   `call_later`, and lifespan timeout) from the same frozen value. Every
   scheduled wake-up stayed in the future, so no scheduled callback ever ran.
5. The repair kept the classification (timer-boundary) but changed the
   mechanism: patch the module's pacing constant
   (`_STALE_SERVING_LOG_INTERVAL_S`-style interval) to a tiny test value, keep
   the real clock untouched, and wait with short real `asyncio.sleep`s
   (multiples of the test interval). The loop clock stays real, scheduled
   callbacks fire, and the degraded-mode behavior still advances fast in test
   time.
6. Result: the focused cache tests (110) plus the auth-adjacent (488), proxy
   (66), and plan-command (22) suites all passed green with the pacing-constant
   patch. The same tree hung reproducibly with the clock attribute patch.

## Generalization boundaries

- The hazard is not asyncio-specific in mechanism — it is "patch a name that a
  hidden clock consumer also reads." Asyncio is the most common hidden
  consumer because the loop scheduler reads `time.monotonic` at the C level
  through the same module attribute.
- Any framework with an internal scheduler tick (reactor loops, watchdog
  timers) shares the shape: a process-global clock patch freezes its future
  callbacks. The pacings-constant + real-short-sleep repair generalizes: find
  the constant the subject reads, not the clock the engine reads.
- If a clock patch is truly required for an asyncio-hosted subject, activate
  it only after startup/lifespan completes and release it before teardown,
  and verify no lifespan-scheduled task must fire during the patched window.
  Prefer the pacing-constant design whenever the subject exposes one.

## Diagnostic recipe

- Symptom: test run stops progressing; CPU idle.
- Confirm: run with `faulthandler` (e.g. `pytest -o faulthandler_timeout=30`
  or `python -X faulthandler`). A thread stack parked in `selectors.select`
  (or `select`/kqueue/epoll variants) with no coroutine frames ticking means
  the loop has nothing in the past to run — the scheduler clock is frozen.
- Then audit active patches for any attribute on a shared stdlib module
  (`time.monotonic`, `time.time`, `threading.Event.wait` on shared objects).
