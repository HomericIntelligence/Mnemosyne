---
name: coded-rejection-boundary-catch-completeness
description: "Make a coded rejection boundary catch every exception type that its own call sites raise, and send only client-cause faults to the client status. Use when a user-supplied value reaches a typed error mapping, a boundary claims one status class, a malformed input still returns a 5xx, or a resource fault is reported to the caller as a bad input."
category: architecture
date: 2026-11-01
version: "1.1.0"
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
- The boundary catches a broad family for a user-supplied value, such as every `OSError`, and a server resource fault can reach it.
- A future edit could wrap every member of a family into the client code while the suite stays green.

Do not use this skill for a failure that a traceback already explains as a server bug. Fix the bug there.

## Verified Workflow

### Quick Reference

```text
1. List each call under the boundary that can fail.
2. For each call, list the exception types it raises for client input.
3. Include every type in the boundary, or translate it at the call site.
4. Split each caught family by fault cause. Map the client cause to the client
   code. Re-raise the server cause unchanged.
5. Add one behavior test per sibling type, and one per fault cause of a shared
   family. Confirm each test fails first.
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
3. Split each caught family by fault cause. Inside one family, a member can be a
   client cause or a server cause. For `OSError`, the common client causes are a
   missing entry, a permission fault, a wrong entry type, and a link loop. A
   descriptor exhaustion, an I/O fault, or a stale handle is a server cause.
4. Map each fault to one typed rejection. Use one code and one public message when
   the separate reasons would let a caller probe files that they do not own.
5. Use an allowlist of the client-cause members, and re-raise every other member
   unchanged. A re-raised member reaches the server failure path, so the
   server-error rate stays visible. Do not wrap the whole family into the client
   code.
6. Keep the detailed exception text in the server log only. Keep the client
   message free of paths, line content, and user text.
7. Write one behavior test per sibling type that you found in step 2, and one per
   fault cause of a shared family. Confirm that each test fails against the old
   boundary before you change it. A test for one cause leaves the other cause
   unguarded.
8. State the guarantee at its true scope. A best-effort read can run before the
   roots check. Say "before it opens the file", not "before any filesystem
   access".
9. Check for a competing open change that reports the same shape. Verify each
   reported shape on your own head before you trust or dismiss it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Catch only `OSError` | Wrapped a strict path resolution in `except OSError`. | A path with an embedded NUL byte raised `ValueError`. A symbolic-link loop raised `RuntimeError`. Both escaped the boundary and returned a server error. | List the types per call. A transport or resolution helper can raise a type outside the family that you expect. |
| Best-effort read outside the guard | Left a size read unguarded because the intake open "re-checks" the source later. | The read ran first, raised `ValueError` for the same malformed path, and reached no handler. | Guard every fallible call before the typed rejection. A later check does not protect an earlier call. |
| One test for the family | Tested a missing file and a permission fault. | Both are `OSError`. The suite passed while the `ValueError` and `RuntimeError` branches were open. | Add one test for each exception type, not each symptom. |
| Absolute scope claim | The interface document said the roots check runs "before any filesystem access". | A best-effort size read runs first. The claim was false, even though the status behavior was correct. | State the guarantee for the operation that provides it. |
| Whole family mapped to the client code | Wrapped every `OSError` from the open call into the unavailable-source code. | A descriptor exhaustion and an I/O fault then answered as a bad path. The server-error rate stayed flat, so the alert that watches server errors never fired. | Classify by fault cause, not by exception type. A server cause must stay a server error. |
| One cause test for a split family | Tested the client cause at one call and the server cause at a different call. | The split at the untested call could regress to a whole-family wrap, and the suite would stay green. | Test both causes at every call that performs the split. |

## Results & Parameters

### Configuration

```python
CLIENT_CAUSE = frozenset({errno.ENOENT, errno.EACCES, errno.ENOTDIR, errno.ELOOP})

try:
    resolved = submitted.resolve(strict=True)
except (OSError, ValueError, RuntimeError) as error:
    if isinstance(error, OSError) and error.errno not in CLIENT_CAUSE:
        raise                                     # server cause: keep the 5xx
    raise SourceError(
        f"cannot resolve {submitted}: {error}",   # server log only
        code="source_unavailable",                # stable public code
        public_message=UNAVAILABLE_MESSAGE,       # no path, no user text
    ) from error

try:
    fd = os.open(resolved, flags)
except OSError as error:
    if error.errno not in CLIENT_CAUSE:
        raise
    raise SourceError(...) from error
```

| Parameter | Value |
| --- | --- |
| Status rule | A client-input fault returns the client status. A configuration fault takes its own code and status. A server cause keeps the server status. |
| Fault-cause rule | Allowlist the client-cause members of a broad family. Re-raise every other member at the call site. |
| Public message | One template for every fault in the same trust class. Keep paths and user text out. |
| Test count | One behavior test for each exception type that step 2 lists, and one for each fault cause at each split call. |

### Expected Output

- A malformed path returns the coded client rejection. Its message has no path and no server traceback.
- A resource or I/O fault from the same call still returns the server error.
- The server log keeps the detailed cause.
- The regression test for each sibling exception type and each fault cause passes.

## Set a State Label Only After a Clean Verdict

A verdict label starts the checks. Read the check result before you set the label:

- Set the label only when the verdict is clean at the head you reviewed, the head has not moved, the required check passed at that exact commit, and no review thread is open.
- Do not set the label when a check failed or did not run. A failing check stays red, and the label starts more checks.
- Keep any prior verdict label that you have no authority to change. Report that the owner or the automation must flip it.
- Do not rebase a signed pull-request branch only to clear a stale base when the merge state is clean. A rebase rewrites the commits and invalidates the check result at the reviewed head. Leave the synchronization to the owner and report it.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal gateway | A path-based batch intake with a coded rejection envelope | Three regression tests for an embedded NUL byte, a symbolic-link loop, and the request route. All failed before the repair and passed after it. A later review round split the client-cause and server-cause errors at two calls and pinned each cause with a test. See [notes](coded-rejection-boundary-catch-completeness.notes.md). |

## References

- [Python exception hierarchy](https://docs.python.org/3/library/exceptions.html)
- [pathlib resolution and strict mode](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve)
- [Generic error code hides seam type mismatch](generic-error-code-hides-seam-type-mismatch.md)
- [Strip embedded NUL at subprocess egress](subprocess-embedded-null-byte-sanitize.md)