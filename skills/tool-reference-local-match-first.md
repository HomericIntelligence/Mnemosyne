---
name: tool-reference-local-match-first
description: "Resolve an ambiguous tool or project reference by checking the local environment for an exact-name match before treating the name as a misspelling of a well-known tool. Use when a user asks about a name whose spelling is close to a famous project and a same-named artifact can exist in the home directory, the working tree, or on PATH."
category: tooling
date: 2026-10-23
version: "1.0.0"
user-invocable: false
tags:
  - disambiguation
  - user-reference
  - local-environment
  - tool-name
  - home-directory
  - grounding
---

# Check the local environment for an exact-name match before treating a reference as a misspelling

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Answer the question about the tool that the user means, not about the famous tool that the name resembles. |
| **Outcome** | successful — one read-only existence check separates a private same-named artifact from a similarly spelled public tool and prevents a correction round-trip. |

## When to Use

- A user refers to a tool, script, or project by an informal name, and that spelling is one or two edits from the name of a well-known public tool.
- The message contains typos or clipped grammar, so the name itself can look like a transcription error.
- The user works in an environment that can hold private tools: a home directory, a shared filesystem, or the session working directory.
- The correct answer depends on the intended target: version, status, usage, or behavior.

## Verified Workflow

### Quick Reference

Before you answer the well-known interpretation, run a read-only check for the name exactly as the user wrote it:

```bash
NAME="<tool-name-as-written>"
ls -d "$HOME/$NAME" "./$NAME" 2>/dev/null
command -v "$NAME" 2>/dev/null
```

If an exact match exists, answer about that artifact. If no match exists, answer the well-known interpretation.

### Suggested Approach

- Keep the name exactly as written. A user can misspell other words in the sentence and still write the tool name correctly.
- Check all of these locations: a file or directory in the home directory, a file or directory in the working tree, and an executable on `PATH`. A private tool can exist as an uninstalled directory or script, so `command -v` alone is not sufficient.
- Rank an exact local match above a fuzzy match to a public tool. One-edit similarity to a famous name occurs easily by accident, because users name private tools freely.
- When the check identifies a local artifact, inspect that artifact for the asked attribute. For example, read the version constant in the script instead of assuming behavior from the public tool.
- If the check finds two live candidates that the question does not separate, report both in one short line. Do not guess.
- If the check finds no local match, answer the well-known interpretation directly. Do not ask a clarifying question that a one-second check could have answered.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Read the name as a misspelling of the famous tool and reported the famous tool's version. | The user meant a private, same-named script in the home directory. The answer required a correction round-trip. | A name one edit away from a famous tool can be the exact name of a private tool. Run the exact-name environment check before treating the spelling as an error. |

## Results & Parameters

### Configuration

| Evidence | Decision |
| --------- | -------- |
| Exact-name file or directory in `$HOME` or the working tree | Answer about the local artifact; inspect it for the asked attribute. |
| `command -v` resolves the exact name | Answer about that executable. |
| No exact local match | Answer the well-known interpretation directly. |
| Multiple live candidates | Report both candidates in one line; do not guess. |

### Expected Output

- One read-only probe that completes in approximately one second.
- A direct answer about the correct target, without a correction round-trip.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Interactive agent session on a shared compute host | A version question about a private scheduler-helper script whose name is one letter short of a major JavaScript runtime | See [notes](tool-reference-local-match-first.notes.md). |
