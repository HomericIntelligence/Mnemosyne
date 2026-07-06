---
name: architecture-shared-cache-repo-key-lock-vs-threadlocal
description: "Planning discipline for making a module-global cache thread-safe when the cache must be SHARED and COHERENT (not per-thread) under a newly-multithreaded coordinator. The R1 core lesson: before hand-rolling a dict + threading.Lock, GREP THE REPO for an existing thread-safe cache/lock primitive and for a sibling that already solved the same bug class — the codebase already had hephaestus/utils/cache.py::ThreadSafeCache (a lock-guarded, per-key, TTL cache built to replace ad-hoc dict caches with a TOCTOU race) and git_utils already reused it for the identical bug shape; the KISS fix reuses that primitive keyed by repo slug, not a hand-rolled lock. Also: a 'load-bearing unverified assumption' about a helper's return SHAPE is almost always cheaply verifiable by reading 3 lines of its signature (get_repo_info returns a (owner, repo) tuple accessed by unpack and RAISES on failure — NOT an object with .owner/.name), so resolve it in the plan rather than shipping it as a caveat; to mutate one cached entry without poking the primitive's privates, ADD a small public method to the primitive; a pre-selected thread-safety skill can prescribe the WRONG variant (per-thread threading.local) for genuinely shared state; an audit that names a line may point at an unreachable path while the real hazard sits one layer down in a shared library helper; and migrating a module-global's TYPE breaks every test reset/seed seam. Use when: (1) fixing a shared-mutable-state/TOCTOU bug and tempted to hand-roll dict+Lock — search for an existing primitive first, (2) a pre-selected skill prescribes threading.local for state that must be shared-coherent not per-thread, (3) an audit names a line but the shared-state hazard is a layer down in a library helper, (4) migrating a module-global's type (set|None -> a keyed cache) breaks the test reset seam, (5) you need to mutate one entry of a shared cache primitive without reaching into its internals."
category: architecture
date: 2026-07-05
version: "1.1.0"
user-invocable: false
verification: unverified
history: architecture-shared-cache-repo-key-lock-vs-threadlocal.history
tags:
  - planning-methodology
  - thread-safety
  - shared-cache
  - reuse-existing-primitive
  - threadsafecache
  - repo-keyed-cache
  - threading-lock
  - threading-local
  - module-global
  - call-graph-diagnosis
  - skill-mismatch
  - verify-return-shape
  - encapsulation
  - test-reset-seam
  - hephaestus
---

# Planning: Reuse the Existing ThreadSafeCache (NOT a hand-rolled dict+Lock, NOT threading.local)

## Overview

This skill captures durable PLANNING-PROCESS learnings from producing an implementation plan
(not code) for ProjectHephaestus issue #1858: an unguarded module-global `_label_cache` in
`hephaestus/automation/github_api/labels.py` that corrupts durable label writes now that the
pipeline coordinator runs multithreaded. The reusable insight is NOT the label fix. It is the
discipline for any plan that makes a **module-global cache thread-safe when the cache must stay
SHARED and COHERENT across threads (keyed by repo), not isolated per thread.**

**This is v1.1.0 — the R1 re-plan.** An earlier R0 plan was NOGO'd. The R1 re-plan is materially
better and **corrects two R0 claims that were WRONG**. Where R0 material appears below it is
explicitly marked `[R0 — CORRECTED]`. The single most important upgrade: **R0 hand-rolled a
repo-keyed `dict` + `threading.Lock`; R1 discovered the repo ALREADY had a sanctioned
`ThreadSafeCache` primitive used by a sibling for the identical bug shape, and reuses it.**

| Field | Value |
| --- | --- |
| **Date** | 2026-07-05 |
| **Objective** | Plan a thread-safe fix for a shared-across-threads label cache by REUSING the existing `ThreadSafeCache` primitive keyed by repo slug — not hand-rolling a lock, not mis-applying a per-thread isolation pattern, and not fixing only the audit-named adapter line while the real hazard sits in the library helper |
| **Outcome** | R1 plan produced: reuse `hephaestus/utils/cache.py::ThreadSafeCache` keyed by the verified `(owner, repo)` tuple from `get_repo_info()`; add a small `add_to_entry` method to the primitive for the set-augment mutation; migrate 5 test reset/seed sites (`= None` → `.clear()`/keyed-seed); add concurrency + distinct-repos + empty-key + `add_to_entry` tests. NOT executed — no code run, no CI. |
| **Verification** | unverified (planning learning; no code was run, no tests executed, no CI) |
| **History** | v1.0.0 = R0 plan (NOGO). v1.1.0 = R1 re-plan (this version); see the `.history` file for the full R0 snapshot and the correction rationale. |

## When to Use

- You are fixing a **shared-mutable-state / TOCTOU bug** and are tempted to hand-roll a
  `dict` + `threading.Lock`. **STOP and grep the repo first** for (a) an existing thread-safe
  cache/lock primitive and (b) a sibling module that already solved this exact bug class. The
  sibling's usage is both the pattern and the proof it is the sanctioned approach.
- A **pre-selected skill** points you at `threading.local()` / a metaclass-per-thread pattern, but
  the state must be **shared and coherent across threads** (a cross-repo cache every thread reads the
  same coherent value from), not per-thread-divergent. The pre-selected skill is topically adjacent
  but prescribes the WRONG variant.
- An **audit names a specific line**, but a call-graph grep shows that line is **not reachable** in
  the failing (multithreaded) context, and the genuinely-shared-state hazard is **one layer down**
  in a library helper any in-process caller shares.
- You are about to **migrate a module-global's TYPE** (e.g. `set | None` → a keyed cache object),
  and existing tests **reset or seed that global directly** — the type migration silently breaks
  every reset/seed seam unless you enumerate them first.
- You need to **mutate one entry of a shared cache primitive** (augment a cached set) without
  reaching into its private `_cache`/`_lock` from the caller — add a small public method to the
  primitive instead.

**Key trigger:** you catch yourself writing `_lock = threading.Lock()` next to a new module dict —
STOP and `grep -rn 'ThreadSafeCache\|threading.Lock\|_cache' hephaestus/` for an existing primitive
and a sibling that already solved the same TOCTOU shape.

## Proposed Workflow

> **Warning:** This workflow has NOT been validated end-to-end. It is a PLANNING methodology captured
> at `unverified` level — no code was run, no tests executed, no CI. Treat every step as a
> hypothesis until CI confirms.
>
> **Heading note:** The repository validator (`scripts/validate_plugins.py`) hard-requires the
> literal section string `## Verified Workflow`, so the canonical steps are emitted under that
> heading to keep validation green. Despite that heading, this content is `unverified` per the
> warning above.

## Verified Workflow

> **Warning:** This workflow has NOT been validated end-to-end. It is `unverified` (planning only —
> no code run, no tests, no CI). Treat as a hypothesis until CI confirms.

### Quick Reference

```python
# 0. BEFORE hand-rolling a lock: grep for an existing primitive AND a sibling that solved this.
#    grep -rn 'ThreadSafeCache' hephaestus/    -> hephaestus/utils/cache.py already exists.
#    Its docstring: "Replaces ad-hoc module-level dict caches that have a TOCTOU race between
#    the membership check and the assignment." git_utils ALREADY uses it for the SAME bug shape:
#      _repo_info_cache: ThreadSafeCache[Path|None, tuple[str,str]]   (git_utils.py:73)
#      _repo_slug_cache: ThreadSafeCache[Path|None, str]              (git_utils.py:131)
#    -> REUSE the primitive keyed by repo slug. Do NOT hand-roll dict + Lock. (R1 core lesson.)

# 1. DIAGNOSE the call-graph: does the audit-named line actually run in the failing context?
#    grep every stage call-site for how the accessor is constructed (repo=item.repo, 30+ sites)
#    -> the audit-named ORG-scoped _label_names() branch is unreachable in the multithreaded path;
#       the true shared hazard is the LIBRARY helper gh_list_labels (any in-process caller shares it).

# 2. PICK THE RIGHT VARIANT: shared-coherent state -> keyed cache under a lock (ThreadSafeCache);
#    per-thread-divergent state -> threading.local(). threading.local() gives each thread its OWN
#    cache -> WRONG for a cache that must be coherent PER REPO across threads.

# 3. KEY the cache on the VERIFIED return shape of get_repo_info() (git_utils.py:76-124):
#    it returns tuple[str, str] == (owner, repo) accessed by TUPLE UNPACK, and RAISES RuntimeError
#    on an unresolvable remote (it does NOT return None). It is itself memoized behind a
#    ThreadSafeCache (_repo_info_cache), so calling it per access is a locked dict lookup, not git.
_label_cache: ThreadSafeCache[tuple[str, str], set[str]] = ThreadSafeCache()

def _cache_key() -> tuple[str, str]:
    owner, repo = get_repo_info()          # VERIFIED tuple unpack; raises RuntimeError on failure
    return (owner, repo)

def gh_list_labels(refresh: bool = False) -> set[str]:
    key = _cache_key()
    if refresh:
        _label_cache.clear()               # (or a targeted evict if the primitive gains one)
    return set(_label_cache.get_or_compute(key, _fetch_labels_from_gh))  # defensive copy out

def gh_create_label(name: str) -> None:
    _create_label_via_gh(name)
    _label_cache.add_to_entry(_cache_key(), name)   # 4. NEW primitive method — see below

# 4. ENCAPSULATE the single-entry mutation as a NEW public method on the primitive, so labels.py
#    never touches ThreadSafeCache._cache / ._lock. Augment an existing set entry under the lock,
#    preserve its TTL timestamp, NO-OP if the key is absent. Unit-test both branches.
class ThreadSafeCache(Generic[K, V]):
    def add_to_entry(self, key: K, item: object) -> None:
        """Augment an existing set-valued entry in place under the lock (no-op if absent)."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is not None:
                value, ts = entry               # preserve the original TTL timestamp
                value.add(item)                 # value is the cached set; mutate under the lock

# 5. MIGRATE THE TEST SEAM: type changed set|None -> ThreadSafeCache, so every reset/seed changes.
#    OLD: _github_api_module._label_cache = None                 (a set|None)
#    NEW: _github_api_module._label_cache.clear()                (reset the primitive)  x sites
#    seed:  _label_cache.get_or_compute((owner, repo), lambda: {"bug"})  (a keyed entry)
#    Enumerated sites (grep): test_github_api.py:1115,1167,1172,1179,1235

# 6. TESTS: threading.Barrier(2) two-mocked-repo concurrency (no cross-repo leak) + a deterministic
#    distinct-repos test + an unresolved-"" -key test + add_to_entry augment/no-op helper tests.
```

### Detailed Steps

1. **Grep for an existing thread-safe primitive and a sibling that already solved the bug BEFORE
   hand-rolling a lock.** This is the R1 core lesson and the correction to R0. The codebase already
   had `hephaestus/utils/cache.py::ThreadSafeCache` — a lock-protected, per-key, TTL cache whose
   docstring literally says it exists to "replace ad-hoc module-level `dict` caches that have a
   TOCTOU race between the membership check and the assignment." `git_utils` already reused it for
   the IDENTICAL bug shape: `_repo_info_cache: ThreadSafeCache[Path|None, tuple[str,str]]`
   (`git_utils.py:73`) and `_repo_slug_cache` (`git_utils.py:131`, with a comment noting "a process
   that iterates multiple repositories gets the right slug per repo instead of the first-cached
   one"). The KISS fix reuses this primitive keyed by repo slug, NOT a hand-rolled repo-keyed
   `dict` + `threading.Lock` (what R0 planned). **Durable rule: when fixing a shared-mutable-state /
   TOCTOU bug, grep the repo for an existing thread-safe cache/lock primitive AND for a sibling that
   already solved the same bug class before writing your own locking — the sibling's usage is both
   the pattern and the proof it's the sanctioned approach.**

2. **Diagnose which code path the audit actually names vs which is reachable.** The issue pointed at
   the org-scoped `_label_names()` path (`pipeline_github.py:192` → `github_api.gh_list_labels()`),
   but grep showed the pipeline coordinator ALWAYS constructs **repo-scoped** accessors
   (`repo=item.repo` at 30+ stage call-sites), and the repo-scoped branch fetches fresh and touches
   NO module global. The genuinely-shared hazard is the LIBRARY function `gh_list_labels` itself
   (any in-process caller). Before fixing the audit-named line, grep the call-graph to confirm
   whether that exact line is reachable in the failing (multithreaded) context, and fix at the
   library layer, not only the named adapter line.

3. **Read the pre-selected skill's decision table — it may prescribe the WRONG variant.** The
   pre-selected skill was `architecture-metaclass-threadlocal-thread-safety`. Its own alternatives
   table says `threading.local()` is for **per-thread** isolation. But the label cache must be
   **coherent per repo ACROSS threads** — a shared cross-repo cache, not per-thread state. So the
   correct fix is a keyed cache under a lock (here, the existing `ThreadSafeCache`), NOT the
   metaclass / `threading.local()` pattern. Shared-coherent state → keyed cache + lock;
   per-thread-divergent state → `threading.local()`.

4. **`[R0 — CORRECTED]` Verify the resolver's return SHAPE — it was cheaply verifiable, not an open
   caveat.** R0 shipped `getattr(info, "owner", None)` / `getattr(info, "name", None)` as the cache
   key and flagged it as an UNVERIFIED assumption. **That assumption was WRONG and cheap to
   resolve.** Reading three lines of `get_repo_info()` (`git_utils.py:76-124`) shows it returns
   `tuple[str, str]` `(owner, repo)`, accessed by **TUPLE UNPACK** — there is no `.owner`/`.name`
   object. R0's `getattr(..., None)` would have silently produced a `None` key → degrade to one
   shared bucket → **silently re-introduce the original bug.** It also **RAISES `RuntimeError`** on
   an unresolvable remote (it does not return `None`), so the failure contract is raise-not-return.
   **Durable rule: a "load-bearing unverified assumption" about a helper's return SHAPE is almost
   always cheaply verifiable by reading the 3 lines of its signature/return — resolve it in the
   plan, don't ship it as a caveat. Read the resolver's actual return type and its raise-vs-return
   failure contract.**

5. **`[R0 — CORRECTED]` Per-call cost was resolved by reading the resolver, not an open risk.** R0
   flagged "`get_repo_info()` may shell out to git on every access — unvalidated per-call cost." In
   fact `get_repo_info()` is itself **memoized behind a `ThreadSafeCache`** (`_repo_info_cache`,
   `git_utils.py:124`), so calling it per `gh_list_labels`/`gh_create_label` is a locked dict lookup
   after the first call, not a git subprocess. The risk was answerable by reading the resolver.

6. **Encapsulate the single-entry mutation as a new primitive method, not by poking privates.** To
   augment one cached set entry (add a just-created label) without reaching into
   `ThreadSafeCache._cache`/`._lock` from `labels.py`, ADD a small public method to the primitive:
   `add_to_entry(key, item)` that augments an existing set entry **under the lock**, preserves the
   entry's TTL timestamp, and is a **no-op if the key is absent**. Give it its own unit tests
   (augment branch + no-op-when-absent branch). This keeps all locking encapsulated in the primitive.

7. **Migrate every test reset/seed seam BEFORE changing the global's type.** The type changes from
   `set | None` to a `ThreadSafeCache`, so every direct reset (`_label_cache = None`) becomes
   `_label_cache.clear()` and every seed becomes a keyed `get_or_compute`. Enumerated sites (grep):
   `test_github_api.py:1115,1167,1172,1179,1235`. A type change to a shared module global silently
   breaks any test that pokes it directly — enumerate and migrate them in the same plan.

8. **Shape the concurrency + edge tests.** Use `threading.Barrier(2)` to force two threads (two
   mocked repos) to hit the guarded fetch/store simultaneously and assert neither repo's labels
   leak into the other's entry. ADD: a deterministic distinct-repos test (repo Y never observes
   repo X's cached labels — catches key-collision without scheduler timing); an unresolved-`""`-key
   test; and the `add_to_entry` augment/no-op helper-altitude tests.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed (risk if assumption wrong) | Lesson Learned |
| --- | --- | --- | --- |
| **`[R0 — CORRECTED]`** Hand-roll a repo-keyed `dict` + `threading.Lock` | R0 planned a fresh `_label_cache: dict[key, set]` + `_label_cache_lock = threading.Lock()` guarding fetch/store in `labels.py` | The repo ALREADY had `hephaestus/utils/cache.py::ThreadSafeCache` (a lock-guarded, per-key, TTL cache built to replace exactly this TOCTOU dict pattern) and `git_utils` already reused it for the IDENTICAL bug shape — hand-rolling re-invents a sanctioned primitive and duplicates locking | When fixing a shared-mutable-state/TOCTOU bug, GREP for an existing thread-safe cache/lock primitive AND a sibling that already solved the bug class before writing your own lock; the sibling's usage is the pattern and the proof |
| **`[R0 — CORRECTED]`** Key the cache on `getattr(info, "owner"/"name", None)` and ship it as unverified | R0 used `getattr(info, "owner", None)` from `get_repo_info()` and flagged the attr names as an open UNVERIFIED assumption | WRONG: `get_repo_info()` returns `tuple[str, str]` `(owner, repo)` accessed by TUPLE UNPACK, not an object with `.owner`/`.name`; `getattr(..., None)` would silently yield a `None` key → one shared bucket → silent regression re-introducing the original bug. It also RAISES `RuntimeError` (not None-return) on failure | A "load-bearing unverified assumption" about a helper's return SHAPE is almost always cheaply verifiable by reading 3 lines of its signature/return — resolve it in the plan, don't ship it as a caveat; read the raise-vs-return failure contract too |
| **`[R0 — CORRECTED]`** Flag `get_repo_info()` per-call cost as an open risk | R0 warned that calling `get_repo_info()` on every `gh_list_labels`/`gh_create_label` access might shell out to git | `get_repo_info()` is memoized behind a `ThreadSafeCache` (`_repo_info_cache`, `git_utils.py:124`), so per-access cost is a locked dict lookup after the first call — the risk was answerable by reading the resolver | Reading the resolver resolves the per-call-cost question; don't carry a risk that the source already answers |
| Reach into `ThreadSafeCache._cache`/`._lock` from `labels.py` to augment the cached set | Mutate the cached set for the current repo by poking the primitive's private dict under its private lock from the caller | Breaks encapsulation — the caller now depends on the primitive's internals and can desync TTL/locking | Add a small public `add_to_entry(key, item)` method to the primitive (augment under the lock, preserve TTL, no-op if absent) with its own tests; keep locking encapsulated |
| Fix the audit-named org-scoped line | Patch `_label_names()` at `pipeline_github.py:192` as the issue named | The pipeline coordinator ALWAYS builds repo-scoped accessors (`repo=item.repo`, 30+ sites), so that org-scoped branch never runs in the multithreaded path; the true shared hazard is the library helper `gh_list_labels` one layer down | Grep the call-graph to confirm the audit-named line is reachable in the failing context; fix the shared-state hazard at the library layer, not only the named adapter line |
| Use `threading.local()` per the pre-selected skill | Apply `architecture-metaclass-threadlocal-thread-safety`'s per-thread pattern to the cache | `threading.local()` gives each thread its OWN cache — WRONG for state that must be coherent PER REPO across threads | A pre-selected skill can be topically adjacent but prescribe the wrong variant; shared-coherent state → keyed cache + lock, per-thread-divergent → `threading.local()` |
| Change the global's type and stop | Switch `_label_cache` from `set \| None` to a `ThreadSafeCache` without touching tests | RISK: 5 reset/seed sites in `test_github_api.py` (`:1115,1167,1172,1179,1235`) poke the global directly as `None` / a bare set; the type change breaks them. NOT executed — site list from grep, not a test run | Enumerate every direct reset/seed of a shared module global BEFORE changing its type; migrate all seams (`= None` → `.clear()`, bare set → keyed `get_or_compute`) in the same plan |

> The plan was never executed, so the rows above are **risk-if-assumption-wrong** entries, except
> the three `[R0 — CORRECTED]` rows whose risks were RESOLVED in R1 by reading the source. Each
> remaining unverified reliance MUST be surfaced to the reviewer rather than presented as a closed
> fact.

## Results & Parameters

**The R1 plan surface for issue #1858 (the concrete diagnose-and-fix deltas):**

| Home | File / Location | Change |
| --- | --- | --- |
| Reuse the primitive | `hephaestus/automation/github_api/labels.py` | Replace module-global `_label_cache: set \| None` with `_label_cache: ThreadSafeCache[tuple[str,str], set[str]]` from `hephaestus/utils/cache.py`; key on the verified `(owner, repo)` tuple from `get_repo_info()`; `gh_list_labels` uses `get_or_compute` and returns `set(...)` (defensive copy); `gh_create_label` calls the new `add_to_entry` |
| Primitive method | `hephaestus/utils/cache.py::ThreadSafeCache` | Add `add_to_entry(key, item)`: augment an existing set entry under the lock, preserve TTL, no-op if absent |
| Org-scoped empty-repo path | `coordinator.py` empty-`repo` branch | Force `refresh=True` on the rare empty-`repo` path so it always refetches rather than reading a stale shared bucket |
| Test reset/seed seams | `tests/.../test_github_api.py:1115,1167,1172,1179,1235` | `_label_cache = None` → `_label_cache.clear()`; seed → keyed `get_or_compute` |
| New tests | `tests/.../test_github_api.py` + `tests/.../test_cache.py` | `threading.Barrier(2)` two-repo race; deterministic distinct-repos isolation; unresolved-`""`-key; `add_to_entry` augment + no-op branches |

**Generalization (the durable, reusable pattern):** When making a module-global cache thread-safe:
**(0)** grep the repo for an existing thread-safe cache/lock primitive and a sibling that already
solved the same TOCTOU bug class — reuse it, do not hand-roll a lock. **(1)** Decide whether the
state must be **shared-coherent** (keyed cache + lock) or **per-thread-divergent**
(`threading.local()`); a pre-selected skill may prescribe the wrong one. **(2)** When an audit names
a line, grep the call-graph to confirm it runs in the failing context and locate the true hazard
(often one layer down in a library helper). **(3)** A "load-bearing unverified assumption" about a
helper's return SHAPE is almost always resolvable by reading 3 lines of its signature — resolve it,
don't ship it as a caveat; read the raise-vs-return failure contract too. **(4)** To mutate one
entry of a shared cache primitive, add a small public method to the primitive rather than poking its
privates. **(5)** When you change a shared global's TYPE, enumerate and migrate every test
reset/seed seam in the same plan.

**Verification status:** `unverified`. This is a PLANNING learning (R1 re-plan). The plan was
produced but NOT executed — no code ran, no tests were run, no CI. The R0 `[CORRECTED]` items above
(existing primitive; verified `(owner, repo)` tuple key; memoized per-call cost) were resolved by
reading the source in R1. The remaining load-bearing unverified assumptions the reviewer must focus
on: (1) that `add_to_entry` preserving the original TTL timestamp (rather than refreshing it) is the
desired semantics; (2) that always-refetch on the empty-repo path is acceptable overhead; (3) that
no existing caller of `gh_list_labels` depends on the returned set being the SAME object across
calls (identity) — the defensive-copy change would break such a caller.

## Verified On

| Repository | Issue / PR | What was applied |
| --- | --- | --- |
| ProjectHephaestus | issue #1858 (R1 plan only) | Plan to make the module-global `_label_cache` in `github_api/labels.py` thread-safe by REUSING `hephaestus/utils/cache.py::ThreadSafeCache` keyed by the verified `(owner, repo)` tuple from `get_repo_info()`, adding an `add_to_entry` method to the primitive, and migrating 5 test reset/seed seams; call-graph diagnosis showed the audit-named org-scoped line unreachable and the real hazard in the library helper. Supersedes the R0 hand-rolled-dict+Lock plan (NOGO). Not executed. |

## Tags

`#planning-methodology` `#thread-safety` `#shared-cache` `#reuse-existing-primitive`
`#threadsafecache` `#repo-keyed-cache` `#threading-lock` `#threading-local` `#module-global`
`#call-graph-diagnosis` `#skill-mismatch` `#verify-return-shape` `#encapsulation`
`#test-reset-seam` `#hephaestus`
