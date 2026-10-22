---
name: pyside6-signal-never-fires-queued-delivery-key-collision
description: "Diagnose PySide6 signals that never take effect: a cross-thread slot that does not run, a QThread that will not finish, or a key shortcut that stays silent. Use when a queued slot never executes, thread cleanup times out, a loop-less probe receives nothing, or two shortcuts share one key."
category: debugging
date: 2026-10-21
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags:
  - pyside6
  - qt-signals
  - qthread
  - cross-thread
  - connection-type
  - event-loop
  - shortcuts
  - offscreen-probe
---

# PySide6: A Signal That Never Seems to Fire

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-21 |
| **Objective** | Separate three look-alike failures — a queued slot that never runs, a worker thread that never exits, and a keyboard shortcut that does nothing — and fix each with the correct wiring rule. |
| **Outcome** | Successful — minimal probes confirmed each cause and each fix. |

## When to Use

- A slot connected to a signal that is emitted in another thread never runs.
- `QThread.wait(timeout)` returns `False` even though the worker emitted `finished`.
- A minimal probe that reads its result before `app.exec()` receives nothing, or prints `QObject::killTimer: Timers cannot be stopped from another thread`.
- Two `QShortcut` objects are bound to one key (for example, a parent widget and a child widget both claim Space). Neither one fires.

## Verified Workflow

### Quick Reference

```python
# 1) A blocked main thread must not depend on a queued delivery to itself.
#    Run teardown work directly on the emitting thread:
job.finished.connect(thread.quit, Qt.ConnectionType.DirectConnection)
thread.finished.connect(release_hook, Qt.ConnectionType.DirectConnection)

# 2) Queued receivers run only while the receiver's event loop runs.
#    Test delivery inside app.exec() and let the slot quit the loop.

# 3) Bind every key exactly once. Route by focus instead of registering
#    a second shortcut with the same key.
```

### Suggested Approach

Qt picks the connection type at emit time: a direct call when the emitting and receiving objects live in the same thread, otherwise a queued delivery into the receiver's thread. Three failures follow from this rule.

1. **Queued quit during a blocked wait.** The worker object lives in the worker thread, and the `QThread` object lives in the main thread. With the default connection, `finished` → `thread.quit` is queued to the main thread. A main thread that is inside `thread.wait()` processes no events, so the quit never runs, `wait()` times out, and dropping the thread reference afterwards aborts the process. Connect `quit` with `DirectConnection` so the emit itself stops the worker loop. Apply the same rule to the release hook on `thread.finished`: a queued hook does not run while the main thread stays blocked.

2. **Queued delivery without a running loop.** A plain Python callable (a lambda or a local function) receives queued signals only while an event loop runs in its thread. A probe that checks its result before `app.exec()` reports zero deliveries and looks broken, and Qt may print timer warnings from its delivery machinery. The same wiring delivers correctly inside a live loop. Probe with a loop: start `app.exec()`, let the slot record the payload and quit the loop, then read the result. Timer warnings in a loop-less harness are one symptom of this cause, not a second defect.

3. **Two shortcuts on one key.** Qt suppresses both `QShortcut` objects when they bind the same key, even when one context is more specific than the other. Context specificity does not pick a winner. Give each key one owner — one shortcut or one `QAction` — and route to the focused widget, or handle the key in `keyPressEvent` of the single widget that owns it.

When a fix needs proof, write a minimal probe: one worker object moved to a `QThread`, one signal, one receiver. Run it under the offscreen platform plugin (`QT_QPA_PLATFORM=offscreen`) so no display is needed. Change one variable per run: connection type, loop presence, or key ownership.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Two shortcuts on one key | Bound the same key on a parent and a child shortcut and expected the more specific context to win | Neither shortcut fired | One owner per key; route by focus |
| Queued quit before a blocked wait | Connected `finished` to `thread.quit` with the default connection, then called `thread.wait()` on the main thread | The quit waited in the main queue that the blocked wait prevented; `wait()` timed out and a dropped thread reference aborted the process | Use `DirectConnection` for quit and release hooks that must complete before a blocked wait ends |
| Probe read before the loop | Emitted a payload to a lambda and read the result before `app.exec()` | Zero deliveries — queued calls ran only after a loop started | Start the loop first; let the slot signal completion |

## Results & Parameters

### Configuration

```python
from PySide6.QtCore import Qt

# Teardown wiring that survives a blocked main thread:
job.finished.connect(worker.quit, Qt.ConnectionType.DirectConnection)
worker.finished.connect(cleanup, Qt.ConnectionType.DirectConnection)

# Cross-thread delivery test: complete it only inside a running loop:
job.done.connect(lambda payload: (results.append(payload), app.quit()))
app.exec()
worker.wait(10_000)
```

### Expected Output

- The worker thread exits promptly and `wait()` returns `True`.
- The probe reports the delivered payload after the loop runs.
- Each key press triggers exactly one handler.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A private PySide6 desktop application | 2026-10-21 — three minimal offscreen probes covering connection type, loop presence, and key duplication | Direct quit finished and released the thread; the queued quit timed out; the lambda receiver delivered only with a live loop; duplicate-key shortcuts both stayed silent |

## References

- [Qt: Signals and Slots](https://doc.qt.io/qt-6/signalsandslots.html)
- [Qt: QThread](https://doc.qt.io/qt-6/qthread.html)
- [Qt: QShortcut](https://doc.qt.io/qt-6/qshortcut.html)
