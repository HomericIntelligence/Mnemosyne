---
name: bash-exported-function-child-reach
description: "Diagnose and prevent unbound-variable crashes inside bash functions that run in a child bash process. Use when: (1) removing an exported environment variable that an exported function or a backgrounded child reads, (2) a child reports an unbound variable at a line number that does not match the file, (3) a test harness runs only a slice of a generated script, so top-level assignments never execute, or (4) a stub must read data that a migration moved from the environment to a file."
category: debugging
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - bash
  - export-f
  - set-u
  - unbound-variable
  - child-process
  - environment-removal
  - script-serialization
  - test-harness
  - stub-fidelity
  - migration
---

# Exported Bash Functions and Child-Process Reach

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Keep child bash processes working when environment transport is replaced with script locals, arguments, or files. |
| **Outcome** | Operational. An unbound-variable crash in a child bash process was traced to a removed export, fixed in the script and in the harness. |

## When to Use

- You remove or rename an environment variable while a script uses `export -f` or runs `bash -c` children.
- A child process exits with a kill status, and a test reports a missing marker file, not a message.
- An unbound-variable message names a line number that does not match the file text.
- A harness executes only a slice of a generated script, starting below the variable assignments.

This entry applies to the same failure mode as the retired uninitialized-array entry. An unbound
variable under `set -u` in a child is a reach problem, not an array-initialization problem.

## Verified Workflow

### Quick Reference

Before you delete an export, list every variable the child reads. Each one must be exported,
passed as an argument, or read from a file:

```bash
# Find the variables a child function reads.
sed -n '/^my_child() {/,/^}/p' script.sh \
  | grep -oE '\$\{?[A-Za-z_][A-Za-z0-9_]*' | sed 's/\${\?//;s/}$//' | sort -u
```

### Suggested Approach

1. **Get the real error.** Export `SHELLOPTS=xtrace` and set `PS4='+L${LINENO}+ '`, or capture the
   child's standard error. A bare exit code or a missing artifact does not identify the cause.
2. **Do not trust the reported line number.** Bash serializes an exported function onto fewer lines
   than the file has. Confirm the cause with `declare -f my_function` in a child, which prints the
   text that the child actually runs, then read that line.
3. **Separate the two causes.** A parent-only variable is a script defect: export it, pass it as an
   argument, publish it to a file, or mark its read optional with `${var:-}`. A missing assignment
   because a harness ran only a slice is a harness defect: supply the value in the harness
   environment.
4. **Apply the reach rule in the script.** A value that crosses a `bash -c` boundary must be
   exported in the parent. A value that crosses the double-quoted `bash -c` vector applies in two
   steps: export it in the parent function, and read it as a variable, not a literal.
5. **Keep stub fidelity.** When a migration moves data from the environment to a file, update the
   stub to read the file. A stub that keeps the old read reports a false negative.
6. **Re-run the child case alone.** A passing sibling case does not prove the fix, because the
   failure can depend on the end path or the signal.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Read the file at the reported line number. | The child ran serialized function text, so the line number pointed at a different command. | Use `declare -f` to read the child's copy of the function. |
| Attempt 2 | Export the parent variable and re-run immediately. | The harness ran only a slice of the script, so the export never executed in the test. | Fix the script and the harness separately. |
| Attempt 3 | Keep the stub reading a variable inside a quoted argument. | The quoted argument is one child word, so the stub read `None`. | Read moved data from its new source. |

## Results & Parameters

### Configuration

```bash
set -uo pipefail          # the child aborts on an unset variable read
export value_name          # parent export for a child bash -c
export -f child_function   # function reaches the child
```

### Expected Output

- The child runs the function and writes its markers.
- One `.json` evidence file per child name exists.
- The exit status is 0, or the intended non-zero status.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private repository | Four-node batch render tests | See [notes](bash-exported-function-child-reach.notes.md). |

## References

- Bash manual, "Functions" (`export -f`, and the function serialization format)
- Bash manual, "The Set Builtin" (`-u`, `-f`)
- [tooling-safety-wrapper-invocation-contract.md](tooling-safety-wrapper-invocation-contract.md)