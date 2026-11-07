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
## v1.4.0 evidence: concurrent-admission ceiling (2026-11-01)

Host context: one loaded shared agent host ran several waves of general
background lanes (plan-queue and implement-queue agents) under one multi-lane
automation program. The waves admitted lanes in parallel up to a planned
concurrency value.

### Measured signature

- Failure classes: admission-slot timeouts and
  `Timed out waiting for response headers`, both at dispatch or shortly after.
- Onset: the failures appeared at around eight concurrent general background
  lanes. No equivalent failures occurred at six or fewer concurrent lanes on
  the same host in the same window.
- Footprint per failure: zero artifacts on the assigned lane; the failure
  arrived at admission, not mid-work.

### Recovery discipline and outcome

- Each admission-failed lane got one relaunch with a duplicate-work guard
  (search open pull requests and branches for the assigned issue before any
  write; stop and report on a find).
- Freed slots refilled one at a time; the plan and implement queues
  alternated, so no queue starved and the concurrent count never re-entered
  the failure band.
- All four admission-failed lanes completed on their single relaunch. No lane
  needed degradation. Two consecutive identical infrastructure failures
  remained the per-lane hold condition for the session.

### Why the ceiling reading is load-bearing

A mass relaunch would re-create the exact concurrent count that produced the
failures. The throttled refill moved the same total work with zero added
failures, and the no-failure runs below the count are the evidence that the
bound is causal and not a coincidence of the work mix.

## v1.5.0 evidence: model-keyed admission (2026-11-07)

### Context

One shared agent host ran a large set of stopped background sessions. The
operator re-admitted them with one short continuation message each, through the
session prompt endpoint of the agent runtime. Each session kept its own bound
model from its earlier run; the re-admission did not change that binding.

### First reading: host ceiling

At wave start, about 88 sessions were active at the same time. Admission-slot
timeouts appeared, which matched the v1.4.0 host-ceiling signature. The
concurrent count then fell to about four. A probe re-admission still failed
with the same admission timeout, so the host count did not explain the
failures.

### Second reading: one model deployment

Grouping the last idle outcome by bound model id, in the same time window:

| Bound model id (anonymized as A and B) | Admission timeouts | Successes |
| --- | --- | --- |
| A | 87 | 15 |
| B | 7 | 117 |

Model A timed out at about five times its success rate, and model B had no
timeouts in the late window. The concurrent count was near four. Model B
sessions that started in the same minutes completed. Model A produced the
timeouts.

### Recovery discipline and outcome

- The continuation message stayed queued in the session inbox (delivery
  `steer`) while the session was not running. It was not a message that was
  lost, and no lane lost work at admission.
- After the queued set drained, 11 of 13 lanes that had earlier timed out
  completed on the queued message. The admission timeout was backpressure,
  not a dead lane.
- One lane kept failing on every attempt with the same non-timeout payload
  error, both before and after the re-admission window. It was held and
  reported, and it was not counted as capacity evidence.
- Sessions whose working directory belonged to a different project than the
  command ran in did not take the queued message. The message stayed queued
  until the session was resumed from its own directory. The re-admission
  command must bind to the session's own working directory.

### Why the model-keyed reading is load-bearing

Throttling the host would have reduced the concurrent count that was already
far below the ceiling, and it would not have removed the failures. The
model-keyed comparison identified the bound resource in one query and
separated it from a payload failure that looked identical by lane. A rebind or
a schedule change to a model with measured capacity is the action that removes
the backpressure.
