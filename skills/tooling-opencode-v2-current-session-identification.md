---
name: tooling-opencode-v2-current-session-identification
description: "Identify the running OpenCode v2 session before a directive mutates its own session record. Use when a task tells the session to rename or act on itself and no tool reports the current title, when several sessions run in one fleet and recency alone cannot name the caller, or when verification must confirm a session-title change landed on the correct row."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags: [opencode, session-identity, session-rename, sqlite, fleet, self-reference, multi-agent]
---

# OpenCode v2 Current-Session Identification

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Bind the running session to one store row before any self-referential mutation, so a rename or cleanup lands on the correct session and not on a sibling lane. |
| **Outcome** | Successful. One self-referential rename was bound by verbatim prompt match, mutated through the official tool, and verified by an immutable post-write read. Zero wrong-row mutations. |

## When to Use

- A directive tells the running session to act on itself — rename its title, compact it, or close it out — and the available tools accept a session identifier but do not report the caller's own identifier or title.
- A completion or checkpoint protocol renames session titles (for example, replacing a status prefix) and the new title must keep the unchanged remainder of the old one.
- Several agent sessions share one host and store, so multiple rows can show fresh update times inside the same minute.
- An auditor must confirm that a session rename landed on the intended row after it ran.

## Verified Workflow

### Quick Reference

```bash
# 1. Copy the live store before any query. The service owns these files;
#    a snapshot copy cannot contend with its locks.
SNAP="$(mktemp -d)"; DB="$SNAP/store.sqlite"
cp "$HOME/.local/share/opencode/opencode.db"      "$DB"
cp "$HOME/.local/share/opencode/opencode.db-wal"  "$DB-wal" 2>/dev/null || true
cp "$HOME/.local/share/opencode/opencode.db-shm"  "$DB-shm" 2>/dev/null || true

# 2. Narrow candidates by title pattern, never by recency alone.
sqlite3 "$DB" "SELECT id, title, datetime(time_updated/1000,'unixepoch')
               FROM session_v2 ORDER BY time_updated DESC LIMIT 20;"

# 3. Confirm identity with a verbatim first-prompt match in session_message.
sqlite3 "$DB" "SELECT session_id FROM session_message
               WHERE data LIKE '%<verbatim opening words of the first user message>%'
               LIMIT 5;"

# 4. Mutate only through official tooling (the session rename tool or the
#    HTTP session.update operation). Never write the store directly.

# 5. Verify the mutation with a fresh read. An immutable-mode URI keeps the
#    read detached from the owning service.
sqlite3 "file:$HOME/.local/share/opencode/opencode.db?immutable=1" \
  "SELECT title FROM session_v2 WHERE id='<bound-id>';"
```

### Suggested Approach

1. **Accept that there is no self-introspection path.** The v2 HTTP API lists
   sessions (`session.list`, `session.active`) and operates on a known
   identifier (`session.view`, `session.update`, `session.rename`), but no
   operation answers "which session am I". A session-activity listing narrows
   nothing in a fleet: dozens of rows, most of them idle lanes, report a
   running state at the same time. Treat list operations as candidate
   generators only.
2. **Read a snapshot copy, not the live files.** The service rewrites the
   store from memory. Copy the database with its `-wal` and `-shm` siblings
   into a temporary directory and query the copy. For a one-off post-write
   verification, a `file:<path>?immutable=1` URI is lighter: it opens the live
   database read-only without taking write locks.
3. **Confirm identity by verbatim message evidence.** Title prefixes and
   recency are hints, not identity. In a fleet, five or more sessions can
   update within one half-minute window, and sibling lanes carry near-identical
   titles. Match a distinctive verbatim span of the session's own first user
   message in `session_message.data`; an exact substring hit is the identity
   proof. If the match returns more than one session or none, stop and report —
   do not guess.
4. **Mutate through official tooling only.** Direct writes against the store
   while the service owns it lose data (the V2 troubleshooting documentation
   prohibits database edits during service ownership). Use the harness session
   rename tool when it is available; otherwise use `session.update` over the
   HTTP API with the bound identifier.
5. **Verify after the write.** Re-read the bound row from a fresh immutable
   handle or `session.view` and compare the full new title, not only the
   changed prefix. Stale copies from step 2 do not show the mutation; do not
   verify against them.
6. **Screen service state files from artifacts.** The service locator file
   under the state directory contains the API credential. Never copy it into
   guidance, notes, commits, logs, or pull requests. Refer to it by role
   ("the service locator file") and let each operator read it locally.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Archived transcripts | Scanned a directory of exported session transcript files for the current session | The archive was months stale relative to the live store; the running session was absent | Transcript exports are a history source, not an identity source; identity belongs to the live store |
| Recency-only selection | Read the most recently updated row in `session_v2` as the current session | A fleet showed five or more sibling sessions with update times inside one half-minute window; the newest row was a sibling | Recency narrows candidates but never proves identity; confirm with verbatim prompt text |
| Direct live-database query | Opened the service-owned database for an ad-hoc identity query | The owning service rewrites the file from memory; direct reads can contend with its write-ahead log and return torn state | Query a snapshot copy, or use an `immutable=1` URI that takes no write locks |
| Activity listing | Queried the official operation that lists active sessions to find "the" running session | It returned dozens of rows, nearly all idle lanes still marked running | Activity state is not identity; plan for candidate-plus-confirm, not list-and-pick |

## Results & Parameters

### Configuration

```text
Live store:      ~/.local/share/opencode/opencode.db (+ -wal/-shm siblings)
Tables:          session_v2 (id, title, time_updated, ...),
                 session_message (session_id, type, seq, data, ...)
Snapshot:        copy db, -wal, -shm to one temporary directory, then query the copy
Read-only URI:   file:<live-db-path>?immutable=1   (verification reads only)
Mutation:        harness session rename tool, else HTTP session.update with the bound id
Identity proof:  exact substring of the session's own first user message in session_message.data
```

### Expected Output

- One candidate row whose id, title, and recency agree.
- Exactly one `session_message` match for the verbatim prompt span, on the same id.
- The mutation call returns the new title.
- A fresh immutable read returns the bound id with the full new title and no other row changed.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Multi-lane agent fleet, Linux host, OpenCode v2.1.4 | Self-referential completion rename bound by verbatim prompt match | Generalized evidence in [notes.md](../skills/tooling-opencode-v2-current-session-identification.notes.md) |

## References

- [OpenCode v2 session model audit and retargeting](tooling-opencode-v2-session-model-audit.md) — official-API mutation path; no direct store writes.
- [OpenCode v2 session message filter](tooling-opencode-v2-session-message-filter.md) — message-table query pitfalls (own-request contamination, subagent prompt rows).
- [OpenCode v2 corrupt database recovery](tooling-opencode-v2-corrupt-db-recovery.md) — service-owns-store rules and table map.
