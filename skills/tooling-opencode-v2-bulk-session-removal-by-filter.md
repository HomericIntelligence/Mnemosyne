---
name: tooling-opencode-v2-bulk-session-removal-by-filter
description: "Remove many OpenCode V2 sessions that match a filter (for example trivial smoke-test sessions) directly from the live SQLite store. Use when a user asks to find and delete a set of sessions that a title, content, or metadata predicate selects, and the count makes one-at-a-time API deletion impractical."
category: tooling
date: 2026-11-01
version: "1.0.0"
user-invocable: false
tags: [opencode, session, sqlite, bulk-delete, cleanup, live-database, foreign-keys]
---

# OpenCode V2 bulk session removal by filter

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Delete every session that a filter selects, in one transaction, from a database that a running OpenCode process also uses, without corrupting the store or deleting unintended rows. |
| **Outcome** | Successful. The filter-selected set was identified, verified as unreferenced, deleted in one committed transaction, and the store passed an integrity check. |

## When to Use

- A user asks to find and remove a class of sessions, such as trivial smoke-test sessions, rather than one named session.
- The selection predicate is a title pattern, a message-content test, or session metadata.
- The number of sessions makes one-at-a-time service-API deletion impractical.
- A local OpenCode process is running and uses the same database file.

Do not use this workflow when the user names one session, or when the user wants a transcript
preserved. Use the service deletion path for those cases.

## Verified Workflow

### Quick Reference

Read-only discovery first. Back up. Delete children and the parent row explicitly in one
transaction with foreign keys enabled. Verify before commit.

```bash
# 1. Locate the store. The default path applies unless OPENCODE_DB overrides it.
ls ~/.local/share/opencode/opencode.db

# 2. Inventory the schema before writing any query.
sqlite3 ~/.local/share/opencode/opencode.db ".tables"
sqlite3 ~/.local/share/opencode/opencode.db ".schema session_v2"
```

### Select with evidence, not with a guess

Do not treat a title as a proxy for content. A title can be user-edited and can be a
generated label. A filter on title alone can select a session the user does not mean.

1. Find candidate rows by the cheap predicate, such as a title pattern.
2. For each candidate, read the actual user messages from `session_message` where `type = 'user'`.
3. Parse the `data` column as JSON and read the `text` field. Do a parse in a host language
   instead of a SQL JSON function when the column has mixed validity; invalid rows must not
   abort the whole query.
4. Keep a session only when its content matches the user's intent. Report the count and the
   shape of each matching session before you delete.

Use one exact identifier list for every later step. Store it in a file so that selection,
verification, and deletion all consume the same list.

### Check references before you delete

The current schema uses real foreign keys, and most child tables declare `ON DELETE CASCADE` to
`session_v2`. Confirm this on the installed schema, and do not rely on it for the write. Delete
the children explicitly so that the result is correct even if the pragma is off.

Child tables in the current schema:

| Table | Link to the session |
| --- | --- |
| `session_message` | `session_id` |
| `session_part` | `session_id` |
| `session_inbox` | `session_id` |
| `instruction_entry` | `session_id` |
| `instruction_state` | `session_id` |
| `blob_ref` | `session_id` |
| `schedule` | `session_id` |

Verify these external references before deletion. A hit means the row is not safe to delete on
its own:

- `session_v2.parent_id`: a child session would become an orphan.
- `session_v2.fork_session_id`: a fork would lose its origin.

Also find blobs that only the candidate sessions reference. A blob that another session also
references must stay.

Do not assume that a similarly named storage area holds the same data. Check it. Session
transcript files under a session-directory tree can be absent for sessions that exist in the
database, and a file search is a weak negative signal. Use the database as the record for the
database.

Do not assume that an older version's audit table still applies. A table can exist and be empty
for every session. Count the rows for the candidate set before you decide that it needs cleanup.

### Back up, following the directory's existing convention

Copy the database and its sidecar files together. A copy of the main file alone can miss
committed data that a live process holds in the write-ahead log.

```bash
cd <opencode-data-dir>
TS=$(date -u +%Y%m%dT%H%M%SZ)
cp opencode.db     "opencode.db.pre-session-delete-${TS}"
cp opencode.db-shm "opencode.db.pre-session-delete-${TS}-shm"
cp opencode.db-wal "opencode.db.pre-session-delete-${TS}-wal"
```

Name the backup so that it does not end in the exact extension that the application scans for.
Use the naming pattern that the target directory already uses.

### Delete in one transaction, then verify before commit

Use `BEGIN IMMEDIATE` to take the write lock at once. Enable `foreign_keys`. Delete each child
table by the identifier list, delete the parent rows, then re-count every table for the same
list. Commit only when every count is zero. Roll back on any leftover.

Set a busy timeout. A running process can hold the lock, and a zero timeout fails the transaction
without a clear cause.

### Report the real delta

A live process creates sessions while you work. The change in the row count will not equal the
number of rows you deleted. Report the deleted-row counts by table, not only the difference in
the total.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Title-exact match | Selected sessions with a literal equality test on the title. | Returned zero rows. The real rows used longer generated titles around the keyword. | Start with the cheap pattern, then confirm against message content. |
| SQL JSON extraction in the selection query | Used a JSON path function inside SQLite to read message text. | The statement aborted with a malformed-JSON error on one row, so no result came back at all. | Parse the column in a host language per row so that a bad row cannot abort the whole scan. |
| Prefix match treated as exact-reference evidence | Counted child rows with a `LIKE` pattern on the identifier prefix. | The prefix also matched unrelated identifiers, so the count was not evidence of a reference. | Test references with exact identifier sets. |
| Assumed transcript files must exist | Searched a session-file tree for the candidate identifiers. | Found none, which looked like a contradiction. The tree is a separate store and is not the authority. | Resolve a conflict between two stores by name and role, not by assuming that one is wrong. |
| Assumed the versioned audit table needed cleanup | Planned to delete rows from the older audit table. | The table exists but holds no rows for the candidate set. | Count first. A table that exists is not a table that needs a write. |

## Results & Parameters

### Configuration

```yaml
sqlite:
  isolation: "BEGIN IMMEDIATE"
  pragmas: ["foreign_keys = ON"]
  busy_timeout_s: 30
selection:
  step_1: "cheap predicate on the parent row"
  step_2: "per-row parse of the user message text in a host language"
  step_3: "frozen identifier list in a file"
deletion:
  order: "children by exact id list, then the parent row"
  commit_gate: "every post-delete count is zero"
backup:
  files: ["<db>", "<db>-shm", "<db>-wal"]
```

### Expected Output

- A delete report with a non-zero count for each child table that had rows, and the parent count.
- A post-delete count of zero in every table for the identifier list.
- A passing quick integrity check after the commit.
- A backup set that holds the main file and both sidecar files.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Mnemosyne corpus | Bulk removal of filter-selected trivial test sessions from a live local store | The general pattern and the failure modes are recorded in [notes](tooling-opencode-v2-bulk-session-removal-by-filter.notes.md). |

## References

- [OpenCode V2 session deletion effects](tooling-opencode-v2-session-deletion-effects.md): the
  single-session service path and what it removes.
- [OpenCode V2 troubleshooting: database and log locations](https://opencode.ai/v2/docs/troubleshooting/)
- [SQLite: transaction isolation and `BEGIN IMMEDIATE`](https://www.sqlite.org/lang_transaction.html)
- [SQLite: foreign key support](https://www.sqlite.org/foreignkeys.html)