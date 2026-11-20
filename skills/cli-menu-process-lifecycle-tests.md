---
name: cli-menu-process-lifecycle-tests
description: "Build behavior tests for stateful menu-driven CLIs from process lifetime and saved-state preconditions. Use when one invocation performs only one menu action, later actions need state from an earlier action, or a test pipes a menu sequence into one process and later input is never consumed."
category: testing
date: 2026-11-20
version: "1.0.0"
user-invocable: false
tags: [testing, cli, menu, shell, integration-test, process-lifecycle, fixtures, state-preconditions, red-green]
---

# Test menu actions across process and state boundaries

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-20 |
| **Objective** | Exercise every menu action through the public CLI with the process lifetime and saved state that the action requires. |
| **Outcome** | Successful: separate process invocations and public setup flows expose the intended product behavior without harness-induced failures. |

## When to Use

Use this skill when all or some of these conditions apply:

- A shell or other CLI presents an action menu, then exits after the selected action.
- Refresh, update, restore, or delete actions require state that an earlier action creates.
- A test supplies several menu choices to one process, but only the first action runs.
- A test failure can come from either missing product behavior or an invalid harness lifecycle.
- A RED-GREEN test must distinguish an intended product assertion failure from a fixture setup error.

Do not use this entry to decide whether prompts read stdin or `/dev/tty`. Use
[shell-tty-interactivity-verification](shell-tty-interactivity-verification.md)
for that terminal boundary. Use the existing test framework and its normal
process runner; this entry changes lifecycle and state design, not frameworks.

## Verified Workflow

### Quick Reference

Model each test as public actions separated by process boundaries:

```text
fresh state -> process 1: install -> saved state
saved state -> process 2: refresh -> updated state
saved state -> process 3: restore -> restored state
```

Supply only the prompts that belong to each action. Create required state with
the earlier public action. Do not pipe the full menu sequence into one process
unless control flow proves that the process returns to the menu.

### Suggested Approach

1. Read the menu dispatch and every selected action through its exit or loop.
   Record whether the action returns to the menu, exits with status 0, or exits
   on a confirmation path. Input after an exit is unused, even when the exit is
   successful.
2. Record saved-state preconditions for each action. For example, refresh can
   require an install record, and restore can require a backup and a separate
   confirmation. Identify the public action that creates each prerequisite.
3. Start a fresh process for each action when the CLI exits after one action.
   Feed that process only its menu choice and prompts. Reuse the isolated state
   directory across processes so later actions observe earlier results.
4. Establish prerequisites through public actions. Do not copy private backup
   files or manufacture internal records when the public install or setup path
   can create the required state.
5. Classify the first failure before changing product code. Missing required
   state, an action that never ran, an unread prompt, or a fixture transport
   error is a harness error. Correct only that setup and rerun. Keep the product
   behavior assertion unchanged.
6. A behavioral RED remains only after the intended action runs and its observable
   result fails the unchanged product assertion. Then make the minimum product
   change and verify GREEN with the same lifecycle and state sequence.
7. Keep a control test for an existing contract, such as byte-for-byte restore.
   A control failure before product changes signals harness or pre-existing
   behavior that needs separate classification, not evidence for the new feature.

When control flow is unavailable, run a small process-level probe and inspect
which prompts execute and which state changes occur. Record that limit rather
than assuming that piped input implies a persistent menu loop.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Piped install, restore, and confirmation input into one installer process and asserted byte-for-byte restoration. | The installer exited after install. The restore menu choice was never consumed, so the assertion compared installed state rather than restored state. | Derive process boundaries from control flow. Invoke restore in a new process with its own confirmation input. |
| Attempt 2 | Invoked refresh directly in a fresh isolated home to test version-dependent behavior. | Refresh required a backup that the public install action creates. The run stopped on that missing precondition before reaching the behavior under test. | Run install first, preserve its state directory, and invoke refresh in a second process. Treat this setup failure as a harness error, not behavioral RED. |

## Results & Parameters

### Configuration

Define these harness parameters explicitly:

```yaml
state_directory: one isolated directory shared by the action processes
processes:
  - action: install
    input: install choice and install prompts only
    creates: saved settings and restore backup
  - action: refresh
    input: refresh choice only
    requires: saved settings and restore backup
  - action: restore
    input: restore choice and restore confirmation only
    requires: restore backup
```

Use the CLI's documented test seams for state paths and external dependencies.
Keep those paths isolated for each test case. Do not add run-configuration
environment variables to the product only to support the harness.

### Expected Output

- Each selected action executes in its own process and consumes its own prompts.
- Refresh observes the state produced by install; restore observes the backup.
- Setup failures disappear without changes to product assertions.
- The unchanged feature assertion gives a clean behavioral RED before the fix
  and GREEN after it; existing-contract controls retain their original meaning.

Observed evidence: in one privacy-generalized stateful installer harness, these
corrections removed the unused-menu-input and missing-backup failures. The
byte-for-byte restore control passed before product changes, the intended
feature assertions remained RED, and the focused suite passed after the minimal
product change. This evidence covers that harness; it does not establish that
every CLI uses one-action processes or identical saved-state rules.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Stateful installer integration suite (privacy-generalized) | Real menu-driven CLI processes with isolated state and controlled external dependencies | Verified process separation, public state setup, behavioral RED, restore control, and focused GREEN on 2026-11-19 through 2026-11-20. |

## References

- [shell-tty-interactivity-verification](shell-tty-interactivity-verification.md)
  — verifies terminal prompt boundaries; this entry verifies action process and
  saved-state boundaries.
- [bash-noninteractive-installer-wrapper](bash-noninteractive-installer-wrapper.md)
  — removes terminal interaction for unattended installation; this entry drives
  the public menu deliberately in tests.
- [testing-integration-fake-binary-on-path](testing-integration-fake-binary-on-path.md)
  — supplies controlled external executables; combine that seam with the process
  lifecycle defined here.
