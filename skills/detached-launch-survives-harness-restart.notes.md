# Supporting evidence: detached launch survives harness restart

Privacy-safe session detail for `detached-launch-survives-harness-restart`. Times are UTC,
2026-10-07. Paths and host identifiers are generalized.

## Session timeline

| Time | Event |
| --- | --- |
| 18:29 | A two-stage planning plus review pipeline started as a harness-supervised background shell (agent CLI backend, planner and reviewer roles on one model). |
| 19:07 | The planning stage published its artifact (a plan comment, revision 1) and opened a pending review placeholder on the target issue. |
| 19:11:28 | Harness server log: ordered shutdown of the old server instance (`watcher stopped` lines, run identifier A). |
| 19:11:31 | Harness server log: `cli starting ... serve --service` with run identifier B. A deliberate restart 2.5 seconds after the stop, not a crash. |
| 19:11:31+ | The healthy background pipeline was absent from `ps`. The harness emitted "Command cancelled because the server restarted". The per-shell output file of the old instance was removed. |
| 19:22 | Relaunch of the same pipeline with `setsid nohup ... > <operator-owned-log> 2>&1 < /dev/null &`. |
| 19:22:35 | The pipeline resumed directly in the review stage: the published plan made the planning stage complete, so only the review stage re-ran. |
| 19:35 | Review stage finished (748 seconds of review work); pipeline disposition `pass`; the target issue transitioned to the review-approved state label. |

## Diagnosis procedure that identified the cause

1. `ps` inspection: no pipeline process remained; a new server PID existed with a
   start time minutes after the failure notice.
2. Server log boundary: the last lines of the old run identifier were ordered
   shutdown records; the first line of the new run identifier was a startup record
   2.5 seconds later. Ordered shutdown plus immediate start indicates an intentional
   restart, not a crash.
3. The harness-managed shell output file no longer existed; a `stat` returned
   no file. Managed artifact paths of the server did not persist across instances.
4. Two earlier same-day background-job deaths on the same host (a test suite and a
   delegated task) matched the same pattern only after the restart times were
   compared. Per-job debugging had found nothing because the jobs were not defective.

## Detached launch command shape (generalized)

```bash
cd <working-directory> \
  && setsid nohup env PATH="<prepended-tools>:$PATH" <command> \
  > "$HOME/<owned-dir>/<job>.log" 2>&1 < /dev/null &
```

Verification after launch:

- `ps -o pid,ppid,pgid,sess,cmd -p <pid>` shows a session id of the job that differs
  from the session id of the harness server.
- After the launcher shell exits, PPID becomes 1.
- The owned log file grows while the server is free to restart independently.

## Resume-safety evidence

The pipeline kept durable per-stage state on the issue (published plan comment and
review placeholder) plus local state. The relaunch detected the completed stage and
continued in the review stage. Relaunch cost was 13 minutes of wall time instead of
the original 42 or more. A pipeline without durable per-stage artifacts would have
re-run from the start.

## Related verified detail in the same session

- The agent CLI backend under test had its own verification pass end to end:
  authentication probe, run, read-only sandbox selection, session capture and resume,
  and event-stream parsing, on a V2 serving host of a public agent CLI.
- An unrelated provider-side model stall observed in the same session (a model absent
  from the provider model list that hung with zero bytes instead of failing fast) is a
  separate lesson candidate and is not part of this entry.
