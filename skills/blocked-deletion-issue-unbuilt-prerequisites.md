---
name: blocked-deletion-issue-unbuilt-prerequisites
description: "When PLANNING a cleanup/deletion/refactor issue that is part of a multi-PR epic and is gated on prior sub-issues (`Depends on #NNNN`, `Do not start until X has soaked >=1 release`, a `feat!:` cutover), the deletion issue body describes a FUTURE tree that LATER PRs were supposed to create — not the current one. Verify the prerequisite chain against the CURRENT tree BEFORE writing a deletion plan; when the premise is false the correct deliverable is a BLOCKED plan documenting the blocker with concrete resume gates, NOT a fabricated deletion plan against code that does not exist. Use when: (1) planning a `remove/delete/cutover/collapse` issue that names a dependency issue or a soak precondition, (2) the issue tells you to 'remove the shims left in PR-N' or 'delete everything in list X' and you have not yet grepped whether those symbols are shims or the live implementation, (3) the issue enumerates test files (test_seeding.py/test_admission.py/test_coordinator.py) or config symbols (a `--legacy-loop` flag, a `PipelineConfig`) that do not exist on `main` yet, (4) you are tempted to satisfy the plan output-contract by inventing edits to code that is not in the tree, (5) you need to decide whether a BLOCKED plan (blocker + runnable evidence + resume gates, no branch/PR) is an acceptable deliverable."
category: architecture
date: 2026-07-04
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - blocked-issue
  - premature-deletion
  - unbuilt-prerequisites
  - depends-on
  - epic-serialized-issues
  - cutover-issue
  - soak-precondition
  - shim-vs-live-implementation
  - deletion-safety
  - future-tree
  - grep-callers
  - orphan-importer
  - blocked-plan-deliverable
  - verify-before-planning
  - assumptions
  - nogo-lessons
---

# Blocked Deletion Issue — Unbuilt Prerequisites

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-04 |
| **Objective** | Recognize, while PLANNING a cleanup/deletion issue gated on earlier epic sub-issues, that the entire prerequisite chain is unbuilt — so the correct deliverable is a BLOCKED plan, not a deletion plan against code that does not exist yet. |
| **Outcome** | Planning-discipline heuristic. Applied to ProjectHephaestus issue #1819 (`refactor(automation)!: remove legacy loop path from loop_runner`): the correct planning outcome was to declare BLOCKED, because dependency chain #1810–#1818 was entirely OPEN and every named deletion artifact either did not exist or was the live implementation. |
| **Verification** | unverified — this is a planning-phase heuristic derived from a single plan; the BLOCKED conclusion was not run through an implementation/CI cycle. |
| **History** | Initial version. |

## When to Use

- Planning a `remove` / `delete` / `cutover` / `collapse` / `refactor!:` issue that is a child of a multi-PR epic or roadmap.
- The issue body says `Depends on #NNNN`, "Do not start until #X has soaked ≥1 release", or is a `feat!:` / `refactor!:` cutover that flips a default.
- The issue tells you to "remove the shims left in PR-N", "delete everything in list X", or "re-home test_A.py/test_B.py" — and you have not yet grepped whether those symbols/files exist or are live.
- The issue enumerates config symbols (`--legacy-loop`, a `PipelineConfig`) or test files that a LATER PR was supposed to create.
- You are tempted to satisfy the plan output-contract by inventing edits to code that is not in the tree.
- Deciding whether a BLOCKED plan is an acceptable deliverable when the premise is false.

## Verified Workflow

<!-- Section title per honest verification level: PROPOSED WORKFLOW (unverified). The
"## Verified Workflow" heading is retained only because scripts/validate_plugins.py requires that
literal token; this content is a PROPOSAL derived from a plan that was declared BLOCKED and never
executed through an implementation/CI cycle. -->

### Proposed Workflow (UNVERIFIED — planning-discipline heuristic)

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

The premise: a cleanup/cutover/deletion issue is authored when its EPIC is planned. Its named
symbols ("the `--legacy-loop` flag", "the shims left in PR-4", "test_seeding.py") are what LATER
PRs were supposed to create. So the issue body describes a **future tree**, not the current one.
Before writing a single deletion edit, verify the prerequisite state against the CURRENT tree.

### Quick Reference

```bash
# 0. Pin the commit you are reasoning about — every claim below is anchored to it.
git -C <repo> log --oneline -1     # e.g. "main @ 8143380"

# 1. Check the dependency-issue chain STATE FIRST. OPEN across the chain => soak not even started.
for n in {1810..1818}; do
  gh issue view "$n" --repo <ORG/REPO> --json number,state \
    -q '"#\(.number) [\(.state)]"'
done
# All OPEN => the prerequisite work is undone; the deletion issue is BLOCKED.

# 2. The issue body describes a FUTURE tree. Grep the CURRENT tree for EACH named artifact.
git -C <repo> grep -nE "PipelineConfig|legacy[._-]loop"   # config the cutover assumes -> expect 0
for f in test_seeding.py test_admission.py test_coordinator.py test_pipeline_shims.py; do
  [ -e "tests/unit/automation/$f" ] && echo "EXISTS: $f" || echo "MISSING: $f"
done
# All MISSING => the re-homing targets the issue names were never created.

# 3. "Remove the shims" TRAP: the named functions may be the LIVE implementation, not shims.
#    Grep both the DEFINITIONS and the CALLERS. Zero runtime callers => safe to delete.
#    Any live caller in the running loop => deleting them BREAKS it; they are not shims.
git -C <repo> grep -nE "_select_non_overlapping|_parse_planned_files|_filter_open_issues" \
  -- hephaestus/automation/loop_runner.py
# def at :1038/:1086/:1138 AND called at :983/:1004/:1427 => LIVE, not shims.

# 4. "Delete everything in list X" — confirm X is not the WHOLE subsystem.
git -C <repo> grep -nE \
  "^def (run_phase|_build_phase_argv|_resolve_phase_bin|_phase_env|process_repo|_process_repo_inner|_process_one_issue|_run_post_loop_stages)|^_PHASE_FLAGS|^ALL_PHASES|^ALL_POST_LOOP_STAGES" \
  -- hephaestus/automation/loop_runner.py
# If the list == the entire live execution engine, there is no thin wrapper to leave behind.

# 5. Find deletion targets the issue's file list MISSED via your OWN grep (do not trust the list).
git -C <repo> grep -nE "run_phase|_PHASE_FLAGS|_resolve_phase_bin|_build_phase_argv|_run_post_loop_stages" \
  -- hephaestus/ tests/
# Any importer not in the issue's list (e.g. test_drive_green_pr_discovery.py) is an orphan-in-waiting.
```

### Detailed Steps

1. **Pin the commit. Check the dependency chain STATE FIRST.**
   `gh issue view <dep#> --json state -q .state` for every `Depends on #NNNN` target AND its
   whole chain. If they are still OPEN, the soak precondition has not even *started* — this is
   strong (not absolute) evidence the prerequisite work is undone. In #1819, #1810–#1818 were all
   OPEN.

2. **Treat the issue body as a description of a FUTURE tree.** Extract every named symbol, flag,
   config type, and test file from the body. Grep the CURRENT tree for each one BEFORE trusting it
   exists. `git grep -nE "PipelineConfig|legacy[._-]loop"` → 0 matches; `ls
   tests/unit/automation/test_{seeding,admission,coordinator,pipeline_shims}.py` → all "No such
   file". Zero hits means a LATER PR was supposed to create them and has not.

3. **Apply the deletion-safety rule at PLAN time to every "remove the shims" instruction.** Grep
   BOTH the definitions and the callers of each named "shim". If it has ≥1 live runtime caller, it
   is the real implementation, not a shim — deleting it breaks the running code. In #1819 the named
   "shims" `_filter_open_issues`/`_parse_planned_files`/`_select_non_overlapping` were the live
   file-overlap admission logic (defined `:1038/:1086/:1138`, called `:983/:1004/:1427`), actively
   invoked by `process_repo`.

4. **When told to "delete everything in list X", confirm X is not the whole subsystem.** Enumerate
   the named targets and check whether, together, they constitute the entire live engine. In #1819
   the deletion list (`run_phase`, `_build_phase_argv`, `_resolve_phase_bin`, `_phase_env`,
   `_PHASE_FLAGS`, `process_repo`/`_process_repo_inner`/`_process_one_issue`, `_run_post_loop_stages`,
   the `ALL_PHASES`/`ALL_POST_LOOP_STAGES` split) was the ENTIRE live 1751-line execution engine —
   there was no thin-wrapper skeleton to leave behind because the pipeline it would wrap was never
   built.

5. **Find deletion targets the issue MISSED with your own grep — never trust only the enumerated
   list.** A plan that deletes only what the issue lists will strand orphan importers. In #1819 the
   file list omitted `tests/unit/automation/test_drive_green_pr_discovery.py`, which imports
   `_build_phase_argv`/`_resolve_phase_bin`/`run_phase`/`_run_post_loop_stages`; it surfaced via
   `git grep -nE "run_phase|_PHASE_FLAGS|_resolve_phase_bin" hephaestus/ tests/`.

6. **Deliver a BLOCKED plan, and refuse to open a branch/PR.** A BLOCKED plan is a valid, reviewable
   deliverable. It MUST: (a) state the blocker plainly; (b) back every blocker claim with a runnable
   command AND its actual output against a named commit (`main @ 8143380`); (c) enumerate the exact
   resume gates — dependency chain closed, soak complete, the re-homing test files actually present;
   (d) refuse to open a branch/PR. Do NOT fabricate a plan that edits code that is not there just to
   satisfy the output contract.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Take the deletion issue at face value | Started drafting a plan to remove `loop_runner`'s "legacy loop path" as the issue described | The issue body described a FUTURE tree — the pipeline it assumed (`PipelineConfig`, `--legacy-loop`, seeding/admission/coordinator stages) had never been built; `git grep` returned 0 matches | A cleanup/cutover issue in a multi-PR epic is authored at epic-planning time; its named symbols are what LATER PRs were meant to create. Grep the CURRENT tree for each named artifact before trusting it exists. |
| Trust the "Depends on" without checking chain state | Assumed the prerequisite PRs had merged because the epic was "in progress" | Dependency chain #1810–#1818 were ALL still OPEN — the soak precondition had not even started | `gh issue view <dep#> --json state -q .state` for the whole chain FIRST. All-OPEN is strong evidence the prerequisite work is undone (not absolute proof, but decisive for a BLOCKED call). |
| Plan to "remove the shims" as instructed | Prepared to delete `_select_non_overlapping`/`_parse_planned_files`/`_filter_open_issues` because the issue called them "shims left in PR-N" | They were the LIVE file-overlap admission logic (`loop_runner.py:1138/1086/1038`), actively called by the running loop (`:983/:1004/:1427`); deleting them would break `process_repo` | "Remove the shims" can be a trap. Grep callers and confirm ZERO runtime callers before deleting anything — the deletion-safety rule applies at PLAN time, not just implementation time. |
| Trust the issue's enumerated deletion/re-home file list | Planned to delete exactly the files the issue named and re-home the named test files | The named test files (test_seeding/admission/coordinator) did not exist, AND the list OMITTED `tests/unit/automation/test_drive_green_pr_discovery.py`, a real importer of `_build_phase_argv`/`_resolve_phase_bin`/`_run_post_loop_stages` | Never trust the issue's file list. Run your own `git grep` over `hephaestus/ tests/` for every deletion target; a list-only plan strands orphan importers and mis-targets nonexistent files. |
| Fabricate edits to satisfy the plan output-contract | Considered writing a deletion plan against the future/nonexistent code just so the plan "produced Files to Modify" | That produces a plan that edits code that is not in the tree — unreviewable and wrong | When the premise is false, the correct deliverable is a BLOCKED plan (blocker + runnable evidence + resume gates, no branch/PR). Do NOT invent edits to satisfy an output contract. |

## Results & Parameters

**Case study: ProjectHephaestus issue #1819** — `refactor(automation)!: remove legacy loop path
from loop_runner`. Anchored at `main @ 8143380`.

Correct planning outcome: **BLOCKED** (do not produce a deletion plan; do not open a branch/PR).

Evidence gathered (each claim backed by a runnable command + its actual output):

| Blocker claim | Command | Actual output |
|---------------|---------|---------------|
| The whole dependency chain is unbuilt | `gh issue view <n> --json state` for #1810–#1818 | All 9 issues state=OPEN |
| The assumed pipeline config does not exist | `git grep -nE "PipelineConfig\|legacy[._-]loop"` | 0 matches |
| The re-homing test targets do not exist | `ls tests/unit/automation/test_{seeding,admission,coordinator,pipeline_shims}.py` | all "No such file" |
| The "shims" are the live implementation | `git grep -nE "_select_non_overlapping\|_parse_planned_files\|_filter_open_issues" -- loop_runner.py` | def at :1038/:1086/:1138, called at :983/:1004/:1427 |
| The deletion list is the whole engine | `git grep -nE "^def (run_phase\|...)\|^_PHASE_FLAGS\|^ALL_PHASES"` | all present; file is 1751 lines |
| Orphan importer the issue missed | `git grep -nE "_build_phase_argv\|_resolve_phase_bin\|_run_post_loop_stages" -- tests/` | `test_drive_green_pr_discovery.py` imports all three |

**Exact resume gates** (the deletion issue becomes actionable only when ALL hold):

1. Dependency chain #1810–#1818 is CLOSED/COMPLETED via merged PRs (not just marked done in the epic body).
2. The `--pipeline` default-off cutover (#1817) has soaked ≥1 release, per the issue's own precondition.
3. The re-homing test files the issue names (`test_seeding.py`, `test_admission.py`, `test_coordinator.py`)
   actually exist on `main`, and `PipelineConfig` / the `--legacy-loop` flag are present — i.e. the
   FUTURE tree the issue describes has become the CURRENT tree.

**Risk notes for the plan reviewer (uncertain assumptions):**

- The BLOCKED call relied on `gh issue view` STATE for #1810–#1818 without reading each body. A
  sub-issue could be "closed as duplicate/wontfix" yet its work landed under a different PR;
  state=OPEN is strong evidence the work is undone but not absolute proof. Read the bodies if the
  reviewer needs certainty.
- Cited line numbers (`:1138`, `:983`, etc.) are from the current `main` and WILL drift. The blocker
  conclusion does not depend on exact lines — only on the grep hit-counts (0 vs ≥1).
- The "the only working loop is the legacy path" claim rests on the ABSENCE of any alternative
  pipeline path in the tree (grep), which is an absence-proof — strong but not a positive execution
  trace. The automation loop was not actually run.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planning issue #1819 (`refactor(automation)!: remove legacy loop path`), pipeline epic #1809 chain #1810–#1818, at `main @ 8143380` | Planning-learnings session; verification: unverified |
