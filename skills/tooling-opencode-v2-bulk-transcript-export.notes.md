# Notes: OpenCode V2 bulk transcript export to JSONL

Companion evidence for
[tooling-opencode-v2-bulk-transcript-export](tooling-opencode-v2-bulk-transcript-export.md).
Measurements, script mechanics, and the defect timeline live here; every rule
needed for operation lives in the main file. Values come from one verified
export on OpenCode v2.0.31 (public release).

## Why a bulk export exists

The export ran immediately after a corrupt-database recovery: once the merged
live database was verified, transcripts were copied to JSONL so that any future
SQLite incident can no longer take the history with it. A second, independent
reason appeared during the same run: the service was active, so the database
grew between runs — three new sessions and about 240 messages arrived during
roughly one hour of verification work. Bulk re-runs had to be cheap.

## Script mechanics (as verified)

Single-file Python 3 script, stdlib only (`sqlite3`, `json`, `os`, `datetime`,
`argparse`):

- Connection: `sqlite3.connect(f"file:{db}?mode=ro", uri=True)` — read-only
  URI; the service ran throughout; no journal/WAL interaction needed beyond
  the read snapshot.
- Session header columns exported verbatim from `session_v2` (subset):
  `id, project_id, workspace_id, parent_id, fork_session_id, slug, directory,
  title, agent, model, time_created, time_updated, time_idle, tokens_input,
  tokens_output, tokens_reasoning, tokens_cache_read, tokens_cache_write,
  cost, summary_additions, summary_deletions, summary_files`, plus
  `type, source, orphan, project_dir, message_count` enrichment fields.
- Message records keep `id, session_id, type (as msg_type), seq, time_created,
  time_updated` and parse `data` from JSON text into a nested object, falling
  back to the raw string on parse failure so no row is ever dropped.
- File write: full render to `<target>.tmp`, then `os.replace(tmp, target)`
  (atomic on POSIX). The skip check wraps the existing-header parse in a
  broad `except: pass` that falls through to a rewrite — one knob covers torn,
  truncated, and format-changed files.
- Truly concurrent growth: the service added a new session-between-runs row
  set without any effect on the export; WAL keeps the reader's snapshot.
  A mid-scan session deletes or rewrites nothing the exporter relies on.

## Layout produced

```
<dest>/transcripts-v2/
  projects/<slug>/<YYYY-MM-DD>_<session-id>.jsonl   # 1,726 session files
  _orphans/<session-id>.jsonl                       # 55 orphan groups
  index.jsonl                                       # 1,781 records, one per file
  MANIFEST.txt                                      # run summary
```

Index record shape:
`{"id", "project", "title", "time_created", "time_updated", "messages",
"bytes", "file", "orphan"}`.

Observed totals: 1,781 files, 72,566 messages, 701,282,663 bytes
(about 700 MB) from a 775 MB database. Python-side JSON expansion roughly
matches the raw row size; plan destination space at about the database size.

## Defect found by verification (the main-file rule exists because of this)

First full run reported plausible success:

```
dump complete: 1778 transcript files, 72326 messages
```

Per-file inspection then showed two index records with the **same** `file`
value, `_orphans/unknown.jsonl`, with **different** byte counts — the smoking
gun. Root cause: orphan sessions have no `session_v2` row, so the file-naming
expression resolved the id from the missing header to a fixed `"unknown"`
fallback; all 55 orphan groups wrote the same single path, each group
overwriting the last. Only the final group survived on disk; the `index.jsonl`
message totals remained exactly correct because they were summed per group,
not read back from files.

Fix (three small changes, then re-run): pass the orphan `session_id` from the
message rows as an explicit hint, derive the group's display timestamp from its
first message's `time_created`, and always name orphan files
`_orphans/<session-id>.jsonl`. Delete the bogus shared file before re-running.
Post-fix verification: 55 distinct orphan files; zero duplicate targets across
all 1,781 index records; missing-file count 0.

Verification snippet actually used (reusable as-is):

```python
import json, os
idx = [json.loads(l) for l in open("index.jsonl")]
missing = [r["file"] for r in idx if not os.path.exists(r["file"])]
dup = len(idx) - len(set(r["file"] for r in idx))
assert not missing and not dup
# plus: for sampled records, header id == index id and
# counted message lines == index record's message count
```

## Incremental behavior measured

| Pass | Files | Skipped | Wall time | Notes |
| --- | --- | --- | --- | --- |
| Full | 1,781 | 0 | ~30 s | includes index rebuild |
| Incremental (1 h later) | 1,781 | 1,679 | ~12 s | 3 new sessions + ongoing active ones re-exported; orphan groups always rewritten |

Orphan groups bypass the skip check deliberately: they have no session row, so
there is no trustworthy `time_updated` signal. Their aggregate size was small
in this database; if a recovered database ever produces large orphan sets, the
same timestamp+count trick can be applied to a synthesized header.

## Boundaries

- Point-in-time snapshot: the index records a run started/ended state; nothing
  streams. Re-run to advance the snapshot.
- Read-only means read-only: the export never locks, checkpoints, or stops the
  service. Any workflow that *writes* the database (merge, restore, deletion)
  is a different intent with different gating (see the companion corrupt
  database recovery and merge skill, delivered separately).
- Host scheduler was unavailable in the verification environment (user
  crontab denied by policy, no systemd user bus), so the operational mode
  delivered was a manual re-run command; the 12 s incremental cost makes that
  acceptable.
