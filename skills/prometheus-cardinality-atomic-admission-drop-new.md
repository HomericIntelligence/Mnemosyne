---
name: prometheus-cardinality-atomic-admission-drop-new
license: BSD-3-Clause
description: "Bound retained Prometheus label series in a small in-process registry. Use when: (1) metric families retain one sample per label tuple, (2) dynamic label values can grow without bound, (3) concurrent writers must not exceed a per-family cap, or (4) dropped new-series updates must be observable without evicting admitted data."
category: architecture
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - prometheus
  - metrics
  - cardinality
  - label-schema
  - concurrency
  - observability
  - bounded-memory
---

# Bound Prometheus Cardinality with Atomic Drop-New Admission

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Bound every metric family's retained label tuples, enforce declared label dimensions and finite value domains, and report rejected new-series updates without changing ordinary low-cardinality exposition. |
| **Outcome** | Architecture and behavior-first implementation plan: add a bounded registry default, explicit per-family policies, atomic admission and mutation, deterministic drop-new behavior, and a registry-owned overflow counter. No implementation was executed in the source session. |
| **Verification** | **unverified** — repository call sites and proposed tests were identified, but implementation, local tests, and CI were not run. |

## When to Use

- A hand-rolled or stdlib-only Prometheus text registry stores one sample for every distinct label tuple.
- A label such as `tenant`, `repository`, `breaker`, `route`, or `peer` can receive attacker-controlled or continuously changing values.
- Existing callers infer a label schema on first write, and compatibility must be preserved while adding a safe default cap.
- Multiple threads can introduce new tuples concurrently, so a check outside the mutation lock could overshoot the cap.
- Operators must know that samples were discarded, but producers must not fail and already admitted low-cardinality series must not disappear.
- Closed producer domains, such as enum states or stage/outcome combinations, should fail immediately on misspelled values.

Do not use this pattern to disguise labels that should not exist. Request IDs, timestamps, error messages, and other effectively unique values belong in logs or traces, not metric labels.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the implementation passes local tests and CI.

The repository validator currently requires a literal `## Verified Workflow` section. The proposed, unverified steps therefore appear under that compatibility heading below.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms it.

### Quick Reference

```python
from collections.abc import Collection, Mapping

DEFAULT_SERIES_CAP = 100
OVERFLOW_METRIC = "service_metrics_series_overflow_total"


class MetricFamily:
    def __init__(
        self,
        name: str,
        *,
        allowed_labels: Mapping[str, Collection[object] | None] | None = None,
        series_cap: int = DEFAULT_SERIES_CAP,
    ) -> None:
        self.series_cap = validate_positive_cap(series_cap)
        self.allowed_labels = normalise_policy(allowed_labels)
        self.label_names = (
            tuple(name for name, _ in self.allowed_labels)
            if self.allowed_labels is not None
            else None  # preserve first-write inference for legacy callers
        )
        self.lock = threading.Lock()
        self.samples = {(): 0.0}
        self.overflow_total = 0

    def write(self, value: float, labels: Mapping[str, object] | None) -> None:
        key = normalise_labels(labels)
        with self.lock:
            self.validate_schema_and_values(key)
            if key and () in self.samples:
                del self.samples[()]
            if key not in self.samples and len(self.samples) >= self.series_cap:
                self.overflow_total += 1
                return
            self.samples[key] = mutate(self.samples.get(key, 0.0), value)
```

Declare producer policy at registration:

```python
# A closed Cartesian product gets its exact maximum.
jobs = registry.counter(
    "pipeline_jobs_total",
    allowed_labels={
        "stage": {"repo", "planning", "implementation", "finished"},
        "outcome": {"ok", "failed", "interrupted"},
    },
    series_cap=4 * 3,
)

# A dynamic value domain is explicitly open but still bounded.
inflight = registry.gauge(
    "pipeline_inflight_per_repo",
    allowed_labels={"repo": None},
    series_cap=100,
)

# An unlabeled family can retain exactly one sample.
loops = registry.gauge(
    "pipeline_loops_total",
    allowed_labels={},
    series_cap=1,
)
```

### Detailed Steps

1. **Inventory registrations and mutations before choosing policy.** Search metric constructors and every `inc`, `set`, `observe`, or equivalent call. Classify each family as unlabeled, closed finite, mixed closed/open, or legacy inferred. Do not assume an exposed `/metrics` endpoint proves production mutation paths exist.
2. **Add bounds to the existing abstraction.** Extend the current registry with a positive `default_series_cap` and optional per-family `series_cap`. Do not introduce a second registry or a full Prometheus dependency merely to solve retention in a deliberately small implementation.
3. **Represent label policy explicitly.** Use a mapping from permitted label name to either a finite value collection or `None` for an intentionally open value domain. Normalize label names and policy values into the same representation used by sample keys. `allowed_labels={}` means no labels; `allowed_labels=None` preserves first-write schema inference for legacy callers.
4. **Validate policy at registration.** Reject invalid label names, malformed domains, non-positive caps, and the registry-owned overflow family name before adding state. Normalize a finite domain once instead of rebuilding it for every write. Define and test how object values become exposition strings so allowed-value comparisons and rendered labels cannot disagree.
5. **Keep registration idempotent without accepting conflicts.** Returning an existing family by name is safe only when its metric type and any supplied HELP text or policy overrides agree. A lookup that omits overrides may return the existing family; an explicitly conflicting type, HELP text, label policy, or cap must raise `ValueError`.
6. **Use one family-lock critical section.** Label normalization can produce a canonical key before locking, but schema validation, finite-value validation, removal of the bootstrap unlabeled sample, capacity admission, and sample mutation must occur under one family lock. Splitting admission from mutation lets concurrent writers all observe spare capacity and exceed the cap.
7. **Validate before checking capacity.** Unexpected dimensions and disallowed finite values are programming/configuration errors and must raise even when the family is already full. A full cap suppresses only a new *valid* tuple; it must not turn invalid labels into silent drops.
8. **Admit existing keys unconditionally.** If the normalized tuple is already present, counters continue to increment and gauges continue to set at capacity. The cap governs retained tuple count, not update volume.
9. **Drop only a valid new tuple beyond the cap.** Increment that family's private overflow count and return without eviction or producer failure. This is first-new-wins retention: admitted tuples remain stable; later tuples are discarded. Concurrent scheduling may decide which valid tuples arrive first, but the family never retains more than its cap.
10. **Render overflow through one reserved family.** Snapshot samples and each family's overflow count under its family lock. Add the overflow family's HELP, TYPE, and `family="..."` samples only when at least one rejection has occurred. Sort family names and use the normal label escaping and numeric formatting helpers.
11. **Declare policy at every known producer.** Use exact Cartesian-product caps for closed enums, a cap of one for unlabeled families, and a reviewed finite cap for open domains. Mixed policies may close one dimension while explicitly opening another. Keep the bounded default for old or third-party callers that omit policy.
12. **Test behavior, not private storage.** Exercise public writes and rendered text for schema errors, value errors, independent family caps, overflow counts, continued updates to admitted keys, adversarial churn, and synchronized concurrent writers. Also retain exact-output tests proving that low-cardinality exposition is byte-for-byte unchanged before any rejection.
13. **Document the runtime declaration.** Catalog each family, type, permitted dimensions/values, and cap. State that no series is evicted, rejected updates are counted, and the overflow family is absent before the first rejection. Add a source-to-catalog drift guard for the registry-owned overflow name.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Check capacity before taking the mutation lock | Keep schema/key calculation separate from counter or gauge mutation | Concurrent new-series writers can all see capacity and then insert, overshooting the family cap | Admission and mutation are one atomic operation under the family lock |
| Evict an old series when the family is full | Use LRU or FIFO replacement to make room for a new label tuple | Active low-cardinality data disappears, exposition churns, and eviction adds ordering state | Keep admitted tuples stable and drop only new tuples |
| Raise when the cap is full | Treat a new tuple beyond capacity as a producer exception | Observability can terminate or perturb the production path it is meant to describe | Fail fast for invalid policy/labels, but drop-and-count valid capacity overflow |
| Drop overflow silently | Return without recording a rejected update | Memory stays bounded but operators cannot distinguish normal low volume from lost telemetry | Increment a reserved overflow counter once per discarded update |
| Bound only newly audited producers | Add explicit caps to known call sites but leave legacy inference unlimited | An overlooked or future caller can still grow process memory without bound | Apply a positive registry default even when callers omit overrides |
| Restrict dimensions but not values | Freeze the label-name schema while accepting every value | A single permitted dimension such as `tenant` can still create unbounded series | Declare finite domains where they are closed and explicitly mark open domains |
| Replace the registry | Add a Prometheus client dependency or parallel abstraction | It expands dependencies and splits behavior without addressing producer policy ownership | Extend the existing registry when its limited counter/gauge surface is intentional |

No implementation was attempted in the source session. These are design alternatives rejected during planning, not experimentally observed failures.

## Results & Parameters

### Policy Parameters

| Parameter | Recommended starting point | Contract |
|-----------|----------------------------|----------|
| Registry default cap | `100` series per family | Positive and applied when no family override is supplied |
| Unlabeled family | `allowed_labels={}`, `series_cap=1` | Reject every labeled update |
| Closed finite family | Finite sets with cap equal to the Cartesian-product size | Reject unknown dimensions and values immediately |
| Open-domain family | Use `None` for the open dimension and a reviewed finite cap | Admit the first tuples up to the cap; never evict them |
| Overflow count | Increment once per discarded update | Repeated attempts for a non-admitted tuple each count; updates to admitted tuples do not |
| Overflow exposition | One `family`-labeled sample per overflowing registered family | Omit the entire overflow family until the first rejection |

The cap is per metric family, not global. Two families with caps of one and two may retain one and two tuples independently. The registry-owned overflow metric's value domain is the set of registered family names, which should itself be source-owned rather than derived from request data.

### Acceptance Invariants

```python
registry = MetricsRegistry(default_series_cap=2)
counter = registry.counter(
    "requests_total",
    allowed_labels={"tenant": None},
    series_cap=1,
)

counter.inc(labels={"tenant": "admitted"})
counter.inc(labels={"tenant": "discarded"})
counter.inc(labels={"tenant": "admitted"})

rendered = registry.render_prometheus()
assert 'requests_total{tenant="admitted"} 2' in rendered
assert 'requests_total{tenant="discarded"}' not in rendered
assert 'metrics_series_overflow_total{family="requests_total"} 1' in rendered
```

Required concurrency property:

```text
after N synchronized writers each introduce a distinct valid tuple:
retained_series == min(N, family_cap)
overflow_total == max(0, N - family_cap)
```

Required compatibility property:

```text
when no update is rejected:
rendered output before cardinality controls == rendered output after controls
and the overflow HELP/TYPE/sample lines are absent
```

### Proposed Verification

```bash
<package-manager> run pytest <cardinality-test-path>
<package-manager> run pytest \
  <existing-registry-test-path> \
  <metrics-endpoint-test-path> \
  <producer-integration-test-path> \
  <metrics-catalog-drift-test-path>
<package-manager> run <linter> <source-path> <test-path>
<package-manager> run <type-checker> <source-path> <test-path>
```

The behavior-first suite should include a large churn case (for example, 10,000 unique values against a cap of 8) and a barrier-synchronized concurrency case (for example, 16 writers against a cap of 4). Assert public exposition counts and overflow totals, not private dictionaries.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Bounded metric-cardinality implementation plan | [Source-session notes](./prometheus-cardinality-atomic-admission-drop-new.notes.md); implementation and verification were not executed. |
