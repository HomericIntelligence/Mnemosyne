# Notes: Stop the Previous Release's Daemon Before the Repair and the New Start

These notes give the generalized evidence and mechanics behind
[cutover-stop-previous-release-daemon](cutover-stop-previous-release-daemon.md).
Product, project, host, job, repository, and issue identifiers are intentionally
omitted.

## Production trigger (generalized)

A production cutover for one minor release line stopped the previous release's
scheduler allocations — gateway, replica, and donor jobs — and retired the
gateway evidence. No step stopped the previous release's operator daemon, a
foreground host daemon started outside the scheduler on an administrator host.
That daemon feeds a heartbeat file (`operator/heartbeat.json`-class: `pid`,
`service_host`, `cluster`, `heartbeat_at`) every heartbeat period and answers a
local singleton socket with a sibling `.lock` file.

Two consequences:

1. A fail-closed service-path repair (`repair_service_paths(apply=True)`-class)
   re-inventories the service paths after writing a receipt and compares the
   re-inventory with the receipt. The old daemon kept writing the heartbeat
   between the receipt and the re-inventory, so the proof failed with
   `service path inventory changed after inventory receipt at 'operator'` and
   rolled back. Nothing was mode-repaired; the failure is a verification
   rollback, not a mutation.
2. The new release's daemon start takes the singleton lock and binds the same
   socket; a still-live old daemon would collide with that start.

The manual workaround, executed live before the supported stop existed:

```bash
# 1. Read the pid and the host from the heartbeat.
cat operator/heartbeat.json
# 2. Verify the exact release identity of the process on the named host:
cat /proc/<pid>/cmdline
readlink /proc/<pid>/exe
# 3. Confirm the cmdline is the old release's "<operator> serve --root <root>"
#    for the old context; then SIGTERM the daemon on that host, for example:
srun -w <service_host> kill -TERM <pid>
# 4. Confirm the heartbeat froze (heartbeat_at and mtime unchanged across a
#    heartbeat period) before continuing with the repair and the new start.
```

The daemon exited and the heartbeat froze; the cutover continued. All four
steps of that workaround are what the supported stop now automates with
fail-closed evidence.

## The supported stop: mechanics and rationale

### Why a pid-stamped stop and not a socket action

The process to stop always belongs to the previous release. A new shutdown
action does not exist in that release, and the old daemon rejects any request
whose context differs from its own. A pid-stamped signal works on every
release that publishes `pid` and `service_host` in its heartbeat — including
the release line that produced this incident.

### Release identity candidates per interpreter layout

Two interpreter layouts were covered by tests:

- **Older layout**: the release venv's interpreter is a symlink to a base
  Python, so `/proc/<pid>/exe` resolves outside the release tree. Release
  publication rewrites every console-script shebang to the literal release
  interpreter path `<root>/venv/releases/<source_sha>/bin/python`, so argv[0]
  names the release. The stop accepts this layout through argv[0].
- **Newer layout**: the release venv declares its interpreter home inside the
  release tree, so `/proc/<pid>/exe` lies in the release tree and argv[0] can
  be a `venv/current` path typed by the operator. The stop accepts this layout
  through the kernel-resolved `exe`.

The never-resolve-`current` rule exists because publication can re-point
`venv/current` before the stop runs; the resolved path would then name the
wrong release. A literal `venv/current` path counts as neutral.

### Watchdog detection

The supervised form starts the daemon under a watchdog script that restarts a
child after a nonzero exit and stops cleanly when the watchdog itself receives
SIGTERM (it forwards the signal, waits a fixed stop grace, escalates to SIGKILL
only after that grace, and exits 143). The stop detects the watchdog parent by:

- cmdline contains an argument whose basename is the watchdog script name,
  followed by the ` -- ` separator;
- the arguments after the child command path equal the daemon's arguments
  after its interpreter and script (argv[2:]); and
- the parent's UID equals the daemon's UID.

A non-matching parent stays untouched, and the daemon itself receives the
signal. The stop waits for the exit of both the signaled watchdog and the
daemon. A watchdog that restarts the child between the signal and the proof is
caught by the frozen-heartbeat or lock proof, which then fails as
`OperatorStopIncomplete`-class.

### Exit codes (CLI mapping)

| Outcome | Exit |
| --- | --- |
| `stopped`, `already_stopped` | 0 |
| refusal (`OperatorStopRefused`-class; no signal was sent) | 1 |
| incomplete (`OperatorStopIncomplete`-class; signal sent, proof failed) | 2 |

Fixed constants, no CLI tuning: exit grace 30 s (watchdog stop grace 10 s plus
a margin), freeze window 2 s, pidfd poll interval 0.1 s.

### Test seams used for verification

The behavior tests materialize a fake `/proc` tree (cmdline, status, exe
symlink) under a temporary directory and replace `pidfd_open`, the signal
sender, `time.monotonic`, and `time.sleep`. This covers every decision branch
without real processes:

- identity accepted from the shebang argv[0] (old layout) and from the in-tree
  `exe` (new layout);
- refusal when no candidate names the expected release, when a candidate names
  a different release, or when the only path goes through `current`;
- refusals for a non-serve process, a serve of a different root, a different
  UID, a different cluster, and a different host (the refusal names the host);
- idempotence: no heartbeat, pid not running, reused pid with a free lock
  (`pid_reused: true`), reused pid with a held lock (refusal), repeated call;
- watchdog signaled instead of the daemon; non-matching parent untouched; the
  stop never escalates past SIGTERM;
- incomplete outcomes: no exit within the grace, heartbeat rewritten in the
  freeze window, lock held after the exit;
- host-scoped directory selection for per-host operator paths.

### Runbook placement and the external automation gap

The rollout automation that owns the production `stop-old-runtime` /
`start-operator` / `cutover` step names lived outside the product repository.
The deliverable records that gap: the external automation must call the stop
after the allocation stop, before every consistency-checked repair in the
cutover step, and before the new operator start. The in-repo runbook gained the
stop as a release-order step with the same placement.

### Adjacent observation deferred out of scope

A start-up helper discards a stale heartbeat by a local liveness check, but the
heartbeat can come from a different host. This was recorded as an observation
for a separate follow-up, not changed: out of scope for the stop.

## Provenance

Designed and implemented 2026-10-25 through 2026-10-26 from one production
cutover failure and its manual workaround; the plan and its revision-2 GO
review drove the design decisions (pid-stamped stop, literal-path identity,
no age gate, watchdog signaling, lock-based idempotence). Generalized here
without product, host, issue, or scheduler identifiers.
