---
name: tooling-opencode-v2-current-session-rename
description: "Rename the current OpenCode V2 session's own title exactly, for example a ceremony-mandated prefix swap, when the rename tool accepts only a full replacement title and no call identifies the caller's own session. Use when: (1) a protocol mandates an exact title edit such as replacing only a leading status prefix on completion, (2) several sessions share a title prefix and a session ID taken from a listing could rename the wrong session, (3) the current title must be discovered from the live session store, or (4) the rename must be verified afterwards against the intended session row."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags: [opencode, session-management, session-title, rename, sqlite, prefix-swap, wrong-target-prevention]
---

# OpenCode V2 current-session rename with discovered title

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Replace the current session's title with an exact mandated value (for example, swap only a leading status prefix and keep the remainder byte-identical) without renaming a sibling session. |
| **Outcome** | Verified live in a fleet ceremony: five sessions shared the status prefix, and the most recently updated matching row was a different session. The title was discovered from a read-only store query, the rename call omitted the session ID so the host bound the current session, and a post-rename readback of the bound row confirmed the exact target. |

## When to Use

- A coordinator or ceremony protocol mandates an exact title for the current session, such as replacing only the leading status prefix on completion and keeping the remainder identical.
- The rename tool accepts only the complete new title. It computes no prefix replacement and exposes no getter, and no store query or API call identifies the caller's own session.
- Fleet sessions share a title prefix: the candidate list is ambiguous, and a session ID guessed from the listing can rename the wrong session.
- The session store is live: OpenCode V2 keeps sessions in a SQLite database that its background service owns.

## Verified Workflow

### Quick Reference

```bash
# 1. Discover read-only (never write the store; the service owns it)
sqlite3 "file:~/.local/share/opencode/opencode.db?mode=ro" \
  "SELECT id, title, directory, time_updated FROM session_v2 \
   WHERE directory='<your working directory>' AND title LIKE '<prefix>%' \
   ORDER BY time_updated DESC LIMIT 5;"
# 2. Identify your row by task context (title content, directory), NOT by list position.
# 3. Rename through the host tool with sessionID OMITTED (binds the current session);
#    pass only the exact computed new title.
# 4. Verify: re-read the row identified in step 2 and confirm it holds the new title.
sqlite3 "file:~/.local/share/opencode/opencode.db?mode=ro" \
  "SELECT id, title FROM session_v2 WHERE id='<id from step 2>';"
```

### Suggested Approach

Do discovery with read-only SQLite queries against the session store, conventionally at `~/.local/share/opencode/opencode.db` (the `OPENCODE_DB` variable overrides it). The V2 troubleshooting documentation prohibits database edits while the service owns the state; do mutations only through the sanctioned host tool or the HTTP API. Open the database with the `file:<path>?mode=ro` URI so the live WAL database is not disturbed.

Bind identity by context, not position. Recency is not identity: a same-prefix sibling session can update itself moments after your session (titles and update times are mutable; a fleet nudge can touch many rows at any time). Require the candidate row's title and directory to match this session's actual task before you use it.

Let the tool supply the identity anchor. No listing can tell you which row is the caller; only the rename tool's omit-the-ID semantics binds the current session. Therefore never paste a store-derived session ID into the rename call; use the store only to compute the exact replacement title.

Verify against the bound row. The tool result reports the session ID it acted on; this incidentally binds the discovered row to the current session. Re-read that same row ID from the store and confirm it now holds the mandated title. If a different row changed, repair immediately: rename the wrongly touched session back, then repeat the procedure.

If no row matches the prefix and directory, your title differs from what the ceremony expects — report the mismatch instead of inventing a title.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Most-recent match as self | Take the top row of an update-time-ordered prefix listing as the current session | A same-prefix sibling session had a later update timestamp (less than a second later, from a concurrent ceremony run) | Position in a mutable listing is not identity; bind by task-context match, then confirm with a post-rename readback of the same row |
| Pass the discovered session ID to the rename call | Feed a listing-derived session ID into the mutation | If the snapshot is stale or the prefix list is ambiguous, the mutation targets a sibling session and the ceremony completes on the wrong title | Omit the session ID so the host binds the current session; the listing computes only the title string, never the target |

## Results & Parameters

### Configuration

Session discovery query against the V2 store (`session_v2` has `id`, `title`, `directory`, `model`, and epoch-millisecond `time_updated` columns):

```sql
SELECT id, title, directory, time_updated
FROM session_v2
WHERE directory = '<working directory>'
  AND title LIKE '<status prefix>%'
ORDER BY time_updated DESC
LIMIT 5;
```

Verification query (bind to the row ID the tool acted on):

```sql
SELECT id, title FROM session_v2 WHERE id = '<bound session id>';
```

### Expected Output

- The rename tool returns the current session's ID and the exact new title.
- The verification query returns the same row ID holding the new title; no other row changed.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode V2 on Linux (session_v2 store) | Coordinator-mandated completion ceremony: exact prefix swap on a fleet worker session title (2026-10) | Evidence in [notes.md](../skills/tooling-opencode-v2-current-session-rename.notes.md) |

## References

- [OpenCode troubleshooting guide: storage locations and service inspection](https://opencode.ai/v2/docs/troubleshooting)
- [Related skill: OpenCode V2 session model audit (read-only store doctrine, mutation-through-API rule)](tooling-opencode-v2-session-model-audit.md)
- [Related skill: OpenCode V2 batch session messages (titles are mutable; re-derive selection at send time)](tooling-opencode-v2-batch-session-messages.md)
