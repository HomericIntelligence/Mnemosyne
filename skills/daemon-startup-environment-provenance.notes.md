# Daemon Startup Environment Provenance — Notes

Supporting evidence for `daemon-startup-environment-provenance`.

## Source incident (generalized)

- A long-running service was started from an interactive operator session on a node that held a local tunnel to a database.
- The session exported a dial host that named loopback; the service inherited it. The service had no database forward on its own node.
- Every request the service handled failed its connect step. The failures were counted, not printed, so operators saw only an unanswered work queue.
- A sibling component that resolved the same target through its own route worked, which delayed the diagnosis.
- The repair was to start the service with explicit configuration and a scrubbed environment, and to give the queue one owned processor.

## Decision value

- The trigger is per-process route divergence with a healthy sibling; a host-wide network fault produces a different signature.
- The distinguishing evidence is the target class in the failure record versus the documented target.
- The durable rule is configuration provenance at startup, not error visibility. Visibility is covered by a separate entry.

## Privacy screen

No product, organization, host, path, user, or workload identifiers are included. Error text is summarized, not quoted.