# Notes: OpenCode V2 Prior-Session Evidence Recovery

Supporting evidence for `tooling-opencode-v2-prior-session-evidence-recovery`.
Repository, organization, and issue identifiers from the source tasks are
withheld; session ids are instance-local and carry no external meaning.

## Source event (2026-10-24)

A coordinator message arrived in a fresh continuation session: the referenced
task was declared verified-durable "(see tracker)" and a DONE ceremony —
durable learning, session rename, short report — was requested. The message
carried the intended session title but none of the task's content, commands,
or outputs. Options were: ask the user (round-trip), declare no evidence
(false), or recover the record.

Recovery path that worked:

1. `grep` of the interactive shell history for the release keywords → empty.
2. `~/.opencode/sessions/` → only empty year directories; no transcripts.
3. `~/.local/share/opencode/opencode.db` → live SQLite store. Schema was
   introspected with `.tables` and `.schema session_v2`; the evidence tables
   are `session_v2` (identity) and `session_message` (`session_id`, `seq`,
   `type`, `data` JSON, unique on `(session_id, seq)`).
4. Title lookup found exactly three candidate sessions, including the prior
   planning/build session and the current ceremony session itself. The
   planning session's directory (a private monorepo checkout) and user
   messages confirmed the binding.
5. Extraction by `seq` ranges reconstructed the task: operator prompts, the
   milestone-creation commands, the midnight-UTC due-date defect and its
   noon-UTC repair, batch assignment loops, failure logs, and the final
   zero-unassigned verification output. Roughly 30 message rows across five
   `seq` windows were enough for the complete evidence base.
6. The recovered evidence fed normal corpus duplicate analysis and supported
   a durable-learning PR (merged 2026-10-26) plus the session rename — the
   full ceremony with no user round-trip.

## Traps observed in the same flow

- First time filter used a microseconds-scale threshold and returned zero
  rows with no error. Checking `datetime(time_updated/1000,'unixepoch')` on a
  known row exposed the millisecond unit.
- Six days later, `time_updated`-descending listing showed ~40 sessions
  stamped within a single two-minute window — a service-restart or migration
  wave had bulk-touched them. The genuinely newest work was only findable by
  `time_created` and by in-session `seq`.
- `*.poison-*` and `*.bak-*` siblings of the database existed from a past
  incident; the live database passed use as-is, so they were left untouched
  (the corrupt-db-recovery skill covers their provenance and use).

## Verification statements

- `sqlite3` version used: a distribution-default 3.x CLI; `json_extract` was
  not needed for this flow because a Python JSON pass over `data` was clearer
  for nested `content[]` arrays.
- No writes were made to the store. Extraction mattered only for reading;
  durable writes went to the knowledge repository, with live re-verification
  (open-PR listing, corpus revision) before publication.
- The assistant-row `content[]` JSON shape observed: entries with
  `type` in {`text`, `reasoning`, `tool`}; tool entries carry
  `state.input.command` for shell calls, `state.input.code` for runtime
  calls, and `state.output` for results. Truncating each field at ~500
  characters kept single-row output navigable while preserving the decision
  content.
