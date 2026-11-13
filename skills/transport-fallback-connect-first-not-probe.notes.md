# Notes: transport-fallback-connect-first-not-probe

Supporting evidence for the main skill. All site-specific identifiers removed.

## Origin

An administration client for a cluster control plane gained a remote standby
transport (TLS with cluster identity proof) beside a host-local Unix socket.
The initial route selection ran a socket probe before every request and fell
back when the probe failed. The repository's own live-cli tests then recorded
failures only on mutation requests.

## The failure shape

- Read-only status requests: pass.
- Mutation requests through the same client: reset with `ECONNRESET`, but only
  after a few logical operations against the same live, bounded listener in
  the test fixture. Production listeners got the same probe traffic without a
  visible failure because their accept budget was larger.

The test service caps accepted connections at a small budget. Each logical
operation against it opened:

1. a context exchange connection;
2. the effect request connection;
3. one probe connection per request for route selection.

The probe made the server accept the connection and attempt to run its per
request handler pipeline. Because the probe sends nothing, the handler
replies with its malformed-request refusal; that reply went nowhere, so the
service also logged a broken-pipe warning. Five such ghost rows and warnings
per command ended up in the service audit. After the fixed number of wasted
connections, the backlog closed and the next effect request reset before one
request byte was read.

## The isolation experiment

The selection layer was disabled so requests used only the primary path
(`if False` around the fallback branch). Every resetting mutation test
completed. The probe was therefore the sole cause, and the repair targeted
the selection layer rather than the service.

## The repaired design

- One generic client-error base class carries every refusal, unchanged text.
- One subclass marks connect-phase failures: the request provably never left
  the client. Both known-cause unreachability and generic connect failures
  raise in this class.
- Route submission sends to the primary first. Only the subclass opens the
  standby route. Without a valid standby route, the original error
  propagates unmodified.
- `no-reply`, `reset`, and `reply-parse` failures after connect do not raise
  in the subclass. They are terminal for the request and reconcile through
  the read-only status request.

## Related lesson

`reconcile-before-retry-mutation-status-loss` covers what to do once a status
is lost: reconcile with read-only checks, then at most one bounded, idempotent
re-invocation. This skill covers the earlier design decision that prevents
creating the uncertain state at route-selection time. Use both: connect-first
routing, then reconcile a post-connect failure.
