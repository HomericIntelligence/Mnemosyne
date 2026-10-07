---
name: detached-launch-survives-harness-restart
description: "Launch work that must outlive the agent session detached from the harness serving process. Use when a supervised background job dies with a server-restart message, or before automation that runs for tens of minutes or more."
category: tooling
date: 2026-10-07
version: "1.0.0"
user-invocable: false
tags: [background-task, detached-process, server-restart, setsid, nohup, process-group, long-running-automation]
---

# Launch long-running work detached from the harness server

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-07 |
| **Objective** | Keep work alive when its runtime can exceed the lifetime of the agent harness serving process. |
| **Outcome** | Successful — root cause identified (server-supervised process tree); a detached relaunch completed in 13 minutes the pipeline that a supervised run had lost after 42 minutes. |

## When to Use

- Before you launch a pipeline, automation loop, agent job, build, or training run that can take tens of minutes or more.
- After a background job fails with a message such as "Command cancelled because the server restarted" while the job itself was healthy and progressing.
- When the harness runs as a serving process (for example `opencode serve`) and spawns background jobs as its child processes.
- When harness-managed handles (task identifiers, per-shell output files) would be the only progress record for the work.

## Verified Workflow

### Quick Reference

```bash
# Launch detached: a new session, a new process group, and SIGHUP immunity.
# Write output to a path you own. The harness can delete its managed per-shell
# output directory when it restarts.
setsid nohup <command> > "$HOME/<owned-dir>/<job>.log" 2>&1 < /dev/null &

# Verify detachment: the session id (SESS) of the job must differ from the
# session id of the harness server process. After the launcher exits, the job
# is adopted by PID 1 (PPID 1).
ps -o pid,ppid,pgid,sess,cmd -p <pid>

# Track progress from the owned log file, not from session-bound handles.
tail -f "$HOME/<owned-dir>/<job>.log"
```

### Suggested Approach

1. Check the supervision model before you trust it. Compare the job and the server:

   ```bash
   ps -o pid,ppid,pgid,sess -p <server-pid>
   ps -o pid,ppid,pgid,sess -p <background-job-pid>
   ```

   If the job is in the process tree, process group, or session of the server, a
   server stop that terminates its children also terminates the job. Treat managed
   output paths of the harness as ephemeral in the same way.

2. Select the execution mode for the work:

   | Condition | Use |
   | --- | --- |
   | Short task whose result you need before you continue | Foreground |
   | Short independent task with a convenient completion notice | Harness-managed background |
   | Tens of minutes to hours; loss on restart not acceptable | Detached launch with an owned log |
   | Only progress record would live in harness-managed paths | Detached launch with an owned log |

3. Launch with all four detachment parts: `setsid` (new session and process group,
   so a group or session kill cannot reach the job), `nohup` (SIGHUP immunity),
   `< /dev/null` (no shared terminal input), and an operator-owned log path
   (survives harness cleanup).

4. Verify detachment before you trust the launch: a session id different from the
   server, and PPID 1 after the launcher shell exits.

5. Record the PID and the log path in a durable place. Track by log growth and
   process liveness, not by harness shell handles.

6. When a restart cancellation occurs, check survival before you relaunch: the
   process can be absent, or can be alive and adopted by PID 1 with a growing log.

7. Before a relaunch, inspect durable artifacts for partial progress (published
   comments, labels, checkpoints). Idempotent stages resume; in the evidence case
   only the final stage required re-execution.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Harness-supervised background shell for a 42-minute pipeline | A two-stage planning and review pipeline ran as a background shell job of the harness server | An intentional server restart terminated the server process tree; the healthy job died in the review stage; the new server instance also removed the shell output file | Supervised background shells share the lifetime of the server. Long work that cannot accept loss requires detachment at launch |
| Tracking progress through the harness output file | Read the harness-generated shell output file after the restart | The new server instance had cleaned the per-session shell directory of the old instance; the file was absent | Keep progress and output in an operator-owned path; harness artifact paths are ephemeral across restarts |
| Treating repeated background-job deaths as job defects | Two earlier background jobs on the same host (a test suite and a delegated task) died on the same day and were each handled as job-local flakes | The shared cause was harness server restarts; per-job debugging could not find it | When unrelated background jobs die on one host, compare their death times with server restart times before you debug the jobs |

## Results & Parameters

**Detection signature of a server-restart kill:**

- The cancellation message names the server restart as the cause.
- The server log shows an ordered shutdown (watchers and services stopping) followed
  seconds later by a new startup line with a new run identifier. An ordered shutdown
  is consistent with an intentional restart; absence of shutdown lines suggests a crash.
- The job PID is absent from `ps`, and the harness-managed output file is removed
  or truncated.

**Configuration that survived and completed (verified):**

- `setsid nohup <command> > <owned-log> 2>&1 < /dev/null &`
- Job adopted by PID 1 after the launcher exited; session id different from the server.
- The relaunched pipeline ran 13 minutes to a passing completion while the harness
  session that launched it was free to end.

**Restart-safety note:** the same rule applies to other supervisors that stop their
child trees, for example a service manager unit that kills its control group on stop.
Move work out of the supervised tree when the work must outlive the supervisor.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| ProjectHephaestus | Planning and review automation driven through a public agent CLI on a V2 serving host; supervised run lost after 42 minutes; detached relaunch finished with a passing disposition | Session 2026-10-07; see [detached-launch-survives-harness-restart.notes.md](detached-launch-survives-harness-restart.notes.md) |

## References

- [agent-background-task-failure-recovery](agent-background-task-failure-recovery.md) — different failure mode: the background child reports success but contains an API failure. That entry covers child-side silent failure and recovery; this entry covers server-side termination of healthy children.
- [stale-background-bash-tasks-audit](stale-background-bash-tasks-audit.md) — different failure mode: a background shell never terminates. That entry covers deadlines and bounded polling; this entry covers lifetime decoupling from the server.
- [concurrency-and-process-reliability-patterns](concurrency-and-process-reliability-patterns.md) — related mechanism guidance: give individual children session isolation (`start_new_session=True`) instead of calling `setsid` on the main process.
- `setsid(2)` and `nohup(1)` manual pages.
