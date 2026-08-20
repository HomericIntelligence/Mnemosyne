# Concurrency and Process Reliability Patterns — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Cross-process semaphore and worker error handling | [immutable source documenting ProjectScylla PR #151](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/concurrency-and-process-reliability-patterns.md) | Recorded implementation evidence | Retained as global scarce-operation cap |
| Optional NATS import enum failure | [immutable source documenting ProjectScylla PR #1784](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/concurrency-and-process-reliability-patterns.md) | Recorded implementation evidence | Retained as narrow import-guard rule |
| Pytest OOM located with virtual-memory bisection | [ProjectHephaestus PR #412](https://github.com/HomericIntelligence/ProjectHephaestus/pull/412) | Verified by recorded test repair | Retained as bounded-shell diagnostic |
| Transient clone retry | [immutable source documenting ProjectScylla PR #146](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/concurrency-and-process-reliability-patterns.md) | Recorded implementation evidence | Retained as classified bounded retry |
| Executor shutdown leaked an in-flight reviewer subprocess | [ProjectHephaestus PR #2061](https://github.com/HomericIntelligence/ProjectHephaestus/pull/2061) | `verified-ci`: real sleeping-child regression and 137 affected tests | Retained as process-group registry and shutdown ordering |
| General finite bounds for four direct subprocess sites | [ProjectHephaestus issue #2398](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2398) | `unverified`: reviewed plan only | Retained with explicit design-stage boundary |

## Operational parameters

These are starting points, not universal constants:

| Parameter | Suggested bound | Reason |
| --- | --- | --- |
| Operator timeout override | Integer `1..86400` seconds | Reject zero, negative, malformed, and unbounded input |
| Terminal restoration | 2 seconds | Cleanup must not hang shutdown |
| Retry attempts | 3 | Bound transient recovery |
| Retry delay | Exponential, capped near 8 seconds | Avoid a hot loop and excessive delay |
| Timeout exit code | 124 | Stable CLI-facing timeout contract |
| TERM grace | Short fixed interval | Give cooperative descendants time before KILL |

Repository context can justify different values; retain validation and finite upper bounds.

## Process ownership details

- A registry stores only process groups created and owned by the application.
- Registration occurs immediately after spawn and before the blocking call.
- Unregistration belongs in `finally` so success, failure, and cancellation converge.
- PID reuse and already-exited races are expected; permission errors and foreign ownership are not.
- Output included in timeout exceptions may be bytes, text, missing, or sensitive. Normalize safely
  and redact before logging.
- POSIX process groups allow descendant cleanup. Non-POSIX fallback guarantees only direct-child
  termination unless a platform-specific job abstraction is implemented.

## Evidence boundary

The leaked-child process-group pattern has CI evidence including a real subprocess. The generalized
timeout wrapper, hostile diagnostic payloads, and portability matrix from issue #2398 are plan-only
and remain unverified.
