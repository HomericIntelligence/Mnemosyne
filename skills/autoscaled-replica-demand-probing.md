---
name: autoscaled-replica-demand-probing
license: BSD-3-Clause
description: "Probe an autoscaled serving fleet so replicas scale out while you wait, when you hold no operator access. Use when: (1) a pool or model stays off and you wait for replicas to come up, (2) your only status surface is a metadata list endpoint, (3) a bring-up probe answers empty content because a reasoning-parser family returns reasoning only at small budgets, or (4) the gateway answers 503 while a pool is off and you must decide whether capacity is absent or the request is wrong."
category: tooling
date: 2026-11-24
version: "1.0.0"
user-invocable: false
tags: [autoscaling, serving, scale-out, demand-signal, probe, replica, pool, reasoning-parser, warmup, capacity, gateway]
---

# Autoscaled Replica Demand Probing

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Bring up replicas of a served model fleet from the client side, when fleet autoscaling governs scale-out and you hold no operator or decision-log access. |
| **Outcome** | Operational. A metadata-only poll ran for about eleven hours against a healthy gateway while every pending pool stayed off: a metadata read is not a demand signal, so the autoscaler never saw persisting demand and never scaled out. The documented autoscale contract names the client-side lever: scale-out happens when the gateway sees confirmed persisting demand. A probe loop that sends one tiny real request per pending pool per tick is that lever, with one replica added per tick inside floor and ceiling bounds and a fleet node-budget veto above them. |

## When to Use

- A pool or model is reported off, you wait for replicas to come up, and you can send requests but cannot read autoscaler decision logs.
- Your status surface is a metadata list endpoint, such as a models-list route that reports per-model state and replica counts.
- A bring-up or warmup probe answers empty content, and you must decide whether the request budget or the probe acceptance is wrong.
- The gateway answers 503 while a pool is off, and you must decide whether capacity is absent or the request is malformed.
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
```

1. Classify each status read before you rely on it. A metadata read reports state; a real request creates demand. Only demand moves the autoscaler.
2. For each pending pool that is still off, send one tiny real request per tick: a fixed content probe, a small token budget, a short request timeout, and capped attempts per pool.
3. Accept the probe by output, not by exit status or HTTP success alone: treat non-empty `content` OR non-empty `reasoning_content` as a live answer. A reasoning-parser family can return reasoning only at small budgets.
4. Send one warmup request to each pool the moment it first reports live, accept it by the same rule, and discard it: warmup samples never enter a score or a judgment.
5. Dispatch real work immediately after the accepted warmup, serially per pool. Infra errors (HTTP 4xx or 5xx, connection drops) do not consume a work attempt; retry on the next live window with capped attempts.
6. If a healthy gateway persists for many ticks with zero scale-outs, stop trusting the probe and check the budget layers: pool floor and ceiling bounds, and the fleet node-budget veto above the account's group limit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Polled only the models-list endpoint for about eleven hours with a healthy gateway, waiting for two pending pools to report live. | A metadata read creates no demand. The autoscale contract confirms scale-out only for confirmed persisting demand, so the pools never scaled and the window closed empty. | Treat the metadata endpoint as status only. While a pool is off, send a tiny real request per tick so the autoscaler sees persisting demand. |
| Attempt 2 | Sent the warmup content probe with a small token budget and required non-empty `content` as the live answer. | A reasoning-parser model family returns reasoning content and empty `content` at small budgets, so the probe looked failed while the model had answered. | Accept a bring-up probe when `content` OR `reasoning_content` is non-empty. Probe by output text, never by exit status. |
| Attempt 3 | Treated a 503 from the gateway while a pool was off as a malformed request and backed off with longer sleeps. | The 503 was the "capacity absent, not yet scaled" state, not a request error. Backoff removed the per-tick demand signal and delayed any scale-out further. | Keep the capped per-tick probe loop through 503 and timeouts while a pool is off. Back off only after the budget layers fail. |
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

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An autoscaled multi-model LLM serving fleet (six model classes, 0.9B-class to 375B-class sparse MoE) | Client-side bring-up run with no operator access; an about-eleven-hour metadata-only poll against a healthy gateway produced zero scale-outs, and probe windows expired with pools off while the account's scheduler group sat at its node limit | Probe acceptance and dispatch-flow parameters were exercised live during the run. The positive demand-probe scale-out was observed only from the documented autoscale contract, not from a live scale-out; the node-budget veto branch was the suspected cause. See [notes](autoscaled-replica-demand-probing.notes.md). |
