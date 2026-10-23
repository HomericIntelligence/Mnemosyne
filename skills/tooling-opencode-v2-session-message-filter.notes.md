# tooling-opencode-v2-session-message-filter — notes

Supporting evidence from the originating session (2026-10-23). Session
identifiers, user names, internal paths, project names, and issue numbers are
removed; magnitudes are rounded.

## Source tasks

1. "Find all sessions where the last message from the user does not contain a
   given skill invocation; report them."
2. "Send that invocation only to sessions that are marked Done in the title or
   that have no changes today."

## Store observations (live store, read-only)

- Message-type histogram at capture: `assistant` about 70k; `synthetic`,
  `user`, and `idle` in the low thousands each; `compaction`, `system`,
  `model-switched`, `agent-switched`, `shell`, and `location-switched` in the
  low hundreds or less.
- About 50 root sessions out of about 520 total sessions: roughly 90% of the
  store was subagent children. This ratio made `parent_id IS NULL` the
  highest-impact predicate in both tasks.
- Sampled `synthetic` rows all carried `metadata.source = "shell"`
  (background job results). Operator-typed text did not appear in that type.
- The store was live and growing: a WAL of about 28 MB next to a main file of
  about 580 MB. The main-file-only copy used in the first attempt was missing
  exactly those WAL transactions.

## Verified outcomes

- Task 1: the restricted query returned the small expected list. Examining
  the content matches by eye found one false positive: the querying session
  itself, whose request named the skill token as data. Every other match
  started with the token, was a genuine invocation, and a prefix rule
  (`text LIKE '@skill%'`) would have classified it correctly.
- Task 2: composing the content test with `title LIKE 'Done:%'` and a
  midnight staleness boundary selected 15 sessions. Two-snapshot movement
  detection showed all 15 idle. Detached delivery used the batch-send
  workflow; all 15 runs attached and started.
- `REGEXP` failure shape: the query returned no rows and no error text
  reached the terminal through the pipeline. On a large match set, "zero
  rows" can look like "no matches"; that confusion is the real risk.
- `paste` failure shape: `paste -sd"','"` applied its three delimiter
  characters cyclically (`,`, then `'`, then `,`), producing
  `IN ('aaa'bbb'ccc...)`. The SQL parse error pointed at the second value,
  which made the cause visible immediately.

## Evidence limits

- Counts are point-in-time and rounded; the fleet changes continuously, and
  two sessions were actively updated minutes before the snapshot that fed
  the reports.
- Verification used the read store and process state only. No export of an
  actively written session was trusted as evidence.
