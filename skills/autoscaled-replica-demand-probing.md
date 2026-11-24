---
name: autoscaled-replica-demand-probing
license: BSD-3-Clause
description: "Probe an autoscaled serving fleet so replicas scale out while you wait, when you hold no operator access. Use when: (1) a pool or model stays off and you wait for replicas to come up, (2) your only status surface is a metadata list endpoint, (3) a bring-up probe answers empty content because a reasoning-parser family returns reasoning only at small budgets, (4) the gateway answers 503 while a pool is off and you must decide whether a start is pending, capacity is absent, or the request is wrong, or (5) a status projection still reports a model off while a start may be pending, or a served model returns to off."
category: tooling
date: 2026-11-24
version: "1.1.0"
user-invocable: false
tags: [autoscaling, serving, scale-out, scale-in, demand-signal, probe, replica, pool, start-verification, scheduler-queue, reasoning-parser, warmup, capacity, gateway, "503"]
---

# Autoscaled Replica Demand Probing

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Bring up replicas of a served model fleet from the client side, when fleet autoscaling governs scale-out and you hold no operator or decision-log access. |
| **Outcome** | Operational. A metadata-only poll ran for about eleven hours against a healthy gateway while every pending pool stayed off: a metadata read is not a demand signal, so the autoscaler never saw persisting demand and never scaled out. A later probe run sent one short real request to each off model. Six of nine off models started and served; the other three stayed in the scheduler queue, one blocked by a reservation. The first requests returned 503 `model_start_unavailable` before the supervisor published a start verdict; a retry returned `model_starting` and the replica started. Several zero-floor pools that served the probe returned to zero after the demand hold expired. |

## When to Use

- A pool or model is reported off, you wait for replicas to come up, and you can send requests but cannot read autoscaler decision logs.
- Your status surface is a metadata list endpoint, such as a models-list route that reports per-model state and replica counts.
- A bring-up or warmup probe answers empty content, and you must decide whether the request budget or the probe acceptance is wrong.
- The gateway answers 503 while a pool is off, and you must decide whether a start is pending, capacity is absent, or the request is malformed.
- A status projection still reports a model off while a demand start may be pending, or a served model returns to off; you must decide whether that is a failure or the expected scale-in.
- A dispatch plan waits for live windows so it can send real work to each pool the moment it is live.

## Verified Workflow

### Quick Reference

```python
# Per tick, for each pending pool that is still off:
try:
    probe("Reply with exactly: OK", model=pending, max_tokens=16, timeout=30)
except (Timeout, ServiceUnavailable):
    pass  # 503 or a timeout while off means "not yet scaled". Keep the capped loop.
sleep(tick)
# Treat the models-list endpoint as status only. Scale-out follows persisting demand,
# one replica per tick, inside floor/ceiling bounds and the fleet node-budget veto.
# A 503 model_start_unavailable is a verdict race; retry. model_starting means progress.
# Verify a start with the models list and the job scheduler; a status projection can lag.
```

1. Classify each status read before you rely on it. A metadata read reports state; a real request creates demand. Only demand moves the autoscaler. Use the models list and the job scheduler as ground truth; a status projection can lag when its worker heartbeat is stale.
2. For each pending pool that is still off, send one tiny real request per tick: a fixed content probe, a small token budget, a short request timeout, and capped attempts per pool.
3. Classify the 503 and the pending job before you change the loop. `model_start_unavailable` means the demand record exists but the supervisor has no fresh verdict yet; retry after the advertised delay. `model_starting` means the supervisor saw the demand and is starting a replica. A pending job with reason `Priority` is capacity-queued, not failed. A protected-floor job with `ReqNodeNotAvail` is blocked by a reservation. Neither pending reason is a probe failure.
4. Accept the probe by output, not by exit status or HTTP success alone: treat non-empty `content` OR non-empty `reasoning_content` as a live answer. A reasoning-parser family can return reasoning only at small budgets.
5. Send one warmup request to each pool the moment it first reports live, accept it by the same rule, and discard it: warmup samples never enter a score or a judgment.
6. Dispatch real work immediately after the accepted warmup, serially per pool. Infra errors (HTTP 4xx or 5xx, connection drops) do not consume a work attempt; retry on the next live window with capped attempts.
7. If a healthy gateway persists for many ticks with zero scale-outs, stop trusting the probe and check the budget layers: pool floor and ceiling bounds, and the fleet node-budget veto above the account's group limit.
8. Expect scale-in after the demand hold. A zero-floor pool that served the probe can return to zero when the demand window expires; the replica job ends and the model reports off again. That is the expected idle behavior, not a probe failure.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Polled only the models-list endpoint for about eleven hours with a healthy gateway, waiting for two pending pools to report live. | A metadata read creates no demand. The autoscale contract confirms scale-out only for confirmed persisting demand, so the pools never scaled and the window closed empty. | Treat the metadata endpoint as status only. While a pool is off, send a tiny real request per tick so the autoscaler sees persisting demand. |
| Attempt 2 | Sent the warmup content probe with a small token budget and required non-empty `content` as the live answer. | A reasoning-parser model family returns reasoning content and empty `content` at small budgets, so the probe looked failed while the model had answered. | Accept a bring-up probe when `content` OR `reasoning_content` is non-empty. Probe by output text, never by exit status. |
| Attempt 3 | Treated a 503 from the gateway, or a status projection that still showed the pool off, as a failed start, and backed off with longer sleeps. | The first 503 was `model_start_unavailable`: the demand record existed but the supervisor had no fresh verdict yet. A retry returned `model_starting` and the replica started. The status projection lagged the scheduler. | Keep the capped per-tick probe loop through 503 and timeouts while a pool is off. Read the error code; use the models list and the job scheduler as ground truth. Back off only after the budget layers fail. |
| Attempt 4 | Assumed that demand probes guarantee a scale-out on the next tick once the gateway recovers. | The fleet node-budget veto can hold scale-out when the account's scheduler group sits at its node limit; probes were correct, yet nothing scaled for the whole window. | Demand is necessary but not sufficient. When probes persist and nothing scales, verify pool bounds and the node-budget veto before you blame the probe path. |

## Results & Parameters

| Parameter | Value | Notes |
| --------- | ----- | ----- |
| Demand-probe token budget | `max_tokens=16` | Small enough to cost nothing, large enough to count as demand. |
| Poll tick | 60 s | One demand probe per pending off-pool per tick. |
| Probe request timeout | 30 s | A hung gateway must not stall the loop; the probe must yield before the next tick. |
| Warmup budget | `max_tokens=512` | First request after a pool reports live; accepted by content-or-reasoning, then discarded. |
| Infra-error attempts cap | 15 per pool | HTTP 4xx/5xx and connection drops retry on the next live window; a model failure does not retry. |
| Work dispatch | 1 per pool, serial | Match concurrency to replica count; a wider burst starves single-replica pools. |
| Scale-out contract | 1 replica/tick | Confirmed persisting demand gates it; pool floor/ceiling bounds and a fleet node-budget veto bound it. |
| Scale-in contract | Sustained idle window | Idle pools can scale to zero, which restarts the demand loop on the next use. |
| 503 classification | `model_start_unavailable`, then `model_starting` | The first means the demand is recorded but the supervisor has no fresh verdict; retry after the advertised delay. The second means the start is in progress. |
| Start verification | models list and job scheduler | Use these as ground truth. A status projection can lag when its worker heartbeat is stale. |
| Pending job reasons | `Priority` = capacity queue; `ReqNodeNotAvail` = reservation block | Neither reason is a probe failure. Clear them with capacity or reservation changes, not more probes. |
| Scale-in observation | Demand hold expiry | A zero-floor pool returns to zero after the hold; the replica job ends. This is expected. |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An autoscaled multi-model LLM serving fleet (0.9B-class to 375B-class sparse MoE) | Client-side bring-up run with no operator access; an about-eleven-hour metadata-only poll produced zero scale-outs, and a later demand-probe window targeted nine off models. | Probe acceptance and dispatch-flow parameters were exercised live. The later window supplied the positive branch: six of nine off models started and served; the other three stayed in the scheduler queue, one blocked by a reservation. The first requests returned `model_start_unavailable`, then `model_starting`. Several zero-floor pools returned to zero after the demand hold. See [notes](autoscaled-replica-demand-probing.notes.md). |

## References

- [Serving implicit zero-capacity pool](serving-implicit-zero-capacity-pool.md): the control-plane mechanism that turns a demand record into a start verdict for a model with no explicit pool record.
- [Serving replica floor enablement](serving-replica-floor-enablement.md): how a zero floor permits the on-demand start path and a positive floor requires the operator start.
