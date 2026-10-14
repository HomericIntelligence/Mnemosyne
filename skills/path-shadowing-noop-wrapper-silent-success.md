---
name: path-shadowing-noop-wrapper-silent-success
license: BSD-3-Clause
description: "Diagnose and repair an earlier PATH entry that shadows a system command with a script that exits 0 without running it. Use when a command reports success but produces no output and no effect."
category: debugging
date: 2026-10-14
version: "1.0.0"
user-invocable: false
tags:
  - path
  - shim
  - wrapper
  - exit-code
  - silent-failure
  - shell
  - sourcing
  - strace
  - execve
---

# PATH-Shadowing Wrapper Reports Success Without Running Anything

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-14 |
| **Objective** | Explain how a wrapper script placed earlier on `PATH` under a coreutils name can swallow every invocation of that command, report exit 0, and leave the caller with no error and no effect |
| **Outcome** | Success — root cause identified by execve tracing, wrapper repaired, invocation verified on the launching host and on a remote batch-scheduler node |

## When to Use

Trigger this skill when:

- A command exits 0, prints nothing, and produces no side effect, and the caller therefore reports success.
- A wrapper script, launcher, or session tool "starts" but never reaches the program it claims to run.
- A step that runs on a remote node behaves differently from the same step run locally.
- A shell profile sources a script whose purpose is to adjust `PATH`, and you need to know whether that script can also execute.
- You are about to rewrite a correct caller to work around a symptom. Verify the resolution path first.

Do NOT use when the failing command is absent rather than shadowed. Use your shell's command-not-found guidance. A wrapper that runs and reports an error is a different failure; use the tool's own diagnostics.

## Verified Workflow

### Quick Reference

```bash
# 1. What does the name resolve to? List every candidate, in search order.
type -a env

# 2. Is the winner a script, and where does it live?
command -v env
head -1 "$(command -v env)"
file "$(command -v env)"

# 3. Did the intended program run at all? Exit 0 proves nothing.
strace -f -e trace=execve <command> 2>&1 | grep execve
```

An absent `execve` for the intended program is the proof. A zero exit status is not evidence, because the wrapper itself succeeds.

### Suggested Approach

1. **Classify the symptom before the suspect.** Confirm the program produced no effect. A wrapper that exits 0 without running anything is distinguishable from a program that ran and failed, and from one that ran and produced nothing.
2. **Resolve the name, do not assume it.** Use `type -a` to enumerate every candidate in search order. A directory prepended to `PATH` wins over system directories. Inspect the winner with `head -1` and `file`.
3. **Trace execution to confirm.** Use `strace -f -e trace=execve` and look for the intended program. Treat a missing `execve` as the finding and stop speculating about the caller's logic.
4. **Read the wrapper and find the defect.** A script whose body only adjusts `PATH` and never references `"$@"` is a no-op for any caller. This is the common shape: an installer writes a source-only script into its own install directory and also adds that directory to `PATH`, so the script becomes reachable as the executable of the same name.
5. **Repair the wrapper so it executes when invoked.** Keep the source-only behavior intact and add an invocation branch.
6. **Verify at both ends.** Re-run the failing command on the originating host and inside the remote step. Fixing the wrapper restores the original caller; rewriting the caller to avoid the name only hides the defect.

### Repair a script that is both sourced and executed

A script that a shell profile sources must not execute its arguments, and a script invoked as a command must. Test `$0`, not `$#`.

```sh
#!/bin/sh
case ":${PATH}:" in
    *:"/opt/example/bin":*) ;;
    *) export PATH="/opt/example/bin:$PATH" ;;
esac

# Sourced: only the PATH change above is wanted.
# Invoked as a command: run the payload. The absolute path stops PATH lookup
# from resolving the name back to this script.
if [ "${0##*/}" = "env" ]; then
    exec /usr/bin/env "$@"
fi
```

Two constraints matter here:

- **Test `$0`, not `$#`.** When a file is sourced, `$#` holds the *caller's* argument count. An unguarded `exec "$@"` would replace a sourcing script that has its own arguments, and that script would then never finish. `type -a env` inside a sourcing script resolves to `env`; the basename of `$0` does not.
- **Use an absolute path in `exec`.** The wrapper shadows the very name being executed. A bare name would recurse into the wrapper.

### Caller-side defense

When a step's success must be observable, do not let it depend on how a bare name resolves. Prefer an absolute path, or perform the unsetting inside the step with a shell builtin and `exec` the target:

```bash
bash -c 'unset TMUX TMUX_TMPDIR; exec tmux -L "$1" new-session -A -s session -c "$2"' _ "$socket" "$HOME"
```

Treat this as defense in depth, not as the repair. It removes one dependency without fixing the wrapper.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trusted the zero exit status | Read the step's exit 0 as proof the program ran | The wrapper exits 0 whether or not it runs anything | Exit status from a wrapper is not evidence of the payload |
| Rewrote the caller | Replaced the wrapper call with a subshell that unsets variables and execs the target | Behavior changed and the symptom disappeared, but the wrapper still swallowed every other caller, including unrelated tools | Fix the shared defect; do not move one call site |
| Searched a packaged binary for the wrapper's text | Grepped the installed program for the wrapper's distinctive comment | Embedded assets in the packaged binary are compressed, so the literal text is absent; this produced a false negative and misidentified the generating component | Absence of a string in a packaged binary is not evidence of absence |

## Results & Parameters

### Configuration

Before repair, the wrapper exits 0 and emits nothing:

```console
$ env FOO=bar /bin/echo HELLO
$ echo $?
0
```

After repair, the same invocation runs:

```console
$ env FOO=bar /bin/echo HELLO
HELLO
$ echo $?
0
```

### Expected Output

- `type -a` lists a script in a prepended directory ahead of the system binary.
- The trace contains no `execve` for the intended program before the repair.
- The invocation returns the expected output after the repair, on the originating host and on the remote node.
- Sourcing from a script that has its own arguments still completes normally.

## Verified On

| Context | Details |
| ------- | ------- |
| A session wrapper on a shared batch-scheduler cluster | Wrapper installed by a package manager's standalone installer into a directory added to `PATH`; the wrapper launched a remote terminal multiplexer. Root cause confirmed by execve tracing on the login host, and the repair verified on the compute node. |

## References

- [Bash command substitution and eval discard an inner exit code](bash-command-substitution-eval-silent-failure-untestable.md)
- [A negated condition converts every failure into a pass](ci-cd-negated-if-exit-code-swallows-test-failures.md)
