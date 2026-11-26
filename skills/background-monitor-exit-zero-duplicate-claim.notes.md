# Supporting Notes — Background Monitor Exit 0 Duplicate Claim

These notes hold the observed evidence for
[background-monitor-exit-zero-duplicate-claim.md](background-monitor-exit-zero-duplicate-claim.md).
They contain no internal paths, hostnames, or project identifiers.

## Observed sequence

1. A per-user agent CLI plugin started a periodic refresher (`--watch`) that updated a
   model-picker line from a gateway record every 60 seconds.
2. The same refresher was launched several times within a few minutes. Each launch wrote a
   `monitor started` log line.
3. A short time later, a burst of `monitor stopped` log lines appeared in the same second. All
   but one instance had released the claim and exited cleanly.
4. A background task notification reported that one monitor ended without output at exit 0.
5. Inspection showed:
   - one refresher process was still alive from the original launch (runtime more than six
     hours);
   - the claim record held that process identifier;
   - the cache record was refreshed in the same minute as the inspection;
   - the model-picker lineup matched the cached model list exactly, so no rewrite was needed.

## Why the completion was benign

The exited task was a duplicate instance. It lost the exclusive claim to the live process and
ended with exit 0. The claim holder was alive and the artifact was fresh. No relaunch was
needed.

## Diagnostic commands (generalized)

```text
1. Read the claim record. It should name the active process.
2. Check that the named process exists and runs the refresher.
3. Compare the artifact mtime with the interval. It must be newer than one interval.
4. If both pass, record "benign duplicate". If either fails, start one instance.
```

## Generalization limits

The evidence is one recorded session on one host. The rule generalizes the invariant that the
evidence supports: an exclusive claim makes duplicate instances exit quietly, and a silent
completion needs a claim-holder check and an artifact-freshness check before any restart. It
does not generalize the specific interval, the specific file names, or the specific harness.
Re-measure those for each deployment.

## Related entries

- `agent-background-task-failure-recovery` covers completions that carry an error or leave the
  expected edits missing.
- `service-supervision-ownership-parity` covers a service with no start, restart, or liveness
  owner.