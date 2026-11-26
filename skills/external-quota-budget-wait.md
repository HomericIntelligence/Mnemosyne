---
name: external-quota-budget-wait
description: "Replace a fixed client pace with a wait on the provider-reported quota reset. Use when a shared client throttles API calls at a fixed rate, the provider reports remaining quota and a reset time, and callers wait more than necessary or repeat the same throttle log line on every call."
category: architecture
date: 2026-11-26
version: "1.0.0"
user-invocable: false
tags:
  - rate-limit
  - quota-budget
  - token-bucket
  - reset-wait
  - single-flight
  - deadline
  - cache-coherence
  - log-once
---

# External Quota Budget Wait

## Overview

| Field | Value |
| ------- | ----- |
| **Date** | 2026-11-26 |
| **Objective** | Make a shared client spend its external quota at the provider-reported pace instead of a fixed local pace. |
| **Outcome** | Successful. A fixed pace was replaced by a budget wait, and five review rounds removed the failure branches. |

## When to Use

- A shared client throttles external API calls with a fixed refill rate.
- The provider reports `remaining` quota and a `reset` time from a non-consuming endpoint.
- Users lower the fixed rate as a workaround because the client cannot see the real budget.
- Callers wait several seconds for each call although the budget is nearly full.
- The throttle writes the same debug line on every acquire call.

Do not use this skill to diagnose a lockout or an exhausted account. Use
[github-shared-token-lockout-rate-limit-diagnosis](github-shared-token-lockout-rate-limit-diagnosis.md)
for that decision.

## Verified Workflow

### Quick Reference

| Reported state | Decision |
| ------- | -------- |
| `remaining` > reserve | Return at once. Do not spend a bucket token. |
| `0 <= remaining <= reserve` and `0 < reset - now <= one window` | Wait `reset - now + margin`. Drop the cache. Return. |
| `reset <= now` | Warn one time for that value. Use the token bucket. |
| `reset - now > one window` | Warn one time for that value. Use the token bucket. |
| Budget probe unavailable | Use the token bucket. |
| Configured rate is 0 | Disable the wait and the bucket. Do not probe. |

### Suggested Approach

1. Probe the provider's rate-limit endpoint. Choose an endpoint that does not consume
   quota. Cache one tuple per resource: `(remaining, reset_epoch, fetched_at)`.
   Use a short TTL, about 30 seconds.
2. Admit above the reserve without a bucket token. This step removes the fixed pace
   for ordinary traffic.
3. At or below the reserve, wait for the reported reset plus a small margin. Then
   drop the cached tuple so the next caller sees the new window.
4. Validate the reset before a sleep or a format. Require a non-negative integer,
   a value in the future, and a value no more than about one quota window away.
   If a value fails a rule, warn one time for that value and use the bucket. A
   wrong unit must not raise out of the throttle.
5. Keep one tuple from one probe. Do not store `remaining` and `reset` in separate
   caches. A refresh of one member must not pair a stale member with a fresh one.
6. Obey the caller contract. Pass the operation deadline and the shutdown event to
   the probe. Cap the probe timeout by the remaining budget. Re-check the deadline
   after a healthy probe and before the return.
7. Single-flight the probe behind a process lock. Write the tuple one time. Release
   the lock on every path, including probe failure, timeout, and shutdown.
8. Keep the token bucket as the fallback for an unknown or unusable budget. Keep
   the node-local scope, file lock, file mode, and cancellation behaviour.
9. Log the resolved runtime root one time per process. Use a cached function or an
   equivalent guard. Do not write the same debug line on every acquire call.
10. Test each branch with a stubbed probe. Give every test a private runtime root.
    Assert call counts and state, and count log records instead of matching text.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | --------------- |
| Lower the fixed rate | Set the refill rate to 0.2 calls per second to stay below the quota. | Each call waited about 5 seconds. The throttle wrote 59 identical root lines in one run. The provider reported no rate-limit error. | A low fixed rate is a workaround for a budget that the client does not read. |
| Separate caches | Cached `remaining` and `reset` in two entries with separate refresh paths. | A reset-only refresh paired a stale `remaining` with a fresh `reset`. | Store one tuple from one probe. |
| Invalidate on bad payload | Dropped the cache when a reset was in the past or beyond the limit. | A persistent bad payload caused one probe and one warning per call. The TTL no longer limited the probe rate. | Keep the payload until its TTL ends and warn one time for each value. |
| Sleep to any reset | Slept until any reported reset epoch. | A wrong-unit epoch produced a 1000-day sleep. A millisecond epoch raised `ValueError` during datetime formatting. | Bound the wait to one window and guard the format call. |
| Probe outside the deadline | Read the budget before the operation deadline was applied. | A healthy probe returned about 9.5 seconds after the deadline. | Pass the deadline and shutdown to the probe, and re-check both after it. |

## Results & Parameters

### Configuration

```yaml
quota:
  reserve: 100                 # wait at or below this remaining count
  probe_ttl_seconds: 30        # reuse one probe result for this time
  reset_margin_seconds: 5      # wait past the reset before the next call
  max_wait_seconds: 3900       # about 65 minutes; a farther reset uses the bucket
  probe_timeout_seconds: 10    # cap; also capped by the operation deadline
```

### Expected Output

- A caller above the reserve returns without a wait or a bucket token.
- A caller at or below the reserve waits until the reported reset plus the margin.
- A caller with an unusable budget uses the token bucket and logs one warning.
- One root debug line per process, not one per acquire call.
- No exception from a wrong-unit or out-of-range reset value.

## Verified On

| Project | Context | Details |
| ------- | -------- | ------- |
| Private automation project | Shared client with several processes on one host; five independent review rounds | 242 tests in the client package, 661 caller tests, lint and type checks clean. See [notes](external-quota-budget-wait.notes.md). |

## References

- [github-shared-token-lockout-rate-limit-diagnosis](github-shared-token-lockout-rate-limit-diagnosis.md)
- [github-api-secondary-rate-limit-backoff](github-api-secondary-rate-limit-backoff.md)
- [external-request-boundary-invariants](external-request-boundary-invariants.md)
- [testing-deterministic-clock-vs-thread-sleep-classification](testing-deterministic-clock-vs-thread-sleep-classification.md)