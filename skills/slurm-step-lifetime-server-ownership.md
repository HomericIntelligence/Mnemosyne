---
name: slurm-step-lifetime-server-ownership
license: BSD-3-Clause
description: "Keep an interactive server (such as a tmux session) alive across client attach and detach steps inside a Slurm allocation. Use when: (1) detaching a client kills the whole session and its processes, (2) a reconnect opens an empty session instead of resuming, or (3) an attach step launched from inside another allocation is refused with memory or CPU-binding errors."
category: tooling
date: 2026-10-18
version: "1.0.0"
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
| **Outcome** | Successful — a detach leaves the session intact when the durable step creates the server, both sides agree on the exact socket name, the attach is gated on a readiness marker, and inherited scheduler context is scrubbed from step launches. |
| **Verification** | verified-local on a shared Slurm cluster through repeated attach, detach, re-attach, and step-teardown cycles, with cgroup ownership evidence. |

## When to Use

- A wrapper keeps tmux (or a similar terminal server) inside a Slurm job and attaches clients through `srun --pty` steps.
- Detaching a client (tmux prefix + `d`, or the step ending) kills the whole session instead of detaching it.
- Reconnecting starts a fresh empty session while the old server still runs under a different socket name.
- A step started from inside another allocation exits immediately with `Unable to create step`, `Memory required by task is not available`, or `CPU binding outside of job step allocation`.
- You are reviewing a change that rewrites the attach command line; socket-name regressions have silently shipped in exactly this shape.

Do not use this entry for `sbatch --wrap` shell-contract failures or for PATH shims that swallow commands; see the related entries under References.

## Verified Workflow

### Quick Reference

The four rules, each from an observed failure:

1. **The durable step owns the server.** Batch/allocating steps persist; each attach step's process tree is destroyed when the step ends. Create the server in the durable step only.
2. **Both sides agree on the exact socket name.** Include the allocation ID and a stable prefix. One wrong character in the client's socket argument silently defeats the rendezvous.
3. **Gate the attach on a readiness marker.** Job state `RUNNING` is not server readiness. The durable step publishes a marker only after the server exists; clients wait and fail loudly when the server is absent instead of silently creating one.
4. **Scrub inherited scheduler context at the step boundary.** Remove exported `SLURM_*`/`SRUN_*` variables (keep the config pointer) before creating a step from inside another job.

```bash
# Durable (batch) step: create first, then publish.
sock="sess-$SLURM_JOB_ID"
tmux -L "$sock" new-session -d -s main
: >"$STATE_DIR/ready-$SLURM_JOB_ID"     # publish only after creation

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
2. **Remove the silent-create path.** On the client, prefer `attach-session` over `new-session -A`: a missing server must be a loud error, not a doomed do-over inside a disposable step. The marker file converts the race (job RUNNING, server not yet up) into a wait.
3. **Treat the launch environment as untrusted defaults.** `srun` adopts exported scheduler variables (`SLURM_MEM_PER_NODE`, CPU-bind masks, node lists, and similar) as request defaults. Launched from inside a larger job, the request can exceed the target allocation and the controller refuses the step. Unset them with a shell builtin (`compgen -e`) so no external tool is required at this boundary; keep only the cluster-config pointer.
4. **Diagnose with ownership evidence.** Compare each tmux server's cgroup (`step_batch` vs `step_N`), list the node's socket directory for exact names, and read accounting history (`sacct`) to distinguish a step teardown from a walltime expiry. A `CANCELLED` record names the cancelling user; a disappeared allocation with full elapsed time is a `TIMEOUT`.
5. **Automating a reproduction needs a real PTY.** `srun --pty` rejects piped stdin. Wrap a scripted attach in a pseudo-terminal provider (`script(1)`) and trigger detach server-side (`tmux detach-client -a`), which is the same server operation the prefix binding performs.
6. **When the deployed artifact and the repository disagree, believe the artifact.** Compare checksums of the installed program against every revision in the project's history; a copy that matches no commit is an unreviewed mutation and the first suspect.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Fix the attach by rewriting it through a shell wrapper | Replaced `env -u TMUX ... tmux -L "<prefix>$JOB_ID" ...` with `bash -c 'unset TMUX ...; exec tmux -L "$1" ...' _ "$JOB_ID" ...` | The rewrite dropped the socket prefix; `new-session -A` found no server and silently created one inside the srun step; detach then ended the step and the scheduler killed the step's process tree, session included. Observed live: the client-created server sat in `job_<ID>/step_55` while the real one persisted in `step_batch` | Any attach-command rewrite must pin the exact socket argument. A silent-create fallback turns one wrong token into total session loss |
| Attach as soon as Slurm reports the job RUNNING | Attached without waiting for the batch script's server | Same phantom-server outcome as above, intermittently; then the original step server also died when the step ended | A readiness marker published by the server-owning step is the only safe start signal; make a missing server a failed attach, never a created one |
| Launch the attach from inside another allocation | Ran the step launcher from a shell holding another job's environment | Controller refused the step: `Memory required by task is not available`, then `CPU binding outside of job step allocation`; the larger job's exported limits had become the request defaults | `SLURM_*`/`SRUN_*` variables leak across nested launches; scrub them (with a shell builtin, keeping the config pointer) at every step-creation boundary |

## Results & Parameters

### Configuration

- Socket name: one pattern containing the allocation ID on both the durable step and the client (for example `sess-<JOB_ID>`).
- Readiness marker: one file per allocation on storage shared by the login and compute nodes (for example `ready-<JOB_ID>`), created only after the server exists and removed with the allocation state.
- Step placement: `--overlap --nodes 1 --ntasks 1 --pty` for an interactive attach step.
- Scrub list: every exported variable matching `SLURM_*` or `SRUN_*`, except the cluster-config pointer (`SLURM_CONF`).

### Expected Output

- The tmux server process reports `step_batch` in its cgroup; client attach steps appear and disappear as `step_<N>`.
- The identical server PID before and after every detach/reattach cycle; session contents survive.
- Attaching creates no new socket in the node's tmux socket directory.
- A missing server aborts the attach immediately with a clear error instead of starting an empty session.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A Slurm session-manager wrapper for interactive agent workloads | Detach-kills-session incident on a production cluster; three cooperating fixes plus live attach/detach verification | See [slurm-step-lifetime-server-ownership.notes.md](slurm-step-lifetime-server-ownership.notes.md). |

## References

- [tmux manual — sessions and clients](https://man.openbsd.org/tmux.1)
- [Slurm `srun` documentation — step creation and environment](https://slurm.schedmd.com/srun.html)
- [slurm-wrap-shell-contract](slurm-wrap-shell-contract.md)
- [path-shadowing-noop-wrapper-silent-success](path-shadowing-noop-wrapper-silent-success.md)
- [scheduler-service-replacement-identity-continuity](scheduler-service-replacement-identity-continuity.md)
