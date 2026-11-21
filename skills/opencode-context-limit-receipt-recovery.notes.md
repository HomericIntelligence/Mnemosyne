# Supporting Notes: OpenCode Context-Limit Receipt Recovery

## Source boundary

The source was one long OpenCode V2 coordination session on 2026-11-18. Project names, pull-request identifiers, local paths, user identifiers, and repository details are excluded. The evidence supports the recovery decision rule; it does not establish a model-root cause or a frequency estimate.

## Observed sequence

1. The host issued repeated maximum-context and output-limit warnings.
2. Assistant output degraded into repeated fragments. One message contained tool-shaped markup but had no matching tool invocation, result, or delegated-session receipt. Later live reconciliation found no worker, so the claimed launch was not counted as executed.
3. A compression attempt failed with `tool.input-incomplete`. A later call used smaller complete arguments and returned a success receipt. Normal exploration resumed only after that receipt.
4. Degenerate prose claimed that no work remained. Direct live inventory still contained open work. The recovery ledger therefore treated the prose as unreliable and used actual tool results plus live reads.
5. A delegated review result also needed caution: the worker reported that part of its result came from transcript reconstruction. Its artifact and decisive execution claims required direct verification before publication. Existing delegated-claim and forge-readback skills cover the detailed audit procedure.

## Decision value

Existing guidance covers compaction configuration, prior-session database recovery, durable handoffs, and verification of delegated reports. This case adds a different trigger and recovery branch: during a live context emergency, compression is the first action; a malformed pseudo-call is not an action; and a failed compression call needs a smaller complete retry before exploration resumes.

## Verification limits

- No host internals or model weights were inspected. The rule does not diagnose why degeneration occurred.
- No external mutation was inferred from prose alone. Live tool and forge evidence defined the recovered state.
- The repository validator established format compatibility for the new entry. It does not prove that the procedure prevents every context failure.
