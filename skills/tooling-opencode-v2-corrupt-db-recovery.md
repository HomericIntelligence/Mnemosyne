---
name: tooling-opencode-v2-corrupt-db-recovery
description: "Recover session history from a corrupt OpenCode V2 SQLite database and merge it into a rebuilt install. Use when: (1) the server log shows `database disk image is malformed` or sessions fail to drain with SqlError; (2) you must decide whether the file is really damaged or a stale process older than the installed binary is reading it; (3) the data directory was moved aside and a fresh install must re-integrate old sessions; (4) you must select which tables to merge and which to exclude; (5) you plan backups for a database on shared or network filesystem storage."
category: tooling
date: 2026-10-16
version: "1.1.0"
user-invocable: false
tags: [opencode, sqlite, corruption-recovery, database, session-history, merge, backup]
---

# OpenCode V2 corrupt database recovery and merge

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-16 |
| **Objective** | Restore session history from a malformed `opencode.db` into a clean reinstalled OpenCode V2 without re-corrupting the new database. |
| **Outcome** | Successful. 1,709 of 1,764 session rows (96.9%) and 71,829 of 71,868 message rows (99.95%) recovered from a 765 MB malformed database and merged into the live database. Verified end to end through the running service (restored sessions list and open by project). Verified against OpenCode v2.0.29–v2.0.31. |

## When to Use

- The OpenCode V2 server log repeats `SQLiteError: database disk image is malformed`, and sessions fail with `Failed to drain Session` or `Failed to publish Session execution lifecycle`.
- You already moved the data/state/cache directories aside (for example to `.bak` siblings) and started fresh, and now must re-integrate the salvaged state.
- You must decide which tables and directories are safe to merge and which must stay excluded.
- The database lives on shared or network filesystem storage and you want a backup plan before the same failure class repeats.

Do not use this workflow to repair the corrupt file in place. Keep the corrupt sources read-only evidence and merge salvaged rows into the live database instead.

Do not start a salvage or rebuild because the log says `malformed` alone. This message can come from a stale reader against an intact file. Rule out that case first (step 1).

## Verified Workflow

### Quick Reference

```bash
DB=~/.local/share/opencode.bak/opencode.db          # corrupt source (any moved-aside copy)
sqlite3 "file:$DB?mode=ro&immutable=1" .recover > recovered.sql   # salvage rows
sqlite3 recovered.db < recovered.sql                # build a clean recovered DB
sqlite3 "file:recovered.db?mode=ro" "PRAGMA integrity_check;"     # gate: must print ok
opencode service stop                                # no second writer during the merge
sqlite3 ~/.local/share/opencode/opencode.db < merge.sql           # see Results & Parameters
opencode service start
```

### Suggested Approach

1. **Bind the failure class before any write.** Run `PRAGMA integrity_check;` through a `mode=ro` URI on the **live** database first, and treat `ok` as a stop condition for salvage. An integrity-clean live database means the message came from the reader, not the file: a process from an older version applied a schema migration and then read through a rewritten index, so only the indexed access path fails (in the verified case every failure was `select ... from "session_message" ... order by seq`, and the corrupt snapshot reported `Child page depth differs` on the index root page). Compare the versions of the live processes against the installed binary (`grep 'cli starting'`, `opencode --version`): a running service older than the installed binary is the signature. Fix that case by stopping every process and starting once; do not salvage. When the live file does not check clean, bind the torn-write signature from the moved-aside copy: `Rowid out of order`, `invalid page number`, `Child page depth differs`, and duplicate page references across B-trees. Never open the corrupt file for writes; `mode=ro&immutable=1` also prevents journal replay against it.
2. **Record expectations before salvage.** `SELECT count(*)` per key table can succeed on a corrupt database through an intact index even when full scans die mid-way. These counts are the ceiling the salvage can reach, not proof the rows are readable.
3. **Salvage with `.recover`, rebuild, and gate.** `.recover` on a 765 MB source completed in about 15 s on fast storage and produced a dump that rebuilt into an integrity-clean database. Compare the rebuilt counts against the expectations; the delta is the true page-loss set. Then classify `lost_and_found` rows before assuming they are lost table rows: compare `nfield` with each table's column count and sample the `c0..cN` values. Index entries have short keys plus a rowid; real rows carry full column data and JSON payloads. Reattach nothing that is index-shaped.
4. **Stop the service for the whole merge window.** The observed trigger for the corruption was a duplicate background service spawning, followed seconds later by a hot binary upgrade, against a live database on network storage — a torn-write class. Do not reintroduce a concurrent writer during recovery. Gate on a write lock: `sqlite3 <live.db> "BEGIN IMMEDIATE; ROLLBACK;"` must succeed before merging; fail fast and retry later if it stays locked.
5. **Merge with named column lists and `INSERT OR IGNORE`.** Column *order* inside a table can differ between database generations (observed on `project`), so `(col, ...) SELECT col, ...` explicitly. Primary-key conflicts keep the live row, so the fresh install's current sessions always win.
6. **Merge domain tables; exclude runtime and migration tables.** Restore: `project`, `worktree`, `session_v2`, `session_message`, `instruction_blob`, `instruction_state`, `permission`, `event_sequence`, and `kv` rows where `key NOT LIKE 'job.background/%'`. Exclude: `migration` (the rebuilt install is the schema authority), `session_inbox` (a transient execution queue; resurrecting days-old queued steps reproduces the drain-failure cascade), and `job.background/*` kv rows (stale background-job state can resume dead work against the restored messages).
7. **Re-integrate the file trees with no overwrite.** Union-copy `snapshot/`, `tool-output/`, and `shell/` from the moved-aside data directory with `cp -rn`; fresh files win collisions. Restore the small state files (`model.json`, `prompt-history.jsonl`, `frecency.jsonl`, `session.json`) by merging rather than replacing, again while the service is stopped because running instances rewrite these files from memory.
8. **Verify through the product, then back up.** After restart: `PRAGMA integrity_check` on the live database, restored counts present, and `opencode session list -n 1000` inside a project directory returns the restored history (the list counts top-level sessions of the current project, so a global count needs the database query). Take one `sqlite3 <live.db> ".backup '<dst>'"` online backup immediately; the WAL-aware backup API is safe while the service runs.
9. **Prevent the same class.** Keep the service stopped during upgrades and avoid duplicate service processes; both conditions preceded the failure here. Retire the moved-aside directories only as a separate destructive step after the restored history is confirmed in the product.

### Optional: archive transcripts after recovery

A per-session JSONL dump of the merged database (one file per session, header line plus message lines in sequence order; orphan messages grouped under a separate directory) gives a readable archive outside SQLite. Derive per-file skip logic from the session `time_updated` plus message count so reruns stay cheap while the live database keeps growing. When you synthesize file names for sessions whose header rows were lost, take the identifier from the messages themselves — a fixed fallback name makes every group overwrite one file.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Emergency file copy after errors began | Copied `opencode.db` aside two hours after the first `malformed` log entry. | `PRAGMA integrity_check` reported the corruption earlier than the copy; both copies had identical corrupt pages, so the snapshot added no recovery value. | Verify a database copy with `integrity_check` before treating it as a recovery source; the only certain good copy predates the first error. |
| Salvage planned from the `malformed` string alone | Started repair from the repeated log error without checking the live file. | The live database passed `integrity_check` and served history normally; the error came from a live process older than the installed binary, whose index walk raced a schema migration by a newer process. Recovery would have discarded an intact database. | Check the live database with `integrity_check` and compare running versions to the installed binary before any salvage. `malformed` is a symptom, not a verdict on the file. |
| Manual SELECT salvage from the corrupt file | Queried sessions and grouped messages directly on the malformed database. | Aggregate counts returned values through intact indexes, but full scans and grouped queries aborted mid-way with `database disk image is malformed`; partial reads look complete only by accident. | Salvage through `.recover` into a fresh file; never trust direct reads of a corrupt tree as complete. |
| Reattach `lost_and_found` rows as lost table rows | Planned to push all 2,452 salvage-orphaned rows back into their tables. | Sampling by `rootpgno` and `nfield` showed every row was an index entry (short key columns plus a rowid, for example a `(session_id, type, seq)` index), not table data; insertion would have added garbage duplicates. | Treat `lost_and_found` as evidence, not data: classify by field count and content shape, and decline reattachment when rows are index-shaped. |
| Automated backup schedule through the user crontab | Installed a daily `sqlite3 .backup` cron entry. | The host denied user crontab use (`cron.allow`), and no systemd user bus was available for a timer fallback. | Probe scheduler availability (`crontab -l`, `systemctl --user status`) before promising automation; otherwise deliver the tested script with an exact manual invocation. |

## Results & Parameters

### Configuration

Merge skeleton (single transaction; bail on error; roll back on close):

```sql
.bail on
PRAGMA busy_timeout=120000;
ATTACH '/path/to/recovered.db' AS rec;
BEGIN IMMEDIATE;
INSERT OR IGNORE INTO project (id, worktree, vcs, name, icon_url, icon_url_override,
  icon_color, time_created, time_updated, time_initialized, time_active, time_archived,
  sandboxes, commands)
  SELECT id, worktree, vcs, name, icon_url, icon_url_override, icon_color, time_created,
  time_updated, time_initialized, time_active, time_archived, sandboxes, commands
  FROM rec.project;
INSERT OR IGNORE INTO session_v2 (id, project_id, /* ...full column list... */ resume_attempts)
  SELECT id, project_id, /* ...full column list... */ resume_attempts FROM rec.session_v2;
INSERT OR IGNORE INTO session_message (id, session_id, type, seq, time_created, time_updated, data)
  SELECT id, session_id, type, seq, time_created, time_updated, data FROM rec.session_message;
INSERT OR IGNORE INTO kv (key, value, time_created, time_updated)
  SELECT key, value, time_created, time_updated FROM rec.kv
  WHERE key NOT LIKE 'job.background/%';
COMMIT;
DETACH rec;
PRAGMA wal_checkpoint(TRUNCATE);
```

Daily online backup service (works while the service runs; prunes to the last seven):

```bash
sqlite3 "$HOME/.local/share/opencode/opencode.db" ".backup '$HOME/.local/share/opencode/backups/opencode-$(date +%Y%m%d-%H%M%S).db'"
sqlite3 "file:<that-file>?mode=ro" "PRAGMA quick_check;"   # expect: ok
```

### Expected Output

- The rebuilt recovered database prints `ok` from `integrity_check`; merged live database also prints `ok`.
- Live counts reach restored totals (in the verified run: 16 projects, 1,710 sessions, 71,864 messages), and no `Failed to drain` entries appear in the new server log.
- `opencode session list -n 1000` run inside a restored project directory lists the recovered history; sessions whose pages were destroyed open with truncated or missing transcripts (about 3% of sessions here) and are identifiable by message count 0.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2.0.29–v2.0.31 (public release) | 765 MB malformed `opencode.db` (1,764 sessions, 71,868 messages) on network filesystem storage; trigger: duplicate service spawn plus hot upgrade while live | [notes.md](../skills/tooling-opencode-v2-corrupt-db-recovery.notes.md) |
| OpenCode v2.1.x (public release) | Intact `opencode.db` that reported `malformed` from a live process older than the installed binary during a version overlap; `integrity_check` clean, history served normally | [notes.md](../skills/tooling-opencode-v2-corrupt-db-recovery.notes.md) |

## References

- [SQLite `.recover` command and recovery API](https://sqlite.org/cli.html#recover_data_from_a_corrupted_database)
- [SQLite Backup API usage](https://sqlite.org/backup.html)
- [OpenCode V2 troubleshooting: database and log locations](https://opencode.ai/v2/docs/troubleshooting/)
- Related: [tooling-opencode-v2-session-deletion-effects](tooling-opencode-v2-session-deletion-effects.md)
- Related: [slurm-shared-storage-artifact-relocation](slurm-shared-storage-artifact-relocation.md)
