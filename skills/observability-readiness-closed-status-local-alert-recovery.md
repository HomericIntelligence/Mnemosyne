---
name: observability-readiness-closed-status-local-alert-recovery
license: BSD-3-Clause
description: "Design an existing HTTP health route as a bounded readiness endpoint driven by local alert state. Use when: (1) a health endpoint always returns HTTP 200 even during shutdown or degradation, (2) provider payloads can emit missing or unknown status values, (3) readiness must share circuit-breaker, queue-depth, or stall policy with alerting, (4) readiness must recover automatically without restarting the server, or (5) rollout must separate readiness from liveness semantics."
category: architecture
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - readiness
  - health-endpoint
  - observability
  - http-503
  - closed-status-set
  - degradation
  - shutdown
  - circuit-breaker
  - queue-depth
  - stalled-loop
  - automatic-recovery
  - liveness
  - python
---

# Readiness from Closed Status and Local Alerts

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Convert an existing health route into a readiness contract that returns HTTP 200 only when a coordinator is ready, returns HTTP 503 for every non-ready state, exposes a documented bounded status, and recovers when local degradation clears. |
| **Outcome** | A reviewed implementation and acceptance-test design for a Python coordinator. The design reuses the existing provider seam and pure alert evaluator, bounds malformed provider output, gives shutdown precedence, and documents consumer-first rollout. |
| **Verification** | `unverified` — the workflow and test commands were specified and review findings were incorporated, but the implementation and tests were not executed in the source session. |

## When to Use

- `/health` returns HTTP 200 for every successfully serialized provider snapshot, even when the body says the process is degraded or stopping.
- An orchestrator already has a `health_provider` callback or equivalent snapshot seam and does not need a second endpoint or abstraction.
- Alert emission and readiness must agree on degradation caused by open circuit breakers, queue pressure, stalled ticks, or similar in-memory conditions.
- A provider can return missing, non-string, or future/unknown status values and callers need fail-closed behavior.
- Readiness must recover on the next request when a queue drains, a breaker closes, or a stall counter resets.
- Existing consumers may be using the endpoint as liveness and need an explicit compatibility, rollout, and rollback contract.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the implementation and focused tests pass, then CI confirms the full integration.

### Design invariants

1. Keep the existing route and provider interface when repository-wide search shows they already form the complete consumption surface.
2. Define a closed top-level status vocabulary. In the reference contract, accepted statuses are `ok`, `degraded`, `stopping`, and `error`.
3. Map only `ok` to HTTP 200. Map every other accepted status to HTTP 503.
4. Fail closed on missing, non-string, or unknown status values by replacing the entire response with the bounded `{"status": "error"}` HTTP 503 payload.
5. Preserve the full provider snapshot only when its status is valid. Do not leak arbitrary malformed payloads through the endpoint.
6. Keep provider invocation, snapshot copying, status validation, JSON serialization, and response emission inside one exception boundary. Log details server-side; return only the bounded error response.
7. Compute coordinator degradation through the same pure evaluator and thresholds used for alert emission. Duplicating alert rules in the health provider creates policy drift.
8. Give shutdown precedence over degradation: once shutdown is requested, report `stopping` even if alerts are active.
9. Restrict readiness evaluation to local in-memory state. A readiness request must not depend on network, subprocess, filesystem, or control-plane operations.
10. Recompute the snapshot on every request. Do not latch `degraded`; the endpoint should return to `ok` as soon as the source conditions clear.

### Quick Reference

```python
from collections.abc import Callable, Mapping
from http import HTTPStatus
from typing import Any

HEALTH_STATUS_CODES: dict[str, HTTPStatus] = {
    "ok": HTTPStatus.OK,
    "degraded": HTTPStatus.SERVICE_UNAVAILABLE,
    "stopping": HTTPStatus.SERVICE_UNAVAILABLE,
    "error": HTTPStatus.SERVICE_UNAVAILABLE,
}


def render_health(
    provider: Callable[[], Mapping[str, Any]] | None,
) -> tuple[HTTPStatus, dict[str, Any]]:
    """Return a bounded readiness status and JSON-compatible snapshot."""
    payload = {"status": "ok"} if provider is None else dict(provider())
    status = payload.get("status")
    response_status = (
        HEALTH_STATUS_CODES.get(status) if isinstance(status, str) else None
    )
    if response_status is None:
        return HTTPStatus.SERVICE_UNAVAILABLE, {"status": "error"}
    return response_status, payload
```

```python
def health_snapshot(self) -> dict[str, Any]:
    """Return readiness from coordinator-owned state without external I/O."""
    snapshot = self.observability_snapshot()
    active_alerts = evaluate_alerts(
        snapshot,
        queue_depth_threshold=self.config.alert_queue_depth_threshold,
        stalled_ticks_threshold=self.STALL_TICKS_BEFORE_FORCE,
    )
    if self.shutdown.is_set():
        status = "stopping"
    elif active_alerts:
        status = "degraded"
    else:
        status = "ok"
    snapshot["status"] = status
    return snapshot
```

The HTTP handler must wrap both snippets' effective behavior in its existing exception boundary so provider errors and JSON serialization errors become exactly HTTP 503 with `{"status": "error"}`.

### Detailed Steps

1. **Confirm the seam.** Search for the route and provider (`rg -n "health_provider|/health"`). If only server construction, coordinator wiring, and endpoint tests consume it, extend that seam instead of introducing a new endpoint, response type, or service abstraction.
2. **Write the contract first.** Document the accepted status set, exact HTTP mapping, invalid-provider normalization, retained fields for valid snapshots, and the distinction between live and ready.
3. **Test the observable HTTP boundary.** Use one helper that returns `(status_code, decoded_json)` for both 2xx and `urllib.error.HTTPError` responses. Assert `ok`/200, each recognized non-ready status/503, missing status/503, unknown status/503, non-string status/503, provider exception/503, and degraded-to-ready recovery without restarting the server.
4. **Test coordinator transitions independently.** Cover healthy state, every defined alert condition, shutdown precedence while alerts are active, and recovery after local conditions clear. Do not merely assert the pure evaluator's unit tests; prove coordinator wiring supplies the intended thresholds and snapshot.
5. **Add one closed mapping beside the server.** Validate `payload["status"]` against that mapping after copying the provider result. Preserve valid provider fields, but replace invalid output with the bounded error payload.
6. **Preserve the failure boundary.** Catch provider, mapping-conversion, and serialization exceptions without exposing exception text. Log the traceback through the existing logger and immediately emit the bounded 503 response.
7. **Reuse alert policy.** Call the existing pure alert evaluator with the same configured queue-depth threshold and coordinator stall threshold used by alert emission. Keep imports local if the product has an opt-in observability dependency boundary.
8. **Keep evaluation local and fresh.** Snapshot coordinator-owned queues, inflight work, loop counters, stall counters, shutdown state, and a lock-protected in-memory breaker registry. Never probe the provider or control plane during `/health`.
9. **Document compatibility.** State that consumers assuming `/health` always returns 200 are intentionally incompatible. Readiness consumers require both HTTP 200 and `status: ok`; liveness consumers must use TCP success or treat any completed local HTTP response, including 503, as live.
10. **Roll out consumers first.** Update probes and monitors before deploying the server behavior. Roll back by reverting to the preceding application release; no state, payload-field, or configuration migration is required when valid snapshot fields are preserved.
11. **Verify in layers.** Run focused endpoint and coordinator tests, documentation contract tests, then the repository's lint/type/full-test gates. Do not upgrade this skill's verification level until those commands and CI have actually succeeded.

### Source-session acceptance example

See the [ProjectHephaestus planning notes](./observability-readiness-closed-status-local-alert-recovery.notes.md)
for the exact source files, thresholds, response code, test cases, and proposed verification commands.
Those commands are recorded as acceptance checks, not as observed passing results.

## Verified Workflow

> **Warning:** No end-to-end workflow is verified yet. Follow the proposed workflow above and require local test plus CI evidence before changing `verification` from `unverified`.

### Quick Reference

```text
ready       = HTTP 200 + status "ok"
not ready   = HTTP 503 + status "degraded" | "stopping" | "error"
invalid     = HTTP 503 + exactly {"status": "error"}
live        = local server completed a response; readiness is a separate claim
recovery    = recompute from current in-memory state on every request
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treat body status as sufficient | Keep unconditional HTTP 200 and put degradation only in JSON | Standard readiness probes often use HTTP status; they continue routing work to a non-ready process | Align transport status with readiness state: only the ready state is 2xx |
| Accept any provider status | Pass missing, non-string, or unknown status values through | The endpoint no longer has a bounded contract, and consumers can disagree about readiness | Validate against a closed set and fail closed to a bounded error payload |
| Preserve malformed snapshots | Return the original provider payload with an added error status | Untrusted or inconsistent fields survive a provider contract violation | Preserve full snapshots only for valid statuses; replace invalid output entirely |
| Reimplement alert conditions in health code | Write separate queue, breaker, and stall checks | Thresholds and condition definitions can drift from alert emission | Reuse the pure alert evaluator with the same configured parameters |
| Check degradation before shutdown | Report `degraded` whenever alerts are active, even during shutdown | Operators cannot distinguish intentional termination from runtime degradation | Give terminal lifecycle state explicit precedence |
| Probe dependencies from `/health` | Add network or subprocess checks to decide readiness | The diagnostic endpoint can hang, amplify outages, and become unavailable for reasons outside coordinator state | Use coordinator-owned snapshots and lock-protected in-memory provider state only |
| Test provider dictionaries without HTTP | Assert only the callback output | This misses handler mapping, `HTTPError` behavior, normalization, serialization, and recovery through the real route | Exercise both 200 and 503 through the loopback HTTP boundary |
| Reuse readiness as liveness without migration | Change 200 to 503 without updating consumers | Existing liveness systems may restart a healthy-but-draining process or interpret expected degradation as death | Roll out consumer semantics first and document release rollback |

## Results & Parameters

### Closed response contract

| Provider status | HTTP status | Response body |
|-----------------|-------------|---------------|
| `ok` | 200 | Preserve the valid provider snapshot |
| `degraded` | 503 | Preserve the valid provider snapshot |
| `stopping` | 503 | Preserve the valid provider snapshot |
| `error` | 503 | Preserve the valid provider snapshot |
| Missing, non-string, or unknown | 503 | Replace with exactly `{"status": "error"}` |
| Provider or serialization exception | 503 | Return bounded `{"status": "error"}`; log details only server-side |

### State precedence

```text
if shutdown requested:
    stopping
elif any shared alert condition is active:
    degraded
else:
    ok
```

### Reference degradation inputs

- Open circuit breaker from a lock-protected in-memory registry
- Queue depth above the configured alert threshold
- Stalled tick count at the coordinator's alert/force threshold

The exact inputs are product policy. The durable rule is that readiness consumes the same pure evaluator and thresholds as alert emission, and that clearing every input makes the next request ready automatically.

### Verification status

- Design review: closed-status, malformed-provider, test-coverage, compatibility, rollout, and rollback gaps addressed in the proposed workflow
- Local implementation tests: not run in the source session
- CI: not run in the source session

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Readiness endpoint implementation plan | [Source-level planning notes; implementation and verification pending](./observability-readiness-closed-status-local-alert-recovery.notes.md) |
