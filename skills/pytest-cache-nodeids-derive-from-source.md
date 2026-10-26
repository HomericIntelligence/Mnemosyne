---
name: pytest-cache-nodeids-derive-from-source
description: "Never quote pytest node IDs from pytest cache artifacts or stale inventory files. Derive or verify each node ID from the current tree, or collection aborts with `not found` and nothing runs. Use when you build an exact-node command from discovered references."
category: testing
date: 2026-10-24
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags: [pytest, test-selection, collection, caching, evidence, trust-boundaries]
---

# Derive Pytest Node IDs from the Current Tree, Not Cache Artifacts

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Make an exact-node pytest command pass collection on the first attempt |
| **Outcome** | ✅ Verified: one recovered incident, deterministic failure mode, successful recovery |

## When to Use

Use this skill when:

1. You build a targeted pytest command with explicit node IDs and you find candidate
   names by searching the repository, generated state, or copied CI and JUnit output.
2. A run stops at collection with `ERROR: not found: <node> (no match in any of
   [<Module ...>])` and exit code 4 before the test session starts.
3. You resume work in a checkout whose commit differs from the commit that populated
   the runner state, for example a new worktree or a branch that moved.

## Verified Workflow

### Quick Reference

Generated test-runner state is not a source of current test names. Derive or verify
every node ID from the current tree before you put it on the command line.

```bash
# Verify one name in the current source
grep -n "def test_name" tests/test_module.py

# Or inventory what the current tree collects, with no test side effects
pytest --collect-only -q tests/test_module.py
```

### Suggested Approach

1. Treat `.pytest_cache` as ephemeral. `v/cache/nodeids` and `v/cache/lastfailed`
   describe the tree when the entry was written, which can be an older commit or a
   different checkout of the same repository. Search tools surface these files next
   to real test modules, so a grep hit proves existence of text, not of a test.
2. After a collection failure, never retry the same node list. The failure is
   deterministic and its cause sits outside pytest: re-derive the names first, then
   run again.
3. Prefer file-level IDs over function-level IDs when only the module is confirmed.
   A module path cannot go stale the way a renamed or re-parametrized function can.
4. When you must reproduce a prior list, validate it in one read before you run:

   ```bash
   paste -sd' ' ids.txt | xargs pytest --collect-only -q >/dev/null
   ```

   A usage or collection error means rebuild the list from source. Do not run the
   commands separately from the validation.
5. Record the counts. `no tests ran` and exit code 4 are not failures of the product.
   Do not score them as product regressions, and do not report them as executed
   coverage.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Quoting names from a cache artifact | Node IDs were copied from `.pytest_cache/v/cache/nodeids` of a different commit | Collection aborted with `ERROR: not found` and exit code 4; zero tests ran | A cache artifact documents a past run. It is not an input source |
| Retrying the stale list | The same names ran again unchanged | Identical abort: the input, not pytest, was wrong | Do not re-run without a recorded first cause and a corrected input |

## Results & Parameters

| Item | Role |
| ------- | ------- |
| `pytest --collect-only -q` | Zero-side-effect inventory of the current node IDs |
| `grep -n "def <name>"` | Cheapest proof that one function-level ID exists |
| Exit code 4 | pytest usage or collection error: an input problem, not a test result |
| `.pytest_cache/v/cache/{nodeids,lastfailed}` | Prior-run state; read as history only |

## Integration with Other Skills

- **Complements**: the collection-diagnosis entry for configuration-driven misses
  (`testpaths`, markers, plugins, and addopts). That entry covers missing default
  collection; this entry covers stale identifiers given as explicit input.
- **Applies after**: any cache-artifact discovery when the names reach a command line.

## Failed Approaches

- Never treat a cache-file match as proof that a node ID is current.
- Never retry an identical command after a `not found` abort.
- Do not silence the failure with `-o addopts=''` or `--co -q` alone; verify the names.
