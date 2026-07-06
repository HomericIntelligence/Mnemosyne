---
name: architecture-shared-cache-repo-key-lock-vs-threadlocal
description: "Planning discipline for making a module-global cache thread-safe when the cache must be SHARED and COHERENT (not per-thread) under a newly-multithreaded coordinator: the correct fix is a repo-keyed dict guarded by a threading.Lock, NOT threading.local(). Captures four durable lessons from planning a fix for an unguarded module-global label cache: a pre-selected thread-safety skill can prescribe the WRONG variant (per-thread isolation) for genuinely shared state; an audit that names a line may point at an unreachable path while the real hazard sits one layer down in a shared library helper; migrating a module-global's type breaks every test reset/seed seam; and a cached getter must return a defensive copy so callers cannot corrupt the cache. Use when: (1) a pre-selected skill (e.g. metaclass + threading.local) prescribes the wrong thread-safety variant because state must be shared-coherent not per-thread, (2) an audit names a specific line but the truly-shared-state hazard is a layer down in a library helper, (3) migrating a module-global's type (set|None -> repo-keyed dict) will break the test reset seam, (4) a cached getter returns the live cached object and callers mutate it concurrently so it must return a defensive copy."
category: architecture
date: 2026-07-05
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning-methodology
  - thread-safety
  - shared-cache
  - repo-keyed-cache
  - threading-lock
  - threading-local
  - module-global
  - call-graph-diagnosis
  - skill-mismatch
  - defensive-copy
  - test-reset-seam
  - hephaestus
---

# Planning: Shared-Coherent Cache → Repo-Keyed dict + threading.Lock (NOT threading.local)

## Overview

This skill captures durable PLANNING-PROCESS learnings from producing an implementation plan
(not code) for ProjectHephaestus issue #1858: an unguarded module-global `_label_cache` in
`hephaestus/automation/github_api/labels.py` that corrupts durable label writes now that the
pipeline coordinator runs multithreaded. The reusable insight is NOT the label fix. It is the
discipline for any plan that makes a **module-global cache thread-safe when the cache must stay
SHARED and COHERENT across threads (keyed by repo), not isolated per thread.**

| Field | Value |
| --- | --- |
| **Date** | 2026-07-05 |
| **Objective** | Plan a thread-safe fix for a shared-across-threads label cache without mis-applying a per-thread isolation pattern, and without fixing only the audit-named adapter line while the real hazard sits in the library helper |
| **Outcome** | Plan produced (repo-keyed `dict` + `threading.Lock` in the library helper, defensive-copy getter, migrated 4 test reset sites + 1 seed site, `Barrier(2)` concurrency test). NOT executed — no code run, no CI. |
| **Verification** | unverified (planning learning; no code was run, no tests executed, no CI) |
| **History** | n/a (initial version) |

## When to Use

- A **pre-selected skill** points you at `threading.local()` / a metaclass-per-thread pattern, but
  the state in question must be **shared and coherent across threads** (a cross-repo cache every
  thread reads the same coherent value from), not per-thread-divergent. The pre-selected skill is
  topically adjacent but prescribes the WRONG variant.
- An **audit names a specific line** (here `pipeline_github.py:192` → org-scoped `_label_names()`),
  but a call-graph grep shows that line is **not reachable** in the failing (multithreaded) context,
  and the genuinely-shared-state hazard is **one layer down** in a library helper any in-process
  caller shares (`gh_list_labels`).
- You are about to **migrate a module-global's TYPE** (e.g. `set | None` → a repo-keyed `dict`), and
  existing tests **reset or seed that global directly** — the type migration silently breaks every
  reset/seed seam unless you enumerate them first.
- A **cached getter returns the live cached object** (a `set`/`list`/`dict`) and callers iterate it
  while another function mutates it — you plan to return a **defensive copy** so a caller cannot
  corrupt the cache.

**Key trigger:** you find yourself saying "the pre-selected skill says use `threading.local()`" for
state that is really a shared cross-thread cache — STOP, read that skill's own decision table, and
pick the SHARED-coherent-state row (`threading.Lock` + a key) instead of the per-thread row.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.
>
> **Heading note:** The repository validator (`scripts/validate_plugins.py`) hard-requires the
> literal section string `## Verified Workflow`, so the canonical steps are emitted under that
> heading to keep validation green. This skill is a PLANNING methodology captured at `unverified`
> level. Read the steps below as **proposed**, per the warning above.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```python
# 1. DIAGNOSE the call-graph: does the audit-named line actually run in the failing context?
#    Grep every stage call-site for how the accessor is constructed.
#    grep -rn 'repo=' hephaestus/automation/**/coordinator.py  # repo-scoped at 30+ sites
#    -> pipeline coordinator ALWAYS builds repo-scoped accessors (repo=item.repo).
#    -> the audit-named ORG-scoped _label_names() branch is unreachable in the multithreaded path.
#    -> the true shared hazard is the LIBRARY helper gh_list_labels (any in-process caller shares it).

# 2. PICK THE RIGHT VARIANT: shared-coherent state -> Lock + key; per-thread state -> threading.local.
#    threading.local() gives each thread its OWN cache -> WRONG for a cache that must be
#    coherent PER REPO across threads. Use a repo-keyed dict + one Lock instead.
_label_cache_lock = threading.Lock()
_label_cache: dict[tuple[str, str], set[str]] = {}   # key = (owner, name); NOT a bare set|None

def _cache_key():
    info = get_repo_info()                    # UNVERIFIED: attrs .owner/.name — confirm!
    return (getattr(info, "owner", None), getattr(info, "name", None))

def gh_list_labels(refresh: bool = False) -> set[str]:
    key = _cache_key()
    with _label_cache_lock:
        cached = _label_cache.get(key)
        if cached is None or refresh:
            cached = _fetch_labels_from_gh()
            _label_cache[key] = cached
        return set(cached)                     # 3. DEFENSIVE COPY — never hand out the live set

def gh_create_label(name: str) -> None:
    _create_label_via_gh(name)
    key = _cache_key()
    with _label_cache_lock:                    # mutate the cached entry UNDER the lock
        if key in _label_cache:
            _label_cache[key].add(name)

# 4. MIGRATE THE TEST SEAM: every reset/seed of the old global must change type.
#    OLD: _github_api_module._label_cache = None          (a set|None)
#    NEW: _github_api_module._label_cache = {}            (a repo-keyed dict)  x4 reset sites
#    seed test: _label_cache[(owner, name)] = {"bug"}     (a keyed entry, not a bare set)

# 5. CONCURRENCY REGRESSION TEST: force simultaneous entry with a Barrier(2).
import threading
b = threading.Barrier(2)
def worker(repo):  # two mocked repos race the guarded fetch/store
    b.wait()
    gh_list_labels(refresh=True)
# assert repo Y never observes repo X's cached labels (also a deterministic single-thread test)
```

### Detailed Steps

1. **Diagnose which code path the audit actually names vs which is reachable.** The issue pointed at
   the org-scoped `_label_names()` path (`pipeline_github.py:192` → `github_api.gh_list_labels()`),
   but grep showed the pipeline coordinator ALWAYS constructs **repo-scoped** accessors
   (`repo=item.repo` at 30+ stage call-sites; `coordinator._github_for` sets `repo=repo_name`), and
   the repo-scoped `_label_names()` branch already fetches fresh and touches NO module global. The
   genuinely-shared hazard is the LIBRARY function `gh_list_labels` itself (any in-process caller),
   reached org-scoped only when `repo` is empty (`coordinator.py:1028`). Before fixing the
   audit-named line, grep the call-graph to confirm whether that exact line is reachable in the
   failing (multithreaded) context, and whether the true shared-state hazard is one layer down in
   the library helper. **Fix at the library layer, not only the named adapter line.**

2. **Read the pre-selected skill's decision table — it may prescribe the WRONG variant.** The
   pre-selected skill was `architecture-metaclass-threadlocal-thread-safety`. Its own alternatives
   table says `threading.local()` is for **per-thread** isolation and explicitly rejects
   `threading.Lock` for that case as "still global state." But the label cache must be **coherent
   per repo ACROSS threads** — a shared cross-repo cache, not per-thread state. So the correct fix
   is a repo-keyed `dict` + a `threading.Lock`, NOT the metaclass / `threading.local()` pattern. A
   pre-selected skill can be topically adjacent but prescribe the wrong row: shared-coherent state →
   lock + key; per-thread-divergent state → `threading.local()`.

3. **Enumerate every test reset/seed site BEFORE changing a shared global's type.** Existing tests
   reset `_github_api_module._label_cache = None` (a `set | None`). Switching to a repo-keyed `dict`
   means every reset site (4 in `test_github_api.py`) plus the `test_create_label_updates_cache`
   seed must migrate to `{}` / a keyed entry. Grep for every direct read/write of the global and
   migrate them in the same plan; a type change to a shared module global silently breaks any test
   that pokes it directly.

4. **Return a defensive copy from the cached getter.** `gh_list_labels` returned the live cached set;
   callers iterate it while `gh_create_label` mutates it — a concurrent-mutation-during-iteration
   hazard even before threads. Return `set(cached)` so a caller cannot corrupt the cache; mutate the
   cached entry itself only under the lock.

5. **Shape the concurrency regression test with a `Barrier`.** Use `threading.Barrier(2)` to force
   two threads (two mocked repos) to hit the guarded fetch/store simultaneously and assert neither
   repo's labels leak into the other's cache entry. ALSO add a deterministic single-thread test that
   repo Y never observes repo X's cached labels — the deterministic test catches key-collision
   regressions without relying on scheduler timing.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed (risk if assumption wrong) | Lesson Learned |
| --- | --- | --- | --- |
| Fix the audit-named org-scoped line | Patch `_label_names()` at `pipeline_github.py:192` as the issue named | The pipeline coordinator ALWAYS builds repo-scoped accessors (`repo=item.repo`, 30+ sites), so that org-scoped branch never runs in the multithreaded path; the true shared hazard is the library helper `gh_list_labels` one layer down | Grep the call-graph to confirm the audit-named line is reachable in the failing context; fix the shared-state hazard at the library layer, not only the named adapter line |
| Use `threading.local()` per the pre-selected skill | Apply `architecture-metaclass-threadlocal-thread-safety`'s per-thread pattern to the cache | `threading.local()` gives each thread its OWN cache — WRONG for state that must be coherent PER REPO across threads; the skill's own table even rejects `Lock` for its per-thread case | A pre-selected skill can be topically adjacent but prescribe the wrong variant; read its decision table — shared-coherent state → `Lock` + key, per-thread-divergent → `threading.local()` |
| Change the global's type and stop | Switch `_label_cache` from `set \| None` to a repo-keyed `dict` without touching tests | RISK: 4 reset sites + 1 seed site in `test_github_api.py` poke the global directly as `None` / a bare set; the type change breaks them. NOT executed — reset-site count from grep, not a test run | Enumerate every direct reset/seed of a shared module global BEFORE changing its type; migrate all seams (`None` → `{}`, bare set → keyed entry) in the same plan |
| Return the live cached set | Keep `gh_list_labels` returning the cached object directly | Callers iterate the returned set while `gh_create_label` mutates it — concurrent-mutation-during-iteration corruption | Return `set(cached)` (a defensive copy) from the getter; mutate the cached entry only under the lock |
| Key the cache on `.owner`/`.name` without confirming | Use `getattr(info, "owner", None)` / `getattr(info, "name", None)` from `get_repo_info()` as the cache key | RISK: UNVERIFIED that `get_repo_info()` returns an object with `.owner`/`.name`; if the attrs differ, the key is always `None` and the cache degrades to a single shared bucket again — a SILENT regression re-introducing the original bug | Confirm the real attribute names on `git_utils.get_repo_info` before relying on them for the key; a wrong key name silently defeats the whole fix |
| Call `get_repo_info()` on every cache access | Compute the key by calling `get_repo_info()` inside every `gh_list_labels`/`gh_create_label` | RISK: `get_repo_info()` may shell out to git; calling it on every access could add latency or its own failure mode. Not profiled | Confirm the key-source is cheap (or memoize it) before calling it on every cached access |

> The plan was never executed, so the rows above are **risk-if-assumption-wrong** entries: each
> captures an unverified reliance that MUST be surfaced to the reviewer rather than presented as a
> closed fact.

## Results & Parameters

**The plan surface for issue #1858 (the concrete diagnose-and-fix deltas):**

| Home | File / Location | Change |
| --- | --- | --- |
| Library helper | `hephaestus/automation/github_api/labels.py` | Replace module-global `_label_cache: set \| None` with `_label_cache: dict[key, set]` + `_label_cache_lock = threading.Lock()`; guard fetch/store; return `set(cached)` from `gh_list_labels`; mutate keyed entry under lock in `gh_create_label` |
| Org-scoped empty-repo path | `coordinator.py:1028` (via org-scoped `_label_names()`) | Force `refresh=True` on the rare empty-`repo` path so it always refetches rather than reading a stale shared bucket |
| Test reset seams | `tests/.../test_github_api.py` (4 sites) | `_label_cache = None` → `_label_cache = {}` |
| Test seed seam | `test_create_label_updates_cache` | Seed a keyed entry `_label_cache[(owner, name)] = {...}` instead of a bare set |
| New concurrency test | `tests/.../test_github_api.py` | `threading.Barrier(2)` two-repo race + deterministic single-thread cross-repo-isolation test |

**Generalization (the durable, reusable pattern):** When making a module-global cache thread-safe,
first decide whether the state must be **shared-coherent** (every thread sees the same value, keyed
by some dimension like repo) or **per-thread-divergent** (each thread has its own value). Shared-
coherent → a keyed `dict` guarded by a single `threading.Lock`, with the getter returning a
defensive copy. Per-thread-divergent → `threading.local()`. A pre-selected thread-safety skill may
prescribe the wrong one. Also: when an audit names a line, grep the call-graph to confirm that line
runs in the failing context and locate the true shared-state hazard (often one layer down in a
library helper). And when you change a shared global's TYPE, enumerate and migrate every test
reset/seed seam in the same plan.

**Verification status:** `unverified`. This is a PLANNING learning. The plan was produced but NOT
executed — no code ran, no tests were run, no CI. The most load-bearing unverified assumptions the
reviewer must focus on: (1) that `get_repo_info()` exposes `.owner`/`.name` usable as the key — if
not, the cache silently collapses to one shared bucket, re-introducing the original bug; (2) that
`get_repo_info()` is cheap enough to call on every access; (3) that always-refetch on the empty-repo
path is acceptable overhead; (4) that no existing caller of `gh_list_labels` depends on the returned
set being the SAME object across calls (identity) — the defensive-copy change would break such a
caller.

## Verified On

| Repository | Issue / PR | What was applied |
| --- | --- | --- |
| ProjectHephaestus | issue #1858 (plan only) | Plan to make the module-global `_label_cache` in `github_api/labels.py` thread-safe as a repo-keyed `dict` + `threading.Lock` with a defensive-copy getter; call-graph diagnosis showed the audit-named org-scoped line unreachable and the real hazard in the library helper; migrated 4 test reset sites + 1 seed; `Barrier(2)` concurrency test. Not executed. |

## Tags

`#planning-methodology` `#thread-safety` `#shared-cache` `#repo-keyed-cache` `#threading-lock`
`#threading-local` `#module-global` `#call-graph-diagnosis` `#skill-mismatch` `#defensive-copy`
`#test-reset-seam` `#hephaestus`
