---
name: tooling-opencode-v2-counterpart-session-discovery
description: "Find which local OpenCode V2 session is coordinating with an external agent through a shared handoff. Use when the owner asks which session is working with another agent, when the latest handoff note has no local reader, or when near-identical session titles make a title match unsafe."
category: tooling
date: 2026-11-09
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [opencode, session, sqlite, multi-agent, handoff, counterpart, goal, liveness, external-agent]
---

# OpenCode V2 Counterpart Session Discovery

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Name the local session that coordinates with an external agent, or report that no local session does. |
| **Outcome** | Successful. A content query and the session goal record bound the active local session. The newest handoff note had no local reader, so the external agent was reported as outside the local store. |

## When to Use

- The owner asks which session is working with another agent, or names a shared handoff directory.
- Several sessions have similar, duplicated, or auto-generated titles.
- The latest handoff note may be authored by an external account.
- A title match would select the current question-and-answer session or an idle sibling.

## Verified Workflow

### Quick Reference

```bash
DB="file:$HOME/.local/share/opencode/opencode.db?mode=ro"
SELF="${OPENCODE_SESSION_ID:?}"

# Candidate sessions by handoff content, not by title.
sqlite3 -separator $'\t' "$DB" "
SELECT s.id, s.title, s.directory,
       datetime(MAX(m.time_created)/1000,'unixepoch') AS last_message
FROM session_message m
JOIN session_v2 s ON s.id = m.session_id
WHERE m.data LIKE '%<handoff token>%'
  AND s.id <> '$SELF'
GROUP BY s.id
ORDER BY MAX(m.time_created) DESC;"

# Stated objective, when a goal record exists.
sqlite3 -separator $'\t' "$DB" "
SELECT key, json_extract(value,'$.objective'), json_extract(value,'$.status')
FROM kv
WHERE value LIKE '%\"objective\"%'
  AND key LIKE '%<session-id>%';"

# Identity proof: the first user prompt and the latest message time.
sqlite3 "$DB" "
SELECT seq, datetime(time_created/1000,'unixepoch'),
       substr(json_extract(data,'\$.text'),1,200)
FROM session_message
WHERE session_id='<session-id>' AND type='user'
ORDER BY seq LIMIT 3;"
```

### Suggested Approach

1. Search the newest handoff artifact's exact filename or a distinctive phrase in `session_message.data`. The store records the tool calls and outputs that touched the handoff.
2. Exclude `OPENCODE_SESSION_ID`. An auto-generated title can make the current question-and-answer session look like the target.
3. Bind by two independent signals: message content and the stated goal. A goal record is in the plugin `kv` state under a key that ends in the session ID. The key prefix can be encoded. Match the JSON `$.objective` value when a literal key search returns no rows.
4. Measure activity with `MAX(time_created)` in `session_message`. A service restart or store reconcile can touch `time_updated` on many idle sessions.
5. Check the newest handoff note's author and the local reader set. If no local session read it, the counterpart is external. Report that limit. Do not attribute the note to a title-matched local session.
6. Report the bound ID, title, directory, first user prompt, stated goal, last message time, and any external-session limit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Title match | Selected the session whose title matched the handoff topic | The current question-and-answer session had an auto-generated title from the same words. An idle sibling had a similar title. | Titles are labels. Exclude the caller and bind by message content. |
| `time_updated` recency | Read the most recently updated session row | A store reconcile stamped many idle sessions in the same minute. | Use the latest message `time_created` for activity. |
| Local-store assumption | Assumed every agent session is in the local database | The external agent ran under another account. Its row was absent, and only its note authorship was visible. | Report the external limit. Do not invent a local owner. |
| Note as authority | Took the handoff note's requested mutation as approval | A note is evidence, not an authorization record. | Verify owner authority before a production change. |

## Results & Parameters

### Configuration

```yaml
store: "$HOME/.local/share/opencode/opencode.db"
access: "file:<store>?mode=ro"
session_table: session_v2
message_table: session_message
message_text: "$.text"
activity: "MAX(session_message.time_created)"
goal_table: kv
goal_objective: "$.objective"
```

### Expected Output

- One bound session ID, or an explicit `no local reader` result.
- The first user prompt matches the coordination task.
- The latest message time is newer than the idle siblings.
- The report states whether the counterpart is local or external.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Local OpenCode V2 installation | An owner asked which session coordinated with an external agent through a shared handoff | The content query and goal record bound the active local session. The newest note had no local reader, and the external session ID was absent from the local store. |

## References

- [tooling-opencode-v2-prior-session-evidence-recovery](tooling-opencode-v2-prior-session-evidence-recovery.md)
- [tooling-opencode-v2-current-session-identity-binding](tooling-opencode-v2-current-session-identity-binding.md)
- [tooling-opencode-v2-session-message-filter](tooling-opencode-v2-session-message-filter.md)
- [multi-agent-discussion-board-debugging-protocol](multi-agent-discussion-board-debugging-protocol.md)
