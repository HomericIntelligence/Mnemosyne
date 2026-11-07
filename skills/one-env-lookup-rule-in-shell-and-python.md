---
name: one-env-lookup-rule-in-shell-and-python
license: BSD-3-Clause
description: "Keep one environment-derived path identical in a shell launcher and the Python code that calls or is called by it. Use when: (1) you replace a hard-coded temporary base with a platform lookup, (2) a shell script and Python both derive the same scratch, stage, or cache path, (3) the caller runs a child with a scrubbed environment, or (4) a script must pass a path down a positional interface that the child also derives."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [tempfile, gettempdir, tmpdir, temp, tmp, shell, python, fallback-chain, environment-contract, scrubbed-environment, positional-interface, file-descriptor-handoff, staging]
---

# One Environment Lookup Rule Across Shell and Python

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Use one rule for an environment-derived path, so a shell launcher and its Python caller or callee name the same directory on every host. |
| **Outcome** | Operational. The decision rule comes from a planning review of a three-site temporary-base change. The change did not go to implementation yet; the rule is verified against the source layout of the affected repository. |

## When to Use

- You replace a hard-coded temporary or scratch base (`/tmp`, a fixed cache root) with a platform lookup.
- A shell script and Python code derive the same scratch, stage, dependency-cache, or lock path.
- A Python caller starts a shell function with a scrubbed environment, so variables from the user session do not reach the shell.
- A script accepts a path through its positional interface while its parent already knows that path.
- A review asks which value wins when two environment variables name different directories.

## Verified Workflow

### Quick Reference

Pick one rule and give it one owner:

```text
base = first usable of TMPDIR, TEMP, TMP; else the platform default.
```

- Python: `tempfile.gettempdir()` already implements this order, a writability probe, and a per-process cache.
- Shell: implement the same order with a `-d -w -x` probe in one function, then **export** the resolved value as `TMPDIR` before you start any Python child.

```bash
pick_base() {
  for candidate in "${TMPDIR:-}" "${TEMP:-}" "${TMP:-}"; do
    [[ -n "$candidate" && -d "$candidate" && -w "$candidate" && -x "$candidate" ]] || continue
    printf '%s\n' "$candidate"; return 0
  done
  printf '/tmp\n'
}
```

### Suggested Approach

1. List every reader of the base: each shell function, each Python call site, each test fake that imitates a script. The rule applies to the whole list, not only the site named in the bug report.
2. Choose the narrower reader as the owner. Python already owns `gettempdir()` semantics; do not copy a shorter shell order such as `${TMPDIR:-/tmp}` next to it. That order ignores `TEMP` and `TMP`, so the two readers disagree on the host that sets only one of them.
3. Close the gap with an export. Resolve the base once in the shell entry point and export it as `TMPDIR`. Every Python child then resolves the identical value, because `TMPDIR` is the first candidate that `gettempdir()` reads.
4. Check the environment of every child process. A caller that starts a shell function with a scrubbed environment (for example, only `PATH` and `HOME`) prevents the shell from reading the user's variables. In that path, the caller must send the resolved directory explicitly, or send a handle that names it.
5. Prefer a handle that the child already receives. If the caller opens the directory and passes a directory file descriptor, the child can read the path from the handle and keep the identity check that compares device and inode. This removes one new positional argument and one duplicated fact. Use a new argument only when no existing handle names the directory.
6. Keep cleanup safe. When the script deletes the derived directory, keep the delete expression to one variable, keep an exclusive create (no parent creation) for entry-point runs, and require the derived suffix to be script-generated.
7. Prove the change with a regression pair: derive test expectations from the same helper, run the tests before the production change to record the failure, then run them again after. Add a guard leg that shows the old refusal still occurs for a base the guard must refuse.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Change one implementation only | Replaced the literal in the Python sites and left the shell and the test fake unchanged | The shell keeps its own literal or partial order, so the stage path and the stage owner name different directories | State one rule and apply it to the shell, the Python sites, and every test fake |
| Use the short shell form | Wrote the base as the first temporary variable with the platform default | It ignores the two other upper-case variables, so the defect stays on a host that sets only those | Match the full candidate order, or export the Python-resolved value |
| Repeat the path through a new positional argument | Added an optional argument that carried a path the child could already read from its directory descriptor | Two sources for one fact, a placeholder in the middle of the call, and edits at every call site | Derive the path from the existing handle and keep the identity check |
| Prove the repair with a world-writable fixture below a private parent | Ran the staging tests with the base set to that fixture | The guard refuses that fixture for the same ancestor reason, so the run does not show the defect | Use tests-first failure evidence, and keep the guard leg only as a separate check |

## Results & Parameters

- `tempfile.gettempdir()` cache: the value is fixed at the first call in a process. A test that changes `TMPDIR` must also reset `tempfile.tempdir`.
- Shell probe: `-d -w -x` is a close approximation of the Python writability probe. Access-control edge cases can select a different candidate. The export in step 3 removes the effect for all children.
- Descriptor handoff: on Linux, `/proc/self/fd/<n>` resolves to the opened directory. Keep the device and inode comparison against the handle.

See [notes](one-env-lookup-rule-in-shell-and-python.notes.md) for the evidence behind these rules.