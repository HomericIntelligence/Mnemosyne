---
name: duplicate-refresher-single-owner-claim
description: "Enforce one active owner when many independent launchers start the same periodic refresher. Use when: (1) duplicate background refresher processes accumulate, (2) a launcher must not fail when another instance is live, (3) a killed owner leaves a claim or pid file behind, or (4) you design the claim, liveness, and stop path of a per-session monitor."
category: tooling
date: 2026-11-26
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - single-owner
  - claim-file
  - exclusive-create
  - pid-liveness
  - stale-claim
  - standby
  - background-refresher
  - monitor
  - duplicate-process
  - shared-storage
  - graceful-stop
---

# Give a Session-Launched Refresher One Claim Owner

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-26 |
| **Objective** | Keep exactly one active refresher when many independent launchers start the same periodic background command, and make the extra launchers harmless. |
| **Outcome** | Verified behavior. Eight refresher processes were live at one time: one claim owner and seven standby loops left by earlier launchers. The claim made one refresh loop write the shared record. Each standby deferred without a refresh and without an error. The duplicate processes were the defect: each standby held a process and an open record. |
| **Verification** | verified-local: five behavior tests ran on an isolated copy of the installed refresher (free claim, deferral to a live owner, stale-claim takeover, standby handover, graceful stop). The live set was reduced to one owner. See [notes](duplicate-refresher-single-owner-claim.notes.md). |

## When to Use

- Several sessions, cron entries, or installers can start the same periodic refresher, and each start leaves a process, a timer, or an open file.
- A status or one-shot command must give an answer while another instance is live instead of failing or refreshing a second time.
- A process that writes a shared record must have one writer, and the storage does not give a safe file lock.
- A refresher was killed with SIGKILL and left a claim file or a pid file behind.
- You review the stop or cleanup path: which process gets the signal, and which record is removed.

Do not use this skill to run a service that a supervisor must restart. Use it for a refresher that repeats an idempotent read and write, and for which a missing refresh is only a delay.

## Verified Workflow

### Quick Reference

```text
One shared claim path is the only authority for "who refreshes".
Every launcher tries to create it with an exclusive create (O_CREAT|O_EXCL).
Create succeeds  -> this process is the owner; refresh, then release only if the claim still names it.
Create fails     -> read the claim, test liveness, and act by role:
                    live owner  -> one-shot prints the cached state and exits 0;
                                   watch sleeps a bounded interval and retries.
                    stale claim -> compare the content, then remove it and create again.
Never remove a pid file that the claim logic did not create; the stop path reaps it.
```

### Suggested Approach

1. **Use one claim path, not one process per launcher.** Give the claim a single fixed path in the runtime state directory. Put the owner pid and an identity value in it; do not use the pid alone. Write the content to a temporary file and publish it with an atomic replace so a reader never sees half a claim.
2. **Create with an exclusive create.** An exclusive create is atomic on shared storage. Take no file lock. A plain "does the file exist" test followed by a write is a race and lets two owners in.
3. **Make the standby defer, not fail.** The extra launchers are normal, not errors. A one-shot launcher prints the cached state and exits 0. A watch launcher sleeps a bounded interval and tries the claim again, so it takes over when the owner stops. Report the standby state in the log at one line, not per interval.
4. **Prove the owner is alive and is this program.** Test the pid with signal 0, then compare `/proc/<pid>/cmdline` with the refresher identity (fall back to `ps` where `/proc` is absent). A live pid alone is not proof: pids are reused, and an unrelated process at that pid would hold the claim for as long as it lives.
5. **Reclaim a stale claim with a compare and delete.** Re-read the claim, check liveness again, and remove it only if its content equals the content you tested. Between your check and your removal, another launcher can take over and publish a new claim; an unconditional removal would delete that new owner's claim.
6. **Release only your own claim.** On a normal stop, remove the claim only if it still names your pid. If it names another pid, your ownership already ended; leave the claim alone.
7. **Keep the two records separate.** The claim decides who refreshes. A per-instance pid file records who to stop. A SIGKILL cannot run a cleanup handler, so the claim is recovered by step 5, and the orphan pid file stays. Claim logic must ignore pid files. The stop path must reap a pid file whose pid is dead, is a zombie, or is not the refresher.
8. **Bound the stop path.** Signal the claim owner and each recorded pid whose command line names the refresher. Wait a bounded time (about 10 s), then send SIGKILL. Treat a zombie as stopped. Remove each record that you reaped. Never signal a pid that you did not confirm as the refresher.

Decision points that change the outcome:

- If a launcher must give a result now, use the one-shot deferral. If it must stay available, use the watch deferral with takeover.
- If the refresher writes a record that other processes read, the deferral must report the cached record, not an empty result.
- If the storage is a network file system, do not add a lease timeout to the claim. Use step 4 for liveness instead; a timeout would refuse to run after a slow owner.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| One launcher per session, no claim | Each session started its own watch loop and each loop refreshed the shared record | Every loop repeated the same read and write. Eight processes were live at one time, and only the record content showed the waste | A repeated idempotent refresh still costs a process, a record, and a rate limit per launcher. Use one owner |
| Test the claim file, then write it | Checked for the file and wrote it when absent | Two launchers pass the test in the same window and both write | Use an exclusive create. A test and a write are two operations and not one |
| Liveness by pid only | Treated any live pid as the owner | A reused pid that belonged to an unrelated process held the claim indefinitely | Add the command-line identity check |
| Remove a stale claim without a content compare | Unlinked the claim after the liveness test | A launcher that took over in the same window lost its new claim | Re-read and compare the content before the removal |

## Results & Parameters

### Configuration

```text
state directory:     <state-dir>/            runtime state, ignored by version control
claim path:          <state-dir>/active      one fixed path, exclusive create
per-instance files:  <state-dir>/<pid>       one file per started instance
claim content:       pid, process identity, start time
standby interval:     5 s                     watch-mode claim retry
refresh interval:    60 s                     owner loop period
stop timeout:        10 s                     signal wait before SIGKILL
```

### Expected Output

- One owner process refreshes the shared record at the configured interval.
- Each standby logs one line and either exits 0 with the cached state or sleeps and retries.
- After the owner stops with a signal, a standby becomes the owner in about one standby interval, and the state directory holds one claim and one pid file per live process.
- After a SIGKILL, the claim is reclaimed by the next launcher. The orphan pid file stays until the stop path reaps it.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Agent tooling (generalized) | Isolated copy of a per-session refresher monitor | [notes.md](duplicate-refresher-single-owner-claim.notes.md) |

## References

- [service-supervision-ownership-parity](service-supervision-ownership-parity.md): one supervision owner per service.
- [cutover-stop-previous-release-daemon](cutover-stop-previous-release-daemon.md): identity-checked, idempotent daemon stop.
- [concurrent-reader-observes-half-configured-artifact](concurrent-reader-observes-half-configured-artifact.md): publish a complete artifact at its final name.
- [detached-launch-survives-harness-restart](detached-launch-survives-harness-restart.md): a detached launcher outlives its session, which creates the duplicate-launcher case.