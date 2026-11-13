# Notes: debug-external-reachability-not-local-dns

## Source evidence for the shared-cluster branch (amend of 2026-11-13)

Incident: an agent session on one node of a shared GPU cluster had to decide
whether a control-plane operator on a different node was alive.

What was tried and failed:

- A local socket-table read (`ss -x`) filtered on the service's socket path
  returned zero matches.
- A scheduled re-probe repeated the same zero result; each run reproduced the
  instrument mismatch, so the absences carried no new information.
- A cross-user scheduler step into the component's job was refused by the
  scheduler, so direct on-node verification was unavailable from that account.

What refuted the down verdict:

- The component's published state record (an endpoint file with a
  `written_at` field, on the shared filesystem) had been rewritten seconds
  before the check. A record that fresh is decisive proof of liveness.
- The record's timestamp advanced again on a later read, matching the
  component's publish interval.

Follow-up session evidence that confirmed the pattern:

- A second session, independently, published the same three facts (local
  sockets refuse from another host, cross-user scheduler step denied, audit
  record shows the component alive and answering) — same wrong-vantage failure
  mode reached by a different path.
- A third reader nearly repeated the mistake by treating a scheduled probe's
  absence as fresh evidence.

Generalized rule: a host-local observation instrument is bound to its own
node. On a shared multi-node filesystem, service files being visible does not
mean the process is observable. Verify a remote component's liveness from its
published record's timestamp freshness first; only a stale record supports a
down verdict, and even then confirm from the component's node or network
endpoint before acting. Name the vantage point in any recorded verdict.

Privacy: all hostnames, job ids, paths, and account names are generalized.
