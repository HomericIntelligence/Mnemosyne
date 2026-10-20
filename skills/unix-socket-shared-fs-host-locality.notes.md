# Notes: unix-socket-shared-fs-host-locality

## Evidence

The source incident reproduced a refused connection from two host classes of
one cluster against a socket path stored on a shared parallel filesystem.

### Observations

- The socket path existed and was stat-able from a login-class host and a
  compute-class host. Directory metadata alone looked plausible.
- A client on each host class received connection refused. The refusals were
  identical, which ruled out a host-local client fault.
- The listener process did not exist in any relevant scheduler allocation or
  in the serving account's process list on any candidate host.
- The socket file and the adjacent audit file had not advanced since the
  outage date, ten days earlier. The audit file's last entries were the most
  precise liveness evidence available.
- The socket directory carried group-restricted permissions. That fact
  initially suggested an authorization fault and cost investigation time.

### Placement consequences

- The daemon binds its socket in the kernel of its own host. The shared
  filesystem exports the pathname, not the kernel object.
- The deployment's client commands run on an administrator-used login host;
  the daemon therefore belongs on that host, not inside the serving stack's
  compute allocation (the architecture additionally forbids inbound
  connections to allocation nodes).
- The service supports a per-host mode: sockets live under a per-host
  directory and clients select the host explicitly. That mode is the correct
  shape when more than one administrator host exists. The single-host case is
  served by one unscoped instance.

### Diagnostics that worked

1. `test -S` only to classify the path; never as liveness.
2. A one-line AF_UNIX connect probe run on the client host; refusal there is
   the authoritative verdict.
3. `stat` comparison of the socket and its sibling activity artifacts for a
   staleness interval.
4. Process-table and scheduler-job searches for the serving account to find
   where (if anywhere) the listener currently lives.
