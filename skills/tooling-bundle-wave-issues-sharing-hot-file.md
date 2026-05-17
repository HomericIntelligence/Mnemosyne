---
name: tooling-bundle-wave-issues-sharing-hot-file
description: "When N swarm-wave issues all target the same file, bundle them into ONE sub-agent that produces N atomic commits in one PR — do NOT dispatch N parallel agents with 'serialize via rebase'. Use when: (1) a wave plan shows 3+ issues sharing a hot file like src/store.cpp / CMakeLists.txt / routes.cpp, (2) the planner's rationale says 'serialize within wave via rebase', (3) you're tempted to fan out N agents and trust them to coordinate, (4) the issues are semantically related (same module, same concern) so a bundle PR title is coherent. Skip when: issues touch disjoint files (parallel is fine — see [[worktree-parallel-agent-execution]] for hardened parallel dispatch)."
category: tooling
date: 2026-05-16
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - swarm
  - wave-planning
  - bundle-pr
  - hot-file
  - atomic-commits
  - bisectability
  - rebase-avoidance
  - myrmidon
---
# Bundle Wave Issues Sharing a Hot File

## Overview

| Field | Value |
| ------ | ----------- |
| **Date** | 2026-05-16 |
| **Objective** | Avoid parallel-agent rebase contention when N issues all target the same file |
| **Outcome** | Validated 2026-05-16 — MEDIUM Wave 2 5-issue store.cpp bundle shipped as PR #392 with 5 atomic commits, zero rebase coordination cost, full bisectability preserved |
| **Verification** | verified-ci |

When a Myrmidon-swarm wave planner produces a group of K issues that all target the **same file**
(e.g., "Wave N: 5 issues touching src/store.cpp, serialize within the wave via rebase"), do NOT
dispatch K parallel agents and trust them to coordinate via rebase. That's the same
parallel-worktree branch-collision pattern at the file level, plus rebase-on-rebase coordination
cost. Instead, **bundle the K issues into ONE Sonnet (or appropriate-tier) agent that produces K
atomic commits on a single branch in a single PR**.

Key distinction from sibling skill [[parallel-subagent-explicit-file-ownership]]: that skill says
"tell each parallel agent which file IT owns to avoid different agents colliding on the SAME file
by accident". This skill says "when N issues are intentionally all targeted at the same file,
don't dispatch N agents at all — bundle to one agent with N commits".

## When to Use

**Bundle when:**

- A wave/sprint plan shows 3+ issues sharing the same hot file (e.g., `src/store.cpp`,
  `CMakeLists.txt`, `routes.cpp`, a single Python module)
- The planner's `rationale` includes phrases like "serialize within wave via rebase" or
  "sequence by dependency"
- You're about to dispatch N parallel `Agent` calls and trust them to git-rebase against each other
- The N issues are semantically coherent enough that one PR title and one reviewer pass makes sense
- The N issues are all per-issue small enough that one Sonnet (or even Haiku) agent can hold all K
  in its context

**Do NOT bundle when:**

- The N issues touch genuinely disjoint files — parallel-per-issue with hardened branch naming is
  faster (see [[worktree-parallel-agent-execution]])
- The bundle would exceed 10 issues (`/ecosystem-wide-easy-sweep-2026-05-12` v2.0.0 caps bundles
  at 10 for reviewer attention)
- An individual issue in the group is high-risk and needs its own PR for isolated rollback

## Verified Workflow

### Quick Reference

```text
For K wave issues sharing the same hot file:

  ONE general-purpose agent
  → K atomic GPG-signed commits (one per issue, in order)
  → ONE branch (unique name per [[worktree-parallel-agent-execution]] v1.3.0)
  → ONE PR with body: "Closes #A. Closes #B. ... Closes #K."

Result: zero rebase coordination, full bisectability via git revert <sha>.
```

### Detailed Steps

1. **Detect the bundle candidate**: scan wave-plan JSON for issues sharing a `target_files` entry.
   If 3+ issues hit one file, that's a bundle.

2. **One agent, one branch**: dispatch a single
   `Agent({subagent_type: "general-purpose", model: "sonnet", isolation: "worktree", prompt: "..."})`.
   The prompt must list all K issues in their intended commit order with per-issue diagnosis +
   approach.

3. **K atomic commits**: each issue gets its own GPG-signed commit
   (`git commit -S -m "<scope>: <summary> (#N)"`). Bisectable via `git revert <sha>`.

4. **PR body uses period-separated Closes**: `Closes #A. Closes #B. Closes #C.` at the top —
   Markdown tables and comma-lists do NOT trigger GitHub auto-close.

5. **Auto-merge after each wave**: `gh pr merge --auto --squash --delete-branch` so CI green =
   merged.

### Copy-Paste Dispatch Pattern

```python
# CORRECT — bundle K issues sharing src/store.cpp into one Sonnet agent
Agent(
    description="MEDIUM Wave 2 — store.cpp 5 issues",
    subagent_type="general-purpose",
    model="sonnet",
    isolation="worktree",
    prompt="""Implement these 5 issues in ONE PR with one signed commit each, on branch medium/store-concurrency-wave2-<date>.

Issue order (each gets a separate commit, K=5):
  #155 — HmasTask thread-safety
  #161 — call_once hydration (no mutex during HTTP)
  #209 — null-json guard in update_task
  #222 — enforce team_id scope on get_task/update_task
  #340 — deterministic pagination via sorted vector

For each: stale-check, implement, run targeted tests, git commit -S -m '<scope>: <summary> (#N)', then push and gh pr create with 'Closes #155. Closes #161. Closes #209. Closes #222. Closes #340.' at top of body. Enable auto-merge.
"""
)
```

### Validation Pattern

```bash
# Confirm all K commits landed on the branch and PR body resolves all K issues
git log --format='%s' origin/medium/store-concurrency-wave2-<date> ^origin/main | grep -oE '#[0-9]+' | sort -u
gh pr view <N> --json closingIssuesReferences --jq '[.closingIssuesReferences[]|.number]|sort'
# Both should produce the same list of K issues.
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| 1 | Initial MEDIUM Wave 1 plan from partitioner: 5 parallel agents on 5 issues, with 2 of them (#182 + #189) both targeting `CMakeLists.txt` | Dispatching 5 parallel agents would have produced the worktree branch-collision pattern between #182 and #189 (same file, rebase race) | Pre-check the wave plan for intra-wave hot-file conflicts. When found, bundle the conflicting subset into one agent before dispatch — don't trust the planner's "rebase within wave" suggestion. |
| 2 | Wave 2 partition plan: 5 parallel agents on 5 store.cpp issues with note "serialize 155→161→209→222→340 within the wave via rebase" | Same risk — 5 agents on one file = 5-way rebase coordination, almost guaranteed to produce silent conflicts or duplicated commits | "Serialize via rebase" is a coordination protocol with N! failure modes when N parallel agents each have to detect the head moved. ONE agent with K commits has 0 failure modes. |

## Results & Parameters

### Evidence (concrete, traceable)

ProjectAgamemnon Myrmidon swarm 2026-05-16, MEDIUM Wave 2:

- Wave planner output: 5 issues (#155, #161, #209, #222, #340) all touching `src/store.cpp` for
  thread-safety + correctness work. Planner rationale: "all touch store.cpp; sequence by rebase
  155 → 161 → 209 → 222 → 340".
- Dispatch decision: bundle into ONE Sonnet `general-purpose` agent producing 5 atomic GPG-signed
  commits in one PR.
- Result: PR #392 opened with 5 commits, auto-merge armed, full bisectability preserved
  (`git revert <sha>` reverts a single issue). Zero rebase coordination needed.
- Per-issue commits: 7f1713f (#155 HmasTask thread-safety), 08b8ef5 (#161 call_once hydration),
  0af9a96 (#209 null-json guard), 5894470 (#222 team_id scope), ee4fec0 (#340 deterministic
  pagination).

Contrast with the earlier SIMPLE Bundle 4/5/6/7 dispatch (4 parallel Haiku agents on disjoint
files) which collapsed into a union PR #386 via the branch-collision pattern documented in
[[worktree-parallel-agent-execution]] v1.3.0. The store-bundle approach pre-empts that risk by
design (no parallel push at all).

## Verified On

| Project | Context | Details |
|---|---|---|
| ProjectAgamemnon | 2026-05-16 Myrmidon swarm MEDIUM Wave 2 — 5 store.cpp issues → PR #392 | Bundled approach shipped 5 atomic commits with zero rebase contention vs. the 5-parallel-agent plan that would have hit the rebase-race pattern documented in [[worktree-parallel-agent-execution]] v1.3.0 |
