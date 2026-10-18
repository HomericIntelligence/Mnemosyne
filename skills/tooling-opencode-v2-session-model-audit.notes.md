# Evidence and limits

Verified against a live OpenCode v2.0.31 installation on Linux (server API v2.0.31). Storage
behavior is consistent with the v2.0.24 source inspection recorded in the sibling entry
`tooling-opencode-v2-session-deletion-effects`.

## Observed store layout

- Database: `~/.local/share/opencode/opencode.db` (SQLite, WAL mode active while the service runs).
- Table `session_v2`: one row per session. The `model` column stores the last-selected model as a
  JSON object with keys `id`, `providerID`, and optional `variant`.
- Table `session_message`: one row per message with columns `session_id`, `type`, `seq`, and a JSON
  `data` payload. Observed types include `assistant`, `user`, `model-switched`, `agent-switched`,
  `idle`, `synthetic`, `compaction`, `system`, and `location-switched`.
- Assistant rows carry the response model in `data.model` with the same `id`/`providerID` shape.
- `model-switched` rows carry both the new model in `data.model` and the previous model in
  `data.previous`; a provider string match across all row types therefore double-counts events.

## API surface used

- `opencode api get /api/info` reported the server version and confirmed the background service.
- `opencode api get /openapi.json` enumerated session operations; the retarget operation is
  `POST /api/session/{sessionID}/model` with operation ID `session.switchModel`. Its request body is
  `{"model": <Model.Ref>}` and `Model.Ref` accepts `providerID`, `id`, and `variant`.
- Each retarget call returned an empty success response; the result was confirmed by re-reading the
  store.

## Audit results on the verified host (anonymized)

- 231 sessions in the store.
- 12 sessions had at least one assistant response from the target zero-cost provider family.
- 9 of those were still set to a target-family model as their current model and were retargeted in
  bulk through `session.switchModel` to the approved paid provider.
- 3 had already returned to the approved provider and were left unchanged.
- Global `opencode.json` and `cli.json` contained no `model` field; usage came from manual
  per-session selection, so no configuration change was required.
- Final verification query over `session_v2.model` returned zero rows for the target provider.

## Limits

- Verified only against v2.0.31. Table names, message types, and the `Model.Ref` schema can change
  in later releases; re-read `openapi.json` and the live schema before reuse.
- Model identity strings are per-installation and are generalized in the main entry.
- No session titles, session identifiers, local paths, provider account names, or message content
  are retained in this record. Only public documentation locations, schema facts, and anonymized
  counts are used.
