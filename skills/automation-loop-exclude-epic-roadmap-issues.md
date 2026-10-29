---
name: automation-loop-exclude-epic-roadmap-issues
license: BSD-3-Clause
description: "Exclude epic and roadmap tracking issues from code-task discovery. Use for label/title filters, explicit issue overrides, worker lanes assigned a bare tracking-issue number, and false positives from titles that merely mention epics."
category: tooling
date: 2026-07-17
version: "1.3.0"
user-invocable: false
verification: verified-ci
tags: [epic, roadmap, tracking-issue, automation-loop, issue-discovery, gh-cli, state-skip, partition, label-and-title-signal, planner-filter, dry-chokepoints, pure-function-contract, worker-lane, pre-flight-gate, coordinator-assignment, worker-ownership-gate, dispatch-gate, zero-mutation-stop]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/automation-loop-exclude-epic-roadmap-issues.history"
history-cleanup-date: "2026-09-20"
---

# Automation Loop: Exclude Epic/Roadmap Tracking Issues from Discovery

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-29 |
| **Objective** | Stop an auto-discovery automation/planning loop from planning + implementing epic/roadmap TRACKING issues (checklists of child work) as if they were code tasks, which produces a wrong code PR |
| **Outcome** | Successful (local) — pure `is_epic`/`partition_epics` helper + filtering at both the loop discovery chokepoint and the standalone planner + idempotent `state:skip` tagging; 2217 automation unit tests pass locally, whole-tree mypy clean, ruff clean |
| **Verification** | verified-local — 2217 unit tests + mypy + ruff clean locally; CI pending on PR #1670 |
| **Source** | ProjectHephaestus issue #1669 / PR #1670 |

> verified-local — 2217 unit tests + mypy + ruff clean locally; CI pending on PR #1670 (not yet verified-ci).

An epic/roadmap issue is a **snapshot of child work** — its body is a checklist, not a spec. If an
auto-discovery loop treats it as a code task, the planner/implementer will fabricate a code change and
open a PR that has nothing to do with the actual (child) work. The fix is to detect tracking issues at
discovery time and exclude them from every path that feeds the planner. A coordinator that assigns a
bare issue number directly to an agent worker lane bypasses these paths; the worker's pre-flight gate
is then the last detection point and must stop the lane with zero writes.

## When to Use

- An auto-discovery automation/planning loop plans an epic/roadmap tracking issue and emits a wrong code PR.
- You are about to design an issue-type filter and reaching for `gh issue list --json issueType`.
- A repo has an `epic`/`roadmap` label convention but it is NOT consistently applied (so label-only detection misses issues).
- You need tracking issues excluded from convergence / open-issue-count gates as well as from planning.
- A loop supports both auto-discovery AND an explicit `--issues` override (both paths must filter).
- A coordinator or operator assigns a bare issue number directly to an agent worker lane — no discovery
  or planner filter sees the target, so the worker's pre-flight gate must catch the tracking container.
- A worker/agent is DISPATCHED against an explicitly named issue (a human or coordinator picked the
  target, bypassing every loop filter) and the named target itself carries the container signals —
  the dispatch text can even cite the same issue as an EXAMPLE of a container while naming it as the
  target. Live issue state outranks dispatch text, however specific the dispatch seems.
- An issue whose title merely MENTIONS epics (a bug report about epic handling, an audit finding) was
  excluded from planning and durably tagged `state:skip` — the anywhere-in-title false positive.

## Verified Workflow

### Quick Reference

```bash
# 1. VERIFY native issue types are unreachable before designing any type filter:
gh issue list --json issueType   # -> "Unknown JSON field: issueType" on the installed gh
# => label + title are the ONLY available signals.

# 2. Detection signal (case-insensitive):
#    epic iff  ('epic' or 'roadmap' in labels)
#          OR  ('epic'/'roadmap' as a standalone token in the first ~3 title words)
#    NEVER match anywhere in the title: a bug report titled "...tags state:skip
#    epic labels on the wrong repo" was excluded and skip-parked by the
#    anywhere-match (Hephaestus #2245, fixed in PR #2253).

# 3. WORKER ownership gate — run BEFORE any mutation when dispatched on an
#    explicitly named issue (the terminal chokepoint when no loop filtered first):
gh issue view <n> --json state,title,labels \
  --jq '{state, title, labels: [.labels[].name]}'
# container iff: OPEN AND ('epic'/'roadmap' in labels OR a leading title marker
#   such as '[epic]:' / 'Epic:' / '[roadmap]'; 'state:skip' corroborates)
# container -> STOP, report the container disposition (e.g. 'owned: epic/meta'),
#   make ZERO mutations: no labels, no comments, no branch, no worktree, no plan,
#   no adoption of the container's children.
```

```python
# Pure helper in the label-vocabulary module (hephaestus/automation/state_labels.py):
_EPIC_TITLE_LEADING_TOKENS = 3  # tracking issues LEAD with the marker

def is_epic(labels: Iterable[str], title: str) -> bool:
    lowered = {label.lower() for label in labels}
    if {"epic", "roadmap"} & lowered:
        return True
    leading = " ".join(title.lower().split()[:_EPIC_TITLE_LEADING_TOKENS])
    return any(
        re.search(rf"(?<![a-z0-9_]){marker}(?![a-z0-9_])", leading)
        for marker in ("epic", "roadmap")
    )

def partition_epics(issues_meta):  # -> (kept, epics)
    kept, epics = [], []
    for meta in issues_meta:
        (epics if is_epic(meta.labels, meta.title) else kept).append(meta)
    return kept, epics
```

### Detailed Steps

1. **Confirm the gh field gap first.** Run `gh issue list --json issueType`. On the installed gh this
   returns `Unknown JSON field: issueType`. Native issue types are not available, so label + title are
   your only signals. Do not design a filter around `issueType`.

2. **Put the detection logic in ONE pure module.** Add `is_epic(labels, title)` and
   `partition_epics(issues_meta) -> (kept, epics)` to the existing label-vocabulary module
   (`hephaestus/automation/state_labels.py`). Both are pure functions — easy to unit test, reused by
   every caller (DRY).

3. **Filter at the loop discovery chokepoint.** In `_list_open_issue_numbers`
   (`hephaestus/automation/loop_repo_manager.py`), change the `gh issue list` JSON projection from
   `number` to `number,labels,title`, JSON-parse the output (do NOT use `--jq` — you need the structured
   fields), call `partition_epics`, and return only the kept numbers. `_count_open_issues` calls this
   same function, so convergence / open-issue gates auto-exclude epics for free.

4. **Filter at the standalone planner too.** In `PlannerStateManager.filter`
   (`hephaestus/automation/planner_state.py`), reuse the already-cached labels plus a NEW batched
   `fetch_all_issue_titles_graphql` (write it as a sibling of `fetch_all_issue_labels_graphql` in
   `review_state.py`). Both paths are required: an explicit `--issues` run bypasses the loop's discovery
   filter (`cfg.issues or _list_open_issue_numbers(...)`), so the planner must filter independently.

5. **Tag excluded epics `state:skip` idempotently — OUTSIDE the pure discovery function.** Add a
   `skip_epics(epics_labels)` helper that guards with `is_skipped` (no-op if already skipped) and reuses
   `gh_issue_add_labels`. Do the tagging best-effort, wrapped in `try/except`, in the CALLER — never
   inside `_list_open_issue_numbers`, which must keep its "return `[]` on any failure, never raise"
   contract. A write that can fail must not be able to break discovery.

6. **Gate at the worker lane — the last chokepoint.** A coordinator can hand a worker lane a bare
   issue number (an epic sibling of the lane's launch epic, a roadmap parent) without any loop or
   planner pass. The lane's pre-flight gate must fetch `gh issue view <N> --json labels,title,state`,
   apply the same `is_epic` rule, and on a match STOP with zero writes — no label, comment, branch,
   worktree, or PR — and report the tracking-container evidence to the coordinator. The coordinator
   re-issues a child issue; the lane must never plan the container itself. This gate complements the
   discovery and planner filters instead of replacing them — the three chokepoints have no shared
   failure cause (P054, defense in depth).
   Live issue state outranks dispatch text, even when the dispatch cites the same issue as an example
   of a container while naming it as the target.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Native issue type | `gh issue list --json issueType` to filter by GitHub issue type | Installed gh returns `Unknown JSON field: issueType` — native types are not exposed by the CLI | Fall back to label + title detection; verify gh field availability BEFORE designing any issue-type filter |
| Label-only detection | Detect epics solely by the `epic`/`roadmap` label | Convention not consistently applied — at the time, 94 open issues and ZERO carried the label | Add a title-substring fallback (`epic`/`roadmap` in the title, case-insensitive) |
| Tag inside pure discovery | Write `state:skip` from inside `_list_open_issue_numbers` | Violates that function's "return `[]` on failure / never raise" contract — a failed label write would break discovery | Keep writes OUT of pure discovery; do best-effort tagging in the caller, wrapped in try/except |
| Anywhere-in-title match | Match `epic`/`roadmap` as a standalone token ANYWHERE in the title | A bug report titled "Multi-repo loop tags state:skip epic labels on the wrong repo" (#2245) was excluded from planning and durably skip-parked; any issue ABOUT epic handling triggers it. Hyphens do not block the token regex, so "roadmap-exclusion" also matches | Tracking issues LEAD with the marker ("Epic: ...", "Q3 Roadmap tracking"); match only within the first ~3 whitespace tokens (Hephaestus PR #2253, verified-ci) |
| Trust the dispatch over live issue state | A single-issue worker dispatched on an explicitly named target proceeds to plan/label/branch because "the coordinator named it" | The dispatch named an OPEN container (`epic` label, `[epic]:` title, `state:skip`) as the work target while itself citing that issue's family as a stop example — an internally contradictory dispatch that only live issue state resolves; proceeding would fabricate plan scope on a checklist, churn labels/comments on the container, create a stray branch/worktree, and can double-plan children another lane owns | The worker ownership gate is the terminal chokepoint (loop filters and explicit overrides are all bypassable by a direct dispatch): classify the named target with `gh issue view` BEFORE any mutation; on container signals stop with zero mutations and report the container disposition |

## Results & Parameters

```text
Detection rule (case-insensitive):
  is_epic = ('epic' or 'roadmap' in labels) OR ('epic' or 'roadmap' substring in title)

Why the title fallback matters: 94 open issues, 0 carried the epic/roadmap label at the time.
Native gh issue types are NOT reachable: `gh issue list --json issueType` -> "Unknown JSON field".

Two filtering chokepoints plus a worker-lane gate, one shared pure helper (DRY):
  hephaestus/automation/state_labels.py
    - is_epic(labels, title) -> bool                 # pure
    - partition_epics(issues_meta) -> (kept, epics)  # pure
    - skip_epics(epics_labels)                       # idempotent write; guards via is_skipped,
                                                     #   reuses gh_issue_add_labels

  hephaestus/automation/loop_repo_manager.py
    - _list_open_issue_numbers: gh issue list --json number,labels,title  (JSON-parse, NOT --jq)
        -> partition_epics -> return kept numbers
        -> MUST keep "return [] on any failure, never raise" contract
        -> skip_epics tagging done best-effort in the CALLER, wrapped try/except
    - _count_open_issues calls _list_open_issue_numbers -> convergence/open-issue gates auto-exclude epics

  hephaestus/automation/planner_state.py
    - PlannerStateManager.filter: reuse cached labels + NEW fetch_all_issue_titles_graphql
        (sibling of fetch_all_issue_labels_graphql in review_state.py)
    - Needed because explicit `--issues` runs bypass loop discovery:
        cfg.issues or _list_open_issue_numbers(...)

  worker-lane pre-flight gate (third chokepoint):
    - gh issue view <N> --json labels,title,state -> same is_epic rule
    - epic match -> STOP with zero writes; report tracking-container evidence
    - catches coordinator-direct assignments that bypass discovery + planner filters
    - live issue state outranks dispatch text, even when the text cites container examples itself

Verification (local only): 2217 automation unit tests pass; whole-tree mypy clean; ruff clean.
CI on PR #1670 still pending -> NOT verified-ci.
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1669 / PR #1670 — exclude epic/roadmap tracking issues from the automation discovery + planner loop | 2217 unit tests + mypy + ruff clean locally; CI pending |
| Model-serving-fleet repository (generalized) | A worker lane was assigned the sibling epic of its release-campaign launch epic as a bare single-issue target; the lane's pre-flight gate found the `epic` label, `[epic]` title prefix, and tracked-child checklist, then stopped with zero forge/git writes (2026-10) | Third chokepoint validated in operation; gate lived in the lane's assignment instructions — no code change required |
| Fleet single-issue worker dispatch | Worker dispatched on an explicitly named issue whose live state was OPEN + `epic` label + `[epic]:` title + `state:skip`; the dispatch text itself cited that container family as the stop condition | Verified-local — the `gh issue view --json state,title,labels` read executed and returned the cited signals; the worker stopped at the ownership gate with zero mutations (no labels, comments, branch, or worktree) and reported the container disposition |
