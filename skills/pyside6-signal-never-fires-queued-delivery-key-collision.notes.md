# Notes: pyside6-signal-never-fires-queued-delivery-key-collision

Supporting probe evidence for the main entry. Recorded 2026-10-21. All probes
ran under `QT_QPA_PLATFORM=offscreen` with PySide6 (Qt 6). Paths, project
names, and session details are omitted; only the probe design and results are
kept.

## Probe 1 — queued delivery to a plain Python callable

Design: a `Job(QObject)` with `done = Signal(object)` moved to a `QThread`;
`worker.started → job.run`; `job.done → on_done` with the default connection;
`job.finished → worker.quit` as `DirectConnection`.

- **No event loop running:** the receiver was never invoked. Reading the
  result after `worker.wait()` reported an empty list. The payload sat in the
  receiver thread's queue because nothing pumped events.
- **Loop running, slot quits the loop:** the receiver ran, appended the
  payload, and quit the loop; the result was present after `wait()`.
  A single-shot safety timer (5 s) guarded against a delivery failure hanging
  the probe.
- **Takeaway:** delivery to lambdas is correct in a real application (the loop
  always runs). It is the loop-less harness that misleads. Any probe must
  treat "slot ran" as observable only after, or from inside, a live loop.

## Probe 2 — queued quit versus a blocked wait

Design: same job/thread pair; compare `Qt.ConnectionType.AutoConnection`
against `Qt.ConnectionType.DirectConnection` for `job.finished → thread.quit`,
with the main thread calling `thread.wait()` immediately after `start()`.

- **Queued quit:** `wait()` reached its deadline and returned `False`. The
  quit event targeted the main thread, and the main thread was blocked inside
  `wait()`, so it could not process the quit. Releasing the thread object
  while its thread still ran produced the fatal
  `QThread: Destroyed while thread '' is still running` abort — a
  consequence of the stuck teardown, not an independent bug.
- **Direct quit:** the emit called `quit` on the worker thread; the loop
  exited; `wait()` returned promptly and cleanup hooks ran.
- **Release hooks:** `thread.finished → release_hook` queued to the main
  thread does not run while the main thread stays blocked. The production
  pattern uses `DirectConnection` for both connections, and a shutdown path
  that cancels first, waits with a deadline (15 s), and terminates as a last
  resort.

## Probe 3 — duplicate key shortcuts

Design: two `QShortcut` objects bound to the same key sequence, one on a
parent widget and one on a child widget, each appending a distinct marker.

- Neither marker appeared. Qt suppressed both registrations rather than
  selecting by context specificity.
- **Takeaway:** "the more specific widget context wins" is false for
  `QShortcut`. Single ownership per key with explicit routing is the working
  pattern; the main entry records the fix.

## Timer-warning symptom

`QObject::killTimer: Timers cannot be stopped from another thread` and the
matching `startTimer` warning appeared in a harness that serviced queued
delivery to Python callables without a normally running event loop. The
warning and the observed delivery behavior share one root cause: Qt's
delivery machinery running outside the loop it expects. With a live loop the
probes delivered payloads and printed no warnings. Treat the warning as a
harness diagnostic; fix the harness before searching for an application bug.

## Signal-to-entry mapping

| Probe | Entry section | Confirmed rule |
| --- | --- | --- |
| Probe 1 | Suggested Approach, cause 2 | Queued receivers need a running loop |
| Probe 2 | Suggested Approach, cause 1 | Direct connections for teardown that precedes a blocked wait |
| Probe 3 | Suggested Approach, cause 3 | One owner per key; context specificity does not disambiguate |
| Timer warnings | When to Use, Failed Attempts | Warning text is one symptom of the missing loop |
