---
name: architecture-shared-utility-placement-boundary-yagni
description: "Plan WHERE a new shared utility lives under an enforced one-way import boundary, classify which of several similar caches actually share a shape before migrating, and keep a concurrency-cache's test spec consistent with its own design plus its public surface minimal. Use when: (1) an issue offers two homes (library module vs product/automation module) for a new shared helper and a dependency-arrow ADR + base-import-surface guard constrain the pick, (2) you are scoping a refactor that claims several module-level dict/set caches are 'the same' and should collapse into one TTL/locking abstraction, (3) you are writing the concurrency test for a cache that computes OUTSIDE its lock (assert equality + no-lost-writes, never object identity) and want to avoid a YAGNI public API surface."
category: architecture
date: 2026-06-30
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [architecture, library-boundary, import-surface, cache, ttl, thread-safety, toctou, concurrency-testing, yagni, planning, dry, placement]
---

# Shared-Utility Placement Under a Boundary + Concurrency-Test/YAGNI Discipline

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-30 |
| **Objective** | Plan placement + API of a new `ThreadSafeCache` utility (TTL + locking) replacing ad-hoc module-level dict caches, under ProjectHephaestus's automation→library boundary + stdlib-only base-import-surface guard, and survive a review cycle |
| **Outcome** | Plan produced: place in the **library** (`hephaestus/utils/cache.py`); migrate the **two** key→value dict caches; deliberately **NOT** migrate the set-shaped `_label_cache`. First plan got a **NOGO (Grade B)** for a design↔test contradiction + a YAGNI getter; revised plan fixed both |
| **Verification** | unverified — planning-only session; no code written, no tests run, no CI. Plan went through ONE review cycle (NOGO → revise) |

## When to Use

- An issue gives you **two candidate homes** for a new shared utility (a *library* module vs a *product*/automation module) and the repo enforces a one-way dependency arrow (e.g. `docs/adr/0001-automation-library-boundary.md`: automation may import library, never the reverse).
- The repo has a **base-import-surface guard** (e.g. `tests/unit/test_import_surface.py`) asserting `import pkg` pulls no heavy deps (`curses`/`fcntl`/`pydantic`/product modules).
- An issue frames **N "similar" module-level caches/dicts** as uniformly migratable into one abstraction — before you scope, you must diff their actual SHAPES.
- You are writing or reviewing the **concurrency test** for a cache/memoizer that computes **outside** its lock, and need to know what is and is not a valid invariant to assert.
- You are deciding the **public API surface** of a brand-new shared utility and want to avoid speculative methods (YAGNI).

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms. (Despite the literal heading, which is a fixed schema requirement, this is a **proposed**, planning-only workflow — no code was written, no tests were run, no CI ran. Every placement, behavior, and test claim below is something the implementer/reviewer MUST verify against live source and the suite before relying on it.)

### Quick Reference

```bash
# 1. Determine the dependency-arrow direction — read the ADR, do not trust the summary
cat docs/adr/0001-automation-library-boundary.md

# 2. Find every consumer of the utility-to-be. If a LIBRARY module consumes it,
#    the utility MUST live in the library (product cannot be imported by library).
grep -rn "_repo_info_cache\|_repo_slug_cache\|get_repo_slug\|clear_repo_caches" hephaestus/

# 3. Confirm the candidate library module is stdlib-only (no curses/fcntl/pydantic/automation)
grep -nE "^(import|from) " hephaestus/utils/git_utils.py | head
python -m pytest tests/unit/test_import_surface.py tests/unit/test_automation_boundary.py

# 4. COUNT and DIFF each claimed-duplicate cache — do not assume they share a shape
grep -n "_repo_info_cache\|_repo_slug_cache\|_label_cache" hephaestus/**/*.py
grep -rn "_label_cache" tests/   # tests reveal the real contract (assignment shape)
```

### Detailed Steps

1. **Placement is forced by the dependency arrow, not preference.** A utility consumed by a *library* module must live in the *library*, because the boundary forbids library→product imports. Here the choice was `hephaestus/utils/cache.py` (library) vs `hephaestus/automation/_review_utils.py` (product); because `git_utils.py` (a library module that imports only `hephaestus.utils.*`) is a consumer, only the library home is legal. Read the ADR itself — do not infer the arrow from a CLAUDE.md summary. This generalizes the same library-layer-placement lesson recorded in `dry-refactoring-workflow` Phase 18 (the `CLI_LOG_FORMAT` constants case) — cross-reference it.
2. **Placement is also gated by the base-import-surface guard.** A library utility must be **stdlib-only** (`threading`, `time`, typing — no `curses`/`fcntl`/`pydantic`/automation imports), or `tests/unit/test_import_surface.py` goes red the moment any library module imports it. Verify the new module imports nothing heavy, and that adding `from hephaestus.utils.cache import ThreadSafeCache` to a consumer introduces **no import cycle**. (UNVERIFIED in this session: that `git_utils.py` imports only from `hephaestus.utils.*` and is cycle-free with the new import; and the existence/behavior of `test_import_surface.py` + `test_automation_boundary.py` — read from the CLAUDE.md summary, not run.)
3. **Classify the "N similar" caches — count and DIFF, never blind-merge.** The issue framed three module-level caches as uniformly migratable. Reading the real code/tests showed only two share a shape:
   - `_repo_info_cache` and `_repo_slug_cache` are `key → value` **dict** caches → migrate to `ThreadSafeCache[K, V]`.
   - `_label_cache` is a `set[str] | None` (a whole-repo label SET plus a refresh flag), assigned directly by tests (`_github_api_module._label_cache = {"bug"}` / `= None`) and mutated **in place** by `gh_create_label` (`.add(name)`) — a fundamentally different SHAPE. Forcing it into `ThreadSafeCache[K, V]` would be a mismatched abstraction requiring a rewrite of helpers plus ~10 tests (violates KISS/YAGNI). **Document this as an intentional non-migrated variant with rationale + a follow-up-issue note** rather than silently dropping it or jamming it into the abstraction. (Mirrors the classify-don't-blind-merge / intentional-variant discipline in `dry-refactoring-workflow`.)
4. **A plan must hand the implementer a TEST SPEC consistent with its own DESIGN (the first NOGO).** The first plan's design ran `compute()` OUTSIDE the lock (deliberate, so a slow `git remote` for one key does not block other keys), but its concurrency test told the implementer to "assert all threads return the SAME OBJECT." Under compute-outside-lock that invariant is **false**: N threads racing the same COLD key each run `compute`, the store is last-writer-wins, so racers legitimately get distinct-but-EQUAL objects. The reviewer correctly NOGO'd this as a design↔test contradiction the implementer would have to re-derive (or ship a flaky test). **Fix the test, not the design:**
   - same-key concurrency test asserts (a) no crash and (b) all results are EQUAL by `==` (`compute` returns equal-but-distinct values);
   - a SEPARATE distinct-keys test asserts NO LOST WRITES (`observed == {i: i for i in range(N)}`, proving the locked store);
   - object-identity / call-once is asserted ONLY in a single-threaded warm-hit test where it actually holds.
   - **Durable rule:** when a cache/memoizer computes outside its lock, never assert identity across concurrent callers — assert equality + no-crash + no-lost-writes; reserve identity/call-once for the serialized warm-hit path.
5. **Keep the public surface equal to its actual call sites (the second NOGO — YAGNI).** The first `ThreadSafeCache` exposed a `get()` method with eager-expiry-on-read (a write under a read) that **no consumer** in the rewire used. The reviewer flagged it YAGNI. **Fix:** expose ONLY the methods the rewire uses (`get_or_compute` + `clear`); a future caller adds a getter together with its own test. **Durable rule:** a new shared utility's public surface should equal its actual call sites at introduction time, not its imagined ones.
6. **Preserve ad-hoc cache behavior exactly when wrapping it** (see Results & Parameters for the full reviewer-risk list): success-only memoization, fallback folded inside the compute closure, intact `clear_*()` fixture contract, and call out the TTL default as a real behavior change.
7. **Re-verify external references before editing.** Line numbers drift; cited files may not have been opened. Re-grep `git_utils.py` / `github_api.py` and the test files, and actually read the ADR + import-surface tests rather than trusting their assumed behavior.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed (or would have) | Lesson Learned |
|---------|----------------|-------------------------------|----------------|
| Place in product module | Considered `hephaestus/automation/_review_utils.py` as the home for the shared cache | A *library* module (`git_utils.py`) consumes it; library→product imports are forbidden by the boundary ADR | Placement is forced by the dependency arrow — a utility consumed by a library MUST live in the library |
| Blind-migrate `_label_cache` with the others | Issue framed `_repo_info_cache`, `_repo_slug_cache`, `_label_cache` as one migration into `ThreadSafeCache[K,V]` | `_label_cache` is `set[str] \| None` (whole-repo set + refresh flag), directly assigned by tests and mutated via `.add()` — wrong SHAPE; mismatched abstraction that would break helpers + ~10 tests | Count and DIFF every claimed-duplicate before scoping; classify, then document intentional non-migrated variants with a follow-up issue |
| Assert "same object" under compute-outside-lock | First plan's concurrency test told the implementer all threads racing one cold key return the SAME OBJECT | Compute runs outside the lock + last-writer-wins store → racers get distinct-but-EQUAL objects; the invariant is false → flaky test / design↔test contradiction → NOGO (Grade B) | Assert equality + no-crash for same-key; assert no-lost-writes for distinct-keys; reserve identity/call-once for the serialized warm-hit path |
| Expose `get()` with no consumer | First `ThreadSafeCache` shipped a `get()` with eager-expiry-on-read used by no rewire call site | Speculative API surface — YAGNI NOGO | A new utility's public surface should equal its actual call sites at introduction; defer getters until a real caller (with its own test) needs them |
| Memoize the compute result unconditionally | Naive `get_or_compute` would cache whatever `compute` returns, including on the exception path | Original cached only SUCCESSES; caching exceptions changes behavior | Preserve success-only semantics — a raising compute propagates and stores nothing |
| Trust cited line numbers / ADR summary | Relied on `git_utils.py:70/73-122/...`, `github_api.py:114-115`, ADR text from CLAUDE.md | Line numbers drift after edits; the ADR and import-surface tests were never re-opened | Re-grep and re-read the actual files before editing |

## Results & Parameters

**Proposed final plan for ProjectHephaestus issue #1440 (UNVERIFIED):**
- New file `hephaestus/utils/cache.py` — `ThreadSafeCache[K, V]` with TTL (default `300s`) + `threading.Lock`, double-checked `get_or_compute(key, compute)` calling `compute` **outside** the lock, success-only memoization, and a `clear()` method. Public surface is exactly `get_or_compute` + `clear` (no speculative `get()`). `time.monotonic()` for TTL (immune to wall-clock jumps).
- Migrate the two dict caches in `git_utils.py`: `_repo_info_cache`, `_repo_slug_cache` → `ThreadSafeCache` instances; fold `get_repo_slug`'s `"repo"` fallback inside the compute closure; keep `clear_repo_caches()` signature unchanged (autouse fixture `test_git_utils.py:29-34`).
- **Do NOT migrate** `github_api.py`'s `_label_cache` (`set[str] | None`, direct test assignment, in-place `.add()`); record as intentional variant + follow-up issue.
- Tests: same-key concurrency → assert no-crash + all results EQUAL (`==`); distinct-keys concurrency → assert `observed == {i: i for i in range(N)}` (no lost writes); single-threaded warm-hit → assert call-once / object identity.

**Behavior-preservation / reviewer-risk list (the reviewer MUST focus here):**
- **Success-only memoization** — `get_or_compute` must NOT memoize exceptions; a raising `compute` propagates and stores nothing (original caches only successes).
- **Fallback caching** — `get_repo_slug`'s `"repo"` fallback is currently CACHED; fold the fallback INSIDE the compute closure so the fallback value is what gets memoized (preserves "computed once, reused for TTL window"). Tradeoff to flag: a transient `git remote` failure now caches `"repo"` for the whole TTL window.
- **Clear fixture contract** — keep `clear_repo_caches()`'s signature intact so the autouse fixture (`test_git_utils.py:29-34`) keeps working unchanged.
- **TTL default 300s is a behavior change** — the original cache was infinite (process-life). The issue explicitly asks for TTL, so it is intended, but it alters semantics from "cache forever" to "expire after 5 min" and should be called out.
- **Library placement hinges on no-import-cycle + stdlib-only** — not test-verified in this session. Run `test_import_surface.py` and `test_automation_boundary.py`.
- **`_label_cache` non-migration** — confirm the issue's acceptance criteria don't REQUIRE migrating all three caches; if they do, the scope-narrowing is a deviation needing explicit justification.

**External references relied on but NOT directly verified (flag for reviewer):**
- `docs/adr/0001-automation-library-boundary.md` — cited from the CLAUDE.md summary, not re-read.
- `tests/unit/test_import_surface.py`, `tests/unit/test_automation_boundary.py` — existence/behavior assumed from CLAUDE.md, not opened.
- Exact line numbers (`git_utils.py:21/70/73-122/129/132-156/159-162`, `github_api.py:114-115`, `utils/__init__.py:4-44`, `test_github_api.py:1095,1147`, `test_git_utils.py:29-34`) — read once, may drift; re-grep before editing.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1440 — Create ThreadSafeCache utility to replace ad-hoc module-level dict caches with TTL + locking | Planning-only session (TASK/PLAN/REVIEW pipeline); plan produced but NOT executed (no code, no tests, no CI). One review cycle: NOGO (Grade B) → revised. Verification: **unverified**. |
