# ProjectHephaestus readiness planning notes

## Session scope

The source session produced an implementation-ready plan for converting the existing
ProjectHephaestus `/health` route from an always-HTTP-200 diagnostic snapshot into a coordinator
readiness endpoint. No source implementation or acceptance command was executed in that session.

The repository search identified only these consumers of the existing `health_provider` seam:

- `hephaestus/observability/server.py`
- `hephaestus/automation/pipeline/coordinator.py`
- endpoint tests

The plan therefore retained both the route and provider interface.

## Exact contract

```python
_HEALTH_STATUS_CODES: dict[str, HTTPStatus] = {
    "ok": HTTPStatus.OK,
    "degraded": HTTPStatus.SERVICE_UNAVAILABLE,
    "stopping": HTTPStatus.SERVICE_UNAVAILABLE,
    "error": HTTPStatus.SERVICE_UNAVAILABLE,
}
```

- Preserve valid provider snapshots.
- Replace missing, non-string, or unknown statuses with exactly `{"status": "error"}` and HTTP 503.
- Map provider and JSON serialization failures to the same bounded response while logging details.
- Give `shutdown.is_set()` precedence over active degradation alerts.
- Recompute readiness on every request so it returns to `ok` after the condition clears.

## Coordinator parameters

The coordinator snapshot should be passed to `hephaestus.observability.alerts.evaluate_alerts()`
with:

- `queue_depth_threshold=PipelineConfig.alert_queue_depth_threshold`
- `stalled_ticks_threshold=_STALL_TICKS_BEFORE_FORCE`

The evaluator's defined degradation sources are:

- an open circuit breaker;
- queue depth above the configured threshold;
- stalled ticks at the coordinator threshold.

The import belongs inside `_health_snapshot()` to preserve ProjectHephaestus's opt-in
observability import boundary. Circuit-breaker state comes from the existing in-memory snapshot
provider, which copies the registry under a lock. No external I/O is required.

## Planned file changes

- `hephaestus/observability/server.py`: add the closed status-to-HTTP mapping and bounded invalid
  provider behavior.
- `hephaestus/automation/pipeline/coordinator_runtime.py`: derive readiness through
  `evaluate_alerts()` with shutdown precedence.
- `tests/unit/observability/test_server.py`: cover every accepted status, missing/unknown/non-string
  status, provider failure, and degraded-to-ready recovery through loopback HTTP.
- `tests/unit/automation/pipeline/test_coordinator.py`: cover healthy state, shutdown precedence,
  every alert-derived degradation source, and recovery.
- `docs/observability.md`: document readiness semantics, status vocabulary, compatibility,
  consumer-first rollout, release rollback, and the readiness SLO.
- `docs/architecture.md`: document the full snapshot, failure normalization, shared alert policy,
  in-memory boundary, and liveness/readiness distinction.

## Proposed acceptance commands

```bash
uv run pytest tests/unit/observability/test_server.py::test_health_status_controls_readiness_http_status -v
uv run pytest tests/unit/automation/pipeline/test_coordinator.py::TestCoordinatorHealth -v
uv run pytest \
  tests/unit/observability/test_server.py \
  tests/unit/docs/test_observability_doc.py \
  tests/unit/docs/test_automation_loop_architecture.py -v
uv run pytest \
  tests/unit/observability/test_server.py \
  tests/unit/automation/pipeline/test_coordinator.py::TestCoordinatorHealth -v
```

## Review corrections incorporated

- Defined the closed `ok`/`degraded`/`stopping`/`error` vocabulary instead of leaving provider
  status values open-ended.
- Added separately named tests for missing, unknown, and non-string status values.
- Replaced malformed provider output entirely rather than preserving inconsistent fields.
- Documented the HTTP status change as intentionally incompatible for consumers that assumed
  `/health` always returned HTTP 200.
- Required consumer-first rollout and release rollback, with no data or configuration migration.
