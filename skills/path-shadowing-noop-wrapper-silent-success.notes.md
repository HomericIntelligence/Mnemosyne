# Notes — PATH-Shadowing No-Op Wrapper

Supporting evidence for `path-shadowing-noop-wrapper-silent-success.md`.

## Symptom shape

A session wrapper printed its "attaching" message, returned to the shell prompt immediately, and exited 0. The intended program never started. The wrapper also produced no error, so the calling shell and any job scheduler both read the step as successful.

## Diagnostic sequence and observations

Resolution order for the command name, on the affected host:

```console
$ type -a env
env is /home/USER/.install/bin/env      # installer-written script
env is /usr/bin/env                     # system binary
```

The installer-written script won because its directory was prepended to `PATH`.

Inspecting the winner showed a POSIX script, not an ELF binary, whose entire body adjusted `PATH` and never referenced `"$@"`:

```sh
#!/bin/sh
case ":${PATH}:" in
    *:"/home/USER/.install/bin":*) ;;
    *) export PATH="/home/USER/.install/bin:$PATH" ;;
esac
```

Exit-status evidence was uninformative in both directions:

| Invocation | Before repair | After repair |
| ---------- | ------------- | ------------ |
| `env FOO=bar /bin/echo HELLO` | no output, exit 0 | `HELLO`, exit 0 |
| `env -u NAME /bin/echo OK` | no output, exit 0 | `OK`, exit 0 |
| `env -u NAME=VALUE /bin/echo OK` | no output, exit 0 | `Invalid argument`, exit 125 |

The third row is worth keeping: a malformed option produced a diagnostic and a non-zero status only after the repair. Before the repair the wrapper discarded the arguments and produced nothing, so even an invalid invocation looked like success.

Execve tracing supplied the actual finding:

```console
$ strace -f -e trace=execve <wrapper> 2>&1 | grep execve
execve("/.../srun", [...])        = 0
execve("/.../sbin", [...])       = 0
--- SIGCHLD ... ---
exit_group(0)
```

No `execve` for the wrapper command or the terminal multiplexer appeared. The step's zero status was the wrapper's own status.

## Why the wrapper existed

The generator's intent was legitimate: a source-only script that is idempotent, so it can be appended to several shell profiles and run repeatedly without corrupting `PATH`. The installer also placed a sibling script with a fish-syntax extension in the same directory and sourced the appropriate variant from each shell's configuration files.

The defect is that the script's name matched a coreutils binary while its directory was on `PATH`. The design solved idempotency for *sourcing* and did not consider that the same file is reachable as the *executable*. The directory name derived from the tool that requested the install and carried no authorship information; the template text matched the generating project's published installer byte for byte.

## Repair verification

The repair keys on the basename of `$0` rather than `$#`. Sourcing behavior was confirmed to survive:

| Check | Result |
| ----- | ------ |
| Source the script when its directory is absent from `PATH` | directory prepended |
| Source it twice | prepended once, no duplicate |
| Source it from a script that has its own arguments | script completes and prints its own output |
| Invoke it as a command | payload runs |

The sourcing-with-arguments case is the one that justifies the `$0` test. When a file is sourced, `$#` is the caller's argument count, so a guard written as `[ "$#" -gt 0 ]` would have replaced the sourcing script with `env` and never returned.

## Scope of the defect

The impact was not limited to the wrapper that exposed it. Every program on the host that resolved the shadowed name through `PATH` inherited the same no-op. The same installer had produced a second instance under a different prefix on the same machine.

Corollary for triage: when one command is silently doing nothing, assume other commands may be silently doing nothing too, and audit the resolution order of the names the affected tool depends on.
