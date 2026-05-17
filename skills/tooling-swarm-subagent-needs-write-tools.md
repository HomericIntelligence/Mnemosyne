---
name: tooling-swarm-subagent-needs-write-tools
description: "For any swarm sub-agent that must commit/push/edit/create-PR, set subagent_type=general-purpose. feature-dev:code-architect / code-explorer / code-reviewer are read-only by design — they produce blueprints, not code. There is no error at dispatch; agents run 5-10 min then report 'FAILED — no Bash/Write/Edit tools'. Use when: (1) dispatching parallel sub-agents for issue implementation, (2) any agent prompt that includes 'git commit' or 'gh pr create' or file edits, (3) you notice a sub-agent returning detailed file blueprints with diff content but no PR URL, (4) you see 'I do not have shell execution' or similar tool-availability complaint at the end of an agent run."
category: tooling
date: 2026-05-16
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - sub-agent
  - swarm
  - subagent-type
  - tool-availability
  - dispatch
  - myrmidon
  - implementation-vs-design
---

## Overview

| Field | Value |
|---|---|
| Date | 2026-05-16 |
| Objective | Avoid dispatching swarm implementation agents under a read-only subagent_type |
| Outcome | Validated 2026-05-16 — initial MEDIUM Wave 1 misdispatch wasted ~80k tokens on planning-only output; re-dispatch with general-purpose shipped PRs #387-#390 successfully |
| Verification | verified-ci |

## When to Use

- Dispatching parallel sub-agents via the `Agent` tool for issue implementation
- Any agent prompt that includes `git commit`, `git push`, `gh pr create`, `gh issue close`, or any `Write`/`Edit` operation
- You notice a sub-agent returning detailed file-level blueprints with diff content but no PR URL
- An agent's final reply contains phrases like "I do not have shell execution", "available tools don't include Bash", "I can only Read/Grep"
- The subagent_type name **sounds** implementation-y (e.g., "code-architect") but you haven't verified its toolset

## Verified Workflow

### Quick Reference

```text
For implementation work in a swarm:
  subagent_type: "general-purpose"   ✓ has Bash, Write, Edit, full toolset

For research/design only:
  subagent_type: "feature-dev:code-architect"     ← read-only
  subagent_type: "feature-dev:code-explorer"      ← read-only
  subagent_type: "feature-dev:code-reviewer"      ← read-only
  subagent_type: "Explore"                        ← read-only
  subagent_type: "Plan"                           ← read-only
```

### Detailed Steps

1. Before dispatch, read the agent's prompt — if it contains any write action (commit/push/PR/edit/close/label), the subagent must have write tools.
2. Default to `subagent_type: "general-purpose"` (or omit the field entirely; default is implementation-capable).
3. Reserve the `feature-dev:*` subagents and `Explore`/`Plan` for pure research, blueprinting, code review, codebase mapping — phases where output is text/analysis, not file changes.
4. If a misdispatch happens, salvage the blueprint output by passing it as a context block to a `general-purpose` re-dispatch (saves re-analysis cost).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| 1 | Dispatched 4 parallel `feature-dev:code-architect` sub-agents for MEDIUM-tier C++ issue implementation (commit + push + gh pr create) | All 4 produced detailed file-level blueprints with exact line numbers and diff content, ran 5-10 min each, then failed with "I do not have shell execution (Bash) or file write (Write/Edit) tools available in this agent environment" — no PRs created | The subagent description "Designs feature architectures by analyzing existing codebase patterns and conventions, then providing comprehensive implementation blueprints" should have been the tell. "Providing blueprints" ≠ "executing implementation". |
| 2 | Assumed `feature-dev:code-reviewer` would commit review-driven fixes | Same root cause — read-only toolset (`Glob, Grep, LS, Read, NotebookRead, WebFetch, TodoWrite, WebSearch, KillShell, BashOutput`) | The "feature-dev:*" family is consistently read-only by design. Any task that ends with a write action needs `general-purpose`. |

## Results & Parameters

Copy-paste ready dispatch pattern:

```python
# CORRECT for implementation work
Agent(
    description="MED-<N> implement issue",
    subagent_type="general-purpose",   # write-capable
    model="sonnet",                     # or "opus" / "haiku" per tier
    isolation="worktree",
    prompt="""...git commit / push / gh pr create steps..."""
)

# CORRECT for research/design only
Agent(
    description="Design partition plan",
    subagent_type="feature-dev:code-architect",   # read-only — produces a blueprint doc
    model="sonnet",
    prompt="""Read codebase, emit phase4-waves.json with per-issue briefs..."""
)
```

## Verified On

| Project | Context | Details |
|---|---|---|
| ProjectAgamemnon | 2026-05-16 Myrmidon swarm — MEDIUM Wave 1 misdispatch then re-dispatch (PRs #387-#390) | Initial read-only dispatch produced blueprints; re-dispatch with `general-purpose` shipped distinct PRs |
