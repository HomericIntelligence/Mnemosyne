---
name: log-invariant-once-per-process
license: BSD-3-Clause
description: "Log a hot-path output that stays the same within one process only once per distinct value, or remove that output when its message carries no diagnostic signal. Use when a debug line repeats identically for every call and an already downgraded level still floods the log."
category: ci-cd
date: 2026-11-23
version: "1.0.0"
user-invocable: false
verification: unverified-by-ci
tags:
  - python
  - logging
  - observability
  - noise-reduction
  - debug-level
  - hot-path
  - invariant
  - throttle
  - caplog
---

# Logging: Emit an Invariance-Level Record Once per Process

## Overview

| Field | Value |
| ------- | ------- |
| **Theme** | A hot path calls a resolver for the same invariant (a runtime root, an identity, a stable discriminator) and each call emits the same debug line from a helper such as `logger.debug("... root=%s", base)` |
| **Outcome** | One record per process per distinct value, or no record when the text is constant and carries no diagnostic signal |
| **Distinction** | This augments, not replaces, level-gating lessons: lowering an already-`DEBUG` line does not stop the flood if the host always shows `DEBUG` |

## When to Use

- A log line repeats identically for every call on a hot path, for example one line per token acquisition or per issue processed.
- The logged value is an **invariant of the process**: a resolved directory root, a constant discriminator, a stable process identity. Recomputing it returns the same result on every call.
- The running configuration already enables `DEBUG` and the flood comes from a `DEBUG` (not `INFO`/`WARNING`) record.
- The message **never changes**: constant text with no varying payload such as command, arguments, duration, cause, or outcome.

## Verified Workflow

### Decision Tree

```
For a record at a hot path, assess its content:
├─ "Is the message constant text with no varying payload?"
│   ├─ YES → Remove the record. A constant line has no diagnostic value.
│   └─ NO  → "Is the attached value invariant inside one process?"
│       ├─ YES → Emit once per process per distinct value. Re-emit only
│       │          when the value actually changes (for example after an
│       │          explicit configuration override).
│       └─ NO  → Keep the record. It is signal, not spam.
└─ A second question (should the *level* hold?) stays open: this rule applies
   only when the level question has already been resolved, such as an already-
   correct `DEBUG` line.
```

### Pattern: emit once per distinct value

A module-level guard caches the last logged value so a re-resolution of the
same invariant stays silent within the process:

```python
_logged_runtime_base: Path | None = None

def _log_runtime_base_once(base: Path) -> None:
    global _logged_runtime_base
    if base == _logged_runtime_base:
        return
    _logged_runtime_base = base
    logger.debug("Throttle scope=%s root=%s", GLOBAL_THROTTLE_SCOPE, base)
```

The guard references the *value* (here the resolved root). A controlled
reconfiguration produces a new value, so the record appears once per distinct
configuration. Tests: resolve a state path three times under a capture fixture
and assert exactly one matching record. Give each test its own distinct value
(temporary directory or configured root) so guard state cannot leak between
tests.

### Estimation guard

Free-form keying also works when the payload has several fields. Guard the
record on the resolved value tuple, not on a call counter; a counter drifts
from what the operator sees.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Downgrade the level | Changed a repeated `DEBUG` line to `INFO` | The fleet run already logged at `DEBUG`; the flood continued with the identical text | A level change does not help when the host always shows `DEBUG` |
| Delete the varying line | Removed the loader message but kept a constant `logger.debug("Running subprocess")` line for the start of each subprocess | The constant text gave no command, arguments, or result, so the entry had no diagnostic value | A constant message with no payload is removed, not moved to a new level |
| Keep the per-call line | Left `logger.debug("Running subprocess")` in place for any future caller | The line fires on every call and holds no information for an operator or a debugger | Review the *content* of a hot-path line before deciding on frequency |
| Throttle the record rate | Added a timestamp-based rate limiter for the log | A periodic gate hides legitimate new values and adds infrastructure for one deterministic value | The correct gate is the *distinct value* of the invariant, not time |

## Results & Parameters

The two fixes this pattern covers:

1. **Invariant record gated on a value.** A throttle helper resolved its
   node-local root for every acquisition and emitted
   `Throttle scope=machine root=<resolved>` each time. After a distinct-value
   guard, one record per process replaced the repeated identical record.
2. **Constant message removed.** A subprocess wrapper emitted
   `logger.debug("Running subprocess")` per call with no payload, causing
   repeated identical `DEBUG` lines on a long run. The line was removed; the
   informative `Subprocess failed with exit code …` failure record was kept.

A remaining observable is the per-process boundary: each new process still
emits the record once for its own distinct value.

### Expected output after the fix

```
[DEBUG] ... throttle root resolved once per process per distinct root
[DEBUG] ... identical line repeat count per call ≈ 0 on the same process value
```

## Verified On

| Base | Context | Details |
| --------- | ------- | --------- |
| A shared automation codebase | Two merged fixes: gate the repeated resolved-root record once per process; remove a constant per-call marker | Line was `... root=<value>` at `DEBUG`; after the fix the same process prints the value once. See [notes](log-invariant-once-per-process.notes.md) for the general pattern and its verification boundary |

## References

- [Logging: Downgrade Noisy Messages in Happy Path](logging-downgrade-noisy-happy-path.md) — covers the *level* decision for fallback and success-path logs
- [Observability: Logging and Process Monitoring](observability-logging-and-process-monitoring.md) — when the process-level boundary (per-process, per host, or per node) must be part of the diagnostic plan
