---
name: tooling-opencode-v2-session-message-filter
description: "Find and list OpenCode V2 sessions by the content of their stored messages, such as sessions whose last user message lacks a skill invocation. Use when a title filter cannot express the condition, when the last message from the human user is the decision input, or when the result feeds a batch operation."
category: tooling
date: 2026-10-23
version: "1.0.0"
user-invocable: false
tags: [opencode, session, sqlite, message-content, last-message, subagent-exclusion]
---

# OpenCode V2 session filtering by message content

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Select the sessions whose stored messages satisfy a condition, such as a missing skill invocation in the last user message. |
| **Outcome** | Successful. Two fleet questions were answered on a live multi-hundred-session store (OpenCode v2.1.1): a list of sessions whose last user message lacked a skill invocation, and a content-plus-recency target list that fed a batch send. |

## When to Use

- A user asks which sessions satisfy a condition on message text: contains, lacks, starts with, or ends with a token.
- The last message from the human user is the decision input, not any message.
- Authorship matters: only text that the human typed counts.
- A recency condition applies, such as "no changes today".
- The selected sessions feed a follow-up action, such as a batch message.

## Verified Workflow

### Quick Reference

```bash
# Last user message of each root session, from the live store (read-only):
sqlite3 -separator $'\t' "file:$HOME/.local/share/opencode/opencode.db?mode=ro" "
WITH last_user AS (
  SELECT session_id, MAX(seq) AS maxseq
  FROM session_message
  WHERE type = 'user'
  GROUP BY session_id
)
SELECT s.id, s.title, s.time_updated,
       substr(json_extract(m.data, '\$.text'), 1, 120)
FROM session_v2 s
JOIN last_user lu ON lu.session_id = s.id
JOIN session_message m
  ON m.session_id = s.id AND m.seq = lu.maxseq AND m.type = 'user'
WHERE s.parent_id IS NULL
ORDER BY s.time_updated DESC;"
```

### Suggested Approach

1. Open the live store read-only with the URI form `file:<db>?mode=ro`. The service keeps running, and the read gets a consistent snapshot under WAL. Do not stop the service. The transcript-export skill in References uses the same access pattern.
2. If an offline copy is necessary, copy `<db>`, `<db>-wal`, and `<db>-shm` in one operation. A copy of the main file alone is complete only after a full checkpoint; before that, it silently lacks recent transactions.
3. Restrict the message set before any content test:
   - `type = 'user'`: only text that the human sent. `synthetic` rows carry injected tool results (inspect `metadata.source`). `idle`, `compaction`, `system`, and `*-switched` rows are housekeeping rows.
   - `session_v2.parent_id IS NULL`: only root sessions. Child sessions belong to subagents, and their `user` rows contain the prompt of the parent agent. Child sessions can be the large majority of the store; without this filter, agent-authored text dominates the result.
4. Use `MAX(seq)` per session to find the last message, then join back on `(session_id, seq)`. The unique index on that pair makes the join exact.
5. Read the visible text with `json_extract(data, '$.text')`. It is a top-level field, not a parts array.
6. Treat a substring match on a mention token such as `@skill` as a candidate, not as proof of invocation. The token also occurs in mentions, in quoted requests, and in the request of the querying session itself. For a small result set, examine each match: an invocation starts with the token or states the invocation intent around it. Adjudicate the requesting session explicitly.
7. Express recency on the epoch-millisecond columns (`time_updated`, `time_created`). Divide by 1000 for `datetime(..., 'unixepoch')`. State the day boundary (UTC or local) before you apply a "today" filter.
8. Compose the filters in SQL: the content test on the joined last row, plus the recency and authorship predicates. When the result feeds a delivery, give the candidate list to `tooling-opencode-v2-batch-session-messages` and re-derive the state at send time. Do not add send logic here.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Offline copy of the database file only | Copied `opencode.db` to scratch space, then ran the selection | The copy silently missed every transaction still in the WAL; recent sessions and messages were absent | Copy `<db>`, `<db>-wal`, and `<db>-shm` together, or skip the copy and query the live store with `mode=ro` |
| `REGEXP` word-boundary match in the `sqlite3` CLI | `text REGEXP '(^|[^a-z])@skill'` to separate invocations from mentions | The stock CLI has no REGEXP implementation; the query returned no rows and no visible error in the pipeline | Use `LIKE` to make a shortlist, then post-filter or adjudicate in the shell |
| Unscoped substring count | `LIKE '%@skill%'` over all user-type rows to count invocations | The matches included the querying session's own request (a mention, not an invocation) and subagent prompts | Apply the type, root-session, and last-row restrictions first; examine the matches that survive |
| `paste`-built SQL `IN` list | `ids | paste -sd"','"` to build `'a','b','c'` | `paste -d` cycles through its delimiter string one character at a time; the generated SQL was malformed | Quote each value first, then join with a single-character delimiter: `sed "s/.*/'&'/" | paste -sd,` |

## Results & Parameters

### Configuration

- Store: `~/.local/share/opencode/opencode.db` (SQLite, WAL mode).
- `session_v2`: one row per session. Columns used here: `id`, `parent_id`, `title`, `time_updated` (epoch ms).
- `session_message`: one row per message. Columns used here: `session_id`, `type`, `seq`, `time_created`, `data` (JSON). Unique index on `(session_id, seq)`.
- Message text: `json_extract(data, '$.text')`.
- Prefix test for a bare invocation: `text LIKE '@skill%'`. A full-text `LIKE '%@skill%'` finds mentions as well; adjudicate those matches.

### Expected Output

- One row per root session: session id, title, last update, and a text preview.
- A fleet with heavy subagent use returns far fewer rows than the raw session count. That ratio is a useful sanity check on the `parent_id` filter.
- The list is stable for finished sessions. Active sessions can change their last user message at any time; state the snapshot time in the report.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Local OpenCode V2 installation (v2.1.1) | Operator request: list root sessions whose last user message lacks a skill invocation, then deliver the invocation only to the subset that a title prefix and a staleness rule selected | [notes](tooling-opencode-v2-session-message-filter.notes.md) |

## References

- [OpenCode V2 documentation](https://opencode.ai/v2/docs/) and the V2 troubleshooting guide (storage locations)
- [tooling-opencode-v2-batch-session-messages](tooling-opencode-v2-batch-session-messages.md) — delivery to the selected sessions
- [tooling-opencode-v2-bulk-transcript-export](tooling-opencode-v2-bulk-transcript-export.md) — the same read-only WAL access pattern for full export
- [tooling-opencode-v2-session-model-audit](tooling-opencode-v2-session-model-audit.md) — `json_extract` message-store queries for model inventory
