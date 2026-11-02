---
name: shell-tty-interactivity-verification
description: "Detect terminal interactivity in a shell script with a subshell open of /dev/tty, never with test -r/-c /dev/tty, which is always true, and verify both branches of TTY-gated CLI behavior with a pty (printf | script -qec) for the interactive path and setsid with stdin from /dev/null for the non-interactive path. Use when a shell script decides on prompts or confirmations from terminal presence, when test -r /dev/tty or test -c /dev/tty is used as the interactivity check, or when a functional check must prove an interactive path really prompts and a headless path never prompts or hangs."
category: tooling
date: 2026-10-31
version: "1.0.0"
user-invocable: false
license: BSD-3-Clause
tags: [bash, shell, tty, dev-tty, controlling-terminal, interactivity-detection, script-pty, setsid, prompt-gating, onboarding-script, functional-verification]
---

# Shell TTY Interactivity Detection and Functional Verification

**Supporting cases:** [notes](./shell-tty-interactivity-verification.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-31 |
| **Objective** | Detect terminal interactivity correctly in a shell script, and verify with a functional check that an interactive path prompts on a terminal and a non-interactive path never prompts or hangs. |
| **Outcome** | Successful: `test -r/-c /dev/tty` (always true) replaced by a subshell open of `/dev/tty` as the interactivity test; the interactive branch verified under a pty (`script(1)`) and the non-interactive branch verified under `setsid` with stdin from `/dev/null`. |

## When to Use

- A shell script decides on prompts, confirmations, or interactive UI from
  terminal presence, and you must write or review that decision.
- `test -r /dev/tty`, `test -c /dev/tty`, or a comparable `access(2)`-based
  check on `/dev/tty` is used as the interactivity test.
- An onboarding, setup, or wrapper script has both an interactive path and a
  non-interactive path, and a functional check must prove each path behaves.
- A harness run gives false evidence because the prompt decision passed on a
  host without a terminal.

## Verified Workflow

### Quick Reference

- Detection: a subshell that tries to open `/dev/tty`. It succeeds only with a
  controlling terminal.

```bash
if (exec 9<>/dev/tty) 2>/dev/null; then
    interactive=1
else
    interactive=0
fi
```

- Interactive verification: allocate a pty and pipe the answers.

```bash
printf 'y\n' | script -qec <command> /dev/null
```

- Non-interactive verification: remove the controlling terminal and stdin.

```bash
setsid <command> </dev/null
```

Never use `test -r /dev/tty` or `test -c /dev/tty` for interactivity. `/dev/tty`
has mode 0666 (`crw-rw-rw-`) on common systems, so `access(2)` succeeds even
when the process has no controlling terminal: the check is always true.

### Suggested Approach

1. Write or repair the interactivity decision. An open of `/dev/tty` fails
   with `ENXIO` ("no such device or address") when the process has no
   controlling terminal, so the subshell-open test in the Quick Reference is
   the boundary between the two paths. Do the open in a subshell so a failed
   open cannot leave a broken descriptor in the caller.
2. `[ -t 0 ]` and `[ -t 1 ]` answer a different question: they test whether a
   descriptor is a terminal, not whether the process has a controlling
   terminal. Use them only for stream routing (for example color or pager
   decisions), not as a prompt-suppression decision for a script that reads
   answers from `/dev/tty` directly. For that separate problem, remove the
   controlling terminal as in
   [bash-noninteractive-installer-wrapper](bash-noninteractive-installer-wrapper.md).
3. Verify the interactive branch under a pty. `printf 'y\n' | script -qec <cmd>
   /dev/null` gives the command a controlling pty and feeds the answers as
   terminal input, so a prompt read from `/dev/tty` receives the answer.
4. Verify the non-interactive branch under a removed session. `setsid <cmd>
   </dev/null` starts the command in a new session without a controlling
   terminal and without terminal stdin. A correct non-interactive run completes
   with no prompt read: any attempt to open `/dev/tty` fails loudly with
   "no such device or address".
5. Assert on observed behavior, not on the predicate: the interactive
   transcript must show the prompt and the piped answer consumed, and the
   `setsid` run must complete without a prompt line and without a hang. Route
   evidence this way so a check cannot pass on a false predicate.
6. `script(1)` flag forms (`-qec`) are the util-linux form. When that form is
   unavailable, allocate the pty with an equivalent tool (for example the
   Python `pty` module) and keep the same two assertions.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | `test -r /dev/tty` (and `test -c /dev/tty`) as the interactivity test in a functional check of a prompt gate. | `/dev/tty` is mode 0666 (`crw-rw-rw-`), so `access(2)` succeeds on a host with no controlling terminal; the check was true in every run, including headless runs. | `access(2)` success on `/dev/tty` does not imply a controlling terminal. Detect interactivity by an open of `/dev/tty` in a subshell, which fails with `ENXIO` without one. |
| Attempt 2 | Verify the interactive branch with piped input only, for example `printf 'y\n' \| <cmd>` on the host terminal or harness stream. | A prompt that reads from `/dev/tty` does not read piped stdin; with no controlling terminal the read fails, so the interactive branch is never exercised and the check is vacuous for the prompt path. | Exercise prompt reads from `/dev/tty` under a pty from `script(1)`; pipe answers only after the pty exists. |

## Results & Parameters

### Configuration

```bash
# Predicate: 0 = no controlling terminal, 1 = interactive.
if (exec 9<>/dev/tty) 2>/dev/null; then interactive=1; else interactive=0; fi

# Positive probe: must show the prompt and consume the piped answer.
printf 'y\n' | script -qec <command> /dev/null

# Negative probe: must complete with no prompt line and no hang.
setsid <command> </dev/null
```

### Expected Output

- Positive probe: the transcript shows the prompt text and the piped answer,
  and the command follows its confirmed path.
- Negative probe: the command completes without a prompt. An unguarded read
  from `/dev/tty` fails with `/dev/tty: No such device or address` (`ENXIO`),
  which distinguishes "never prompts" from "prompted and blocked".

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Repository onboarding script harness (privacy-generalized) | Functional verification of an interactive confirm step in a setup script; local probes on a headless Linux host reproduced each predicate result in this skill | [notes](./shell-tty-interactivity-verification.notes.md) |

## References

- `setsid(1)`, `setsid(2)`, `script(1)`, `access(2)` manual pages; `ENXIO` on
  `/dev/tty` open without a controlling terminal.
- [bash-noninteractive-installer-wrapper](bash-noninteractive-installer-wrapper.md)
  — same mechanism, different intent: it removes the controlling terminal so an
  upstream installer takes its non-interactive path. This entry decides and
  verifies interactivity for a script's own prompts.
- [shell-wrapper-container-detection](shell-wrapper-container-detection.md) —
  terminal checks used to route container `exec` flags; adjacent vocabulary,
  unrelated decision.
