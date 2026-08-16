---
name: shared-predicate-gate-discovery-parity
license: BSD-3-Clause
description: "Keep discovery and completion gates on one pure eligibility predicate. Use when: (1) one path enumerates actionable records while another counts remaining work, (2) their filters can drift, or (3) a loop declares convergence while discovery still finds work."
category: architecture
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [predicate, discovery, gate, convergence, dry, automation]
---

# Shared Predicate for Gate and Discovery Parity

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-07 |
| Objective | Ensure enumeration and zero-work gates classify the same records identically. |
| Outcome | Put one pure predicate beside the primary discovery model and reuse it in discovery, counting, and completion checks. |

## When to Use

- A discovery function returns actionable items while a separate gate asks whether any remain.
- Both paths repeat conditions for lifecycle state, draft status, health, or eligibility.
- A loop exits with zero work even though a later listing finds candidates.
- Fixing one filter requires a reviewer to remember a sibling implementation.

## Verified Workflow

### Quick Reference

```python
def is_actionable(record: Record) -> bool:
    return (
        not record.is_draft
        and record.lifecycle == "open"
        and any(check.is_failure for check in record.checks)
    )


def discover(records: list[Record]) -> list[Record]:
    return [record for record in records if is_actionable(record)]


def remaining_count(records: list[Record]) -> int:
    return sum(is_actionable(record) for record in records)
```

1. Define the classification vocabulary before extracting code: actionable, ignored, pending, terminal, or other domain states.
2. Put the pure predicate with the module that owns discovery semantics, not in an orchestration caller.
3. Make every gate consume the predicate or the discovery result. Do not re-express the conditions.
4. Pass configuration as explicit immutable arguments if classification varies by policy; avoid mutable module globals.
5. Table-test boundary cases once against the predicate.
6. Add a parity property: for the same snapshot, `remaining_count(records) == len(discover(records))`.
7. Keep data fetching outside the predicate so gate and discovery can use the same immutable snapshot in tests.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Copy the filter | Repeated the conditions in discovery and the completion gate | A later fix changed only one copy, producing false convergence | Share one classification predicate |
| Put the predicate in the gate | Made the primary discovery module import orchestration code | Ownership became inverted and encouraged circular imports | Keep classification beside discovery; let gates depend inward |
| Make classification mutable global policy | Tests changed a module-level list of accepted states | Results depended on import and test order | Pass immutable policy explicitly |
| Test both implementations separately | Added examples for each duplicated filter | The suites could still encode different expectations | Add a direct parity invariant over the same snapshot |

## Results & Parameters

```python
def test_gate_matches_discovery(records):
    assert remaining_count(records) == len(discover(records))
```

The shared predicate answers only classification. Discovery still enumerates work, while the gate still decides whether processing may stop.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Pull-request automation service | Failing-item discovery and completion gate | Reusing one predicate removed a silent disagreement between the count and enumeration paths; the parity regression passed in CI. |
