---
name: tooling-opencode-v2-bulk-transcript-export
description: "Export every OpenCode V2 session transcript from the live opencode.db to readable JSONL. Use when: (1) you need a searchable archive of all transcripts outside SQLite; (2) the live database keeps growing and re-runs must stay cheap; (3) you need a durability copy of transcripts after a database incident; (4) session_message rows exist whose session_v2 row is missing."
category: tooling
date: 2026-10-17
version: "1.0.0"
user-invocable: false
tags: [opencode, transcripts, export, jsonl, sqlite, incremental, archival]
---

# OpenCode V2 bulk transcript export to JSONL

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-17 |
| **Objective** | Produce a complete, readable, re-runnable archive of every V2 session transcript outside the live SQLite database. |
| **Outcome** | Successful. 1,781 transcript files (1,726 sessions + 55 orphan groups), 72,566 messages, about 700 MB exported from a running service's 775 MB database. Incremental re-run skipped 1,679 of 1,781 files and finished in about 12 s. Verified against OpenCode v2.0.31. |

## When to Use

- You want all V2 transcripts as searchable text (JSONL) outside SQLite: for archival, analysis, or pre-incident insurance.
- The database keeps growing while a service runs, and repeated exports must not rewrite thousands of unchanged files.
- You recovered session history from a damaged database and want transcripts in a form SQLite corruption can no longer destroy.
- `session_message` rows reference session IDs that no longer exist in `session_v2` (orphans; observed after a corruption recovery) and must not be silently dropped.

Do not use this workflow for recovery of a malformed database (recover and merge first, then export) or for the official per-session export used before targeted deletion.

## Verified Workflow

### Quick Reference

```bash
python3 dump-transcripts.py --dest <archive-dir>          # incremental (default)
python3 dump-transcripts.py --dest <archive-dir> --full   # rewrite everything
# produces:  transcripts-v2/projects/<slug>/<YYYY-MM-DD>_<session-id>.jsonl
#            transcripts-v2/_orphans/<session-id>.jsonl
#            transcripts-v2/index.jsonl  +  MANIFEST.txt
```

Each transcript file has one `{"type": "session", ...}` header line followed by one
`{"type": "message", ...}` line per `session_message` row in `seq` order.

### Suggested Approach

1. **Open the live database read-only; keep the service running.** A `file:<db>?mode=ro` URI connection gives a consistent snapshot under WAL without taking locks that disturb writers. Export never requires a service stop, a lock gate, or a checkpoint — unlike a merge into the database.
2. **Derive the layout from durable keys.** Group files as `projects/<slug>/<date>_<session-id>.jsonl` where `slug` comes from the project `worktree` basename (collision-safe: append a short id fragment when two projects share a basename) and `date` comes from `time_created`. Keep the session id in every file name; ids are the only join key you can trust later.
3. **Skip unchanged files for incremental re-runs.** Read the first line of an existing transcript and skip the rewrite when the stored header's `time_updated` and `message_count` both equal the current session row's values. Active sessions keep changing `time_updated`, so they re-export naturally; finished sessions stabilize. Expect >90% skips on routine re-runs (observed: 1,679 of 1,781).
4. **Handle orphan groups as first-class output.** Find message groups whose `session_id` has no `session_v2` row with a `LEFT JOIN ... WHERE s.id IS NULL` anti-join, and dump them under `_orphans/<session-id>.jsonl`. Take the identity — and the display timestamp — from the message rows themselves, because the header row is exactly what is missing. Never use a fixed fallback file name: see the failure table.
5. **Write files atomically.** Render to `<file>.tmp` and `os.replace` onto the target, so an interrupted run cannot leave a torn transcript that the skip logic would later trust. Guard the skip-check parse: any unreadable existing header rewires the file for rewrite.
6. **Verify per file, not by totals.** After each run, load `index.jsonl` and assert: every recorded file exists; each file's header `id` and message count equal its index record; and there are **zero duplicate `file` targets** across records. The duplicate-target check is the one that caught the orphan collision below — aggregate totals were still exactly right while 54 of 55 orphan groups had silently overwritten each other.
7. **Re-run manually when no scheduler exists.** An export is a point-in-time snapshot; a growing database simply makes re-runs worthwhile, not stale. A full pass was about 30 s and an incremental pass about 12 s for about 700 MB on fast storage, so manual re-runs are practical. Probe scheduler availability before promising automation (user crontab can be host-denied; do not assume systemd --user).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Fixed fallback name for header-less groups | Named orphan files `<fallback>.jsonl` when the session header row was missing (`None`), so all 55 orphan groups wrote to one path. | Every group's file overwrote the previous one; the final file held only the last group while all 55 index records pointed at the same path. | Derive an orphan group's file name from the `session_id` carried by its message rows; there is no valid "unknown" bucket when each group is a distinct session. |
| Verification by aggregate totals | Accepted the first run because its file count and message totals matched expectations. | Totals were exact (72,566 messages across 55 index records) even though 54 orphan groups existed only as overwritten index entries. | Always check per-record file existence and duplicate targets; totals cannot detect many-records-one-file collisions. |

## Results & Parameters

### Configuration

Core queries (read-only connection):

```sql
SELECT <columns> FROM session_v2 ORDER BY time_created;
SELECT id, session_id, type, seq, time_created, time_updated, data
  FROM session_message WHERE session_id = ? ORDER BY seq;
SELECT DISTINCT m.session_id FROM session_message m
  LEFT JOIN session_v2 s ON s.id = m.session_id WHERE s.id IS NULL;   -- orphan groups
```

Skip check (per existing file, first line parsed as JSON):

```python
if head.get("time_updated") == sess["time_updated"] and head.get("message_count") == len(msgs):
    return skip  # unchanged since last export
```

### Expected Output

Summary line, for example:

```
dump complete: 1781 transcript files (1679 skipped up-to-date), 72566 messages, 701282663 bytes, 55 orphan groups
```

A clean verification prints zero missing files, zero duplicate targets, and orphan spot-checks whose header ids match their index records.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2.0.31 (public release) | Live 775 MB `opencode.db` with 1,726 sessions and 9,507 orphan messages in 55 groups; service running during export | [notes.md](../skills/tooling-opencode-v2-bulk-transcript-export.notes.md) |

## References

- [SQLite URI filenames (read-only access)](https://sqlite.org/uri.html)
- Related: [tooling-opencode-v2-session-deletion-effects](tooling-opencode-v2-session-deletion-effects.md)
