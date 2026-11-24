# autoscaled-replica-demand-probing — development notes

Supporting evidence for the main skill. Generalized; no fleet, host, repository, model, or account identifiers.

## Run context

A client-side bring-up run dispatched an identical evaluation task to each model of a six-class served fleet (0.9B-class, 3.7B-class, 7B-class, 32B-class, 36B-class sparse MoE, 375B-class sparse MoE), one dispatch per model, serial. The dispatcher polled fleet status every 60 s and sent each model its task the moment the status read reported it live.

## Measurements

- A metadata-only status poll ran about eleven hours against a healthy gateway while two pending pools stayed off. Zero scale-outs followed. The fleet autoscale policy states scale-out converts gateway demand signals to desired-replica steps, gated by confirmed persisting demand, one replica per tick, inside per-pool floor/ceiling bounds, with a fleet node-budget veto above the account's scheduler group. The metadata read supplied no demand signal, so the contract explains the empty window.
- Two earlier windows closed with the gateway down (connection refused, then 503, then request timeouts), which independently prevented both demand creation and dispatch.
- After the demand-probe fix (per-tick probe with a 16-token budget per pending off-pool), a third window ran its full deadline with the gateway mostly healthy and the pool still off. The account's scheduler group sat at its node limit for the whole run, so the fleet node-budget veto was the suspected holder. The positive demand-probe scale-out was therefore observed only from the documented contract, not from a live scale-out.
- One pending pool reported a brief live window during the run and the dispatcher dispatched its task within the same minute: 0.9 s warmup acceptance path, then 140.9 s task completion with the full-context token budget (context minus 1024 prompt-headroom tokens).
- Warmup acceptance finding: a reasoning-parser model family returns non-empty reasoning content with empty visible content at small budgets (observed at 512-token warmup budgets and at 747 completion tokens with an empty final answer on the smallest class). Accepting either field fixed warmup verification for every reasoning-parser class.
- Budget failure mode: the gateway rejects a request whose prompt plus completion budget exceeds the model context (observed HTTP 400). The workable dispatch budget is the full context minus prompt headroom (about 1024 tokens).

## Dispatcher parameters exercised

- Warmup: fixed content probe, `max_tokens=512`, discarded, accepted by non-empty `content` OR `reasoning_content`.
- Work dispatch: one per model, serial, completion budget = context − 1024, dispatch timeout 4 h, run deadline 12 h.
- Infra errors (HTTP 4xx/5xx, connection drops) did not consume a work attempt; capped at 15 retries across live windows. Model failures did not retry.
- Demand probe while off: `max_tokens=16`, 30 s request timeout, per-tick, attempts capped.

## Evidence limits

- The demand-probe positive branch is contract-backed, not observed live: no window in this run ended with a probe-driven scale-out. The node-budget veto was the suspected cause; probe correctness was not disproven.
- The metadata-read-is-not-a-demand branch is backed both by the documented contract and by the observed eleven-hour empty window.
- The probe-acceptance branch is backed by live warmup observations across every reasoning-parser class in the fleet.
- Scale-in and scale-to-zero behavior was not exercised in this run; it comes from the same documented policy.

## Aside: dispatcher wedge

One dispatcher instance froze for about thirty hours past its run deadline with zero log output while its status file stayed empty. A blocked stdout stream (output consumer stopped, `print` blocking on a full pipe) froze the loop before any further logging. Kill and relaunch recovered it. The fix class for long-running pollers: keep a deadline check that does not depend on stdout consumption, or log through a mechanism that cannot block the loop.
