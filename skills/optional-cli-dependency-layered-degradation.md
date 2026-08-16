---
name: optional-cli-dependency-layered-degradation
license: BSD-3-Clause
description: "Use when: (1) a containerized validation path crashes because an optional system binary is absent, (2) Python converts the missing binary into a domain result but a shell caller still treats that result as fatal, (3) required and optional command dependencies need explicit, observable preflight behavior."
category: ci-cd
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [ci, subprocess, optional-dependency, command-v, graceful-degradation, containers]
---

# Optional CLI Dependency Layered Degradation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Keep optional external commands from crashing validation while preserving fail-closed behavior for required commands and real validation failures. |
| **Outcome** | Missing-command handling became explicit at both the Python subprocess boundary and the shell orchestration boundary; local validation passed. |
| **Verification** | verified-local |

## When to Use

- A minimal CI image raises `FileNotFoundError` for a command available on developer machines.
- A Python helper catches the missing command, but its shell caller still exits non-zero on the translated domain result.
- A validation suite includes an optional enhancement that should skip observably when unavailable.
- You need to distinguish "tool absent" from "tool present but validation failed."

Do not use graceful degradation for a command that defines the validity of the required gate. Install it, replace it with a portable validator, or fail with a clear preflight error instead.

## Verified Workflow

### Quick Reference

```python
try:
    result = subprocess.run(
        [tool, "--check", str(target)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
except FileNotFoundError as exc:
    raise OptionalToolUnavailable(tool) from None
except subprocess.CalledProcessError as exc:
    raise ValidationFailed(exc.stderr) from exc
```

```bash
if command -v optional-tool >/dev/null 2>&1; then
  python -m package.optional_validation
else
  echo "SKIP: optional-tool is not installed" >&2
fi
```

### Detailed Steps

1. Classify the command as required or optional before changing error handling. A missing required validator must remain fatal.
2. At the Python boundary, catch only expected process failures. Translate a missing executable separately from a non-zero validation result so callers can preserve the distinction.
3. Use `raise ... from None` when intentionally replacing `FileNotFoundError` with a concise domain diagnostic; this also satisfies exception-chaining lint rules.
4. At a shell orchestration boundary, preflight an optional executable with `command -v`. Emit an explicit skip message and avoid invoking a path that cannot succeed.
5. Do not let the shell guard suppress a real failure. When the executable exists, propagate the Python validator's exit status unchanged.
6. Add negative controls for both states: command absent should produce the documented skip, while a fake present command that exits non-zero must still fail.
7. Run the validation inside the same minimal container or CI image whose dependency surface triggered the problem.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Catch the Python exception only | Translated `FileNotFoundError` inside the helper | The shell caller still classified the translated result as a hard validation failure | Optionality is an end-to-end contract; every orchestration layer must preserve it. |
| Add only a shell `command -v` guard | Skipped the top-level invocation when the command was absent | Direct Python callers and alternate entrypoints still crashed | Defend the subprocess boundary as well as the known shell boundary. |
| Append `|| true` | Suppressed every failure from the validation command | Real invalid input and tool defects became false successes | Skip only the proven absent-optional-tool case; propagate all other failures. |
| Treat every missing command as optional | Converted an absent required validator into a passing job | The CI gate became vacuous | Decide required versus optional first and keep required checks fail-closed. |

## Results & Parameters

### Exit Contract

| Condition | Required tool | Optional tool |
| --------- | ------------- | ------------- |
| Executable absent | Fail with installation guidance | Emit an observable skip and continue |
| Executable returns non-zero | Fail | Fail |
| Executable times out | Fail or retry under an explicit policy | Fail or retry under an explicit policy; never convert it to an absence skip |
| Executable succeeds | Continue | Continue |

### Verification Harness

```bash
# Missing case: PATH contains no optional-tool; expect SKIP and exit 0.
PATH="<minimal-bin-dir>" <validation-script>

# Present-but-broken case: prepend a fake executable that exits 1; expect failure.
PATH="<fake-bin-dir>:$PATH" <validation-script>
```

Successful verification proves that absence is the only soft path and that an available but failing tool cannot be mistaken for success.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private Python validation repository | Minimal-container dependency gap | The Python and shell boundaries were corrected together and the repository's local validation suite passed; identifying details were intentionally generalized. |

## References

- [PR enumeration and subprocess soft-fail contracts](pr-enumeration-discovery-idempotency.md)
- [Binary-free CI validators](ci-config-validators-binary-free-python.md)
