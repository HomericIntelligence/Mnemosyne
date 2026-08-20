---
name: e2e-experiment-runner-bug-patterns
description: "Diagnose E2E experiment state-machine, checkpoint/resume, judge, rate-limit, path, baseline-inheritance, and rerun failures. Use when retry semantics confuse infra and bad grades, progressive resumes lose context, --until advances too far, agents silently do no work, judge output is empty/invalid, or rerun checkpoint states disagree."
category: debugging
date: 2026-06-07
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: mixed
history: e2e-experiment-runner-bug-patterns.history
tags: [e2e, state-machine, checkpoint, resume, judge, rate-limit, path-resolution, rerun]
---

# E2E Experiment Runner Bug Patterns

## Overview

Experiment runners combine nested state machines, durable files, concurrent checkpoint writes,
external CLIs, and costly retries. Diagnose from the persisted state and exact artifact paths before
resetting work. Keep pipeline progress distinct from judge outcome and make restore logic symmetric
with validation/write logic.

Detailed ProjectScylla/ProjectHephaestus cases are indexed in
[`e2e-experiment-runner-bug-patterns.notes.md`](e2e-experiment-runner-bug-patterns.notes.md). The
complete prior source is in
[`e2e-experiment-runner-bug-patterns.history`](e2e-experiment-runner-bug-patterns.history).

## When to Use

- Infra crashes and valid bad-grade terminal runs are retried together.
- Checkpoint writes race or resume raises assertion/file-not-found errors.
- Repeated resume works initially then fails on the third or fourth attempt.
- `--until` executes one extra action, signals do nothing, or state names are misread.
- A merged baseline fails when one parent is missing despite other completed parents.
- Agents report zero tokens/cost due to relative working-directory errors.
- Rate-limit JSON appears on stdout or an exit-zero response contains an error.
- Judge output is empty, prose, partial JSON, regenerated from changed inputs, or inconsistently valid.
- A rerun script uses the executor constructor or checkpoint status incorrectly.

## Verified Workflow

### 1. Preserve state semantics

Treat progress and outcome as different axes:

```text
run_states.failed/rate_limited    -> incomplete infrastructure state; retry
run_states.worktree_cleaned       -> pipeline complete at any grade; do not retry
completed_runs.passed/failed      -> valid judged outcome; do not retry
completed_runs.agent_complete     -> agent finished, judge incomplete
```

Retry based on nonterminal `run_states`, not a second pass over bad grades. Infra retries should not
depend on an opt-in flag. Reset only affected incomplete/rate-limited runs; dry-run and back up the
checkpoint before any post-hoc mutation.

### 2. Make checkpoint writes atomic per process

Multiple threads share a PID, so PID-only temp names collide. Serialize write-plus-replace with one
lock and include process and thread identity in the temp file. Write a complete serialized model,
flush as required, then atomically replace the target. Test concurrent writers and interrupted temp
files.

### 3. Restore every field required by the resumed state

Before building actions, restore tier configuration/directory for nonterminal resumed tiers. For a
run at or beyond judge completion, load a valid judgment. At or beyond finalization, load the run
result, filtering legacy extra keys through the current frozen model schema.

Validation and load functions must share one path constant. If a fourth resume fails after earlier
successes, compare every existence check, writer, and loader path before blaming state synchronization.
Run a fresh experiment and resume it at least four times to verify progressive durability.

Reconstruct `RunContext` before action dispatch on mid-sequence `--until` resume; required fields
cannot remain `None` merely because earlier actions are skipped.

### 4. Define state transitions and until semantics precisely

State names describe the action just completed; the action registered while in that state produces
the next state. `advance_to_completion(until=X)` must advance once, examine the post-advance state,
and stop when it equals X. Apply the same contract to experiment, tier, subtest, and run machines.

Reset a tier to the state whose next action reruns subtests—do not choose a similarly named state
whose action selects results. Replace assertions at recoverable resume boundaries with explicit
reconstruction or classified errors. Pass the actual shutdown callback into terminal/signal guards
and test Ctrl+C from a running transition.

### 5. Degrade merged-baseline inheritance correctly

When a primary result exists but has no winner, independently try the fallback winner file; an
`elif` can suppress that fallback. For multiple parent tiers, warn and continue on a missing parent,
then fail only when all required parents are unusable. A rerun path may skip/clean a tier on baseline
construction failure rather than corrupting the whole experiment.

### 6. Canonicalize subprocess paths

Resolve workspace paths before using them as `cwd` and record the same resolved value in command
logs. A relative workspace interpreted after parent-directory changes can make every agent fail with
`cd: No such file or directory`, exit 1, zero tokens, zero cost, and near-zero duration. Inspect raw
agent stderr/result artifacts before classifying model failure.

### 7. Detect rate limits in every response shape

Scan stderr and stdout for reset time. External CLIs may return error JSON on stdout with exit zero.
Detector return `0` can mean “rate limited, reset unknown”; test `is not None`, not truthiness or
`or` chaining. Handle both subprocess exceptions and successful JSON envelopes whose `is_error` is
true. Wait/retry only after a recognized quota result; otherwise raise the original error.

For post-hoc diagnosis, look for a tier cliff: early success followed by short runs with status 429,
zero tokens/cost, and error JSON. Dry-run the reset script, apply only affected runs, and rerun those
tiers. A quota-failed run misrecorded as cleaned plus a bad-grade outcome will require explicit repair.

### 8. Make judge input/output durable and singular

Extract an entire fenced JSON block, then parse it; a non-greedy “through first brace” regex truncates
nested objects. Retry malformed prose with a strict JSON-only reminder and bounded attempts.

Pass judge prompts over stdin when variadic CLI options could consume a positional prompt. Prefer a
streaming JSON format and collect assistant text events when the final result field is empty. During
regeneration, reuse the saved `judge_prompt.md`; rebuild from the workspace only as an explicit,
warned fallback because the workspace may have changed.

Use one validity predicate for live, restored, regenerated, and consensus paths. Require a score,
respect `is_valid`, map legacy fallback judgments to invalid, and filter invalid entries before
consensus.

### 9. Keep rerun APIs and checkpoint values exact

Construct the executor only with constructor-owned dependencies; pass tier, baseline, run directory,
and subtest to the per-run method using its exact parameter names. Record checkpoint completion as
`passed` or `failed` from the judge result; `agent_complete` is the only incomplete-agent terminal
marker. Do not invent `completed` when the checkpoint enum does not accept it.

### 10. Verify with a staged resume matrix

Exercise fresh free stages, agent execution, post-agent/judge preparation, judge execution, final
report/checkpoint cleanup, and final completion. At each `--until` boundary, reload in a new process,
assert restored context, and continue. Include concurrent checkpoint writers, corrupted/missing
artifacts, invalid judge entries, partial parent tiers, signal shutdown, and four successive resumes.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Outcome retry | Retried `completed_runs=failed` | Bad grade was a valid result | Retry incomplete run state only |
| PID temp | Shared checkpoint temp by PID | Threads collided and rename saw ENOENT | Lock and include thread ID |
| Partial restore | Restored state enum only | Later action fields remained `None` | Restore all fields required past boundary |
| Split path constants | Validated one judge file, loaded another | Progressive resume failed late | Share one writer/validator/loader path |
| Pre-advance until | Compared old state after action | Executed one extra expensive stage | Compare post-advance state |
| `elif` fallback | Tried winner fallback only when result absent | Null winner suppressed fallback | Test fallback independently |
| Relative cwd | Passed workspace without resolving | All agents silently failed `cd` | Resolve and log canonical cwd |
| Truthy reset | Combined detector results with `or` | Reset sentinel zero disappeared | Check `is not None` |
| Partial JSON regex | Stopped at first closing brace | Nested judge JSON truncated | Extract full fence then parse |
| Positional prompt | Put prompt after variadic CLI option | CLI consumed it as option value | Send prompt over stdin |
| Rebuilt judge prompt | Regenerated from changed workspace | Result was not comparable | Reuse saved prompt first |
| Invented rerun status | Wrote `completed` | Checkpoint validation rejected it | Use passed/failed/agent_complete |

## Results & Parameters

```text
experiment/tier/subtest/run identity and config hash
run state, completed outcome, retry/reset disposition
checkpoint path, temp identity, writer thread, serialized digest
resume boundary and every restored RunContext/TierContext field
judge/result/run-result shared path constants
until target, pre/post state, signal outcome
resolved workspace cwd and raw agent stdout/stderr/result
rate-limit detector source/reset epoch and reset dry-run diff
saved judge prompt digest, parse attempts, validity/consensus set
parent baseline successes/failures and rerun checkpoint status
fresh plus four-resume verification matrix
```

## Verified On

- ProjectScylla fixes across retry, checkpoint, resume, until, baseline, path, judge, and rerun flows.
- ProjectHephaestus rate-limit retry path.
- Verification is `mixed`: individual fixes have local/CI evidence, while some campaign diagnoses and
  parameter values remain observational; see notes/history.
