---
name: cli-hint-names-final-identifier
description: "A CLI that submits work and later feeds a follow-up command must print the exact identifier that the follow-up command accepts, not the input the user typed. Use when: (1) a user passes a source reference to a follow-up command and gets a pattern or not-found error, (2) a submit command derives a name (slug, alias) that a later stage can rename, (3) you add a next-step hint to command output."
category: tooling
date: 2026-11-25
version: "1.0.0"
user-invocable: false
tags:
  - cli
  - output-hint
  - identifier
  - slug
  - next-step
---

# CLI Hint Names the Final Identifier

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Make a submit-style command tell the user how to run the next command, with an identifier that the next command accepts. |
| **Outcome** | Successful. One review round found a wrong-identifier case. A second round gave a GO. |

## When to Use

- A user ran a submit command with a source reference (for example `org/name`), then passed the same reference to a follow-up command. The follow-up command rejected it with a pattern error.
- The submit command prints a derived identifier, but prints no instruction for the next step.
- A later stage can publish the result under a different name than the one derived at submit time (a collision suffix, a revision suffix, or a reserved name).

## Verified Workflow

### Quick Reference

- Print the next command in the submit output, with the derived identifier.
- If a later stage can rename the result, say that the final name comes from the result record. Do not state the submit-time name as final.
- After a wait or status step, print the next command from the result record field that holds the real name. Fall back to the derived identifier only when that field is empty.

### Suggested Approach

1. Find how the follow-up command resolves its argument. Note the grammar that it accepts and the key that it uses to find the stored record (for example a file stem).
2. List every path that can publish the result. For each path, check whether the stored name equals the derived name. A collision, a reserved name, or a new revision commonly changes the name.
3. Put the hint on two lines of output: a provisional hint at submit time, and a final hint after the result exists. Take the final name from the stored result, not from a second derivation.
4. Strip only the exact suffix that the store adds (use `removesuffix`, not `rstrip` or `split`).
5. Check that no script or doc parses the old output. Add a new line instead of changing an existing line.
6. Do not add a test that pins the hint text. Test the choice of name (result field over derived name) only when the code has a testable function for it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Print the next command with the derived identifier at submit time and after wait. | A later stage can publish under a different name. The hint then points to another record, or to a protected one. | Use the result record for the final hint. Make the submit-time hint provisional. |
| 2 | Assert the hint text in a CLI output test. | It pins a string and gives no behavior evidence. Review rejected it. | Remove the assert. |

## Results & Parameters

```text
submitted <id> as <derived>; track with `status <id>`
after the pull is accepted, load it with `load <derived>`; the result's name line gives the final name
...
load it with `load <result.stored_name minus suffix>`
```

### Expected Output

- The user never passes the source reference to the follow-up command.
- The final hint and the stored-name line of the result agree.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| One internal CLI | A pull command and a load command | Two independent review rounds. Round 1 found the rename case. Round 2 gave a GO. Checks ran locally. CI was pending at the time of writing. |

## References

- [CLI format output and silent fallback](cli-format-output-pola-silent-fallback.md)
