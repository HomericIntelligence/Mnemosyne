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

## Cutover step-design branch (2026-11)

This branch comes from read-only review of a committed cutover step and the
product client paths. It has no live run.

### Observed step shape

- A versioned cutover chain held one step that started or replaced the operator
  daemon. The step ran on the operator host by hand, but neither its header
  nor its code said so.
- The step started the daemon with its standard streams discarded. Two start
  failures left no line in the operator log. The causes were a configuration
  exception and a failed database connect, and they appeared only when the
  same command ran in the foreground.
- An earlier fix added a database reachability proof before the stop signal.
  That proof runs the replacement's own code with the local forward address
  injected. From a remote host the forward does not exist, so the proof fails
  before any signal. This is good evidence, but it is not a guard: it does not
  name the host fault, and it depends on the start path.
- The readiness gate waited for a heartbeat of the launched pid. The heartbeat
  proved that the process wrote state. It did not prove that a client could
  reach the socket with the registered context.

### Product seams that made the fix small

- The start command writes its own log file and exits with a distinct code for
  a configuration error. Its standard-error stream also caught the failures
  that appeared before the log file opened, such as an import error or a
  command-line parse error. Keep both surfaces and print both on failure.
- The client transport maps a dead listener to a no-reply error class and
  exits 1.
- The operator admits a request only when the cluster identity, the
  deployment identity, and the registered specification digest all match. A
  mismatch returns a context-mismatch error code.
- The plain status request returns the cluster and the serving host name. It
  does not evaluate pool health. The release status verb exits with the
  runtime status code, so one degraded pool makes it exit nonzero.

### Design rules that the review produced

1. State the host-locality rule in the step header. Name every command that
   needs the local socket, not only the daemon start.
2. Guard on the scheduler allocation variable before any effect, and exit
   nonzero with the reason.
3. Keep the database proof before the stop signal, and treat a failure there
   as the pre-failure evidence for the stop path.
4. Run the reply probe through the same binary and context selection helpers
   that started the daemon. Require exit 0 plus the identity fields of the
   reply.
5. Print the tail of the daemon log and of the captured startup stream on any
   start or probe failure.
6. Test the step offline by sourcing the shared library and stubbing the
   client function in each case: the allocation guard, the accepted reply, the
   context mismatch, the wrong cluster, and the two-log failure tail.
