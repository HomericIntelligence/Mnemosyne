---
name: derived-default-map-canonical-keys
license: BSD-3-Clause
description: "Derive default counter or state maps from the canonical key provider. Use when: (1) routing or retry keys are duplicated in a dataclass default, (2) adding a key breaks a stale literal expectation, or (3) a test should prove derivation rather than compare two copies of the same list."
category: architecture
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [single-source-of-truth, default-factory, counters, routing, testing, dry]
---

# Derive Default Maps from Canonical Keys

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-07 |
| Objective | Prevent a default state map from drifting from the routing or policy keys it represents. |
| Outcome | Generate each fresh default through the canonical key provider and test the dependency seam with a sentinel key. |

## When to Use

- A dataclass or model initializes one counter per route, budget, phase, or policy key.
- The authoritative key set already exists in a registry or helper.
- Adding or renaming a key requires edits in both production code and a literal test list.
- A test compares a derived map with the same helper used to build it and therefore cannot prove the dependency.

## Verified Workflow

### Quick Reference

```python
from dataclasses import dataclass, field


def canonical_keys() -> tuple[str, ...]:
    return ("plan", "review", "repair")


def new_counter_map() -> dict[str, int]:
    return {key: 0 for key in canonical_keys()}


@dataclass
class WorkItem:
    attempts: dict[str, int] = field(default_factory=new_counter_map)
```

1. Identify the actual authority for membership. Prefer a pure key-provider function over importing a mutable registry object.
2. Build the default with a factory so every instance receives an independent dictionary.
3. Keep initialization semantics separate from routing semantics: derive membership, then initialize each value to the domain default.
4. Patch the provider at the namespace where the factory resolves it and inject a sentinel key.
5. Assert the new instance contains the sentinel with the initial value. Also assert two instances do not share mutations.
6. Remove literal key lists and redundant same-source assertions.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Maintain a second literal list | Copied routing keys into the default map | The copies diverged after a routing change | Derive membership from the canonical provider |
| Compare output with the same provider | Asserted `set(item.attempts) == set(canonical_keys())` | A hard-coded implementation could still pass while both expectations changed together | Inject a sentinel through the provider seam |
| Use one module-level dictionary | Reused the same mutable map for every item | One item's counters contaminated another | Use a default factory that returns a new map |

## Results & Parameters

```python
def test_default_map_is_derived(monkeypatch):
    monkeypatch.setattr(module_under_test, "canonical_keys", lambda: ("sentinel",))
    assert module_under_test.WorkItem().attempts == {"sentinel": 0}


def test_default_map_is_not_shared():
    first = WorkItem()
    second = WorkItem()
    first.attempts["plan"] += 1
    assert second.attempts["plan"] == 0
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Queue-based automation pipeline | Routing-budget state model | Deriving the attempt map from the routing keys removed duplicated membership and passed focused and CI tests. |
