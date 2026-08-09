---
name: architecture-pipeline-stage-order-is-semantic
description: "Use when: (1) a pipeline has both an enum and a route table that imply stage order, (2) queue initialization, scope trimming, or drain order copy the sequence independently, (3) route tests or architecture docs hand-copy every route row, (4) adding or reordering a route should update all order-sensitive consumers automatically."
category: architecture
date: 2026-08-05
version: "2.0.0"
user-invocable: false
verification: unverified
history: architecture-pipeline-stage-order-is-semantic.history
tags:
  - pipeline-order
  - routing-table
  - queue-order
  - scope-routing
  - drain-order
  - single-source-of-truth
  - generated-tests
---

# Pipeline Stage Order Must Have One Executable Authority

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Make one declarative routing table authoritative for pipeline order, success/failure targets, budgets, scoped routing, queue initialization, and downstream-first draining. |
| **Outcome** | Proposed architecture: derive every order-sensitive consumer and structural test from the routing table instead of synchronizing enum order, explicit tuples, test cases, and documentation rows. No implementation was executed in this session. |
| **Verification** | **unverified** — design and acceptance commands were prepared, but no code, tests, type checking, or CI ran. |
| **History** | [changelog](./architecture-pipeline-stage-order-is-semantic.history) |

## When to Use

- A stage enum defines valid identifiers while a route table defines how those stages connect.
- `PIPELINE_ORDER`, downstream drain order, queue construction, or scoped routing repeats the same sequence.
- Adding a stage requires synchronized edits to runtime code, tests, and a normative documentation table.
- Route validation uses a hand-authored expected-row table that can drift with the production table.
- A reorder should automatically affect every consumer that depends on order, while still failing structural invariants if the graph becomes invalid.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the implementation passes local tests and CI.

The repository validator currently requires a literal `## Verified Workflow` section. The proposed, unverified steps therefore appear under that compatibility heading below.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms it.

### Quick Reference

```python
class StageName(StrEnum):
    """Valid identifiers; declaration order is not execution order."""


ROUTES: dict[StageName, Route] = {
    # Insertion order is the executable pipeline order.
}

PIPELINE_ORDER: tuple[StageName, ...] = tuple(ROUTES)
_DRAIN_ORDER: tuple[StageName, ...] = tuple(reversed(PIPELINE_ORDER))

self.queues = {
    stage: StageQueue(work_window)
    for stage in PIPELINE_ORDER
}
```

```python
def test_routes_drive_all_derived_orders() -> None:
    assert set(ROUTES) == set(StageName)
    assert PIPELINE_ORDER == tuple(ROUTES)
    assert _DRAIN_ORDER == tuple(reversed(PIPELINE_ORDER))


@pytest.mark.parametrize(("stage", "route"), ROUTES.items())
def test_route_entries_are_closed(stage: StageName, route: Route) -> None:
    assert route.next in ROUTES
    assert set(route.fail_routes.values()) <= set(ROUTES)
    assert all(name and limit > 0 for name, limit in route.budgets.items())
```

### Detailed Steps

1. **Separate identifier validity from execution order.** Keep the enum as the closed vocabulary of legal stages. State explicitly that enum declaration order is not the execution contract.
2. **Choose the routing table as the executable authority.** Define the order only after the table exists: `PIPELINE_ORDER = tuple(ROUTES)`. Modern Python dictionaries preserve insertion order, so table order and route definitions live in one location.
3. **Derive every order-sensitive runtime consumer.** Build coordinator queues from `PIPELINE_ORDER`, reverse it for downstream-first draining, and make scope contiguity, scoped entry, and route trimming iterate over the same derived order.
4. **Generate structural tests from production data.** Parameterize route closure, failure-target closure, positive budgets, and terminal-sink checks from `ROUTES.items()` instead of copying every row into tests.
5. **Generate all contiguous scopes.** Enumerate every non-empty slice of the non-terminal derived order. For each scope, assert retained key order and that every success/failure target stays within the scope or terminates at the sink.
6. **Keep targeted semantic tests.** Generated structural tests complement, rather than replace, focused cases for loopbacks, terminal behavior, defensive copies, and budget provenance.
7. **Remove normative documentation mirrors.** Documentation should explain the route schema and name `ROUTES` as authority. Do not reproduce every executable row or budget as a second normative table.
8. **Run self-falsifying searches and tests.** Search for independent order tuples and hand-copied route rows, then run routing, property, coordinator, and type-checking suites.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Derive order from enum declaration | Used `PIPELINE_ORDER = tuple(StageName)` and treated member order as semantic | The route table still had to be maintained separately, so adding or reordering a route required two executable edits | Let the enum define valid names and the route table define execution order |
| Keep a hand-written `PIPELINE_ORDER` tuple | Repeated every stage beside the route table | It creates a second authority that can silently drift even when both values type-check | Derive the tuple with `tuple(ROUTES)` |
| Derive drain order independently | Repeated a downstream-first tuple near shutdown code | A route reorder can update forward routing while shutdown still drains in stale order | Define drain order as `reversed(PIPELINE_ORDER)` |
| Hand-copy every route into tests | Maintained a complete expected route table in the test suite | The test and implementation can require synchronized edits, weakening the test as an independent structural guard | Generate closure and budget cases from `ROUTES`; keep only targeted semantic expectations hand-authored |
| Publish a normative architecture route table | Duplicated stage rows, targets, and budgets in prose | Documentation becomes another source that must change with production routing | Document the schema, invariants, and authoritative code location instead |
| Test targets but not retained order | Checked that scoped routes were closed without asserting key sequence | A scope could contain valid targets in the wrong order | Assert `tuple(trimmed)` equals the filtered route-derived order for every contiguous scope |

## Results & Parameters

### Required Invariants

```python
assert tuple(ROUTES) == PIPELINE_ORDER
assert set(ROUTES) == set(StageName)
assert _DRAIN_ORDER == tuple(reversed(PIPELINE_ORDER))
```

For every route:

- the success target exists in `ROUTES`;
- every failure target exists in `ROUTES`;
- every declared budget name is non-empty and its limit is positive;
- the terminal stage routes to itself;
- non-terminal stages retain a catch-all failure route when that is part of the pipeline contract.

For every contiguous non-terminal scope:

- trimmed keys equal the original route order filtered to the selected stages;
- every retained success/failure target is selected or terminal;
- queue and drain consumers need no manual update after a route insertion or reorder.

### Proposed Verification

```bash
uv run pytest tests/unit/automation/pipeline/test_routing.py
uv run pytest tests/unit/automation/pipeline/test_routing_properties.py
uv run pytest tests/unit/automation/pipeline/test_coordinator.py
uv run mypy hephaestus/ scripts/ tests/
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1950 design session | Proposed replacing enum-derived and hand-copied order authorities with `ROUTES` insertion order. No implementation or verification was performed. |
