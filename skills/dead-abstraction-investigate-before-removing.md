---
name: dead-abstraction-investigate-before-removing
description: "Before removing a 'dead abstraction' (a centralized helper/registry with zero callers), INVESTIGATE rather than pre-emptively delete. A zero-caller module may be useful scaffolding waiting to be wired up OR a harmful orphan duplicate. Use when: (1) a strict review flags a well-built but unused module as a 'dead abstraction' removal candidate, (2) you are tempted to file a bare 'no callers -> delete' PR, (3) several parallel refactor PRs may have produced competing mechanisms for the same goal. The deciding factors for removal are an ALREADY-WIRED competing mechanism, an OPEN PR heading a different direction, and STALE defaults vs trunk (a footgun)."
category: architecture
date: 2026-06-27
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [yagni, dead-code, duplication, competing-mechanism, triage, refactor-hazard]
---

# Dead Abstraction: Investigate Before Removing

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-27 |
| **Repo** | ProjectHephaestus |
| **Issue / PR** | #1665 / #1666 (removal of `hephaestus/config/env.py`) |
| **Objective** | Decide whether a 461-line "centralized HEPH_* env var registry" (`EnvRegistry`) with ZERO callers should be removed |
| **Outcome** | Success — removal PR authored, validated locally (ruff/mypy/pre-commit/import-surface all green), and merged this session |
| **Verification** | verified-local (the removal PR was validated and merged; the reusable artifact is the triage METHOD, not the deletion itself) |
| **Category** | architecture |

---

## When to Use

Apply this pattern when:

- A strict review (or your own audit) flags a **well-built but unused module** — a "centralized X", registry, or helper with **zero callers** — as a "dead abstraction" removal candidate.
- You are about to file a bare **"it has no callers, delete it"** PR. That justification alone is *insufficient*: a zero-caller module may be genuine scaffolding waiting to be wired up.
- Several **parallel refactor PRs** may have landed competing mechanisms for the same goal, and you need to identify which one is canonical and which are orphans.

The core insight: **"no callers" is necessary but not sufficient grounds to delete.** The deciding factors are (a) is there an ALREADY-WIRED competing mechanism, (b) is there an OPEN PR heading a different direction, (c) are the abstraction's defaults already STALE vs trunk. Removal is correct when at least one holds — and the PR must justify removal by the *duplication / footgun*, not by mere unusedness.

---

## Verified Workflow

### Quick Reference

```bash
# 1. Read what the abstraction actually DOES — is it well-built or junk?
#    (env.py was pure-stdlib, thread-safe, typed, fail-open — NOT junk.
#     "Well-built" means you CANNOT delete on "it's bad code" grounds.)

# 2. Confirm zero PRODUCTION callers (exclude its own tests) AND that it isn't exported:
grep -rn "<module>\|<ClassName>" <pkg>/ scripts/ | grep -v "/<module-file>:" | grep -v test
grep -n "<module>" <pkg>/<subpkg>/__init__.py        # is it even exported?

# 3. Look for an ALREADY-WIRED competing mechanism solving the same goal:
grep -rln "<the_real_helper>" <pkg>/ | grep -v test  # who actually uses the alternative?

# 4. Look for an OPEN PR heading a different direction (CLI flags vs env vars, etc.):
gh pr list --state open --json number,title,body \
  --jq '.[] | select((.title+.body)|test("<topic>";"i")) | "#\(.number) \(.title)"'

# 5. Check whether the abstraction's DEFAULTS are already STALE vs trunk (the footgun test):
#    compare each hardcoded default in the abstraction to the LIVE value on main.

# 6. Decision:
#    if (already-wired duplicate) OR (stale defaults / footgun) OR (open PR moving away)
#       -> REMOVE, with a PR that EXPLAINS the N-way duplication + points to the chosen
#          mechanism, AND file a tracking issue documenting the duplication.
#    else -> WIRE IT UP or HOLD. Never a bare "no callers -> delete".
```

### 1. Read what it actually does — well-built or junk?

First understand the abstraction's functionality. In the observed case `hephaestus/config/env.py` was a genuine, well-engineered centralized registry: pure stdlib, thread-safe, typed, fail-open. Because it was well-built, **"this is bad code" was NOT available as a reason to delete it.** That forces the justification onto duplication/staleness grounds, which is exactly the rigor this skill enforces.

### 2. Confirm zero production callers — and check exports

Grep for production importers, excluding the module's own test file, and confirm it is not re-exported from the package's `__init__.py`:

```bash
grep -rn "config.env\|EnvRegistry" hephaestus/ | grep -v test   # -> 0
grep -n "env" hephaestus/config/__init__.py                     # -> not exported
```

Zero callers + not exported establishes it is *currently* inert. This is the necessary precondition — but on its own it only tells you the module is unused, not that it is *safe* or *correct* to delete.

### 3. Find an already-wired competing mechanism

Search for a sibling helper that solves the same goal and is **actually wired up**. Here a sibling PR (#1642) had merged `constants.read_timeout_env` + `AGENT_*_TIMEOUT` constants — the mechanism actually used by `claude_timeouts.py`. The tracking issue `env.py` was built for (#1430) effectively got *that* solution. So `env.py` was an orphaned **third** mechanism for the same job. Decision factor (a): **an already-wired duplicate exists.**

### 4. Find an open PR heading a different direction

List open PRs touching the same topic. Here PR #1657 ("replace HEPH_* env vars with explicit CLI options") was actively moving the codebase *away* from env vars toward CLI flags — making a brand-new env-registry unlikely to ever be adopted. Decision factor (b): **the codebase direction diverges from the abstraction.**

### 5. The footgun test — are its defaults stale vs trunk?

Compare each hardcoded default in the abstraction to the live value on `main`. Here `env.py` hardcoded `HEPH_PLANNER_AGENT_TIMEOUT` = 7200 but main already used 300 (via `AGENT_PLAN_TIMEOUT`, #1642); model defaults like `claude-opus-4-7` were superseded. **Anyone who wired it up would silently get WRONG values.** A stale unused abstraction is worse than inert — it is a trap. Decision factor (c): **stale defaults make it an active footgun.**

### 6. Decide and execute correctly

If any of (a) already-wired duplicate, (b) open PR moving away, (c) stale defaults hold, **REMOVE** — but:

- Write a PR that **explains the N-way duplication** and points to the chosen canonical mechanism (do not say merely "unused").
- `git rm` the module **and its test together** so the test-structure mirror invariant stays satisfied.
- Verify zero external refs / no COMPATIBILITY-table entry / no `__init__` export *before* deleting.
- **File a tracking issue** documenting the N-way duplication so the lesson outlives the PR.

If NONE of the factors hold, do not delete: **wire it up** or **hold**. This is an instance of the parallel-refactor / competing-mechanism hazard that arises when many auto-generated refactor PRs land at once.

---

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Bare "unused -> delete" PR | Proposed a "remove the dead abstraction — it has no callers" PR immediately | User pushed back: a zero-caller module may be genuinely useful scaffolding waiting to be wired up; "no callers" alone isn't grounds to delete. Investigation showed `env.py` was well-built — the REAL reasons were the already-wired duplicate (#1642), the divergent open PR (#1657), and stale defaults | Investigate functionality + competing mechanisms + open PRs + default-staleness BEFORE removing; justify by the duplication/footgun, not by "unused" |
| Assumed it was canonical | Assumed the centralized registry was the canonical solution to its tracking issue #1430 | A DIFFERENT, simpler mechanism (`constants.read_timeout_env`, #1642) had already landed and was actually wired up; #1430 effectively got that. The registry was an orphaned parallel implementation | When multiple PRs target the same goal in parallel, identify which mechanism actually got WIRED UP; the others are duplicates to remove, not keep |
| Skipped the staleness check | Considered the unused module merely inert and harmless | Its hardcoded defaults (timeout 7200 vs live 300; superseded model id `claude-opus-4-7`) were already stale vs trunk — anyone wiring it up would silently get WRONG values | A stale unused abstraction is worse than inert; it is a footgun. Compare every hardcoded default to the live value on main before deciding |

---

## Results & Parameters

| Item | Value |
|------|-------|
| Abstraction removed | `hephaestus/config/env.py` (461 LoC, `EnvRegistry`) |
| Callers in production | 0 (also not exported from `config/__init__.py`) |
| Reason for removal | NOT "unused" — the already-wired duplicate (#1642) + divergent open PR (#1657) + stale defaults (footgun) |
| Already-wired duplicate | `constants.read_timeout_env` + `AGENT_*_TIMEOUT` (#1642), used by `claude_timeouts.py` |
| Divergent open PR | #1657 "replace HEPH_* env vars with explicit CLI options" |
| Stale-default examples | `HEPH_PLANNER_AGENT_TIMEOUT`=7200 vs live 300; model id `claude-opus-4-7` superseded |
| Removal mechanics | `git rm` module + its test together (keeps test-structure mirror invariant); verify no refs / COMPATIBILITY / `__init__` export first |
| Follow-up | Filed a tracking issue documenting the 3-way duplication |
| Local validation | ruff / mypy / pre-commit / import-surface all green; PR merged this session |
| Generalization | Instance of the parallel-refactor / competing-mechanism hazard when many auto-generated refactor PRs land at once |

---

## References

- `pola-consolidate-duplicated-silent-default-resolver` — the inverse situation: *consolidating* multiple duplicated resolvers into one fail-loud resolver. This skill instead decides whether an *unused* competing abstraction should be removed.
- `orphan-config-detection` — detecting config files referenced by nothing; related "orphan" idea applied to config rather than code abstractions.
