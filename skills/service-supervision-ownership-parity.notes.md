# Notes: service-supervision-ownership-parity

## Evidence

The source incident concerned a shared-cluster inference deployment with an
authorization service for typed administrator operations. The service speaks to
clients over a local Unix socket and must run as the deployment's service
account.

### How the outage stayed invisible for ten days

- The only recorded start of the service was manual: an interactive process
  inside a long-lived scheduler allocation owned by the service account.
- The allocation's steps failed one after another on the outage date. The
  socket file and the service's audit file both stopped advancing within the
  same hour and never advanced again.
- A major stack component was restarted days later for an unrelated reason.
  That restart covered in-allocation children only; the authorization service
  was not in any restart scope, so it stayed dead.
- A fleet status document described components as supervisable. The document
  enumerated only the components its own machinery could reach; the failing
  endpoint did not appear at all, so the inventory showed no gap.
- Every typed administrative operation failed for the whole window, including
  a routine credential enrollment and a promotion-gating attestation. The
  client-facing error was a generic refusal with no diagnosis attached.

### Inventory that found the root cause

The fix investigation enumerated every long-running component and its launch
machinery:

- One batch job internally spawns and supervises the stack's serving children
  through a template with a restart budget and teardown semantics.
- The authorization service appeared in no job template, in no restart scope,
  and in no liveness probe. Its only launch path was a foreground command.
- The deployed release exposed it as a standalone entry point; the newer
  source tree routed it through a service command. The restore handoff had to
  name the entry point of the deployed release, not the source-tree one.

### Remediation delivered

- Immediate restore instructions for the service account: a supervised start
  in a terminal multiplexer, run on the host where administrators run the
  client (kernel locality of the transport).
- A minimal watchdog script (restart on nonzero exit, stop on clean exit,
  give up with a distinct status after repeated rapid failures) plus behavior
  tests covering clean-stop, restart-then-stop, rapid-failure give-up, and
  counter reset.
- An operations-runbook section covering placement, supervised start, restart
  semantics, maintenance-stop order, and a connect-level liveness probe.
- A deliberate scope cut: host-placement policy stayed a documented owner
  decision because the architecture text discourages persistent services on
  login-class hosts while the transport requires the daemon on each
  administrator host.
