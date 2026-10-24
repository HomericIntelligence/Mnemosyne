# Evidence notes: automation-loop-random-model-pool-operation

Supporting evidence for [automation-loop-random-model-pool-operation](automation-loop-random-model-pool-operation.md). Repository, organization, issue, and host identifiers are withheld per the learn privacy rules; the patterns and measurements below are the decision-relevant content.

## Context

- Multi-item issue campaign on a per-issue automation loop (planner, reviewer, implementer agent jobs) running against a self-hosted model gateway.
- Operator policy restricted the drawable pool to two approved deployments. A third catalog-listed deployment was down for the campaign duration (provider error on every request), and a fourth was excluded by policy.
- The runner drew planner / implementer / reviewer / fallback at random (`shuf`) from the served set for each wave, and per-run role binding was recorded in the run header.

## Attempt timeline for the target planning item

| # | Wall time | Agent jobs | Disposition | First cause |
| --- | --- | --- | --- | --- |
| 1 | interrupted by operator after publish | 1 | RESUMABLE at plan_review | operator stop; review cycle left bound to the drawn reviewer |
| 2 | 17.8 s | 0 | BLOCKED:review-session-lost | fresh random draw picked a different reviewer than the session record; journal fail-closed |
| 3 | 19.4 s | 0 | zero items admitted | attempt 2's block had swapped `state:needs-plan` for `state:plan-blocked`; seeding selects on the needs-plan label |
| 4 | 92.1 s | 3 | FAIL: reviewer error retries exhausted (review-session-lost path) | drawn reviewer deployment was down; provider answered `No worker available` on every request |
| 5 | interrupted by operator | 1 job in flight | RESUMABLE at plan_review | operator stop after a live verifier process check |
| 6 | refused at launch | 0 | runner guard | another coordinator loop was live on the same intake checkout |
| 7 | 3725.3 s | 5 (3654.8 s agent time) | PASS, plan GO | content-probed draw, `--reset-plan-review-session`, seeding label restored; rounds NOGO → amend → NOGO → amend → GO |

External confirmation: a parallel operator-driven run of the same item without the reset flag reproduced `BLOCKED:review-session-lost` in 37.1 s with zero agent jobs, exactly as predicted from the bound-session record.

## Exact failure signatures

- Session guard: `review-session-lost: reviewer tool or model changed; reset the review session`; pipeline disposition `BLOCKED:review-session-lost`; the failure path applies the `state:plan-blocked` label to the issue.
- Dead deployment: `provider.invalid-request: No worker available for model '<name>'`. The agent CLI prints this line and still exits with status 0, which is why the probe must match output content.
- Silent no-op: a run whose candidate set is empty prints a normal pipeline summary with a zero-item count and exits 0 in under 20 seconds.

## Probe used

```bash
probe() { timeout 75 <agent-cli> run --model "<provider>/$1" \
  "Reply with exactly: OK" 2>&1 | grep -q OK; }
for cand in <allowed-deployments>; do
  probe "$cand" && POOL+=("$cand") || echo "EXCLUDED: $cand"; done
```

Observed: both policy-approved deployments answered OK within the timeout; the down deployment printed the provider error (exit 0) and was excluded by the missing token.

## Recovery commands (generalized)

```bash
# One-time recovery after BLOCKED:review-session-lost, before relaunch:
gh issue edit <n> --remove-label state:plan-blocked --add-label state:needs-plan
# Then relaunch with a fresh review cycle (plan text survives):
<loop> --issues <n> --reset-plan-review-session ...
```

## Privacy

Campaign logs and planning journals are internal evidence and are not copied here. Measurements above were taken from those logs; identifiers, paths, hostnames, organization and repository names, and model-deployment specifics that could identify the installation are generalized.
