---
name: testing-jetstream-flaky-stream-state-leak
description: "Planning-reasoning checklist for diagnosing flaky JetStream/NATS integration tests whose root cause is suspected to be persistent broker stream / durable-consumer state leaking across test runs. Use when: (1) planning a fix for integration tests that fail intermittently with count-mismatch asserts (e.g. `assert 2 == 1`) only under full-suite or repeated runs; (2) the suspected cause is persistent broker/stream state (JetStream streams, durable consumers) leaking between runs; (3) choosing between purging shared state in an autouse fixture vs. making the subscriber consume only new messages (DeliverPolicy.NEW)."
category: testing
date: 2026-06-19
version: "1.0.0"
verification: unverified
user-invocable: false
tags:
  - flaky
  - integration-test
  - jetstream
  - nats
  - test-isolation
  - stream-state
  - durable-consumer
  - deliver-policy
  - purge-stream
  - planning
  - autouse-fixture
  - pytest
---

# Diagnosing Flaky JetStream/NATS Stream-State Leaks (Planning)

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-19 |
| **Objective** | Avoid unverified root-cause and unverified-API mistakes when planning a fix for flaky JetStream/NATS integration tests that fail only under repeated/full-suite runs |
| **Outcome** | Planning hypothesis only — failure was never reproduced; subscriber-type leak and nats-py API shapes were asserted but not confirmed |
| **Verification** | unverified — planning skill only; no test was run and no failure was reproduced |

## When to Use

- Planning a fix for integration tests that fail intermittently with count-mismatch asserts (e.g. `assert 2 == 1`) **only** under full-suite or repeated runs (passes in isolation).
- The suspected cause is persistent broker/stream state — JetStream streams or durable consumers — leaking across test runs.
- Choosing between option (a) "purge shared state in an autouse fixture" and option (b) "make the subscriber consume only new messages" (e.g. `DeliverPolicy.NEW` / DeliverNew).
- Any plan that asserts core NATS `subscribe()` and JetStream `pull_subscribe` behave identically with respect to history replay.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```python
# Autouse cleanup fixture — gated on the integration marker AND broker reachability.
# Purges every shared stream before each integration test; true no-op otherwise.
import pytest
import pytest_asyncio

@pytest_asyncio.fixture(autouse=True)
async def _purge_jetstream(request):
    # Gate 1: only run for integration tests.
    if request.node.get_closest_marker("integration") is None:
        yield
        return
    # Gate 2: never break the suite if the broker is down.
    try:
        import nats
        nc = await nats.connect("nats://localhost:4222", connect_timeout=1)  # calibrate to CI
    except Exception:
        yield
        return
    js = nc.jetstream()
    jsm = js  # JetStreamManager surface
    try:
        for stream in ("STREAM_A", "STREAM_B"):
            try:
                await jsm.purge_stream(stream)        # VERIFY this API on installed nats-py
            except Exception:                          # tolerate NotFoundError (stream absent)
                pass
        yield
    finally:
        await nc.drain()

# Durable consumer that ignores pre-existing stream content.
from nats.js.api import ConsumerConfig, DeliverPolicy
cfg = ConsumerConfig(deliver_policy=DeliverPolicy.NEW)   # VERIFY enum + kwarg on installed nats-py
sub = await js.pull_subscribe("subject", durable="d", config=cfg)  # VERIFY config= kwarg
```

```bash
# The load-bearing verification — a single green run does NOT prove a state-leak fix.
for i in $(seq 1 20); do pytest <module> -m integration -q || break; done
```

### Detailed Steps

1. **REPRODUCE before diagnosing.** Run the suspected test in a tight loop and across the full suite to confirm the count-mismatch is real and depends on run order / run count. Do **not** treat the issue's stated symptom (`assert 2 == 1`) as proof of the mechanism — it only proves a count mismatch, not its cause.
2. **Distinguish subscriber types empirically.** Determine whether the failing subscriber is core NATS `subscribe()` (live-only, no replay) or a JetStream `pull_subscribe` / push durable consumer (replays stream history and/or retains a delivery cursor). The root cause and the correct fix differ by type; conflating them mis-locates the bug.
3. **Prefer BOTH defenses when cheap.** Add an autouse per-test purge fixture (`jsm.purge_stream(name)`, tolerating NotFoundError) for guaranteed-clean state, PLUS `DeliverPolicy.NEW` on durable consumers so they ignore pre-existing stream content. Belt-and-suspenders: a purge alone won't fix a durable consumer that already advanced its cursor, and DeliverNew alone won't help future or other subscribers.
4. **Verify the nats-py API surface against the installed version** before committing the plan: confirm `jsm.purge_stream`, `ConsumerConfig` / `DeliverPolicy.NEW`, and that `pull_subscribe` accepts a `config=` kwarg. API names and kwargs drift across nats-py releases; an unverified kwarg fails at runtime.
5. **Gate the autouse fixture correctly.** It must be a true no-op for unit tests and when the broker is unreachable — check the test marker (`request.node.get_closest_marker("integration")`) AND wrap `connect` in try/except. Otherwise it slows or breaks the entire non-integration suite.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust the issue's `assert 2 == 1` symptom as proof of the leak mechanism | Wrote the root-cause section from the symptom alone, without reproducing | The same symptom has multiple causes (subject overlap between tests, JetStream replay, durable cursor retention); the right fix can't be picked without reproduction | Reproduce and bisect the mechanism before asserting a single root cause |
| Assume core NATS `subscribe()` and JetStream `pull_subscribe` behave the same w.r.t. replay | Reasoned about "stale messages" generically across subscriber types | Core `subscribe()` is live-only (no replay); only JetStream consumers replay history / retain cursors — conflating them mis-locates the bug | Identify the exact subscriber type per failing test before designing the fix |
| Cite nats-py APIs (`purge_stream`, `DeliverPolicy.NEW`, `pull_subscribe(config=)`) from memory | Wrote fix snippets without checking the installed nats-py version | API names and kwargs drift across nats-py releases; an unverified kwarg fails at runtime | Grep the installed package / docs for the exact API before putting it in a plan |
| Add an autouse cleanup fixture without gating | Fixture would connect to a broker for every test | Connecting to a broker on unit tests slows/breaks the non-integration suite | Gate autouse cleanup on the integration marker AND wrap connect in try/except for broker-down |

## Results & Parameters

- **Decision rule.** Option (a) purge fixture = guaranteed-clean state but pays a per-test broker round-trip cost; option (b) `DeliverPolicy.NEW` = cheap, no per-test connection, but only protects the consumers you change. Use **both** for durable-consumer tests.
- **Verification that PROVES the fix.** A repeat loop (e.g. `for i in $(seq 1 20); do pytest <module> -m integration -q || break; done`) is the load-bearing check — a single green run does not prove a state-leak fix. Per-test isolation passing is NOT sufficient; pass-when-run-together-repeatedly is the criterion.
- **Risk note.** `connect_timeout=1` in the fixture can itself become flaky on a slow / loaded CI broker — calibrate the connect timeout to CI, not localhost.
