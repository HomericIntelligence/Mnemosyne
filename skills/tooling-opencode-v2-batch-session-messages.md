---
name: tooling-opencode-v2-batch-session-messages
description: "Send one message to many existing OpenCode V2 sessions in parallel, skipping sessions that are currently working. Use when a user asks to continue, resume, or nudge every session that matches a title filter, such as a shared prefix."
category: tooling
date: 2026-10-19
version: "1.1.0"
user-invocable: false
tags: [opencode, session, batch-message, cli, jq, background-process, concurrency]
---

# Send one message to many OpenCode V2 sessions

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-19 |
| **Objective** | Deliver the same message to each existing idle session that a filter selects, without blocking the requesting session and without interrupting a busy session. |
| **Outcome** | Successful across three waves: 6 + 17 + 3 sessions selected by one shared title prefix received `continue`. Each detached run stayed alive and produced output, except one target whose provider consistently answers 500 after the message lands. |

## When to Use

- A user asks to send the same message (for example `continue`) to many existing OpenCode sessions.
- The target sessions share a property that a filter can select, such as a title prefix.
- Some target sessions may be working; those must be skipped, not interrupted.
- The requesting session must stay responsive while the target sessions run for a long time.

## Verified Workflow

### Quick Reference

```bash
# 1. Classify: take two session snapshots ~20 s apart and keep only sessions
#    whose .time.updated did not move and whose last update is older than 120 s.
opencode api get /api/session \
  | jq -r '.data[] | select(.title | startswith("<prefix>")) | [.id, .time.updated] | @tsv' \
  > snap1.tsv
sleep 20
opencode api get /api/session \
  | jq -r '.data[] | select(.title | startswith("<prefix>")) | [.id, .time.updated] | @tsv' \
  > snap2.tsv
# join on id: busy when updated moved, or when (now - updated) < 120 s

# 2. Probe every owned log before any launch (a failed redirect aborts the
#    command before it runs; the batch then reports success without sending).
for id in <session-id>...; do
  : > "<owned-log-dir>/$id.log" || { echo "storage not writable; stop"; break; }
done

# 3. Send detached, one owned log per session, excluding the requesting session.
for id in <session-id>...; do
  nohup opencode run --session "$id" "<message>" \
    > "<owned-log-dir>/$id.log" 2>&1 &
  echo "$! $id" >> launched.txt
done

# 4. Verify delivery from process state and log growth, not from a session export.
ps -o pid,etime,cmd -p $(cut -d' ' -f1 launched.txt)
ls -la <owned-log-dir>/
```

### Suggested Approach

1. Enumerate sessions with the HTTP API (`opencode api get /api/session`,
   response shape `{data, cursor}`) and dedupe by `.id`. `opencode session
   list` covers only the project directory of the current working directory;
   sessions that own work elsewhere still appear in the API with their own
   `location.directory`.
2. Re-derive the target list from the freshest snapshot at send time. Titles
   are mutable: a session that vanished from a title-prefix filter in an
   earlier snapshot can reappear, and an idle snapshot from minutes ago can be
   stale in both directions (busy→idle and idle→busy).
3. Classify busy with two snapshots, not with the `idle` time field: the
   `idle < updated` field heuristic is true for nearly every session and does
   not detect work. A session is busy when `.time.updated` moved between two
   snapshots or its latest value is fresher than ~120 s. Borderline sessions
   (automation loops that self-continue) drift across the threshold between
   checks; re-check them at send time and skip unsettled ones.
4. Exclude the requesting session explicitly. When its own title matches the
   filter, the send goes to that session again and can start an uncontrolled
   loop.
5. Probe each owned log with an empty redirect before launching. When the
   filesystem refuses the write (full shared filesystem, transient ENOSPC),
   a failing redirect makes the send a silent no-op while the launcher still
   prints a PID. Put the log directory on known-writable storage (a local
   disk beats a nearly full shared filesystem) or retry after the storage
   recovers.
6. Start each send as a detached background process with one owned log file
   per session. `opencode run --session <id> "<message>"` continues the named
   session with its stored agent and model.
7. Verify with process state and log growth, and classify per-session
   failures from the log tail. One log ending in
   `Error: UnexpectedStatus: 500` seconds after start is a per-session
   provider failure: the message was still delivered into that session (the
   run attaches, appends the message, then fails on the model call). Report
   it separately; retries show the same 500. Do not use `opencode session
   export` for live verification: an actively updated session can supply
   truncated JSON that does not parse.
8. Classify each exit before you report the send as complete. An exit is not
   one outcome. Read the last export event of the target session and the log
   tail:

   | Exit shape | Evidence | Meaning | Action |
   | --- | --- | --- | --- |
   | Clean turn, waits for you | Terminal `idle` event, `outcome: succeeded or failed`, and a final answer that asks a question or names a next step. | Delivery succeeded and the turn completed. | Report it. Re-send only if the reply requests the same message again. |
   | Stalled on a tool turn | Last message `finish: "tool-calls"`, `error: null`, and a tool item with `executed: false`. | The run ended before a final answer. The message landed, but the turn did not advance. | Re-send once; if it stalls again, report it as stalled. |
   | Agent cannot act | The reply says the session must change agent or mode (for example plan to build) to continue. | `opencode run --session` keeps the stored agent. A message cannot change it. | Report the needed agent change. Do not loop more sends. |
   | Provider failure | Log ends in `Error: UnexpectedStatus: <code>`. | The message was delivered and the model call failed. | Report separately. Do not retry for delivery. |

   A batch that mixes these shapes needs a second wave for the actionable
   rows, not a blind resend of every exited run. Keep the owned logs for
   later review. The run transcript also stays in the session itself.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Export-based verification of live sessions | Read new messages from `opencode session export <id>` immediately after launch to confirm delivery. | Two failure shapes occurred: `jq` parse errors (`Unfinished string at EOF`), because writes to the active sessions truncated the export, and an empty result, because the export schema puts message text in the top-level `text` field of each message, not in a nested `parts` array. | Verify live sends with process state and owned log files. Learn the export schema from an idle session, and export an actively written session only after it becomes idle. |
| `idle`-field busy detection | Skip sessions whose stored `idle` timestamp was older than `updated`. | The condition held for nearly every session and skipped almost nothing while some sessions were visibly working. | Busy classification needs a freshness window and movement detection between snapshots, not a stored field comparison. |
| Batch launch during ENOSPC | Launch 16 detached sends in one loop on a shared filesystem at its capacity threshold. | Every `nohup ... > log 2>&1 &` returned "No space left on device" for the redirect, so no command ran, yet the loop printed 16 PIDs and "launched". Small probe writes seconds earlier had succeeded; the mount accepts and refuses writes intermittently. | Probe each owned log with an empty redirect before launching; treat probe failure as a batch abort. Verify with `ps` and log sizes after launch, not with the launcher output. |
| Trusting a cached target list | Reuse a target list captured ~20 minutes before the send. | Between classification and send, two sessions crossed the freshness threshold (one started working, one settled idle), and a previously busy session had been idle for over an hour. | Re-derive state from a fresh snapshot at send time; the busy set is a moving window. |
| Reporting a batch complete on process exit alone | Count exited runs as finished sends and stop at the first wave. | Eight of 17 exited after a clean turn that asked a question, one `continue` stalled on a turn with `finish: "tool-calls"` and `error: null`, and one target was on an agent that could not act and asked for a mode switch. A blind resend or an early stop misreports each case differently. | Classify exits with the step 8 table and send a second wave only for the actionable rows. |

## Results & Parameters

### Configuration

- `opencode api get /api/session`: authoritative fleet view, response
  `{data, cursor}`. Thread `?cursor=<cursor>` for later pages and dedupe by
  `.id`; omitting the cursor re-fetches page one and duplicates rows.
- Filter keys: `.id`, `.title`, `.time.updated`, `.location.directory`.
- Freshness constant: treat an update fresher than ~120 s as activity; ~20 s
  between the two classification snapshots is enough for movement detection.
- `opencode run --session <session-id> "<message>"`: continues an existing
  session with its stored agent and model. Add `--fork` to branch the session
  instead, or `--model` / `--agent` to override the stored selection. Use
  `--agent` when a target must change agent or mode to act on the message.
- Launch wrapper: `nohup <command> > <owned-log> 2>&1 &`. Record each printed
  PID for later verification, and probe the log path first.

### Expected Output

- One long-lived `opencode run` process per selected session; `ps` shows its
  elapsed time increasing.
- Each owned log first shows the session configuration line (agent and model)
  and then grows as the run produces output. A log can stay at 0 bytes until
  the run writes its first output.
- A per-session `Error: UnexpectedStatus: 500` log means the run attached,
  delivered the message, and died on the model call: delivery succeeded,
  continuation did not.
- A run process can exit after one completed turn. Liveness of the process
  proves neither delivery nor progress in either direction, so classify each
  exit with the step 8 table.
- The requesting session stays unblocked, and its terminal receives no send
  output.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Local OpenCode V2 installation (v2.0.32) | Operator request: send `continue` to every idle session sharing one title prefix, repeated on demand (three waves, 26 sends) | [notes](tooling-opencode-v2-batch-session-messages.notes.md) |

## References

- OpenCode CLI help: `opencode --help`, `opencode session list --help`, `opencode session export --help`, `opencode run --help`
- [OpenCode V2 documentation](https://opencode.ai/v2/docs/)
- [detached-launch-survives-harness-restart](detached-launch-survives-harness-restart.md)
- [tooling-opencode-v2-session-deletion-effects](tooling-opencode-v2-session-deletion-effects.md) — session storage and export behavior
- [tooling-cli-batch-terminal-outcome-contracts](tooling-cli-batch-terminal-outcome-contracts.md) — honest outcome reporting for batch CLI work
