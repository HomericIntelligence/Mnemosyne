---
name: derived-default-map-canonical-keys
license: BSD-3-Clause
description: "Derive lookup maps, per-key views, and per-key name maps from one canonical identity record, and classify a forwarded-only parameter before you cite or remove it. Use when: (1) routing or retry keys are duplicated in a dataclass default, (2) several per-key literal maps of names, flags, or capabilities drift apart, (3) a dead kwarg is called by an issue or plan as unread and must be checked by symbol, or (4) a test should prove derivation rather than compare two copies of the same list."
category: architecture
date: 2026-08-07
version: "1.2.0"
user-invocable: false
verification: verified-ci
tags: [single-source-of-truth, default-factory, counters, routing, testing, dry, identity-record, divergent-maps, dead-parameter]
---

# Derive Default Maps from Canonical Keys

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-07 |
| Objective | Prevent a default state map from drifting from the routing or policy keys it represents. |
| Outcome | Generate each fresh default through the canonical key provider and test the dependency seam with a sentinel key. Scope extended to per-key name and flag maps that already diverge from one identity record. |

## When to Use

- A dataclass or model initializes one counter per route, budget, phase, or policy key.
- The authoritative key set already exists in a registry or helper.
- Adding or renaming a key requires edits in both production code and a literal test list.
- A test compares a derived map with the same helper used to build it and therefore cannot prove the dependency.
- Two or more literal maps over the same key set disagree. For example, a display-name map and a co-author-name map give different values for one key.
- A function parameter is accepted, forwarded under its own name, and never read in any function body on that chain.
- A work item states that a parameter is dead. Grep every body on the chain by the symbol name before you cite, keep, or remove it.

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

```python
# Per-key name, flag, and capability maps come from one identity record.
@dataclass(frozen=True, slots=True)
class Record:
    display_name: str
    commit_author_name: str
    cli_name: str


RECORDS: dict[str, Record] = {...}

DISPLAY_NAMES = {key: record.display_name for key, record in RECORDS.items()}
AUTHOR_NAMES = {key: record.commit_author_name for key, record in RECORDS.items()}
```

```python
import ast


def forwarded_only_names(module: ast.Module) -> dict[str, set[str]]:
    """Map each function name to the parameter names that its body never reads."""
    unread: dict[str, set[str]] = {}
    for node in ast.walk(module):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = {a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)}
        read = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        unread[node.name] = params - read
    return unread
```

1. Identify the actual authority for membership. Prefer a pure key-provider function over importing a mutable registry object.
2. Build the default with a factory so every instance receives an independent dictionary.
3. Keep initialization semantics separate from routing semantics: derive membership, then initialize each value to the domain default.
4. Patch the provider at the namespace where the factory resolves it and inject a sentinel key.
5. Assert the new instance contains the sentinel with the initial value. Also assert two instances do not share mutations.
6. Remove literal key lists and redundant same-source assertions.
7. Derive each per-key view from the identity record by comprehension. Keep public names and their key type unchanged so existing consumers and tests continue to work.
8. Do not hide a real divergence inside the record. If two maps must hold different values for one key, give the record two separate fields and name each field for its consumer.
9. Classify a parameter as dead only with per-function evidence. Parse each function on the chain and compare its parameter names with the names its body reads. A parameter that the signature declares and no body reads is dead, even when the function forwards it under its own keyword name. A parameter is not proven dead by `grep` hits alone: those hits include the signature and the forwarding keyword. A removal is safe when `inspect.getsource` over every signature reports only the declaration and same-name forwarding. Then remove the argument from each call site, and update the one test that still supplies it by keyword.
10. Leave a parameter that only one intermediate layer forwards and another layer reads. That parameter is a live seam, and a removal changes behavior at the reader.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Maintain a second literal list | Copied routing keys into the default map | The copies diverged after a routing change | Derive membership from the canonical provider |
| Compare output with the same provider | Asserted `set(item.attempts) == set(canonical_keys())` | A hard-coded implementation could still pass while both expectations changed together | Inject a sentinel through the provider seam |
| Use one module-level dictionary | Reused the same mutable map for every item | One item's counters contaminated another | Use a default factory that returns a new map |
| Collapse divergent name maps by choosing one value | Replaced two per-key name maps with one derived map that kept the more common value | The other consumer emits a different value on purpose, so a silent behavior change reaches unrelated output | Model the divergence as two record fields with consumer-named fields, not as one canonical value |
| Judge a parameter dead from keyword-search hits | A plan stated that a boolean parameter was never read, and a keyword search found many hits, most of which were the signature and same-name forwarding | The count did not separate reads from re-declarations, so the verdict needed one more step | Compare each body's `Name` reads with its parameter list; declaration plus same-name forwarding is the removal-safe signature |
| Change a key type while centralizing | Rebuilt the maps with enum keys instead of the existing string keys | Every consumer lookup and every test that indexes the map with a plain string breaks | Keep the established key type and convert only inside the record table |

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

```python
def test_per_key_view_is_derived_from_record(monkeypatch):
    monkeypatch.setitem(module_under_test.RECORDS, "sentinel", Record("S", "S", "s"))
    assert module_under_test.DISPLAY_NAMES["sentinel"] == "S"
```

```python
def test_forwarded_only_parameter_is_removal_safe():
    module = ast.parse(inspect.getsource(module_under_test))
    unread = forwarded_only_names(module)
    assert "use_default" in unread["_model_args"]
    assert "use_default" in unread["_model_config"]
    assert "timeout" not in unread["_run_with_fallback"]
```

- Dead parameters: run the body-read check on every function in the chain. Declaration plus same-name forwarding is dead. A parameter that a downstream body reads is a live seam. Re-export the canonical name from its old module after a move, so a patch on either name still reaches one derivation.