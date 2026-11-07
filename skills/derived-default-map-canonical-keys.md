---
name: derived-default-map-canonical-keys
license: BSD-3-Clause
description: "Derive lookup maps, per-key views, and per-key name maps from one canonical identity record, classify a forwarded-only parameter before you cite or remove it, and decide how to update a frozen design record that the centralization makes stale. Use when: (1) routing or retry keys are duplicated in a dataclass default, (2) several per-key literal maps of names, flags, or capabilities drift apart, (3) a dead kwarg is called by an issue or plan as unread and must be checked by symbol, (4) a test should prove derivation rather than compare two copies of the same list, or (5) an issue says to amend an accepted design record that the new central record makes stale."
category: architecture
date: 2026-08-07
version: "1.3.0"
user-invocable: false
verification: verified-ci
tags: [single-source-of-truth, default-factory, counters, routing, testing, dry, identity-record, divergent-maps, dead-parameter, immutable-adr, supersede-by-new-record, descriptive-record]
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
- A design record is accepted and its policy forbids edits, but its provider list, line references, or symbol claims are stale after a centralization. Another record already supersedes one clause of it.

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
11. Give a moved public name a derived view instead of a second definition. Re-export the map, the enum, and the accessor from the old module as comprehensions or one-line delegations over the canonical records. A consumer or a test that patches the old name must still reach the one derivation.
12. Keep the established key type for the record table and for each derived view. Convert to an enum only inside the record table when callers index by plain strings.
13. Decide the design-record update from the local policy before you write the central record. If accepted records are immutable, do not edit the record body:
    - Create one new record that states the central record implements the cited clause.
    - Set its `Supersedes:` field to the stale claim classes. Example: provider enumeration and source references.
    - State which earlier decisions stay in force. A no-catalog decision stays in force when the central record holds no model names.
    - Annotate only the old record status line. Then update the index row for both records.
    - When the stale claim is one clause of an earlier partial supersession, the `Supersedes:` field of the new record names that clause.
14. Re-locate every cited symbol by symbol name. An issue that cites a source reference and a count of its providers can be stale in both, because the provider set grew after the record was written.
15. If a task requires centralizing a name that a non-Python consumer also holds, for example an install script that probes a binary, use a consistency test instead of a generated step when the shell cannot import the record:
    - The test scans the consumer files for the probe pattern.
    - The test asserts each probed name is a `cli_name` of a record.
    - A later literal that names a record without its compatible binary pair then fails the test.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Maintain a second literal list | Copied routing keys into the default map | The copies diverged after a routing change | Derive membership from the canonical provider |
| Compare output with the same provider | Asserted `set(item.attempts) == set(canonical_keys())` | A hard-coded implementation could still pass while both expectations changed together | Inject a sentinel through the provider seam |
| Use one module-level dictionary | Reused the same mutable map for every item | One item's counters contaminated another | Use a default factory that returns a new map |
| Collapse divergent name maps by choosing one value | Replaced two per-key name maps with one derived map that kept the more common value | The other consumer emits a different value on purpose, so a silent behavior change reaches unrelated output | Model the divergence as two record fields with consumer-named fields, not as one canonical value |
| Judge a parameter dead from keyword-search hits | A plan stated that a boolean parameter was never read, and a keyword search found many hits, most of which were the signature and same-name forwarding | The count did not separate reads from re-declarations, so the verdict needed one more step | Compare each body's `Name` reads with its parameter list; declaration plus same-name forwarding is the removal-safe signature |
| Change a key type while centralizing | Rebuilt the maps with enum keys instead of the existing string keys | Every consumer lookup and every test that indexes the map with a plain string breaks | Keep the established key type and convert only inside the record table |
| Edit the accepted design record to match the new record | The work item said to amend the accepted record, so the plan rewrote its provider list and source references | The repository policy and index say an accepted record is immutable, so a body edit conflicts with the record-keeping contract even when the new values are correct | Read the index rule before you write. Add one new record that supersedes the stated claim classes, annotate only the old status line, and update both index rows |
| Hold every field in one record with one shared value | The records had a per-consumer display name and a per-consumer commit-trailer name that legitimately differ | One shared value silently changes user-visible output for one consumer | Store each value in its own consumer-named field. Prevent the original drift with one field per consumer, not with one value for both |
| Add a generated step so a shell consumer reads the record | The install script cannot import the Python module, so the plan proposed code generation | A generated artifact adds a build step and a staleness window for one string comparison | Use a consistency test that scans the shell surface and asserts every probed name is a record `cli_name` |

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

```python
import re
from pathlib import Path


def probed_binaries(script: Path, pattern: str) -> set[str]:
    """Return every binary name that a shell consumer probes."""
    return set(re.findall(pattern, script.read_text(encoding="utf-8")))


def test_script_probes_resolve_to_record_cli_names() -> None:
    known = {record.cli_name for record in RECORDS.values()}
    probed = probed_binaries(INSTALL_SCRIPT, r"(?:has_cmd|command -v)\s+([A-Za-z0-9_.-]+)")
    assert probed - {"bash", "git", "npm", "uv", "node"} <= known
```

- Non-Python consumers: a consistency test proves that the shell surface names only record `cli_name` values. It also fails a later literal that names a record whose binary differs, for example a versioned record that shares one binary. When an issue asks for a generated step, the plan states why the test is the smaller control.
- Design records: before you edit an accepted record, read the directory index for the immutability rule and the supersession vocabulary. Grep the index for the record number to find an existing partial supersession. Use the next free number taken from the index at write time, not from a plan.
