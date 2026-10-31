# Notes: OpenCode V2 corrupt database recovery and merge

Companion evidence for [tooling-opencode-v2-corrupt-db-recovery](tooling-opencode-v2-corrupt-db-recovery.md).
Long commands, measurements, and verification detail live here; every rule the
skill needs for operation lives in the main file. Values come from the verified
incidents below: one recovery on OpenCode v2.0.29–v2.0.31 public releases, a
stale-reader misdiagnosis on v2.1.x, and a post-merge sequence-counter defect on
v2.1.x. Identifiers of individual sessions, hosts, and installations are
generalized.

## Timeline of the observed incident

1. Background service reported `previousVersion=undefined`; a second
   `serve --service` process spawned.
2. About 15 s later a CLI `upgrade` ran the installer for the next patch
   version while sessions were draining.
3. About 40 s after the upgrade began, the server log produced the first
   `SQLiteError: database disk image is malformed` on `session_message`
   inserts. The error then repeated about 1,200 times (every session drain)
   until the service was stopped about 2.5 h later.
4. Triage moved data/state/cache directories to `.bak` siblings and a fresh
   install created a new empty database. The configuration directory was never
   affected (a sibling `config.bak` observed on the host predated the incident
   by days and belonged to an older major-version archive). V1-era session
   JSONL files under `~/.opencode/sessions/` also stayed intact because they
   are not V2 paths.

## Stale-reader misdiagnosis (intact file, `malformed` in the log)

A second incident produced the same `malformed` string with an undamaged file.
It is recorded because it changes the first decision of this workflow.

- The live database passed `PRAGMA integrity_check` (`ok`) while the log held
  hundreds of `SQLiteError: database disk image is malformed` entries.
- Every failure used one shape: `select id, session_id, type, seq,
  time_created, time_updated, data from "session_message" ... order by seq`.
  Point reads and history listing worked; only the indexed path failed.
- The version timeline showed an overlap: the first error appeared, an older
  build kept starting for another 14 min, and the next build started 4 min
  after that. Both builds ran against the same database.
- In the retained corrupt snapshot from that window, `integrity_check`
  reported `Child page depth differs` on tree 49. Tree 49 was the
  `(session_time_created, id)` index on `session_message`, not the table.
  Damage limited to the index B-tree is consistent with a reader walking an
  index that another process had already rebuilt, not with torn writes on the
  data pages.
- A controlled test on the same network filesystem (four concurrent writers,
  WAL mode, 1,600 inserts) produced zero errors and an integrity-clean result.
  This removes the filesystem from the cause list for this incident.
- Consequently, a salvage run here would have replaced a healthy database.

## Corruption and salvage measurements

Source: 765 MB `opencode.db`, WAL-checkpointed single file (no `-wal`/`-shm`
siblings by the time of triage).

`PRAGMA integrity_check` (read-only URI) reported B-tree damage across several
trees:

- `Rowid <n> out of order` (multiple trees and pages)
- `invalid page number 168432384`
- `Child page depth differs`
- `2nd reference to page <n>` (cross-tree duplicate)
- `Page <n>: never used`

Expectation counts taken directly on the corrupt file returned
`session_v2=1,764`, `session_message=71,868`, `event=0` — counts succeeded
through intact indexes while row scans failed (`GROUP BY` on `session_id`
aborted with malformed mid-scan).

Salvage run (sqlite3 3.51.1):

```bash
sqlite3 "file:<corrupt>?mode=ro&immutable=1" .recover > recovered.sql   # ~14 s, 718 MB of SQL
sqlite3 recovered.db < recovered.sql                                    # ~21 s, 774 MB
sqlite3 "file:recovered.db?mode=ro" "PRAGMA integrity_check;"           # ok
```

Result: `session_v2=1,709` (55 rows lost), `session_message=71,829` (39 rows
lost), `lost_and_found=2,452`.

## lost_and_found classification method

1. `SELECT rootpgno, count(*), min(nfield), max(nfield) FROM lost_and_found GROUP BY rootpgno ORDER BY 2 DESC;`
2. Join `rootpgno` against `sqlite_master.rootpage` in the recovered file.
   None of the orphaned root pages mapped to a schema object.
3. Sample `c0..cN` values per group. All groups were index-shaped:
   - `nfield=2`: single key plus rowid (message-id index, timestamp index).
   - `nfield=3`: two keys plus rowid.
   - `nfield=4`: three keys plus rowid, for example
     `(session_id, type, seq, rowid)` from a `session_message` lookup index.

Conclusion in this run: zero table-row orphans; all 2,452 rows were index
debris, so nothing was reattached. The 39 lost message rows and 55 lost
session rows were on destroyed data pages and unrecoverable.

## Schema drift observed between database generations

Same OpenCode major version family, different generations of the same table:

- `project`: identical column set, different column order
  (`time_archived` appeared before `sandboxes`/`commands` in one generation,
  after in the other). Every other merged table had identical shape and order.

Table inventory of the source (rows): `project=16`, `worktree=531`,
`session_v2`, `session_message`, `instruction_blob=795`,
`instruction_state=1,764`, `permission=1`, `event_sequence=1,771`, `kv=8`,
`session_inbox=52`, `migration=50`, `account*`/`credential`=0, `event`=0.

Merge policy applied (see main file for rationale):

- Merged: all above except exclusions; `kv` filtered with
  `key NOT LIKE 'job.background/%'` (seven stale background-job records
  excluded; they reference restored message ids and could resume dead work).
- Excluded: `migration` (schema authority is the rebuilt install),
  `session_inbox` (transient execution queue; its later re-drain was the
  visible error cascade), and every empty table.
- Conflict rule: `INSERT OR IGNORE`, so fresh-install rows win primary-key
  collisions. Ordered parents before children (`project` → `session_v2` →
  `session_message` → satellites) inside one `BEGIN IMMEDIATE` transaction.

Messages whose session row was lost stayed orphaned (about 9,500 rows, 13% of
messages): present in the table but unreachable from any restored session.
Left in place; deletion was not authorized by evidence.

## State-file merge results (small files, service stopped)

- `prompt-history.jsonl`: 50 old lines + 2 new lines → 33 after exact-line
  dedup (the old file held internal duplicates).
- `model.json`: recent lists unioned new-first; variant maps merged with live
  keys winning; favorites unioned by `(providerID, modelID)`.
- `session.json`: `pinned` unioned.
- `frecency.jsonl`: concatenated with exact-line dedup.

## Verification record after merge

- Live database `PRAGMA integrity_check` → `ok`.
- Post-restart server log: zero `Failed to drain` / `Failed to publish`
  entries; one unrelated benign CLI help error.
- Through the service (`opencode session list` is per-project): restored
  projects listed hundreds of top-level sessions each (531 and 411 in the two
  largest), including a 975-message session from the corrupt window.
- `snapshot/` (about 410 MB after union), `tool-output/`, `shell/` copied
  no-clobber; artifact trees are only needed for old sessions' undo/tool
  output continuity.
- Online backup produced and `quick_check`-verified immediately after merge
  (775 MB). Backup scripting note: rotation must remove `-wal`/`-shm`
  sidecars together with the main file, and probes showed the host denied
  user crontab (`cron.allow`) with no systemd user bus, so scheduling was
  delivered as a manual command instead of an installed timer.

## Transcript dump (optional archival step, evidence for the main-file rule)

- 1,781 JSONL files (1,726 sessions + 55 orphan groups), 72,566 messages,
  about 700 MB; full pass about 30 s on fast storage, incremental rerun about
  12 s with 1,679 files skipped.
- Orphan-group bug caught by verification: a fixed fallback filename made all
  55 orphan groups overwrite one file. Rule recorded in the main file: derive
  identifiers from the messages, not from missing header rows.
- Dump verification sampled random index records, checked header ids, message
  counts, and last-line JSON validity.

## Post-merge sequence-counter defect (v2.1.x, weeks after the merge)

A later batch of new turns sent to many restored sessions showed three distinct
failure signs. Only the third one is the counter defect; the first two must not
trigger counter repairs.

1. Instant failure with `Location not found` for the session's stored project
   directory: the directory was deleted after the session was stored. This is a
   placement defect. The fix is to re-point the session at an existing directory
   through the session-management API (`session_move`-class tooling); counter
   repairs do not apply.
2. Attach hang with no transcript rows beyond two housekeeping rows
   (`agent-switched`, `system`). Both candidate causes (missing directories and
   low counters) were present in the same window, so this sign alone does not
   identify a cause. Treat it as a prompt to run the audit, not as a diagnosis.
3. Turns that ran to completion with large CLI transcripts (hundreds of
   kilobytes of tool activity) but persisted no assistant rows. Some of these
   sessions did persist the incoming user row and two housekeeping rows — at
   `seq` 0–4, with current timestamps, underneath weeks of older history.

### Bind of the cause

- Every affected session had an `event_sequence` row far below the maximum
  `seq` in its merged `session_message` history. Observed counters ranged from
  single digits to a few thousand against stored maxima in the hundreds to
  thousands.
- The service allocates each new message's `seq` from `event_sequence`. With a
  low counter, appends start near zero: the first rows land at still-unoccupied
  low positions (which is why the user row and housekeeping rows persisted),
  and once allocation reaches occupied values the unique `(session_id, seq)`
  index rejects every further insert. The CLI transcript proves the turn ran;
  the missing rows prove the writes did not persist. No error surfaced through
  the product in the observed runs.
- Sessions with no `event_sequence` row appended correctly at high `seq`
  values: the service rebuilds the counter lazily when the row is absent.
  Absence is safe; present-but-low is the only hazardous state.
- A counter slightly above the stored maximum is benign: it only skips a
  couple of `seq` slots (allocated-but-unpersisted turns). The repair query in
  the main file never lowers such a counter.

### Repair record

- One transaction raised 15 low counters to their sessions' stored maxima
  (`UPDATE ... WHERE seq < MAX(session_message.seq)` per aggregate). The live
  service held no conflicting lock; the write committed without error.
- End-to-end proof on one repaired session: counter moved 4 → 967 (the stored
  maximum); a verification turn then persisted five rows at `seq` 968–972, and
  the counter read 972 afterwards — the healthy invariant restored.
- Re-sending turns to repaired sessions needs one extra check: some restored
  sessions recorded model choices that no longer exist in the installed
  provider list, and the turn fails immediately with `Model unavailable` until
  the send overrides the model.

### Verification method after any restore

- Classify recent activity by `time_created` windows (rows newer than the send
  time), never by `MAX(seq)`: while low rows are still landing, `MAX(seq)`
  reports old history as the newest message and every delivered turn looks
  undelivered.
- Turn outcome lives in the newest `idle` row's `outcome` field within the
  window; the newest assistant row's `finish` and `error` fields give the
  model-side result. A delivered turn with neither assistant rows nor an `idle`
  row in the window is a candidate for the counter audit.
- Store-scale context: a full audit found `event_sequence` rows for only about
  1.6k of about 4.3k sessions. Absence is safe, so exposure concentrates in
  sessions that have a row and were touched by a merge or repair.
