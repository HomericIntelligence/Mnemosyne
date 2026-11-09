# Notes: OpenCode V2 counterpart session discovery

## Source context

An owner asked which local OpenCode V2 session was coordinating with a second agent through a shared
handoff directory. The handoff notes were authored by the second agent. Several local sessions had
titles that contained the same words as the handoff topic.

## What the store showed

| Check | Result |
| ------- | -------- |
| Content search for the newest handoff filename | Two local sessions had touched older notes in the same directory. |
| Goal record search | One local session carried the stated objective to work with the other agent. |
| First user prompt | That same session opened with the command-validation task named by the handoff. |
| Latest message time | That session was still writing messages. The other candidates were idle. |
| Newest handoff note | The external agent authored it. No local session had read it. |

The active local session was the correct counterpart. The external agent's session ID was absent
from the local store because it ran under another account. The correct report therefore named the
local session and stated the external-session limit. It did not claim that the local session had
read the newest note.

## Traps that changed the answer

1. **Auto-generated title.** The current question-and-answer session had a title generated from the
   owner's question. That title matched the handoff topic. The answer would have selected the caller
   if `OPENCODE_SESSION_ID` had not been excluded.
2. **Near-identical idle title.** A planning session had a close title and had read the older notes.
   It was idle. A title-only answer would have selected it.
3. **Bulk `time_updated`.** Many idle sessions shared one update minute after a store reconcile. The
   latest message `time_created` separated the active session.
4. **Goal key encoding.** The plugin goal key contained an encoded prefix. A literal key search for
   the word `goal` returned no rows. Matching the JSON `$.objective` value found the record.

## Query pattern

```bash
DB="file:$HOME/.local/share/opencode/opencode.db?mode=ro"
SELF="${OPENCODE_SESSION_ID:?}"

# Candidates by message content, newest activity first.
sqlite3 -separator $'\t' "$DB" "
SELECT s.id, s.title, datetime(MAX(m.time_created)/1000,'unixepoch')
FROM session_message m
JOIN session_v2 s ON s.id = m.session_id
WHERE m.data LIKE '%<distinctive handoff phrase>%'
  AND s.id <> '$SELF'
GROUP BY s.id
ORDER BY MAX(m.time_created) DESC;"

# Goal records, matched by the JSON objective value.
sqlite3 -separator $'\t' "$DB" "
SELECT key, json_extract(value,'$.objective'), json_extract(value,'$.status')
FROM kv
WHERE value LIKE '%\"objective\"%';"
```

Use a distinctive phrase from the handoff note, not a common word such as a directory name. A
directory name occurs in every session that listed the directory.

## Report shape

- Bound session ID and exact live title.
- Working directory.
- First user prompt preview.
- Stated goal and status.
- Last message time.
- Whether the newest handoff note has a local reader.
- The external-session limit, when it applies.

## Validation

Both commands passed in the delivery worktree:

- `python3 scripts/validate_plugins.py` reported 1062/1062 valid.
- `python3 scripts/check_pii.py` reported no direct PII patterns.

## Limits

- The local store cannot show a session that runs under another account or host.
- Note authorship is evidence of the author. It is not proof that a local session read the note.
- A handoff note does not grant authority for a production change. Verify owner authority first.
