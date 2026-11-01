---
name: typed-boundary-cause-diagnostic-on-exit
description: "Add the exception cause to a typed boundary that reports one fixed failure sentence. Use when several distinct failures collapse into the same message and exit code, or when a CI job fails with no attributable cause."
category: debugging
date: 2026-11-01
version: "1.0.0"
user-invocable: false
tags: [diagnostics, exception, ci, fail-closed, stderr, exit-code, traceability]
---

# Report the Exception Cause at a Typed Boundary

## Overview

| Field | Value |
| ------- | ----- |
| **Date** | 2026-11-01 |
| **Objective** | Make a typed fail-closed boundary name the exception that caused the failure. |
| **Outcome** | Each distinct cause prints a distinct reason. The stable sentence, the exit code, and the output artifacts do not change. |

## When to Use

- One `except` tuple catches several classes, then prints one fixed sentence and returns a failure code.
- A job fails, and the log shows that sentence only. You cannot assign the failure to an owner.
- A parser or validator raises one typed error for many causes, so the cause is not visible.
- You must keep the old message, the exit code, or the machine-readable output for a consumer.

Do not use this skill when a traceback is already printed. The traceback names the cause.

## Verified Workflow

### Quick Reference

```python
except (ValueError, OSError, KeyError, TypeError) as error:
    print("Evidence is incomplete or invalid.", file=sys.stderr)
    print(f"Why: {type(error).__name__}: {error}", file=sys.stderr)
    return 1
```

Add one line. Keep the first line byte-identical. Keep the return code. Write the new line to stderr.

### Suggested Approach

1. Find the boundary that prints one sentence. Get the exception object with `as error`.
2. Print the type name and the message on a second line. Use `type(error).__name__` and `error`.
   The message of a type the code raises itself can repeat the fixed sentence. The type name
   is still a distinct signal.
3. Send the new line to stderr. Do not change stdout, exit codes, or output files. A CI step
   that parses an artifact cannot then break.
4. List each consumer of the boundary. Confirm each one reads the exit code or an output file,
   and none parses the sentence. If a consumer parses stderr, stop. Use structured output instead.
5. Confirm the code does not print a secret, a credential, or untrusted payload in the message.
   A message from an untrusted source can contain data that the boundary redacts everywhere else.
6. Run the input that failed. Confirm the new line names the cause and the exit code is the same.

A unit test is optional. Repository policy can reserve tests for library behavior. Static
evidence is sufficient here: the consumer list, the unchanged first line, and one probe run
of the failing input.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Add an error field to the output record | Extended the machine-readable record with a cause field. | The record schema rejected unknown keys and failed closed. The fix caused a new failure. | Keep diagnostics on stderr. Do not change the validated record. |
| Print the traceback | Replaced the sentence with a full traceback. | Consumers and operators lost the stable sentence they match and report on. | Keep the stable line. Add the cause beside it. |

## Results & Parameters

### Configuration

```yaml
boundary_diagnostic:
  first_line: unchanged
  cause_line: "Why: {type_name}: {message}"
  stream: stderr
  exit_code: unchanged
  output_files: unchanged
  redaction: no secret, credential, path, or payload in the message
```

### Expected Output

```text
Evidence is incomplete or invalid.
Why: FileNotFoundError: [Errno 2] No such file or directory: '.../absent.json'
```

- The first line is byte-identical to the previous output.
- The second line names the exception class and its message.
- The exit code is still `1`.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| General automation | CI shard runner with one fixed failure sentence | Focused suite passed. Four workflow consumers read only exit codes and artifact files. A missing-input probe printed the cause line and exited `1`. |

## References

- [Python exception hierarchy](https://docs.python.org/3/library/exceptions.html)
- [Preserve Primary Failure Diagnostics](preserve-primary-failure-diagnostics.md)
- [Parse Boundary: Typed Error Context Needs Safe Access](parse-boundary-error-context-safe-access.md)