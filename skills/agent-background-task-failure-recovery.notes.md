# Notes: agent-background-task-failure-recovery

Privacy-safe supporting evidence. Provenance: LLM360/comet pull request #3239
(merged as squash commit `20f7f37231`), author evidence record in the pull
request comment thread.

## v1.3.0 evidence: verdict-lane spawn wave (2026-10-30)

Session context: a merged-bound fix required an independent reviewer verdict
before merge. The author dispatched skill-bearing review subagents from the
main session.

| Dispatch | Product | Result |
| -------- | ------- | ------ |
| 1 | issue review | `Failed to drain Session: invalid or missing API key` |
| 2 | source review | `invalid or missing API key` |
| 3 | issue review (retry) | `invalid or missing API key` |
| 4 | source review (retry) | `Timed out waiting for response headers` |
| 5 | combined review (retry) | `invalid or missing API key` |
| probe | trivial no-skill "OK" task | success (once) |

Every failure surfaced at the spawn call. No dispatched agent made a tool
call; the footprint was zero in every case.

## Decisions taken and their outcomes

- **Inline review, labeled.** The author completed the review inline and
  published it as an author evidence record. The record states that it is not
  an independent reviewer state and names the infrastructure failures as the
  reason. The independence requirement was not relaxed.
- **Operator escalation.** The merge decision went to the operator with the
  evidence record, the PR's required checks (50/50 green), and the live
  reproduction log. The operator directed the merge.
- **No self-issued gate.** The author did not apply the repository's
  implementation gate label from its own review. The label moved only after
  the operator decision.

## Why the trivial probe was weak evidence

The probe carried no skill content, a minimal prompt, and a short response.
The failing spawns carried skill payloads and long prompts. One probe success
in the failure window therefore separated two hypotheses — total outage versus
profile-dependent failure — only after the next real dispatch failed again.
The procedural fix is the ordering: probe with the same profile as the failing
work, retry the real dispatch once, then degrade.
