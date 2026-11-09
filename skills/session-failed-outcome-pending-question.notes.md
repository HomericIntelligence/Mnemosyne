# Session Failed Outcome Pending Question — Notes

Supporting evidence for the main entry. Not part of normal retrieval.

## Observed case (generalized)

During a fleet completion sweep on a shared OpenCode v2 host, one session carried the
recorded terminal outcome `failed`. Its title named a research task: restore a sealed
experiment campaign and find missing runner bundles. A bounded read of its messages showed:

1. Hundreds of successful tool turns over about an hour: hash-verified rebuild of a sealed
   runtime, byte-exact input verification, and code delivery (a pull request with hundreds
   of tests).
2. A final assistant text that reported one unrecoverable input class — sealed runner
   modules absent from every reachable storage root — and exactly one remaining decision
   the operator had to make.
3. The terminal message: a question call with two recovery options, in a pending state,
   never executed, never answered.

So the run ended at the operator-question boundary. The failure label records that ending;
it does not record a task crash. Classifying from the label alone would have produced a
re-dispatch of completed evidence work.

## Fleet record fields observed in the same sweep

- A session row carries `busy` and `idle` epoch-millisecond markers besides the outcome
  label. On this fleet the markers disagreed with message reality on several sessions
  (busy older than idle, idle far older than fresh message activity), consistent with the
  busy-flag lesson of the related completion-record entry.
- Sessions that self-continue under automation loops can hold fresh update times with no
  progress. Outcome plus terminal message content separates real work from churn.

## Relationship to the completion-record entry

The companion entry `session-batch-status-flag-lies` covers one side: the busy marker lies; read the
completion record and the newest message time. This entry adds the failure-label branch
of the same rule: even the recorded failure outcome can be the wrong classification when
the terminal message is an unanswered operator question. Together they reduce to one
rule: every recorded state is a hint; durable message content is proof.

## Reporting shape that worked

The monitor report for the sweep separated three buckets: done (success outcome plus final
answer text), failed (error trace), and blocked on operator (unexecuted question call).
Each blocked row carried the question header so the operator could answer without opening
the session transcript.
