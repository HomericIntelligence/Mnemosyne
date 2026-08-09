# ProjectHephaestus Source-Session Notes

## Verification status

These notes capture an implementation plan, not an executed change. No Hephaestus
source was modified, no criterion-specific tests were run, and no CI result exists.
The corresponding skill therefore remains `unverified`.

## Registry seam

The target is the stdlib-only registry in
`hephaestus/observability/metrics.py`. It supports counters, gauges, and
Prometheus text exposition without a Prometheus dependency.

The existing path obtains a normalized sample key under the family lock, releases
that lock, and then reacquires it in `Counter.inc()` or `Gauge.set()` to mutate the
sample. A cardinality check inserted into the first critical section would race:
multiple writers could all observe spare capacity before any inserts. The planned
change replaces that split with one policy-aware admission-and-mutation critical
section.

Planned public additions:

```python
MetricsRegistry(default_series_cap=100)

registry.counter(
    name,
    help_text="",
    allowed_labels={"label": {"finite", "values"}},
    series_cap=2,
)

registry.gauge(
    name,
    help_text="",
    allowed_labels={"open_dimension": None},
    series_cap=100,
)
```

The reserved overflow name is
`hephaestus_metrics_series_overflow_total`. It is rendered only after a rejected
update, with one `family="<metric-name>"` sample per overflowing family.

## Producer policies

Repository search found two production producer surfaces: the queue pipeline
coordinator and the NATS subscriber.

### Pipeline

Closed domains:

- `stage`: every `StageName` value (`repo`, `planning`, `plan_review`,
  `implementation`, `pr_review`, `merge_wait`, `finished`)
- job `outcome`: `ok`, `failed`, `interrupted`
- breaker `state`: `closed`, `open`, `half_open`
- alert `name`: `circuit_breaker_open`, `queue_depth_exceeds`,
  `pipeline_stalled`

Planned caps:

| Family | Policy | Cap |
|--------|--------|----:|
| `hephaestus_pipeline_queue_depth` | closed `stage` | 7 |
| `hephaestus_pipeline_inflight_per_repo` | open `repo` | 100 |
| `hephaestus_pipeline_jobs_total` | closed `stage` × `outcome` | 21 |
| `hephaestus_circuit_breaker_state` | open `name`, closed `state` | 100 |
| `hephaestus_pipeline_alert_active` | closed alert `name` | 3 |
| Every unlabeled pipeline family | no labels | 1 |

### NATS subscriber

Closed domains:

- error `kind`: `connection`, `terminal`, `handler`, `decode`
- subscriber `state`: every `SubscriberState` value (six at planning time)
- circuit-breaker `state`: every `CircuitBreakerState` value (`closed`, `open`,
  `half_open`)

Each closed family's cap equals its enum/domain size. The messages counter and
last-message timestamp gauge are unlabeled with a cap of one.

## Planned behavior-first tests

A new `tests/unit/observability/test_metric_cardinality.py` would cover:

- rejection of unexpected dimensions and disallowed finite values;
- independent per-family caps and overflow samples;
- 10,000 distinct open-domain values against a cap of 8, retaining 8 and
  reporting 9,992 rejected updates;
- 16 barrier-synchronized writers against a cap of 4, retaining 4 and
  reporting 12 rejected updates.

Producer integration assertions would prove that a pipeline stage named
`adversarial` and a NATS error kind named `adversarial` raise `ValueError`.
Existing registry and HTTP-server tests would guard unchanged low-cardinality
exposition. The observability documentation drift test would include the
registry source so the reserved overflow family cannot become undocumented.

## Proposed verification commands

```bash
uv run pytest tests/unit/observability/test_metric_cardinality.py
uv run pytest \
  tests/unit/observability/test_metrics.py \
  tests/unit/observability/test_server.py \
  tests/unit/automation/pipeline/test_bounded_diagnostics.py \
  tests/unit/nats/test_subscriber.py \
  tests/unit/docs/test_observability_doc.py
uv run ruff check hephaestus/ tests/
uv run mypy hephaestus/ scripts/ tests/
```

Documentation changes were planned for `docs/observability.md`,
`docs/architecture.md`, and `docs/nats.md`: list each producer's allowed values
and cap, document first-new-wins/drop-new behavior, state that admitted tuples
remain updateable, and state that the overflow family is absent until the first
rejection.
