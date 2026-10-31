---
name: tooling-opencode-v2-current-session-identity-binding
description: "Bind the current OpenCode V2 session to an explicit session ID by content evidence before any session-metadata mutation. Use this when a closing ceremony or bookkeeping step must rename or annotate the running session on a host that has parallel sibling lanes in one directory, where directory, title pattern, and update time do not disambiguate."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags: [opencode, session, identity-binding, sqlite, rename, fleet-parallel-lanes, negative-check, closing-ceremony, current-session]
---

# OpenCode V2 Current-Session Identity Binding

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Bind "the current session" to one explicit session ID with positive and negative content evidence before a session-metadata mutation, on a host that runs many parallel fleet lanes in one directory. |
| **Outcome** | Successful (OpenCode v2.1.4). One closing ceremony renamed the correct terminal lane after five sibling lanes in one directory collided on directory and update time; one sibling shared the same `time_updated` second. |

## When to Use

- A closing ceremony or bookkeeping step must mutate metadata of "this session", for example a terminal-status title-prefix change (`M: ...` to `Done: ...`), through a tool that takes an explicit session ID.
- The host runs several parallel lanes (fleet worker dispatches), so several recent sessions have the same working directory and near-identical `time_updated` values.
- You cannot read your own session ID from inside the session: the tool catalog has no session-info call, and the serve listener requires authentication for the session API.
- A title pattern alone would bind the wrong lane: siblings follow the same title convention with a different lane token.

## Verified Workflow

### Quick Reference

```bash
# 1. Candidate set: recent root sessions in this working directory.
sqlite3 -separator $'\t' "file:$HOME/.local/share/opencode/opencode.db?mode=ro" "
SELECT id, title, time_updated FROM session_v2
WHERE directory = '<your working directory>'
  AND parent_id IS NULL
  AND title LIKE '<lane title prefix>%'
ORDER BY time_updated DESC LIMIT 10;"

# 2. Positive probes on the candidate: the run's unique dispatch marker
#    and the run's own report marker both occur in its message store.
sqlite3 "file:$HOME/.local/share/opencode/opencode.db?mode=ro" "
SELECT count(*) FROM session_message
WHERE session_id = '<candidate id>' AND data LIKE '%<dispatch marker>%';"   # expects >= 1
sqlite3 "file:$HOME/.local/share/opencode/opencode.db?mode=ro" "
SELECT count(*) FROM session_message
WHERE session_id = '<candidate id>' AND data LIKE '%<own report marker>%';" # expects >= 1

# 3. Negative probe: one active sibling lane contains neither marker.
sqlite3 "file:$HOME/.local/share/opencode/opencode.db?mode=ro" "
SELECT count(*) FROM session_message
WHERE session_id = '<sibling id>' AND data LIKE '%<dispatch marker>%';"     # expects 0

# 4. Only after binding: mutate through the dedicated tool with the explicit ID,
#    for example session_rename(sessionID: '<candidate id>', title: '<new title>').
#    Never mutate from a title or recency guess, and never write the store directly.
```

### Suggested Approach

1. Treat "the current session" as an external reference from inside a session. There is no self-lookup in the tool catalog, and `/api/session` on the `serve --service` listener returns 401. The read-only store probe below is the bounded fallback; do not spend turns on authentication.
2. Build the candidate set on `directory`, root session (`parent_id IS NULL`), and the lane title prefix. Order by `time_updated` only as a hint: parallel siblings write updates within seconds of each other, and two siblings can share one value to the second.
3. Bind identity with two positive markers. The dispatch marker is a unique string from the run's own instruction (for example its exact target token). The report marker is a unique string from the run's own output (for example its final disposition line). Both must match in the message store of ONE candidate.
4. Add one negative probe: show that at least one active sibling lane contains neither marker. A dispatch marker alone is not proof when coordinators quote each other's dispatches; the negative sibling check is the disambiguation branch.
5. Probe with `data LIKE '%marker%'` over the raw column rather than a guessed JSON path. A wrong `json_extract` path returns 0 rows and no error, which looks like a negative result but proves nothing. Parenthesize compound predicates: bare `AND`/`OR` mixing measures the wrong predicate set.
6. After binding, mutate through the dedicated tool with the explicit session ID. When the ceremony asks for a prefix change, keep the remainder of the title identical and keep the tool's readback as delivery evidence. The store stays read-only; all writes go through the tool.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Session-info lookup in the tool catalog | Looked for a "who am I" call among the session tools | The catalog has rename/move mutation tools but no lookup for the current session | Treat self-identity as external data: bind it through the store probe, then pass the explicit ID to the mutation tool |
| `/session` on the serve listener | GET `/session` with JSON intent | The SPA fallback returns HTML, not JSON | The web app shell answers unknown GETs; only `/api/...` routes return data |
| `/api/session` JSON probe | GET `/api/session` with `Accept: application/json` on the `--service` listener | 401 Authentication required; the token is not available from inside the session | Do not spend ceremony time on authentication; the read-only sqlite probe is the bounded fallback |
| Directory + `time_updated` ordering | "The newest session in this directory is this one" | Five sibling lanes updated within 25 seconds; two shared one second | Title pattern and timestamps only build candidates; content evidence binds |
| Guessed JSON path plus bare AND/OR | `json_extract(data, '$.summary.body') LIKE ...` mixed with unparenthesized `OR` | The path miss returned 0 with no error, and `OR` precedence split the `AND` terms, so the count measured the wrong predicate set | Probe `data LIKE '%marker%'` over the raw column, or use the verified `$.text` path, and parenthesize compound predicates |
| Dispatch marker alone as identity proof | One positive `LIKE` on the dispatch token | Coordinator prompts can quote other lanes' dispatches; one marker can occur in a sibling | Two positive markers plus one negative sibling probe is the binding minimum |

## Results & Parameters

### Configuration

- Store, tables, access pattern, and the `$.text` message field: [tooling-opencode-v2-session-message-filter](tooling-opencode-v2-session-message-filter.md).
- Candidate filter: `directory =`, `parent_id IS NULL`, `title LIKE '<prefix>%'`, `ORDER BY time_updated DESC`.
- Binding rule: one candidate passes two positive markers (dispatch + own report), and one active sibling passes the negative probe (0 matches).

### Expected Output

- One bound session ID, or an unresolved candidate set. Unresolved candidates stay unmutated; report the ambiguity instead of mutating a best guess.
- The mutation tool returns the session ID and the new title on success; keep that readback as the delivery evidence.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared fleet agent host (OpenCode v2.1.4) | Closing ceremony renamed a terminal worker lane among five sibling lanes in one directory; one sibling shared the same `time_updated` second | Dispatch-marker and report-marker probes matched one candidate (counts 1 and 2); one sibling probe returned 0; `session_rename` with the explicit ID returned the new title |

## References

- [tooling-opencode-v2-session-message-filter](tooling-opencode-v2-session-message-filter.md) — read-only store access pattern and message-table shape
- [tooling-opencode-v2-batch-session-messages](tooling-opencode-v2-batch-session-messages.md) — title-prefix selection for multi-session actions
- [tooling-opencode-v2-session-model-audit](tooling-opencode-v2-session-model-audit.md) — session metadata changes go through the official tool or API, not direct store writes
