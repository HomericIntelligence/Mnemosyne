---
name: slurm-step-lifetime-server-ownership
license: BSD-3-Clause
description: "Keep an interactive server (such as a tmux session) alive across client attach and detach steps inside a Slurm allocation. Use when: (1) detaching a client kills the whole session and its processes, (2) a reconnect opens an empty session instead of resuming, (3) an attach step launched from inside another allocation is refused with memory or CPU-binding errors, or (4) a client update did not stop detach from killing the session on an allocation that predates the fix."
category: tooling
date: 2026-10-18
version: "1.1.0"
user-invocable: false
verification: verified-local
tags:
  - slurm
  - srun
  - sbatch
  - tmux
  - step-lifetime
  - cgroup
  - readiness
  - environment-inheritance
  - session
---

# Slurm Step-Lifetime Server Ownership

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-18 |
| **Objective** | Run a long-lived interactive server inside a Slurm allocation so clients can attach, detach, and reattach without losing the session or the processes in it. |
| **Outcome** | Successful — a detach leaves the session intact when the durable step owns and maintains the server, both sides agree on the exact socket name, the attach is gated on a readiness marker, and inherited scheduler context is scrubbed from step launches. A running allocation keeps the batch script it was submitted with, so the fix takes effect after one allocation restart. |
| **Verification** | verified-local on a shared Slurm cluster through repeated attach, detach, re-attach, and step-teardown cycles, with cgroup ownership evidence; a later report confirmed that a running allocation requires a restart after the client fix. |

## When to Use

- A wrapper keeps tmux (or a similar terminal server) inside a Slurm job and attaches clients through `srun --pty` steps.
- Detaching a client (tmux prefix + `d`, or the step ending) kills the whole session instead of detaching it.
- Reconnecting starts a fresh empty session while the old server still runs under a different socket name.
- A step started from inside another allocation exits immediately with `Unable to create step`, `Memory required by task is not available`, or `CPU binding outside of job step allocation`.
- You are reviewing a change that rewrites the attach command line; socket-name regressions have silently shipped in exactly this shape.
- A client update did not stop the failure: detaching still kills the session because the running allocation predates the fix.
- You are about to implement a detach-kill fix: check the default branch and the installed artifact first; the fix may already be merged.

Do not use this entry for `sbatch --wrap` shell-contract failures or for PATH shims that swallow commands; see the related entries under References.

## Verified Workflow

### Quick Reference

The five rules, each from an observed failure:

1. **The durable step owns and maintains the server.** Batch/allocating steps persist; each attach step's process tree is destroyed when the step ends. Create the server in the durable step only, and recreate it on an interval: the last pane shell can exit (`exit-empty`) or an OOM kill can remove the server, and the client must never create a replacement.
2. **Both sides agree on the exact socket name.** Include the allocation ID and a stable prefix. One wrong character in the client's socket argument silently defeats the rendezvous.
3. **Gate the attach on a readiness marker.** Job state `RUNNING` is not server readiness. The durable step publishes a marker only after the server exists; clients wait and fail loudly when the server is absent instead of silently creating one.
4. **Scrub inherited scheduler context at the step boundary.** Remove exported `SLURM_*`/`SRUN_*` variables (keep the config pointer) before creating a step from inside another job.
5. **A running allocation keeps the batch script it was submitted with.** Deploying a new client cannot change a running allocation. Restart the allocation once after the fix, then verify `step_batch` ownership. An allocation that predates the readiness marker has no marker; a fallback attach can land on a step-owned server, so a successful attach is not proof.

```bash
# Durable (batch) step: create, publish, then keep it alive.
sock="sess-$SLURM_JOB_ID"
tmux -L "$sock" new-session -d -s main
: >"$STATE_DIR/ready-$SLURM_JOB_ID"     # publish only after creation
while true; do
  sleep 10
  tmux -L "$sock" has-session -t main 2>/dev/null ||
    tmux -L "$sock" new-session -d -s main
done

# Client step: scrub context, then attach; never create.
(
  for v in $(compgen -e SLURM_) $(compgen -e SRUN_); do
    [[ $v == SLURM_CONF ]] || unset "$v"
  done
  srun --jobid "$job" --overlap --nodes 1 --ntasks 1 --pty \
    bash -c 'unset TMUX TMUX_TMPDIR; exec tmux -L "sess-$1" attach-session -t main' \
    _ "$job"
)
```

Verify ownership after any change to the attach path:

```bash
pid="$(tmux -L "sess-$job" display-message -p '#{pid}')"
grep -o 'step_[a-z0-9]*' /proc/"$pid"/cgroup    # must print step_batch
ls /tmp/tmux-"$(id -u)"/                         # only the agreed socket may appear
```

### Suggested Approach

1. **Understand the kill mechanism.** The scheduler wraps every step in its own process group or cgroup. When the last task of an attach step exits (a detached tmux client), the scheduler removes the step and signals everything still in it. A tmux server created by the client therefore dies with that step, taking every window and workload with it. This is why a detached session can vanish while the allocation keeps running.
2. **Compare the deployed artifact, the checkout, and the default branch before you change anything.** A copy that matches no revision in the project history is an unreviewed mutation and the first suspect. A checkout or installed copy behind the default branch makes a merged fix look missing. Check the installed hash, the checkout revision, and merged changes first; do not write a duplicate fix.
3. **Remove the silent-create path, and keep the server alive.** On the client, prefer `attach-session` over `new-session -A`: a missing server must be a loud error, not a doomed do-over inside a disposable step. In the durable step, recreate the session on a short interval so a server that exits or is OOM-killed comes back; otherwise the loud error becomes a permanent outage. The marker file converts the race (job RUNNING, server not yet up) into a wait.
4. **Treat the launch environment as untrusted defaults.** `srun` adopts exported scheduler variables (`SLURM_MEM_PER_NODE`, CPU-bind masks, node lists, and similar) as request defaults. Launched from inside a larger job, the request can exceed the target allocation and the controller refuses the step. Unset them with a shell builtin (`compgen -e`) so no external tool is required at this boundary; keep only the cluster-config pointer.
5. **Diagnose with ownership evidence.** Compare each tmux server's cgroup (`step_batch` vs `step_N`), list the node's socket directory for exact names, and read accounting history (`sacct`) to distinguish a step teardown from a walltime expiry. A `CANCELLED` record names the cancelling user; a disappeared allocation with full elapsed time is a `TIMEOUT`. If the batch-step server is gone while the batch script is alive, read `memory.events.local` in the batch task cgroup; `oom_kill` counts a killed server.
6. **Automating a reproduction needs a real PTY.** `srun --pty` rejects piped stdin. Wrap a scripted attach in a pseudo-terminal provider (`script(1)`) and trigger detach server-side (`tmux detach-client -a`), which is the same server operation the prefix binding performs.
7. **Restart the allocation after the fix and verify ownership.** A running allocation keeps the batch script it was submitted with, so a client update alone cannot repair it. Restart it once. An allocation that predates the readiness marker has no marker; the client can time out and attach to a step-owned server, and a successful attach is not proof. Require `step_batch` in `/proc/<pid>/cgroup` and an unchanged server PID across a detach/reattach cycle.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Fix the attach by rewriting it through a shell wrapper | Replaced `env -u TMUX ... tmux -L "<prefix>$JOB_ID" ...` with `bash -c 'unset TMUX ...; exec tmux -L "$1" ...' _ "$JOB_ID" ...` | The rewrite dropped the socket prefix; `new-session -A` found no server and silently created one inside the srun step; detach then ended the step and the scheduler killed the step's process tree, session included. Observed live: the client-created server sat in `job_<ID>/step_55` while the real one persisted in `step_batch` | Any attach-command rewrite must pin the exact socket argument. A silent-create fallback turns one wrong token into total session loss |
| Attach as soon as Slurm reports the job RUNNING | Attached without waiting for the batch script's server | Same phantom-server outcome as above, intermittently; then the original step server also died when the step ended | A readiness marker published by the server-owning step is the only safe start signal; make a missing server a failed attach, never a created one |
| Launch the attach from inside another allocation | Ran the step launcher from a shell holding another job's environment | Controller refused the step: `Memory required by task is not available`, then `CPU binding outside of job step allocation`; the larger job's exported limits had become the request defaults | `SLURM_*`/`SRUN_*` variables leak across nested launches; scrub them (with a shell builtin, keeping the config pointer) at every step-creation boundary |
| Plan a fix from the installed copy and the local checkout | Compared the installed file and the checkout with each other, not with the default branch, and prepared a local patch | The default branch already contained the merged fix; the installed copy and checkout were many revisions behind, and the installed file matched no revision | Compare the deployed artifact, the checkout, and the default branch with its merged changes before you write a fix |
| Deploy the client update and expect the running allocation to change | Replaced the client and expected later attaches to be safe | The allocation kept the batch script spooled at submit time, so its server stayed in a step cgroup and the next detach would still kill it; the allocation also had no readiness marker, so the updated client would time out and fall back to that server | A running allocation is a snapshot. Restart it once after the fix, then require `step_batch` ownership and an unchanged server PID across detach |
| Create the session once in the durable step | Started the server and published the marker, with no supervision | The server disappeared (last shell exit, or an OOM kill in the batch task cgroup) while the batch script stayed alive; later attaches had no server | Recreate the session on an interval, and read `memory.events.local` in the batch task cgroup to identify an OOM kill |

## Results & Parameters

### Configuration

- Socket name: one pattern containing the allocation ID on both the durable step and the client (for example `sess-<JOB_ID>`).
- Readiness marker: one file per allocation on storage shared by the login and compute nodes (for example `ready-<JOB_ID>`), created only after the server exists and removed with the allocation state.
- Step placement: `--overlap --nodes 1 --ntasks 1 --pty` for an interactive attach step.
- Scrub list: every exported variable matching `SLURM_*` or `SRUN_*`, except the cluster-config pointer (`SLURM_CONF`).
- Server supervision: recreate the session on an interval (for example 10 s) in the durable step; keep the readiness marker present while the session exists.
- Deployment: restart the allocation after a client fix. The running allocation keeps the batch script it was submitted with.

### Expected Output

- The tmux server process reports `step_batch` in its cgroup; client attach steps appear and disappear as `step_<N>`.
- The identical server PID before and after every detach/reattach cycle; session contents survive.
- Attaching creates no new socket in the node's tmux socket directory.
- A missing server aborts the attach immediately with a clear error instead of starting an empty session.
- An allocation restarted after the fix reports `step_batch`; an allocation that predates the fix keeps a `step_<N>` server until it is restarted, and a successful attach is not proof.
- The batch task cgroup's `memory.events.local` shows `oom_kill` after an OOM kill of the server; the watchdog recreates the session.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A Slurm session-manager wrapper for interactive agent workloads | Detach-kills-session incident on a production cluster; three cooperating fixes plus live attach/detach verification. A later report after the fix: a running allocation submitted before the fix still killed the session, while the default branch already contained the fix and the installed copy was behind | See [slurm-step-lifetime-server-ownership.notes.md](slurm-step-lifetime-server-ownership.notes.md). |

## References

- [tmux manual — sessions and clients](https://man.openbsd.org/tmux.1)
- [Slurm `srun` documentation — step creation and environment](https://slurm.schedmd.com/srun.html)
- [slurm-wrap-shell-contract](slurm-wrap-shell-contract.md)
- [path-shadowing-noop-wrapper-silent-success](path-shadowing-noop-wrapper-silent-success.md)
- [scheduler-service-replacement-identity-continuity](scheduler-service-replacement-identity-continuity.md)
