# Evidence and limits

This record keeps generalized evidence only. It holds no local machine paths, session identifiers,
session content, or account data.

## Verified environment

- OpenCode V2 on a Linux host with a local SQLite store.
- A process was running and used the same database file during the operation.
- The store passed a quick integrity check after the committed delete.

## Schema facts confirmed at the time of writing

The parent session table has an identifier column, a title column, an optional parent identifier
column, and an optional fork-origin identifier column. Child tables that key on the session
identifier declare `ON DELETE CASCADE` to the parent table. Confirm this on the installed schema
before any write; a later release can change the storage design.

Tables observed with a session-identifier column:

- message and message-part tables;
- an inbox table;
- an instruction entry table and an instruction state table;
- a blob reference table;
- a schedule table.

One additional table holds an event log keyed by an aggregate identifier. It existed in the
schema and held zero rows in the observed store. A count for the candidate set was necessary
before concluding that it needed no cleanup.

## Observation about a separate file store

A session-transcript file tree existed under the data directory and held a large number of files.
None of the candidate session identifiers had a file there. This is consistent with the tree
holding a different record set, or holding files only for some sessions. Do not treat an absent
file as proof that the database row is wrong, and do not treat the file tree as the authority for
database contents.

## Why the selection was staged

A cheap parent-row predicate found the candidate set. Content confirmation per candidate needed
row-level parsing because a JSON path function inside SQLite aborted the whole statement on one
invalid message payload. A host-language parse isolates that failure to the one row, and the
remaining candidates still classify.

## Reference checks that mattered

The prefix-based reference count matched unrelated identifiers and produced a false signal. Exact
identifier-set tests produced the correct result: no child sessions, no forks, and no blobs that
only the candidates referenced. Blobs shared with other sessions were excluded with a
`NOT EXISTS` test on the other sessions.

## Verification shape

The commit gate re-counted every affected table for the same frozen identifier list. A non-zero
count in any table triggered a rollback. Two side effects were visible afterwards: the parent
count fell by the size of the set, and the total row count changed by less than that because the
running process created new sessions during the operation.

## Limits

- Verified against one installed V2 release only. Later releases can rename tables or move the
  transcript out of the database.
- The event-log table can carry data in other installations even when it held none here. Count it
  before you assume it is safe to ignore.
- The backup step assumes that the user accepts a local copy of the store as the restore path.
  Do not treat the backup as a substitute for asking when the user wants a transcript kept.