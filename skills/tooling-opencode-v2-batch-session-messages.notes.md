# Notes: tooling-opencode-v2-batch-session-messages

## Provenance

- Learned on 2026-10-18 and extended on 2026-10-19 during operator sessions on
  a local OpenCode V2 installation (`opencode v2.0.32`).
- Source task: "send `continue` to every idle OpenCode session that begins with
  one shared title prefix; repeat on request."
- All session identifiers, user paths, issue references, and the specific
  prefix are withheld per the privacy rules. The generalized commands in the
  main skill are the exact commands that ran, with placeholders substituted.

## Execution evidence, wave 1 (2026-10-18)

1. `opencode session list --format json -n 500` returned the project sessions
   as a JSON array with fields `id`, `title`, `updated`, `created`,
   `projectId`, `directory`. `jq` with `startswith("<prefix>")` selected 6
   sessions. The requesting session title did not match the prefix; the
   exclusion guard in the main skill covers the case in which it would match.
2. Each of the 6 sends was launched as
   `nohup opencode run --session <id> "continue" > <owned-log> 2>&1 &`.
   All 6 processes were present in `ps` output 15 seconds after launch and
   remained alive at the 6-minute check (elapsed time increasing).
3. One log showed the resumed session configuration line (`> build · <model>`)
   within 15 seconds. Other logs stayed at 0 bytes until their runs wrote
   output; this is normal and is not a failure signal.
4. Delivery verification result: all 6 runs confirmed alive through `ps` and
   growing owned logs. The requesting session stayed responsive throughout.

## Execution evidence, waves 2-3 (2026-10-18/19)

1. Wave 2 delivered `continue` to 17 sessions selected as idle by title
   prefix. Two sessions that appeared to match were skipped: one was working
   (its `updated` timestamp moved), one had activity fresher than 120 s.
2. One session produced `Error: UnexpectedStatus: 500` shortly after start on
   three attempts. The wave-2 export check of that session showed the
   `continue` message landed in its transcript anyway: the run attaches,
   appends the message, and only the model call fails. The same 500 recurred
   at wave 3; every other target ran normally.
3. Wave-3 classification identified 17 idle targets and 1 busy target by the
   two-snapshot method. A send-time re-check ~20 minutes later found 2 of the
   idle targets working again (automation sessions that self-continue on a
   loop) and the busy target settled (idle > 4000 s). The busy set is a
   moving window; classify at send time.
4. A title-mutation anomaly appeared at wave 3: a target session disappeared
   from the title-prefix selection between classification runs and reappeared
   later with the same prefix. Re-deriving the target list from the freshest
   snapshot each wave re-included it correctly.
5. ENOSPC incident: a 16-send batch ran while a shared filesystem sat at its
   capacity threshold. Every redirect failed with "No space left on device",
   no `opencode run` process started, and the launcher still printed 16 fake
   PIDs and a success-looking count. A probe of every owned log with an empty
   redirect passed ~1 minute later; the identical batch then launched 15/16
   healthy (the known 500 session excluded) plus 3 deferred targets. Scratch
   state for snapshots was moved to a local disk with hundreds of GB free.
6. Pagination check: the API response is `{data, cursor}`. Omitting the
   `cursor` query parameter re-fetches page one; a naive accumulation loop
   collected the same ~50 sessions 21 times (dedupe by `.id` collapsed the
   inflation). With the cursor threaded, one full enumeration covered ~1000
   sessions across all projects.

## Verification failure detail

Two failure shapes occurred when `opencode session export <id>` was used to
verify delivery on the actively updated sessions:

- `jq` errors: `parse error: Unfinished string at EOF at line <n>, column <m>`
  and `parse error: Unfinished JSON term at EOF ...`. A healthy export of the
  same session had succeeded minutes earlier, which identifies concurrent
  writes as the cause.
- Schema mismatch: a first extraction attempt assumed a nested message-part
  structure and returned empty text. The V2 export schema that this run
  observed is:

  ```text
  {
    "info": { "id", "projectID", "agent", "model", "cost", "tokens",
              "outcome", "time": { "created", "updated", "idle", "viewed" },
              "title", "location": { "directory" } },
    "messages": [ { "id", "time": { "created" }, "text", "type", ... } ]
  }
  ```

  Message text is the top-level `text` field of each message. Synthetic
  system-reminder content also appears as messages of this shape.

## Limits

- Evidence covers one operator fleet on one host. Sessions belonging to other
  project directories appear in the global API enumeration with their own
  `location.directory`; select and page carefully.
- Applied permissions for each continued session come from the configuration
  of that project; the sends did not use `--auto` and the runs progressed.
- Log byte size is a liveness signal, not a correctness signal for the work
  that each continued session performs.
- The 120 s freshness constant and the ~20 s snapshot gap come from three
  waves on one fleet; they err on the side of skipping a session that is
  about to settle. Re-checking a skipped session minutes later is cheap.
