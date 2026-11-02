---
name: coded-rejection-boundary-catch-completeness
description: "Make a coded rejection boundary catch every exception type that its own call sites raise. Use when a user-supplied value reaches a typed error mapping, a boundary claims one status class, or a malformed input still returns a 5xx."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags:
  - error-handling
  - exception-types
  - status-mapping
  - http-boundary
  - input-validation
  - pathlib
  - oserror
  - valueerror
  - rejection-envelope
---

# Coded Rejection Boundary: Catch Every Type the Call Raises

## Overview

| Field | Value |
| ------- | ----- |
| **Date** | 2026-11-01 |
| **Objective** | Keep every client-input fault on the typed rejection path instead of letting an uncaught exception type become a server error. |
| **Outcome** | Successful. A boundary that mapped one typed error to a client status also caught the filesystem family, but not the sibling types that the same call raises. Faults escaped to the default failure path and returned a server error. |
| **Verification** | verified-local. Three behavior tests failed before the repair and passed after it. The project test suites and lint for the changed files passed. |

## When to Use

- A request value flows into a typed rejection, and the boundary is written as
  `except (InputError, SourceError): return rejection(...)`.
- The function under the boundary calls more than one operation that can fail. Examples are a best-effort size read, a strict path resolution, and an open call.
- The change claims a status class for client input, such as "a client fault is a 4xx, not a 5xx".
- A malformed input still returns a server error with no coded message.

Do not use this skill for a failure that a traceback already explains as a server bug. Fix the bug there.

## Verified Workflow

### Quick Reference

```text
1. List each call under the boundary that can fail.
2. For each call, list the exception types it raises for client input.
3. Include every type in the boundary, or translate it at the call site.
4. Add one behavior test per sibling type. Confirm each test fails first.
```

Do not write the boundary tuple from memory. Read the types that the called
functions raise. A standard-library function can raise a type that is not in the
family you expect.

### Suggested Approach

1. Find the calls that run before the typed rejection. In a path-based intake
   they are a best-effort metadata read, a strict resolution, and an authorized
   open. Each one is its own failure point.
2. List the exception types for each call. For a filesystem path, the common set is:
   - `OSError` for a missing file, an unreadable parent, or a permission fault;
   - `ValueError` for a malformed path, such as one that contains an embedded NUL
     byte. The filesystem functions reject the path before any I/O;
   - `RuntimeError` for a symbolic-link loop, which resolution reports as a
     loop, not as an `OSError`.

   `ValueError` is not a subclass of `OSError`. A tuple of only `OSError` misses
   the other two types.
3. Catch the full set at the call site, and map each fault to one typed
   rejection. Use one code and one public message when the separate reasons would
   let a caller probe files that they do not own.
4. Keep the detailed exception text in the server log only. Keep the client
   message free of paths, line content, and user text.
5. Write one behavior test per sibling type that you found in step 2. Confirm
   that each test fails against the old boundary before you change it.
6. State the guarantee at its true scope. A best-effort read can run before the
   roots check. Say "before it opens the file", not "before any filesystem
   access".
7. Check for a competing open change that reports the same shape. Verify each
   reported shape on your own head before you trust or dismiss it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Catch only `OSError` | Wrapped a strict path resolution in `except OSError`. | A path with an embedded NUL byte raised `ValueError`. A symbolic-link loop raised `RuntimeError`. Both escaped the boundary and returned a server error. | List the types per call. A transport or resolution helper can raise a type outside the family that you expect. |
| Best-effort read outside the guard | Left a size read unguarded because the intake open "re-checks" the source later. | The read ran first, raised `ValueError` for the same malformed path, and reached no handler. | Guard every fallible call before the typed rejection. A later check does not protect an earlier call. |
| One test for the family | Tested a missing file and a permission fault. | Both are `OSError`. The suite passed while the `ValueError` and `RuntimeError` branches were open. | Add one test for each exception type, not each symptom. |
| Absolute scope claim | The interface document said the roots check runs "before any filesystem access". | A best-effort size read runs first. The claim was false, even though the status behavior was correct. | State the guarantee for the operation that provides it. |

## Results & Parameters

### Configuration

```python
try:
    resolved = submitted.resolve(strict=True)
except (OSError, ValueError, RuntimeError) as error:
    raise SourceError(
        f"cannot resolve {submitted}: {error}",   # server log only
        code="source_unavailable",                # stable public code
        public_message=UNAVAILABLE_MESSAGE,       # no path, no user text
    ) from error
```

| Parameter | Value |
| --- | --- |
| Status rule | A client-input fault returns the client status. A configuration fault takes its own code and status. |
| Public message | One template for every fault in the same trust class. Keep paths and user text out. |
| Test count | One behavior test for each exception type that step 2 lists. |

### Expected Output

- A malformed path returns the coded client rejection. Its message has no path and no server traceback.
- The server log keeps the detailed cause.
- The regression test for each sibling exception type passes.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal gateway | A path-based batch intake with a coded rejection envelope | Three regression tests for an embedded NUL byte, a symbolic-link loop, and the request route. All failed before the repair and passed after it. See [notes](coded-rejection-boundary-catch-completeness.notes.md). |

## References

- [Python exception hierarchy](https://docs.python.org/3/library/exceptions.html)
- [pathlib resolution and strict mode](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve)
- [Generic error code hides seam type mismatch](generic-error-code-hides-seam-type-mismatch.md)
- [Strip embedded NUL at subprocess egress](subprocess-embedded-null-byte-sanitize.md)