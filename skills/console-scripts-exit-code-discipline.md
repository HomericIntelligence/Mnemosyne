---
name: console-scripts-exit-code-discipline
license: BSD-3-Clause
description: "Enforce exit-code discipline for Python console-script main() functions without breaking existing return-value contracts. Use when a CLI exits 0 despite recoverable errors, helper methods have tuple-return callers, cumulative error state must be tracked through instance state instead of changing signatures, or many console scripts must route failures through one shared boundary."
category: architecture
date: 2026-05-28
version: "2.1.0"
user-invocable: false
verification: verified-local
tags: [python, console-scripts, exit-codes, error-tracking, instance-state, tuple-contracts, cli, ci-cd, error-boundary, assert-migration]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/console-scripts-exit-code-discipline.history"
history-cleanup-date: "2026-09-20"
---

# Console Scripts Exit-Code Discipline

## Overview

A console script that exits `0` after recoverable read/write/validation errors trains CI and shell callers to trust failures. The fix must expose a nonzero process exit while preserving existing helper return contracts that tests and callers already unpack.

This skill consolidates the exit-code discipline and instance-state error-tracking memories. The canonical pattern is: keep public tuple returns stable, record cumulative failure on the instance, and have `main()` return the final exit code consumed by `sys.exit()`.

A shared boundary wrapper generalizes the same contract for many scripts at
once. The wrapper is one module that maps an exception to one exit code and one
stderr line. Each script becomes a thin function that passes its real work to
the wrapper.

| Field | Value |
|-------|-------|
| Date | 2026-07-04 |
| Objective | Generalize console-script exit-code discipline and preserve tuple-contract compatibility details. |
| Outcome | Canonical v2 replaces the narrower instance-state skill; notes and source snapshots are preserved in history. |
| Verification | verified-local for this consolidation; source examples preserve their original verified-ci status in history. |

## When to Use

- A console-script entrypoint calls `sys.exit(0)` unconditionally or returns `None` despite recoverable errors.
- A helper method returns a fixed-shape tuple that existing tests or callers unpack.
- You need cumulative error state across multiple helper calls without changing public method signatures.
- A pre-commit, CI, or shell pipeline can miss failures because a CLI always exits success.
- You are considering expanding tuple shapes, adding error-tracker parameters, or creating a wrapper class solely to carry exit state.
- Many registered scripts each carry their own report-path `except` block, and a refactor must route all of them through one shared boundary.
- You remove a report-path `except` that printed a message and exited, and in-process tests call the entry point directly.
- `argparse` raises `SystemExit` and you must decide whether the wrapper keeps or absorbs it.

## Verified Workflow

### Quick Reference

```python
import sys


class Processor:
    def __init__(self, paths: list[str]) -> None:
        self.paths = paths
        self.had_error = False

    def process_file(self, path: str) -> tuple[bool, dict[str, object] | None]:
        try:
            data = self._read(path)
        except OSError:
            self.had_error = True
            return False, None
        return True, data

    def main(self) -> int:
        for path in self.paths:
            self.process_file(path)
        return 1 if self.had_error else 0

if __name__ == "__main__":
    raise SystemExit(Processor(sys.argv[1:]).main())
```

### Route many scripts through one shared boundary

1. Find each registered entry: `rg -A20 '^\[project.scripts\]' pyproject.toml`.
   Build a census of the target module and function of each entry.
2. Write or reuse one boundary function that takes an entry callable. It must
   catch the exception classes, write one stderr line, and return an exit code.
3. Put the current script body in a private `_run` function that returns `int`.
   Keep the public `main` name, because the entry point names it:
   `def main() -> int: return boundary_main(_run)`.
4. Keep the `SystemExit` pass-through in the boundary. `argparse` raises
   `SystemExit` for `--help` (code 0) and for a usage error (code 2). A wrapper
   that absorbs `SystemExit` changes both codes.
5. Replace a report-path `except` that printed a message and called
   `sys.exit(n)` with a plain call. The helper now raises, and the boundary
   reports it. This changes the exit code. Record the old code and the new code.
6. Confirm the wiring per entry, not per module. A module can import the
   boundary and still leave one entry unmapped when the entry names a
   re-exported function or a package attribute.
7. Update in-process tests. A test that called `main()` inside
   `pytest.raises(SystemExit)` now calls `main()` and asserts the return code.
   A test that expected the removed report message asserts the boundary text.

### Quick Reference for the wrapper

```python
def boundary_main(entry, /, *args, stream=None, **kwargs) -> int:
    try:
        result = entry(*args, **kwargs)
    except SystemExit as exit_request:          # argparse owns these codes
        code = exit_request.code
        return 0 if code is None else code if isinstance(code, int) else 1
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        (stream or sys.stderr).write(format_error(error).text)
        return int(format_error(error).exit_code)
    return result if isinstance(result, int) else 0
```

### Suggested Approach

1. Find console entrypoints that mask errors: `rg 'sys\.exit\(0\)|def main\(.*\) -> None' <package>/`.
2. Identify helper methods with tuple-return callers before changing contracts: `rg 'method_name\(.*\)' tests/ <package>/` and inspect unpacking sites.
3. Add `self.had_error: bool = False` or a similarly named instance attribute in `__init__`.
4. Set the flag at every recoverable error site: file read, file write, validation, missing input, or processing errors that should not immediately abort.
5. Preserve existing helper signatures and tuple shapes. Return the same tuple shape callers already expect.
6. Change `main()` to return `int`; compute `1 if self.had_error else 0` after processing.
7. Make the entrypoint consume the returned code exactly once: `sys.exit(main())` or `raise SystemExit(main())`.
8. Add tests for success exit `0` and error exit nonzero without rewriting unrelated tuple-callsite tests.

For the shared-boundary case, add one wiring test for one representative
script. Do not add a test for each entry. The census command in step 6 is the
evidence for the rest.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| Expand tuple return shape | Changed a helper from a 2-tuple to a 3-tuple carrying error state. | Existing tests and callers unpacked the 2-tuple, causing broad churn. | Track CLI error state outside stable helper return contracts. |
| Add error-tracker parameters | Threaded an extra parameter through helper methods. | It required many callsite edits for a CLI-only concern. | Use instance state when the state belongs to the object lifecycle. |
| Re-raise recoverable errors at the end | Collected errors and raised after processing. | It complicates tests and obscures which path set the final exit code. | Let helpers set state and let `main()` make one exit decision. |
| Add a wrapper CLI class | Split processing and CLI exit behavior into separate classes. | It duplicated processing methods and increased maintenance. | One class can support tuple-return helper use and CLI exit-code use. |
| Return an exit code but keep `sys.exit(0)` | Computed a code in `main()` but the entrypoint still exited success. | The parent process never saw the computed failure. | There must be one final exit-code decision point. |
| Use global error state | Considered module-level `_had_error`. | Globals are harder to isolate in tests and unsafe for concurrent use. | Prefer instance state scoped to the processor. |
| Let the shared boundary absorb `SystemExit` | The wrapper caught the broad exception class only, and it was changed to catch and report everything. | `--help` and usage errors lost their codes. The usage code became the generic error code. | Pass `SystemExit` through unchanged; `argparse` owns codes 0 and 2. |
| Wire the boundary by module, then trust a module-level grep | Checked that each module imported the boundary, and stopped. | One entry mapped to a package attribute. The census reported it unwired. | Verify every entry target resolves to a function that calls the boundary. |
| Move the entry logic without checking import order | Renamed `main` and put the import at the point of use. | Deferred imports and names that shadow a parameter broke at import time. | Put the boundary import at module top with the other local imports. |

## Results & Parameters

Implementation checklist:

```yaml
exit_code_contract:
  success: 0
  recoverable_error: 1
boundary_contract:
  system_exit: pass_through   # argparse owns 0 (help) and 2 (usage)
  keyboard_interrupt: 130
  generic_failure: report_one_stderr_line
compatibility_contract:
  preserve_helper_signatures: true
  preserve_tuple_shapes: true
state_location:
  preferred: instance_attribute
  avoid: [global_flag, tuple_shape_expansion, wrapper_duplication]
entrypoint:
  main_returns: int
  final_call: sys.exit(main())
tests:
  per_script_wiring_test: one_representative_only
  in_process_assertion: assert main() == code
```

Search commands:

```bash
rg 'sys\.exit\(0\)|def main\(.*\) -> None' hephaestus/ tests/
rg 'fix_file|process_file|validate' tests/ hephaestus/
rg -A20 '^\[project.scripts\]' pyproject.toml   # entry census
rg -n 'boundary_main' hephaestus/               # wiring census
```

Historical outcome (issue #632 in the source project):

| Module | Change | Verification |
|---|---|---|
| markdown fixer | Added instance `had_error`, set it at read/write/validation failures, returned nonzero from main. | 119 tests passed. |
| system info | Normalized `main() -> int`. | CI green. |
| dataset downloader | Returned exit code instead of exiting internally. | CI green. |

Shared-boundary rollout outcome:

| Item | Value |
|---|---|
| Entry census | 57 entries; 7 were wired before the change; 50 were wired by the change. |
| Report-path `except` removed | 2, in two validation modules. |
| In-process tests updated | 7 return-code assertions and 1 raised-exception assertion. |
| Exit-code drift | 1 module changed 2 to 1; 1 module changed a printed line to a raised error. |