# Notes: hephaestus-random-model-draw-launch-safety

Supporting evidence for the main skill. Source: one supervised campaign that ran
the Hephaestus automation loop with a per-run random model draw against the four
remaining children of epic #895 on repository comet (2026-10-22 to 2026-10-24).

## Campaign context

- Scope: children #963 (viewer blue-green), #964 (recovery/rollback/cancel),
  #965 (public release commands), #966 (rollout policy). Wave-0 goal: each child
  holds `state:plan-go` before implementation starts.
- Agent backend: opencode v2. Provider pool after exclusions:
  `comet/kimi-k3-fp8` and `comet/deepseek-v4-1-flash-1017`.
  Exclusions with evidence: `comet/kimi-k3` by operator decision;
  `comet/glm-5.3-flash-fp8` after its deployment reported `No worker available`.
- Wrapper: a per-wave `run-wave.sh` that health-probes the pool, draws
  planner/implementer/reviewer/fallback randomly, records the draw in the first
  lines of the wave log, and refuses a launch when a guard condition holds.

## Failure timeline (signatures in order)

All timestamps UTC. Attempt numbers are per the campaign plan document.

1. Attempt 2, 2026-10-23 16:48 — `BLOCKED:review-session-lost` in 17.8 s,
   `agent jobs: 0`. Cause: a stale review session from an earlier wave was
   bound to reviewer `kimi-k3-fp8`; the fresh draw picked `glm-5.3-flash-fp8`;
   the review journal fail-closes on reviewer tool/model change mid-session.
2. Attempt 3, 2026-10-23 22:01 — run admitted 0 items. Cause: attempt 2's
   failure path had published `state:plan-blocked` on #966 ("awaiting external
   intervention"), and seeding excludes that label. External intervention:
   label restored to `state:needs-plan`.
3. Attempt 4, 2026-10-23 22:05 — `reviewer error retries exhausted
   (review-session-lost)` after 3 agent jobs ran. Cause: the drawn reviewer
   `glm-5.3-flash-fp8` deployment was down (`No worker available`). Exit-status
   checks had passed because `opencode` exits 0 on provider failure. Fix:
   content probes added to `run-wave.sh` (success = `OK` in the probe output).
4. Attempt 5, 2026-10-23 22:14 — operator SIGINT. Disposition RESUMABLE at
   plan_review; labels untouched; no zombie writes. Not a failure of the
   rules.
5. Parallel operator run, 2026-10-23 to 2026-10-24 — its #966 plan_review
   failed `review-session-lost` as predicted by the campaign plan: the review
   cycle was bound to attempt-5's reviewer `kimi-k3` while the operator run
   drew `kimi-k3-fp8`, with no reset flag. #966 was re-labeled
   `state:plan-blocked` a second time. (That run's #963 pr_review also failed
   `repository_validation_source_gap` over two duplicate PRs, #2928 and
   #2942 with near-identical diffs — recorded here only as campaign context;
   duplicate-PR triage is outside this lesson.)
6. Attempt 6, 2026-10-23 ~22:30 — REFUSEd by the launch guard. Cause: the
   blanket guard refused any launch while a loop was live anywhere on the
   repository (a sibling intake clone's operator run).
7. Guard fix, 2026-10-24 — `run-wave.sh` same-clone rule: refuse only when a
   live loop shares this run's intake clone. Multi-agent parallel clones are
   the established operating pattern.
8. Attempt 7, 2026-10-24 00:57 to 01:57 — PASS. #966 plan GO.
   Wall 3725.3 s; 5 agent jobs (3654.8 s agent time). Rounds: NOGO at 01:10,
   amend, NOGO at 01:45, amend, GO at 01:57; the loop applied
   `state:plan-go`. Draw: planner and reviewer `kimi-k3-fp8`, implementer and
   fallback `deepseek-v4-1-flash-1017`; probes green. Wave-0 complete: #963,
   #964, #965, #966 all hold `state:plan-go`.

## Why each rule has this shape

- Draw-pin rule: the fail-close triggers on ANY reviewer tool/model change for
  an in-flight review session. With a random per-run draw, EVERY relaunch of an
  in-flight item is a probable trigger. The two repair options are mutually
  exclusive per item: pin the slot to the bound model (keep earlier rounds), or
  `--reset-plan-review-session` (discard rounds, start at round 0 / revision 1;
  acceptable when the item has no usable rounds).
- Label-restore rule: the plan-blocked label is a side effect of the fail-close
  failure path, not of intake. Without the restore, the relaunch admits zero
  items with no error, which reads like an intake defect and costs a diagnosis
  cycle.
- Content-probe rule: provider failure surfaces as exit status 0 with
  diagnostic output on this backend. `No worker available` and a clean exit
  code co-occur. Only an output token distinguishes a live deployment.
- Clone-scoped guard rule: lane and intake state live under each clone's own
  path. Two loops on different clones of one repository do not share mutable
  automation state; a repository-wide guard therefore expresses a coupling that
  does not exist, and it deadlocks queued waves behind unrelated long runs.

## Out-of-scope observations kept for context

- Implementer timeout sizing (5400 s insufficient with forward progress; the
  documented doubling rule and limit) is covered by
  `hephaestus-interrupted-implementation-lane-recovery` and was applied in this
  campaign without change.
- Duplicate-PR collision handling (`repository_validation_source_gap`, two PRs
  for one issue) was left as an operator decision in this campaign; no verified
  resolution was produced here, so no rule is claimed.
