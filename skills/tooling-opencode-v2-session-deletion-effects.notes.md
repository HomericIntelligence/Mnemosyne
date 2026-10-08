# Evidence and limits

Verified against OpenCode v2.0.24. The installed version was checked and the public source was
inspected at the matching tag.

## Verified code path

- `packages/core/src/session.ts` (`Session.remove`): verifies the session exists, interrupts
  execution and waits for idle, closes the model transport, recursively removes child sessions,
  clears session environment variables, publishes `SessionEvent.Deleted`, then calls the bus
  removal.
- `packages/core/src/session/projector.ts`: the `SessionEvent.Deleted` projection deletes the row
  from the session table.
- `packages/core/src/bus.ts` (`remove`): deletes all rows for the session aggregate ID from the
  event sequence table and the event table in one transaction.
- `packages/core/src/tool-output.ts`: truncated tool output files are named by timestamp
  (`tool_<identifier>`) and cleaned with a 7-day retention; no session-linked cleanup exists.
- `packages/core/src/snapshot.ts`: Git-tree snapshots have no session-linked cleanup.

## Documentation evidence

- The V2 troubleshooting documentation states that the database normally lives at
  `~/.local/share/opencode/opencode.db`, overridable with `OPENCODE_DB`, and that installed builds
  write logs to `~/.local/share/opencode/log/opencode.log`.
- The V2 API reference documents the delete endpoint with only the summary "Delete a session and
  its child sessions", plus the experimental session-log and session-export endpoints.

## Limits

- Behavior is verified only for v2.0.24. Later releases can change the storage design.
- The durable session-log, export, and import endpoints are marked experimental in the API
  reference.
- No local machine paths, account data, session identifiers, or session content are retained in
  this record. Only public repository paths, public documentation, and standard XDG data-home
  locations are used.
