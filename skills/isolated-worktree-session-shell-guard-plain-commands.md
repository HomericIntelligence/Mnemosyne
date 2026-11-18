---
name: isolated-worktree-session-shell-guard-plain-commands
license: BSD-3-Clause
description: "Work with a shell guard that refuses commands it cannot prove stay inside a session's own git worktree. Use when: (1) a command is refused with a message that it runs inside a construct too complex to verify, (2) a loop, a command substitution used as an argument, or a computed command name is refused, (3) a git or gh call that targets another checkout is refused, (4) you are tempted to wrap the refused command in another construct to get past the guard."
category: tooling
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [agent-harness, git-worktree, shell-guard, command-refusal, script-file, plain-commands, gh-cli, isolation]
---

# Shell Guard of an Isolated Worktree Session

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Keep a long multi-step session moving when the harness refuses shell commands that it cannot verify. |
| **Outcome** | Operational. Over one long session the guard refused dozens of commands. A fixed set of constructs caused every refusal. Splitting each one into plain commands, or moving the logic into a script file under the job's own temporary directory, removed the problem without any bypass. |

An agent session can be isolated in one git worktree. The guard then refuses a shell command when
it cannot show that the command stays inside that worktree. It reads the command text. It does not
run the command. A construct whose result is computed at run time cannot be shown safe, so it is
refused even when the command is harmless.

## When to Use

- The refusal text says the command runs a program, a path or a value that "cannot be verified" and
  that the session's git operations must target its own worktree.
- A `gh` or `git` call with a loop, a command substitution, or a long filter string is refused.
- You work across several repositories or checkouts from one isolated session.

## Verified Workflow

### Quick Reference

```text
Refused:   for/while/until loops; $(...) as an argument to git, gh, sed, find or python;
           a program or path taken from a variable; bash -c '<loop>'; a here-string after a
           compound command; jq filters with parentheses and string interpolation passed to gh;
           git -C <shared main checkout>, or cd <other checkout> && git.
Accepted:  one plain command with literal arguments; absolute literal paths; pipes between plain
           commands (head, cut, tr, sort, uniq); python on a literal script path;
           gh with a simple --jq; git -C <literal path of a DIFFERENT repository>.
Fix:       split into plain commands, or write a script file in the job's tmp dir and run it.
```

### Suggested Approach

1. Do not wrap a refused command in another construct to get past the guard (`eval`, `bash -c`,
   a process that runs `git` for you against the shared checkout). That defeats the purpose of the
   guard and is likely to be denied. See the related entry on permission denials.
2. Split the command. Run the inner command alone, read its output, then pass the literal value to
   the next command.
3. For a loop or a multi-step check, write a script file with the file-write tool into the job's own
   temporary directory, then run it by its absolute path. Keep the loop inside the script.
4. Keep every `git` operation in a script on the session's own worktree. A script is not a way to
   run `git` against the shared main checkout: that is the protected target.
5. For API output that needs formatting, print the raw JSON fields with a simple filter and format
   them in a small script. Avoid a long filter with interpolation on the command line.
6. For a wait, run the command in the background and rely on its completion notice, or use a
   bounded `timeout` on one literal command. Put an `until` loop in a script file.
7. For another repository, `git -C <literal path>` works. A path that is the shared main checkout
   of the same repository does not.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Foreground wait loop | `until <check>; do sleep 2; done` on the command line | Refused: a loop inside a plain command | Run the wait in a script or in the background |
| Computed argument | `gh api repos/<o>/<r>/commits/$(gh pr view ... --jq .sha)` | Refused: command substitution as an argument | Run the inner command first, then use the literal value |
| Timeout around a loop | `timeout 120 bash -c 'until ...; done'` | Refused: `bash -c` with a loop | The wrapper does not hide the loop from the guard; use a script file |
| Long filter on the command line | `gh pr list --jq '.[] \| select(...) \| "\(.x)..."'` | Refused: a filter that cannot be shown safe | Use a plain `--jq` or a small script |
| Git in the shared checkout | `git -C <shared main checkout> ...` | Refused: it targets another worktree of the protected repository | Work in the session's own worktree; use a literal path only for a different repository |

## Results & Parameters

### Configuration

```yaml
script_location: the job's own temporary directory (not a shared /tmp)
run_with: "bash /absolute/path/to/script.sh"
background: long waits and long installs, with the completion notice as the signal
never: eval, bash -c with a loop, or any process used to reach the shared main checkout
```

### Expected Output

Each refused command becomes two plain commands or one script run by absolute path, and the
session proceeds without a retry of the same refused text.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An agent session on a scheduler cluster | One long release and review session, 2026-10 | Dozens of refusals, all from the constructs above; plain commands and script files fixed each one. |

## References

- [local-production-patch-handover-and-ledger](local-production-patch-handover-and-ledger.md) — a denied action: hand it over, do not work around it
