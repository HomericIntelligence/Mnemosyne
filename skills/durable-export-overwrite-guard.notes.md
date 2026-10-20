# Notes: durable-export-overwrite-guard

## Evidence

The source work was an hourly export of an agent's session transcripts to
one JSONL artifact per session on shared storage. A fixed upstream retention
window means a rerender of an old session can legitimately produce fewer
lines; the guard separates that case from divergence.

### Guard shape

- Each message line carries a sequence number and a stable message identity.
- The guard parses the existing artifact's `(sequence, identity)` stream and
  requires it to be a non-shrinking prefix of the staged stream.
- Legacy artifacts without identities, truncated artifacts, and unparseable
  artifacts are replaceable. The guard refuses to wedge old history.
- Divergence at any slot blocks the overwrite and logs the first divergent
  identity. An explicit `--clobber` flag is the only bypass.

### The exception-tuple arm that almost shipped

The guard's parse failure policy caught `OSError` and `ValueError` but not
`UnicodeDecodeError`, because the author mentally classified decode failures
as "text decode is strict by default and data is clean". Two independent
reviewers and the coordinator reproduced the hole against encoded-corrupt
fixtures: any artifact with a stray byte would hard-fail the whole export run
instead of being classified replaceable. The fix added the arm and a replayed
fixture test. Rule recorded: when review feedback names an exception arm,
replay the failing input class, then check the tuple again for siblings.

### Production catch record

Within the first days of the hourly schedule, the guard's log showed blocked
overwrites:

- several truncation blocks where upstream retention had shortened a source;
- one genuine divergence block: an existing artifact whose head content had
  been rewritten by a foreign writer. A size comparison would have passed it;
  the identity-ordered prefix comparison caught it.

### Test approach

Behavior tests replay recorded failure classes: truncation, same-length
divergence, corrupt encoding, legacy format, clobber bypass, multi-writer
interleave. Mocked time and mocked upstream reads keep the suite
deterministic.
