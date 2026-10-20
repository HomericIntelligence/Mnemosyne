# Notes: slurm-step-lifetime-server-ownership

Supporting evidence from the incident that produced this skill. Identifiers are
generalized: the user, organization, cluster hosts, repository, and product
names are omitted. All commands and mechanisms are public Slurm and tmux
behavior.

## Incident shape

A Slurm session-manager wrapper submitted a batch job whose script started a
detached tmux server (`tmux -L "<prefix>-$SLURM_JOB_ID" new-session -d`), then
attached clients through `srun --jobid <ID> --overlap --pty tmux ... new-session
-A`. A later client-side rewrite of the attach line passed the bare job ID as
the socket name. From then on every attach missed the existing server and
created a second server inside its own srun step.

## Diagnostic chain that found it

1. Two different socket names existed for one allocation:
   `<prefix>-<JOB_ID>` (created by the batch step, days old) and `<JOB_ID>`
   (created at the most recent attach).
2. Process trees: the old server was parented under the batch step; the new
   server's fork parent was the tmux client task of the newest srun step.
3. Cgroup proof, the decisive evidence:

   ```text
   /proc/<client-created-server-pid>/cgroup -> .../job_<ID>/step_55/user/task_0
   /proc/<batch-server-pid>/cgroup         -> .../job_<ID>/step_batch/user/task_0
   ```

   Slurm destroys a step's process tree when the step ends, so any server in a
   `step_N` cgroup dies with that step; `step_batch` survives.
4. The wrapper's own source comment already described the failure mode, and a
   readiness fix existed on an unmerged/pushed branch — but the installed copy
   matched no commit in history (checksum sweep over all revisions), which made
   the stale, regressed copy the first suspect.
5. Oversight evidence: the batch-step server for the allocation had stayed
   alive the whole time with an untouched session; all "lost" work had only
   ever lived in throwaway step-local servers.

## Secondary failure: leaked scheduler context

After the socket fix, step creation was exercised from a shell inside another
allocation. Each attempt failed differently:

- `Memory required by task is not available` — inherited `SLURM_MEM_PER_NODE`
  from the larger enclosing job became the step's memory request and exceeded
  the smaller target allocation.
- `CPU binding outside of job step allocation` — inherited `SLURM_CPU_BIND*`
  masks named CPUs outside the target job's allocation.

A clean environment produced `STEP-OK` immediately. The durable repair scrubs
every exported `SLURM_*`/`SRUN_*` variable except `SLURM_CONF` at the step
boundary, using `compgen -e` so no external binary is required there.

## Verification protocol that reproduced the fix end to end

1. Submit a minimal job; wait for the ready marker (not job state).
2. Record server PID and cgroup; list the node's tmux socket directory.
3. Attach through the real client under a pseudo-terminal (`script(1)` wraps
   `srun --pty`, which refuses piped stdin).
4. Detach server-side (`tmux -L <sock> detach-client -a`) — the same operation
   the prefix-d binding performs.
5. Re-check: `has-session` succeeds, identical server PID, unchanged socket
   list. Repeat the attach/detach cycle once more and require PID equality
   across all three checkpoints.

Result: PASS — identical server PID across two full attach/detach cycles;
sessions and window contents survived; no phantom socket ever appeared.

## Regression guards added upstream

- A stubbed-launcher test that pins the complete socket argument (prefix plus
  job ID) inside the attach command line.
- A test that exports hostile scheduler variables and asserts none reach the
  step environment.

## Environment observations worth keeping

- On a shared cluster with heavy automation, small test allocations can be
  cancelled by an external actor within a minute; walltime limits between
  operator actions must be generous, and forensic readouts (`sacct`
  `CANCELLED by <uid>` vs `TIMEOUT`) separate outside interference from
  incidence expiry.
- Edits in a shared checkout can be discarded by another session's branch
  operations; keep the fixed install artifact separately and verify with
  checksums before relying on any working tree.
