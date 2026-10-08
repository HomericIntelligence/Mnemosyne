---
name: tooling-opencode-v2-session-deletion-effects
description: "State what OpenCode V2 deletes and retains when a session is deleted. Use when answering questions about session deletion, transcript recovery, session logs, or local OpenCode data cleanup."
category: tooling
date: 2026-10-07
version: "1.0.0"
user-invocable: false
tags: [opencode, session-deletion, data-retention, sqlite, event-log, export]
---

# OpenCode V2 session deletion effects

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-07 |
| **Objective** | Give a correct map of the data that session deletion removes and the data that stays on disk. |
| **Outcome** | Verified against the public OpenCode source at tag v2.0.24 and the V2 documentation. Deletion is permanent; there is no trash and no undo. |

## When to Use

- A user asks what happens to messages, logs, or history when they delete an OpenCode session.
- A user must keep a session transcript and has not deleted the session yet.
- A user expects per-session log files or a recovery path that V2 does not have.
- An answer based on V1 file storage or on the API summary alone would be incorrect.

## Verified Workflow

### Quick Reference

Deleting an OpenCode V2 session removes the session row and its complete durable event log from the SQLite database, recursively for child sessions. Deletion does not change the shared application log file, truncated tool-output files, or VCS snapshot data. There is no undo. Export the session before deletion when the user must keep the transcript.

### Data that deletion removes

The delete operation is `session.remove` in the core session service. In v2.0.24 it performs these steps:

1. Verify that the session exists; interrupt active execution and wait for an idle state.
2. Close the model transport for the session.
3. Recursively remove each child session (forks and subagent sessions).
4. Clear the session environment variables.
5. Publish the deleted event, after which the projector removes the session row.
6. Remove every event for the session aggregate from the event table and the event sequence table in one database transaction.

OpenCode V2 stores the session transcript — messages, tool calls, and the durable session event log returned by `GET /api/experimental/session/{sessionID}/log` — as these events. Their removal is permanent.

### Data that deletion keeps

These locations are not session-keyed or are managed by a different lifecycle:

| Data | Location | Lifecycle |
| --- | --- | --- |
| Shared application log | `~/.local/share/opencode/log/opencode.log` | Process logging and rotation; lines about the deleted session stay |
| Truncated tool output files | `~/.local/share/opencode/tool-output/` | Timestamp-keyed files with 7-day retention cleanup |
| VCS snapshot data | `~/.local/share/opencode/snapshot/` | Git-tree snapshots used for undo differencing; not tied to session deletion |

### Keep the transcript: export before deletion

Advise the user to export before deletion:

```bash
opencode api get /api/experimental/session/<session-id>/export
```

### Verify behavior against the installed version

Storage behavior changed between major versions. V1 used JSON files; V2 uses a SQLite database at `~/.local/share/opencode/opencode.db`, overridable with `OPENCODE_DB`. Check `opencode --version` and verify claims against the V2 documentation and the source tag that matches. Do not infer deletion behavior from V1 knowledge or from the API summary alone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Answer from the API reference alone | Used the delete-endpoint summary as the complete answer. | The summary states only "Delete a session and its child sessions"; it does not state which storage artifacts change or which files stay. | For data-lifecycle questions, read the delete implementation in the source tag that matches the installed version. |

## Results & Parameters

Expected shape of a correct answer to a session-deletion question:

- The session transcript and its durable event log are removed from the SQLite database and cannot be recovered.
- Child sessions are removed recursively.
- The retained locations (application log, tool-output files, snapshot data) have separate lifecycles.
- Export before deletion when the transcript must be kept.
- Bind version-specific claims to the verified version.

See the [notes](tooling-opencode-v2-session-deletion-effects.notes.md) for the verified code path, source references, and evidence limits.

## References

- [OpenCode V2 troubleshooting: database and log locations](https://opencode.ai/v2/docs/troubleshooting/)
- [OpenCode V2 HTTP API: session routes](https://opencode.ai/v2/docs/api/)
- [OpenCode source at v2.0.24: session service](https://github.com/anomalyco/opencode/blob/v2.0.24/packages/core/src/session.ts)
- [OpenCode source at v2.0.24: event bus](https://github.com/anomalyco/opencode/blob/v2.0.24/packages/core/src/bus.ts)
