---
name: tooling-subprocess-json-fail-closed-result-validation
license: BSD-3-Clause
description: "Make validators that consume JSON from external CLI tools fail closed instead of treating missing, empty, malformed, or wrong-shaped output as zero findings. Use when: (1) a validator wraps a linter, scanner, compiler, or analyzer through subprocess, (2) findings and tool failures share nonzero exit codes, (3) an exit-zero process can still produce unusable JSON, (4) human and --json CLI modes need honest failure diagnostics and exit status."
category: tooling
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - python
  - subprocess
  - json
  - validation
  - fail-closed
  - external-tools
  - exit-codes
  - stderr
  - ruff
---

# Fail-Closed JSON Result Validation for External Tools

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-05 |
| **Objective** | Prevent an external-tool validator from converting missing targets, tool crashes, empty output, malformed JSON, or invalid result shapes into a successful zero-finding report. |
| **Outcome** | Proposed a reusable boundary contract: normalize finding exit status when the tool supports it, validate inputs before launch, reject every untrustworthy process/result state with a focused exception, and translate that exception honestly at human and JSON CLI seams. |
| **Verification** | unverified — the source and proposed tests were inspected, and the external tool's `--exit-zero` help contract was confirmed locally; the validator changes, focused tests, and CI were not executed. |

## When to Use

- A Python validator runs a linter, scanner, compiler, formatter, or analyzer with `subprocess.run()` and parses JSON from stdout.
- The external tool normally exits nonzero when it finds violations, making findings hard to distinguish from invocation, configuration, or filesystem failures.
- Existing code returns `[]` when stdout is empty or `json.loads()` fails, so an unreliable tool result becomes a false pass.
- A user-supplied target may be missing, but the wrapper currently relies on the external tool's output to reveal that error.
- The CLI supports both human output and `--json`, and automation needs a structured error envelope plus a nonzero exit code on tool failure.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a
> hypothesis until the implementation tests and CI pass.

### Quick Reference

```python
import json
import subprocess
from pathlib import Path
from typing import Any


class ToolReportError(RuntimeError):
    """Raised when an external tool cannot produce a trustworthy report."""

    def __init__(
        self,
        message: str,
        *,
        stderr: str = "",
        returncode: int | None = None,
    ) -> None:
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


def run_json_tool(
    target_arg: str,
    *,
    repo_root: Path,
    command: list[str],
    timeout: float,
) -> list[dict[str, Any]]:
    """Run a JSON-producing tool and reject untrustworthy results."""
    target = Path(target_arg)
    if not target.is_absolute():
        target = repo_root / target
    if not target.exists():
        raise ToolReportError(f"tool target does not exist: {target}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=repo_root,
        timeout=timeout,
    )
    stderr = result.stderr.strip()

    if result.returncode != 0:
        raise ToolReportError(
            f"tool failed with exit code {result.returncode}",
            stderr=stderr,
            returncode=result.returncode,
        )

    output = result.stdout.strip()
    if not output:
        raise ToolReportError("tool returned empty JSON output", stderr=stderr)

    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ToolReportError(
            f"tool returned malformed JSON: {exc}",
            stderr=stderr,
        ) from exc

    if not isinstance(payload, list) or not all(
        isinstance(item, dict) for item in payload
    ):
        raise ToolReportError(
            "tool returned an invalid JSON result shape",
            stderr=stderr,
        )
    return payload
```

### Detailed Steps

1. **Write the outcome truth table before changing code.** Separate valid zero findings, valid findings, process failure, empty output, malformed JSON, and wrong-shaped JSON. Only the first two are report data.

2. **Normalize finding exit status when the tool supports it.** Add the tool's documented flag that returns zero for ordinary findings, such as Ruff's `--exit-zero`. After normalization, any remaining nonzero exit is a tool failure. Do not use this pattern if the tool's flag also hides invocation or configuration failures; verify its documented semantics first.

3. **Validate the target relative to the subprocess working directory.** Resolve relative input against `repo_root` and check existence before launch. Continue passing the caller's original argument when the tool's output paths or CLI behavior depend on that spelling.

4. **Keep stdout and stderr separate.** Parse only stdout as JSON. Preserve stripped stderr as diagnostic data on the focused exception; never merge it into the JSON input stream.

5. **Check process status before parsing.** A nonzero result is a tool failure even if stdout happens to contain JSON. Raise a domain-specific exception with the return code and stderr rather than returning an empty result.

6. **Require a nonempty JSON document on success.** An empty string is not the same as the valid zero-finding payload `[]`. Reject empty or whitespace-only stdout even when the process returned zero.

7. **Validate syntax and result shape.** Catch JSON decoding errors and verify the top-level container plus every item type before accessing fields. If nested fields have required shapes, validate those too. Do not let `dict`, `null`, strings, or primitive list elements masquerade as a report.

8. **Translate the tool exception at public seams without weakening existing contracts.** A Boolean validation helper can catch the exception, print one `[ERROR]` summary and preserved stderr to stderr, and return `False`. Its JSON CLI branch should emit the project's standard status envelope with a nonzero CLI exit and additive diagnostic fields such as `stderr` and `tool_exit_code`.

9. **Test every boundary with a mocked process, then keep real-tool behavior tests.** Mock missing target, nonzero exit, empty stdout, malformed JSON, wrong top-level shape, and wrong item shape. Retain integration-style cases for real `[]` output, real findings, and threshold/configuration behavior so the normalization flag cannot silently suppress report data.

10. **Assert the invocation contract.** Tests should verify the timeout, working directory, JSON-output option, and finding-exit normalization flag. This catches regressions that would make the result-state truth table ambiguous again.

## Verified Workflow

_Not applicable yet._ The actionable methodology is under **Proposed Workflow**.
This placeholder exists for corpus validation and makes no verification claim.
Promote the workflow only after the implementation tests pass; use
`verified-local` for local evidence or `verified-ci` after CI confirms it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Treat empty stdout as no findings | Returned `[]` whenever `stdout.strip()` was empty | Missing targets, launch/configuration failures, and broken tool output could all become a successful validation result | The only trustworthy zero-finding result is a successfully parsed payload with the documented empty shape, such as `[]` |
| Swallow JSON decoding errors | Caught `JSONDecodeError` and returned `[]` | Human diagnostics, truncated output, and tool regressions were indistinguishable from a clean scan | Malformed JSON is a tool-report failure and must preserve context for the caller |
| Parse stdout without checking return code | Used whatever stdout contained regardless of process status | A tool can emit partial or diagnostic-shaped output while failing; parsing it can hide the actual failure | Normalize ordinary finding exits, then reject every remaining nonzero process result before parsing |
| Let the tool discover a missing target | Passed a nonexistent path and inferred success from empty stdout | Tool versions can vary in exit/output behavior, and the wrapper lost a precise operator error | Resolve and validate explicit targets before invoking the external process |
| Validate only JSON syntax | Accepted any value returned by `json.loads()` and iterated it as findings | Valid JSON can still violate the report schema: objects, nulls, strings, or primitive items are not finding records | Validate both the top-level container and item/nested shapes before constructing domain results |
| Emit human text in JSON mode | Printed an error diagnostic and returned failure without a stable JSON object | Machine consumers had to parse stderr or path-dependent text and could misclassify the command | Emit the established structured error envelope on stdout and return a nonzero CLI exit |

## Results & Parameters

### Result-state contract

| Process/result state | Classification | Public Boolean | JSON CLI exit |
| -------------------- | -------------- | -------------- | ------------- |
| Target exists, exit `0`, stdout is valid empty result (`[]`) | Clean report | `True` | `0` |
| Target exists, normalized exit `0`, stdout contains valid finding records | Findings | `False` | Nonzero finding exit, commonly `1` |
| Target missing | Tool/input failure | `False` with stderr diagnostic | `1` with error envelope |
| Process exits nonzero after finding-exit normalization | Tool failure | `False` with preserved tool stderr | `1` with tool return code field |
| Process exits `0` with empty stdout | Tool-report failure | `False` | `1` |
| Process exits `0` with malformed or wrong-shaped JSON | Tool-report failure | `False` | `1` |

### Ruff complexity example

Ruff's documented `--exit-zero` option keeps findings in JSON but returns zero when
findings are present. A complexity wrapper can therefore use this command shape:

```bash
python -m ruff check \
  --select=C901 \
  --config=lint.mccabe.max-complexity=<threshold> \
  --output-format=json \
  --exit-zero \
  <target>
```

Interpretation after adding `--exit-zero`:

```text
exit 0 + []                  -> trustworthy zero findings
exit 0 + [finding, ...]      -> trustworthy complexity findings
exit nonzero                 -> Ruff failure, regardless of stdout
exit 0 + empty/malformed JSON -> untrustworthy Ruff report; fail closed
```

Recommended machine-readable failure shape for a status-oriented CLI:

```json
{
  "status": "error",
  "exit_code": 1,
  "message": "tool failed with exit code 2",
  "stderr": "tool diagnostic",
  "tool_exit_code": 2
}
```

Recommended focused test matrix:

```text
missing target; nonzero exit; empty stdout; malformed JSON; wrong top-level
shape; wrong item shape; stderr propagation; JSON envelope; timeout/flags;
real zero findings; real findings; real configuration or threshold behavior
```

Related skills cover adjacent but distinct boundaries:

- `bash-stderr-jq-separation` covers channel separation for Bash plus `jq`.
- `cli-json-flag-emitter-selection-status-vs-data` covers choosing a CLI JSON emitter.
- `automation-codex-jsonl-fail-closed-routing` covers agent-provider JSONL events.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Proposed Ruff complexity-validator hardening | Existing source was inspected and Ruff's `--exit-zero` help semantics were confirmed locally. The implementation, focused tests, and CI were not run, so the skill remains `unverified`. |
