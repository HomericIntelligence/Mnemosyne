---
name: planning-frozen-registry-guard-co-update
description: "When a planned change removes or edits an entry in a list/registry/manifest that is ENFORCED by a frozen 'exact-set' guard test, the edit silently breaks the guard unless the guard's hard-coded copy is co-updated — or you prove the edit is unnecessary via sibling precedent and drop it. Use when: (1) planning to remove/add/edit an entry in a coverage omit-allowlist, `__all__`, a plugin/skill registry, or any hard-coded enumerated set, (2) an issue suggests a side cleanup like 'also de-list X', (3) you are about to edit pyproject.toml/setup.cfg/a config list and are unsure whether a test pins its contents, (4) adding tests to a coverage-omitted module, (5) a reviewer or CI surfaces a `*_frozen`/exact-set assertion failure after a list edit."
category: testing
date: 2026-07-04
version: "1.1.0"
user-invocable: false
verification: unverified
history: planning-frozen-registry-guard-co-update.history
tags:
  - planning
  - testing
  - frozen-test
  - allowlist
  - registry
  - manifest
  - coverage-omit
  - pyproject
  - guard-test
  - sibling-precedent
  - dry
  - orthogonality
  - prose-count-drift
  - multi-home-invariant
  - stale-list-entry
  - re-derive-ground-state
---

# Planning Changes Behind a Frozen Registry Guard: Co-Update or Drop the Edit

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-04 |
| **Objective** | Plan a change that removes/edits an entry in a list/registry/manifest WITHOUT silently breaking a separate frozen "exact-set" guard test that pins that list's contents — and find EVERY co-update home of the invariant, including second-order prose/docstring counts |
| **Outcome** | Two instances: (#1362) re-plan converged after a NOGO by DROPPING the de-listing step and proving it unnecessary via sibling precedent; (#1811) a stale omit entry whose underlying file was packaged away is safely REMOVED, requiring THREE synchronized co-edits (list + frozen set + a prose count). Both plans unverified. |
| **Verification** | unverified |

A first implementation plan for ProjectHephaestus issue #1362 (add unit tests for two
untested methods of `PostMergeProcessor`) proposed conditionally REMOVING
`hephaestus/automation/post_merge_processor.py` from the coverage omit-allowlist in
`pyproject.toml`. A reviewer flagged a MAJOR gap: a separate frozen guard test
`tests/unit/validation/test_omit_allowlist.py::test_omit_allowlist_frozen` asserts
`actual_set == expected_set` over the EXACT omit list, where `expected_set` is a
hard-coded set (`expected_modules`) IN the test. Removing the module from `pyproject.toml`
without mirroring the deletion in the guard's `expected_modules` makes the guard FAIL — a
hidden two-file change the plan never called out, which earned a NOGO.

The resolution that converged the re-plan: the omit-allowlist entry is ORTHOGONAL to
whether a module has tests. All THREE already-tested sibling collaborators
(`pr_discovery`, `ci_check_inspector`, `ci_fix_orchestrator`) each have a
`test_*_helpers.py` AND remain in the omit list. So adding tests does NOT require
de-listing. The fix: DROP the de-listing step entirely, keep the module in the allowlist,
make ZERO `pyproject.toml` edits, and add a verification step that runs the guard test to
prove it stays green. This eliminated the entire failure path rather than adding a fragile
two-file co-edit.

### New instance (2026-07-04): #1811 — a frozen list can have MORE THAN TWO homes, and one may be a prose count

A second planning task for ProjectHephaestus issue #1811 (pipeline foundation layer)
surfaced the same subject with a fresh wrinkle. Here the omit entry
`hephaestus/automation/github_api.py` was STALE: the flat module had been converted into a
`github_api/` PACKAGE, so the `.py` path no longer exists on disk. Unlike #1362 the edit is
load-bearing and correct — the entry must be REMOVED. But planning the removal revealed the
invariant has THREE synchronized homes, not two:

1. `pyproject.toml` `[tool.coverage.run].omit` — the actual list.
2. `tests/unit/validation/test_omit_allowlist.py` `expected_modules` — the frozen
   hard-coded copy (the same `*_frozen` exact-set guard as #1362).
3. `tests/integration/test_orchestration_smoke.py` — a PROSE COUNT in the module
   DOCSTRING ("17 automation modules" → 16; "10 modules lack main()" → 9) plus an
   enumeration line that names `github_api`. This is NOT a Python set: the smoke test
   derives the module list from `pyproject.toml` at runtime, so the docstring count is
   documentation that drifts SILENTLY — it is asserted only indirectly (a human count that
   no assertion pins), yet it is a genuine co-update site.

Two durable additions beyond the v1.0.0 lesson:

- **A frozen invariant's co-update homes include second-order prose counts and docstrings
  in sibling test files, not just the one `*_frozen` assertion.** A comment or docstring
  that says "N modules" IS a co-update site. Grep for the COUNT ("17 automation",
  "modules lack main"), not only for the `expected_modules` symbol.
- **Re-derive the ground state; don't trust the description.** The plan confirmed via `ls`
  that `hephaestus/automation/github_api.py` is genuinely GONE (replaced by the
  `github_api/` package dir) BEFORE removing its omit entry. A frozen-list entry can ROT
  when its underlying file is renamed or packaged; removing such a dead entry is safe
  ONLY after a filesystem check proves the path no longer exists. This is the "prove the
  edit is safe" branch of the skill, grounded in an `ls` rather than sibling-test precedent.

## When to Use

The generalizable rule: when a planned change edits a list/registry/manifest enforced by a
"frozen"/"exact-set" guard test, EITHER (a) co-update BOTH the source list AND the guard's
hard-coded copy in the same change and add a verification step running the guard, OR (b)
prove the edit is unnecessary by checking whether siblings already in the same state
satisfy the goal without the edit — and drop the edit. Before proposing to remove an entry
from any allowlist, grep the test tree for a test that pins that allowlist's contents.

Use this skill when:

- Planning a change that removes/adds/edits an entry in a coverage omit-allowlist, an `__all__`, a plugin/skill registry, a CODEOWNERS-style manifest, or any hard-coded enumerated set
- An issue suggests a "nice to have" cleanup (e.g. "also de-list X from the omit list") as a side change
- You are about to edit `pyproject.toml`/`setup.cfg`/a config list and are unsure whether a test pins its contents
- Adding tests to a module that is currently coverage-omitted (tests are orthogonal to omit-listing)
- Any time a reviewer or CI surfaces a `*_frozen` / exact-set / `assert ... == {hard-coded set}` test failure after a list edit
- Removing a STALE list entry whose underlying file was renamed/packaged away (confirm the path is gone via `ls` first, then remove — and expect a docstring/prose count to also drift)
- The list is mirrored by a human-readable COUNT ("N modules", "N items") in a docstring/comment/README that no assertion pins — that count is a silent co-update site

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. The plan was never executed; the orthogonality claim rests on reading test/config source, not running the guard test. Treat as a hypothesis until CI confirms.

### Quick Reference

```bash
# BEFORE removing an entry from any allowlist/registry/manifest, find EVERY home:
# 1. the pinning frozen guard (the *_frozen exact-set assertion):
grep -rE "actual_set == expected_set|frozen|expected_modules|EXPECTED_" tests/
# 2. any SECOND-ORDER prose/docstring count that mirrors the list (a silent co-update site):
grep -rEn "[0-9]+ (automation )?modules|modules lack|N items" tests/ docs/
# 3. grep for the ENTRY ITSELF across the whole tree, not just the config file:
grep -rn "github_api.py" .   # <- catches list + frozen set + docstring enumeration
# If removing a STALE entry, first prove the underlying file is actually gone:
ls hephaestus/automation/github_api.py   # must fail (path packaged/renamed away)
# Found a frozen guard? Two safe options:
#   (a) co-update ALL homes (source list + frozen set + any prose count), then run the guard:
#       pixi run pytest tests/unit/validation/test_omit_allowlist.py -v
#   (b) prove the edit is UNNECESSARY: check whether siblings already in the target state
#       satisfy the goal without the edit; if so, DROP the edit entirely (zero source changes).
```

### Detailed Steps

1. **Identify any list/registry/manifest your plan touches.** Coverage omit-allowlists, `__all__`, plugin registries, CODEOWNERS-style manifests, and config enumerations are all candidates.
2. **Grep for EVERY home of the invariant, not just the config file.** Grep the ENTRY itself across the whole tree (e.g. `grep -rn "github_api.py" .`), the `*_frozen` guard (`expected_*`/`EXPECTED_*`/`actual_set == expected_set`), AND any second-order PROSE COUNT that mirrors the list (`grep -rEn "[0-9]+ .*modules|modules lack"`). A docstring/comment that says "N modules" is a co-update site even when no assertion pins it.
3. **If the entry is being REMOVED because it is stale, re-derive the ground state first.** Confirm via `ls` that the underlying file is genuinely gone (renamed/packaged away) before deleting the entry. A frozen-list entry can rot when its source file moves; removing a dead entry is safe only after the filesystem check. Do not trust the issue's description of the file's state — verify it.
4. **If a frozen guard exists, choose one of two safe paths.**
   - Path (a) co-update: edit ALL homes (the source list, the guard's hard-coded copy, AND any prose/docstring count) in the same change, then add a verification step that RUNS the guard.
   - Path (b) drop: check whether siblings already in the target state satisfy the goal without the edit. If they do, drop the edit entirely (zero source changes).
5. **Prefer path (b) when the edit is not load-bearing.** The safest change is the one you do not make; dropping an unnecessary edit removes the failure path instead of adding a fragile multi-file invariant. (When the entry is stale — its file gone — the removal IS load-bearing; take path (a) and co-update every home.)
6. **Add an explicit verification step that runs the frozen guard** before calling the plan verified. Reading the test source is not the same as running it. Re-grep by CONTENT (`github_api.py`, `17 automation`, `expected_modules`) at implementation time — the cited line numbers are point-in-time and DRIFT.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| De-list a coverage-omitted module as a nice-to-have | First plan proposed (conditionally) removing `hephaestus/automation/post_merge_processor.py` from the `pyproject.toml` coverage omit-allowlist while adding tests | A separate frozen guard `test_omit_allowlist.py::test_omit_allowlist_frozen` pins the EXACT set via a hard-coded `expected_modules`; deleting from `pyproject.toml` alone makes `actual_set == expected_set` FAIL — a hidden second-file edit the plan never named (got a NOGO) | Before removing any allowlist entry, grep the test tree for a `*_frozen`/exact-set guard that pins it; either co-update both copies + run the guard, or prove the edit is unnecessary |
| Assume having tests requires de-listing from the omit allowlist | Plan treated "add tests" and "remove from omit list" as coupled steps | Three already-tested siblings (`pr_discovery`, `ci_check_inspector`, `ci_fix_orchestrator`) each have `test_*_helpers.py` AND remain in the omit list — proving the two are orthogonal | Coverage-omit-listing is orthogonal to whether a module has tests; check sibling precedent before coupling them |
| Fix the NOGO by adding a two-file co-edit | One option was to mirror the deletion into the guard's `expected_modules` set (co-update both files) | Technically correct but adds a fragile, easy-to-forget two-file invariant for zero benefit, since de-listing was never required to meet the goal | Prefer eliminating a failure path (drop the unneeded edit) over adding a fragile co-edit to satisfy a guard; the safest change is the one you don't make |
| Declare the (non-)change verified from reading source | Orthogonality + guard behavior were established by reading `test_omit_allowlist.py:49-52` and `pyproject.toml:259-262` via grep, not by running the guard after the (non-)change | Reading is not running; the guard test was never executed post-change | Add an explicit verification step that RUNS the frozen guard (`pytest .../test_omit_allowlist.py`) before calling the plan verified; until then mark unverified |
| (#1811) Assume a frozen omit list has exactly TWO homes | Planning the removal of the stale `github_api.py` omit entry, the first mental model was "edit `pyproject.toml` + mirror in `test_omit_allowlist.py::expected_modules`" — the two homes from #1362 | A THIRD home exists: `tests/integration/test_orchestration_smoke.py`'s docstring carries a prose count ("17 automation modules" and "10 modules lack main()") plus an enumeration line naming `github_api`. Editing only the two Python homes leaves the docstring saying "17" when 16 modules remain — silent doc drift | Grep for EVERY home of the invariant, including second-order PROSE COUNTS and docstrings in sibling test files; a "N modules" comment is a co-update site. Grep the entry itself tree-wide, not just the config file |
| (#1811) Trust that the omit entry still points at a real file | The entry `hephaestus/automation/github_api.py` had sat in the omit list since the module was flat | The flat module was converted to a `github_api/` PACKAGE; the `.py` path no longer exists on disk, so the omit entry was DEAD — pointing at a nonexistent path | Re-derive the ground state: `ls` the path before removing a stale entry. A frozen-list entry rots when its underlying file is renamed/packaged; removal is safe ONLY after the filesystem confirms the path is gone (this is the "prove the edit is safe" branch, grounded in `ls`, not sibling precedent) |
| (#1811) Anchor the plan's edits to cited line numbers | The plan cited `pyproject.toml:299-300`, `test_omit_allowlist.py:57`, `test_orchestration_smoke.py:3/8/11-16` from a point-in-time read | Line numbers drift with any concurrent edit to those files; an implementer following stale coordinates edits the wrong lines | Re-grep by CONTENT at implementation time (`github_api.py`, `17 automation`, `expected_modules`, `modules lack main`) rather than trusting line numbers; treat cited lines as hints only |

## Results & Parameters

The concrete grep recipe to find a pinning guard before editing any allowlist:

```bash
grep -rE "actual_set == expected_set|frozen|expected_modules|EXPECTED_" tests/
```

**Orthogonality evidence (sibling precedent).** Three already-tested sibling collaborators
each have a `test_*_helpers.py` AND remain in the coverage omit-allowlist:

- `pr_discovery`
- `ci_check_inspector`
- `ci_fix_orchestrator`

This proves that adding tests to a module does NOT require de-listing it from the omit
allowlist — the two concerns are orthogonal.

**File/line references (#1362, point-in-time — verify by content).**

- Frozen guard: `tests/unit/validation/test_omit_allowlist.py:49-52` (`actual_set == expected_set` over hard-coded `expected_modules`)
- Source list: `pyproject.toml:259-262` (coverage omit-allowlist)

**Three co-update homes of the omit invariant (#1811, point-in-time — RE-GREP, do not trust line numbers).**

1. `pyproject.toml` `[tool.coverage.run].omit` (~line 299-300) — the actual list; the stale entry `"hephaestus/automation/github_api.py"`.
2. `tests/unit/validation/test_omit_allowlist.py` `expected_modules` (~line 57) — the frozen hard-coded copy.
3. `tests/integration/test_orchestration_smoke.py` docstring (~lines 3, 8, 11-16) — a PROSE COUNT: "17 automation modules" → 16, "10 modules lack main()" → 9, and drop `github_api` from the enumeration line. The smoke test derives the module list from `pyproject.toml` at runtime, so this docstring count is documentation that must be hand-synced; it is asserted only indirectly.

Grep-by-content recipe for #1811 (line numbers drift):

```bash
grep -rn "github_api.py" .                       # the stale entry: list + frozen set
grep -rEn "17 automation|modules lack main" tests/  # the prose count home
ls hephaestus/automation/github_api.py           # must fail — file packaged into github_api/
```

**Context.** ProjectHephaestus issue #1362 asked for unit tests covering two untested
methods of `PostMergeProcessor`. The first plan bundled a de-listing of
`hephaestus/automation/post_merge_processor.py` from the omit-allowlist; the re-plan
dropped it after the NOGO. ProjectHephaestus issue #1811 (pipeline foundation layer)
planned to remove the STALE omit entry `hephaestus/automation/github_api.py` — the flat
module became a `github_api/` package — which is load-bearing and requires editing all
three homes above.

**Risks for the reviewer.**

- Both plans were NOT executed (unverified). No pytest/mypy/CI was run for either.
- (#1362) Orthogonality rests on grep-reading the test and config source; the frozen guard was NOT run after the non-change.
- (#1811) The cited line numbers (pyproject.toml:299-300, test_omit_allowlist.py:57, test_orchestration_smoke.py:3/8/11-16) are point-in-time and DRIFT — re-grep by content before editing.
- (#1811) The smoke test's runtime-derived module list vs. the docstring's hardcoded count is an assumption verified by reading the file, but the exact wording ("10 modules lack main()" → "9", dropping `github_api` from that enumeration) must be re-verified against the file at implementation time.
- (#1811) Whether the resulting "16" count is correct end-to-end depends on no other concurrent omit-list edits landing first.

### Related skills

- `doc-comment-count-drift-verify-frozen-test` — verifying frozen counts/sets after a change drifts the pinned value
- `coverage-omit-orchestration-pure-function-testing` — coverage-omit interplay with pure-function test design
- `planning-test-coverage-verify-premise-and-mock-targets` — verifying the "untested" premise and mock targets when planning coverage tasks

## Verified On

| Project | Scenario | Status |
|---------|----------|--------|
| ProjectHephaestus | Issue #1362 re-plan after NOGO | unverified — plan from source reading, guard not run |
| ProjectHephaestus | Issue #1811 remove stale `github_api.py` omit entry (three-home co-update incl. prose count) | unverified — plan from source reading + `ls` ground-state check; no pytest/CI run |
