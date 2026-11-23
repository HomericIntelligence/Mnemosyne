# log-invariant-once-per-process: supporting notes

## Evidence summary (generalized)

Two independent fixes in a private shared-automation codebase motivate this
lesson; identifiers are not restated here.

1. **Constant per-call marker removed.** A subprocess wrapper called
   `logger.debug("Running subprocess")` immediately before execution for every
   call. The line has constant text and no command, argument, duration, or
   outcome, yet fires once per subprocess. After review, the line was removed;
   the separate failure record (`Subprocess failed with exit code N`) was
   retained. Regression coverage: the wrapper's existing unit tests were
   narrowed to assert the absence of sensitive argument text in captured logs.

2. **Invariant resolved value logged once per process.** A global request
   throttle resolves a node-local root directory for its state file. The root
   selection helper was invoked on **every** acquisition of a request budget,
   and it emitted a `DEBUG` record with the resolved root on each call. On a
   driver run with ~hundreds of requests, the identical line repeated so
   frequently that it dominated the console stream. A module-level guard that
   emits the record once per distinct root removed the repeated identical
   output without removing the value from the first per-process diagnostics.
   Unit test: resolve the state path three times under a logging capture
   fixture, assert exactly one record for the root; give each test its own
   configured root so guard state cannot leak between tests.

## Generalization notes

- **Whole-process boundary.** The guard is per-process. A fleet of short-lived
  processes still emits the record once per process; that is one line per
  process run instead of a repeated identical flood.
- **Re-emit on change.** The guard keys on the *value* (root path, identity).
  When a legitimate reconfiguration happens (via an explicit option or
  environment default change) the helper selects a new value and emits once
  for it. The guard must not use a flat call counter: a counter desynchronizes
  from what the operator sees after process restarts or config changes.
- **Why "never delete noisy logs" does not apply.** This rule presumes the
  line has no diagnostic signal: constant message, invariant value, no call-ID
  context. It is distinct from deleting a *failure or fallback* message that
  still carries actionable content for a real misconfiguration.
- **Verification boundary.** No CI run for this entry exists yet; it is
  derived from merged fixes and manual confirmation of the removed output.
  The `caplog`-style unit test (three resolutions produce one record) is
  the executable check for future forks of the pattern.

## Provenance

- Both fixes observed in a shared automation codebase (repo name not recorded
  here). Change history is preserved by the delivery PR and repository commit
  history; no separate history file is kept for this entry.
