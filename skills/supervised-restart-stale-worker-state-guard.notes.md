# Notes: Supervised Restart Stale Worker-State Guard

Supporting evidence for [the main entry](supervised-restart-stale-worker-state-guard.md).
Generalized from one production incident. Internal identifiers, paths, hostnames, and
issue numbers stay in the owning tracker and are intentionally absent here.

## Incident anatomy

1. The supervised HTTP child of a long-running service job ran healthy with eight
   workers. Each worker published a state file named `<aggregate>.worker-<pid>.json`
   into a runtime directory shared by every child of the job.
2. The supervisor health probe timed out twice. Fresh per-worker state showed the
   workers were alive, so the supervisor preserved the child temporarily.
3. A restart was requested. The supervisor stopped the child's process group and
   launched attempt one. Its startup guard listed the runtime directory, found the
   previous child's `<aggregate>.worker-<pid>.json` files, and raised
   `worker state already exists`, exiting nonzero.
4. Attempt one had already started workers of its own before the guard fired in a
   later attempt, so attempt one's leftovers poisoned attempts two through five the
   same way. The supervisor declared its restart budget (five restarts in 120
   seconds) exhausted and exited. The service job then failed as a whole.
5. Full outage lasted about seven minutes. A replacement service job started with a
   fresh runtime directory and became healthy at once.

## Mechanism details worth remembering

- Nothing in the worker lifecycle deleted the per-PID file. Shutdown wrote a final
  snapshot inside the same file. The aggregator that merged per-worker files into the
  aggregate read dead-worker files deliberately (monotonic counters) and also never
  deleted them.
- The startup guard's intent was contamination defense for first allocation: reject
  unexpected entries in a sealed runtime. Applied unchanged to in-place restarts, it
  indicted the component's own dead workers.
- A sibling component in the same system had two startup paths: a legacy path that
  deleted `<aggregate>.worker-*.json` before launch, and a sealed-runtime path that
  only asserted absence. The asymmetry (cleanup lost in the migration to the sealed
  runtime) is the exact defect shape to look for in similar migrations.
- Diagnostic search pattern in supervisor logs: `already exists` launch crashes
  interleaved with `restarting child`, terminating in `restart budget exhausted`.
- Scheduler evidence: the failed job's end time and the healthy replacement job's
  start time bound the outage window; the discovery record (`job -> fresh runtime`)
  explains why recovery was instant once a new allocation started.

## Repair pattern applied in the verdict

- Clean dead-owner artifacts at stop time (owner) and at start time (guard
  pre-clean), check PID liveness from the filename-recorded identity.
- Restrict strict absence to first allocation and to foreign entries.
- Keep the fail-closed behavior for foreign names, types, owners, and live
  conflicts.
- Regression tests: clean-stop restart, hard-kill restart, foreign injection —
  all through the real supervisor path so the restart budget is exercised.
