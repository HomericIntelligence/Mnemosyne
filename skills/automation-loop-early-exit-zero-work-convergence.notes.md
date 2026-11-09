# Automation Loop Early-Exit — Notes

Supporting evidence for the main entry. Not part of normal retrieval.

## Zero-item summary from a crashed selection

An explicit issue selection was re-run after a long campaign had exited. The summary printed
`items: 0`, `dispositions: {}`, zero agent jobs, and a 45-second wall time. The operator's
first reading was "the selected issues had no eligible work".

The log held a traceback instead. The selection step called a forge query to find an open pull
request for an auto-creation branch; the query raised an API rate-limit error
(`reset epoch 0` in the error). The run never produced a work item, so the empty summary
described the crash, not the queue.

Recovery that held:

1. Searched the log for a traceback and found the selection-path stack.
2. Read the forge quota with a cheap read-only call: core and graphql budgets had recovered
   from the exhaustion that killed the first attempt.
3. Re-ran the identical selection once. The retry passed the selection step and printed a
   work claim within the first minute.

Boundary: a genuinely empty explicit selection is still possible and has its own warning path;
this entry adds the crash branch, not a replacement for it. The distinguishing evidence is the
traceback plus an empty disposition table, not the `items: 0` value alone.
