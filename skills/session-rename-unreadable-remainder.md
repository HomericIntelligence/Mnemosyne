---
name: session-rename-unreadable-remainder
description: "Rename the current harness session when a workflow requires it and the tools cannot read the current title. Use when: (1) a completion or workflow step prescribes a session rename that must preserve an unchanged remainder, (2) the available session tools can rename but cannot read the current title, (3) the run is non-interactive so a user-question call cannot recover the remainder, or (4) the only readback paths are outside the sanctioned tool surface."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags:
  - session-management
  - session-rename
  - write-only-tool
  - non-interactive
  - assumption-stating
  - done-protocol
  - completion-report
  - harness
---

# Session Rename With an Unreadable Remainder

**Supporting detail:** [notes](./session-rename-unreadable-remainder.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Complete a prescribed session rename without corrupting the remainder of a title that the tools cannot read. |
| **Outcome** | Operational decision branch. Verified-live in one completion protocol: the rename tool was write-only, the question call was cancelled by the non-interactive runner, and the reconstructed remainder was applied with the assumption stated. |

## When to Use

- A workflow or completion protocol renames the current session. An example: replace one status
  prefix with another and keep the remainder unchanged.
- The session tools can rename but return no current title. The remainder is write-only
  inaccessible.
- The run is non-interactive. A user-question call is unavailable or the runner cancels it.
- The only readback paths sit outside the sanctioned tool surface. Examples: local harness
  state stores, protected paths, provider-specific internals.

## Verified Workflow

### Quick Reference

```text
1. Probe the session tools for a title readback. None -> the remainder
   is unreadable from tools.
2. Probe interactivity. A cancelled question means: continue with stated
   assumptions.
3. Durable session context supplies the remainder? Rename, state the
   assumption, give the correction path.
4. No durable source? Skip the rename and log it as outstanding.
```

### Suggested Approach

1. Enumerate the session tools before any rename. If none returns the current title, treat the
   remainder as unreadable from tools. Do not fabricate knowledge of it.
2. Check interactivity. A non-interactive runner can cancel a user-question call and instruct
   the work to continue with stated assumptions. Do not keep the step blocked on a datum the
   harness will not supply.
3. If durable session context supplies the remainder — the assignment objective, the protocol
   messages, or the prefix pattern itself — perform the rename with the reconstructed remainder.
   State the assumption plainly in the completion report and record the one-operation correction
   path. A session rename is idempotent, so the correction is cheap.
4. If no durable source supplies the remainder, do not invent it. Skip the rename and report it
   as outstanding. A missing rename beats a fabricated one: after an overwrite, the true
   remainder is unrecoverable from tools.
5. Never read local harness state outside the sanctioned tool surface to recover the title. This
   holds with and without an explicit do-not-touch directive for those paths.

### If a step is unavailable

- Interactive runs can ask the user for the exact remainder directly. Ask once, then rename.
- Harness generations change. Re-probe the session tool surface on each generation before you
  classify a remainder as unreadable.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Ask the user for the exact remainder | Issued a user-question call for the current title during a non-interactive run | The runner cancelled the call and instructed the work to continue with stated assumptions | A cancelled question is itself the answer about interactivity; reorder the decision to assumption plus stated correction |
| Read the harness's local session store for the title | Evaluated and rejected | The path sat outside the sanctioned tool surface and inside a task directive that forbade those paths | A prohibited read is never the fix for an unreadable remainder; use durable context or skip |
| Rename without stating the remainder assumption | Evaluated and rejected | The operator could not distinguish a reconstructed remainder from a read one | Every reconstructed remainder must carry its assumption and the correction path in the report |

## Results & Parameters

### Configuration

```yaml
probe_order: [session_tool_readback, interactivity, durable_context, skip_and_log]
durable_sources: [assignment_objective, protocol_messages, prefix_pattern]
rename:
  properties: [idempotent, cheap_correction]
  requirement: "state the assumption and the correction path in the report"
forbidden: [read_outside_sanctioned_surface, invent_remainder]
```

### Expected Output

- A session title that carries the required prefix change, or a rename logged as outstanding.
- In the reconstructed case, the completion report names the assumption and the correction path.
- Zero reads outside the sanctioned tool surface.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal agent harness | A completion protocol prescribed a prefix-replacing session rename | The session tools were write-only (rename available, no title readback); the runner cancelled the question call and told the work to continue with stated assumptions; the remainder was reconstructed from the assignment objective, the rename succeeded, and the assumption was stated in the report — verified-live single case; see [notes](./session-rename-unreadable-remainder.notes.md) |

## References

- [automation-session-naming-pr-scoped-not-commit-scoped](automation-session-naming-pr-scoped-not-commit-scoped.md) — session naming conventions for automation sessions.
- [tooling-opencode-v2-session-model-audit](tooling-opencode-v2-session-model-audit.md) — session model and tool-surface audit for one harness generation.
