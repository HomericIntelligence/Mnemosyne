# Notes: producer-side-congestion-window

Supporting detail for the main entry. Generalized; no internal identifiers.

## Evidence summary

Evidence comes from one incident-driven change to a production inference gateway's
batch runner. Interactive users saw "workers unavailable" errors whenever batch
work flooded the gateway: the runner dispatched at a fixed in-flight ceiling and
retried queue-timeout / 429 / 5xx / transport answers per request with no bound
on the accumulated wait. A server-side queue resize landed first; the flood kept
moving to the next bottleneck, which is the direct evidence that a sender-side
throttle was the missing layer.

The final shape passed CI in its target repository, shipped behind its existing
configuration surface, and survived three plan-review sweeps plus two exact-head
code reviews. Review findings that materially changed the design are recorded in
the main entry's Failed Attempts table; they are the durable part.

## Parameter rationale

- Floor of one: zero deadlocks throughput; one keeps progress and lets the
  increase rule re-enter.
- Cool-down of a few seconds: a burst answers to one stalled gateway arrives
  within one round-trip; N simultaneous overflow answers must collapse the
  window one time, not N times.
- Wait budget default of one hour with an explicit unbounded option: long enough
  for a real backlog cycle, short enough to fail a request rather than wait a
  day. The budget covers both retry backoff and capacity waits, and is charged
  at the wait site.
- Ceiling defaults to the pre-existing fixed cap: the operator-visible meaning
  of that cap does not change.

## Design verification highlights

- Fairness: parked-waiter starvation was caught by two pre-existing fairness
  tests that assert one principal's parked task never blocks another's. The
  hungry-task gate made them pass again.
- Ticket symmetry: a release-at-slot-acquisition variant leaked one ticket per
  success and permanently closed the gate within N requests in a simulation;
  the symmetric variant returns the counter to zero at idle. Tests assert the
  counter's return to zero at every cycle end.
- Credit-mediated admission: the deployment issued server capacity credits;
  gating credit holders before they occupied an execution slot kept the window
  effective in that mode. Verified by a live-attempt-ceiling integration test.
- Wall-clock budget termination was proven with an injected monotonic clock;
  sleepless test runs cannot otherwise terminate a wait-budget path.

## Boundary

- The window adapts one producer's dispatch. It does not set downstream queue
  sizes; the receiver-side companion entry covers bounded queues in the service.
- It is effective only where congestion answers are distinguishable at the
  producer: a dedicated queue-full/queue-timeout code versus generic overload.
  When the gateway has no dedicated code, fall back to treating 5xx and 429 as
  OVERLOAD only, and accept slower floor contact as the cost.
